"""Изолированные базы и подмена внешнего ИИ для тестов."""

from collections.abc import Callable, Iterator
from secrets import token_urlsafe

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import OpenAI
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend import ai_service, main
from backend.auth_service import create_access_token, get_password_hash
from backend.db import Base, get_db
from backend.db1 import Base1, get_db1
from backend.models import Build, Component, User


@pytest.fixture
def engine() -> Iterator[Engine]:
    """Создать отдельную базу в памяти для каждого теста."""
    value = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(value)
    Base1.metadata.create_all(value)
    yield value
    value.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """Открыть сессию тестовой базы."""
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="session")
def password() -> str:
    """Вернуть пароль, используемый только в тестах."""
    return "local-test-password"


@pytest.fixture(scope="session")
def hashed(password: str) -> str:
    """Один раз посчитать хеш тестового пароля."""
    return get_password_hash(password)


@pytest.fixture
def user(db: Session, hashed: str) -> User:
    """Добавить владельца тестовой сборки."""
    value = User(
        username="student", email="student@example.com", hashed_password=hashed
    )
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@pytest.fixture
def other_user(db: Session, hashed: str) -> User:
    """Добавить пользователя без доступа к чужим данным."""
    value = User(username="other", email="other@example.com", hashed_password=hashed)
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@pytest.fixture
def auth(user: User) -> dict[str, str]:
    """Подготовить заголовок авторизации владельца."""
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def build(db: Session, user: User) -> Build:
    """Сохранить сборку владельца."""
    value = Build(
        name="Рабочий ПК",
        components={"cpu": {"id": 1, "name": "Intel", "price": 10000, "type": "cpu"}},
        user_id=user.id,
    )
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@pytest.fixture
def catalog(db: Session) -> list[Component]:
    """Добавить два комплектующих разных типов."""
    parts = [
        Component(name="Intel Core", price=10000, type="cpu", description="Процессор"),
        Component(name="Intel Arc", price=20000, type="gpu", description="Видеокарта"),
    ]
    db.add_all(parts)
    db.commit()
    return parts


@pytest.fixture
def client(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Запустить API с подключением только к тестовой базе."""
    factory = sessionmaker(bind=engine)

    def get_session() -> Iterator[Session]:
        with factory() as session:
            yield session

    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main, "engine1", engine)
    main.app.dependency_overrides[get_db] = get_session
    main.app.dependency_overrides[get_db1] = get_session
    ai_service.user_messages.clear()
    try:
        with TestClient(main.app) as value:
            yield value
    finally:
        main.app.dependency_overrides.clear()
        ai_service.user_messages.clear()


@pytest.fixture
def requests() -> list[httpx.Request]:
    """Сохранить HTTP-запросы, отправленные в подменённый ИИ."""
    return []


@pytest.fixture
def ai_mock(
    monkeypatch: pytest.MonkeyPatch,
    requests: list[httpx.Request],
) -> Callable[[dict[str, object], int], None]:
    """Настроить настоящий SDK на локальный HTTP-ответ без сети."""

    def configure(payload: dict[str, object], code: int) -> None:
        def handle(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(code, json=payload)

        def get_client() -> OpenAI:
            return OpenAI(
                api_key=token_urlsafe(16),
                base_url="https://ai.example.test/v1",
                http_client=httpx.Client(transport=httpx.MockTransport(handle)),
                max_retries=0,
            )

        monkeypatch.setattr(ai_service, "get_client", get_client)

    return configure
