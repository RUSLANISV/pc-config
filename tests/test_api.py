"""Проверки HTTP-сценариев сайта на отдельной базе."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.auth_service import create_access_token
from backend.models import AIRequestChat, Build, User


def test_register_api(client: TestClient, password: str) -> None:
    """Регистрация возвращает только публичные данные."""
    data = {"username": "new", "email": "new@example.com", "password": password}

    result = client.post("/register", json=data)

    assert result.status_code == HTTPStatus.OK
    assert result.json()["email"] == data["email"]
    assert "password" not in result.json()
    assert "hashed_password" not in result.json()


def test_register_api_duplicate(client: TestClient, user: User, password: str) -> None:
    """Регистрация занятого адреса возвращает ошибку."""
    data = {"username": "new", "email": user.email, "password": password}

    result = client.post("/register", json=data)

    assert result.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("valid", [True, False])
def test_login_api(
    client: TestClient, user: User, password: str, *, valid: bool
) -> None:
    """Вход выдаёт токен только при правильных данных."""
    data = {"email": user.email, "password": password if valid else "wrong"}

    result = client.post("/login", json=data)

    expected_type = "bearer"
    expected = HTTPStatus.OK if valid else HTTPStatus.BAD_REQUEST
    assert result.status_code == expected
    if valid:
        assert result.json()["token_type"] == expected_type
        assert result.json()["access_token"]


def test_profile(client: TestClient, auth: dict[str, str], user: User) -> None:
    """Профиль соответствует токену."""
    headers = auth

    result = client.get("/me", headers=headers)

    assert result.status_code == HTTPStatus.OK
    assert result.json()["id"] == user.id


@pytest.mark.parametrize("path", ["/me", "/history", "/userbuilds"])
def test_private_routes_require_token(client: TestClient, path: str) -> None:
    """Личные данные не выдаются без входа."""
    url = path

    result = client.get(url)

    assert result.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.usefixtures("catalog")
@pytest.mark.parametrize(("query", "expected"), [("intel", 2), ("Core", 1)])
def test_search(client: TestClient, query: str, expected: int) -> None:
    """Поиск находит названия целиком и по части."""
    params = {"query": query}

    result = client.get("/search_components", params=params)

    assert result.status_code == HTTPStatus.OK
    assert len(result.json()) == expected


@pytest.mark.usefixtures("catalog")
def test_search_type(client: TestClient) -> None:
    """Фильтр типа исключает детали другой категории."""
    params = {"query": "Intel", "type": "gpu"}

    result = client.get("/search_components", params=params)

    assert result.status_code == HTTPStatus.OK
    assert [part["type"] for part in result.json()] == ["gpu"]


def test_search_missing(client: TestClient) -> None:
    """Отсутствие совпадений возвращает 404."""
    params = {"query": "missing"}

    result = client.get("/search_components", params=params)

    assert result.status_code == HTTPStatus.NOT_FOUND


def test_create_build(
    client: TestClient, auth: dict[str, str], user: User, db: Session
) -> None:
    """Сборка сохраняется с владельцем из токена."""
    data = {"name": " Новый ПК ", "components": {"cpu": {"id": 1, "price": 10000}}}

    result = client.post("/builds", headers=auth, json=data)

    assert result.status_code == HTTPStatus.OK
    assert result.json()["name"] == "Новый ПК"
    assert result.json()["user_id"] == user.id
    assert db.get(Build, result.json()["id"]) is not None


def test_create_invalid_build(client: TestClient, auth: dict[str, str]) -> None:
    """Пустая сборка не сохраняется."""
    data = {"name": "ПК", "components": {}}

    result = client.post("/builds", headers=auth, json=data)

    assert result.status_code == HTTPStatus.BAD_REQUEST


def test_read_build(client: TestClient, auth: dict[str, str], build: Build) -> None:
    """API возвращает сохранённые детали сборки."""
    url = f"/builds/{build.id}"

    result = client.get(url, headers=auth)

    assert result.status_code == HTTPStatus.OK
    assert result.json()["components"] == build.components


def test_update_build(
    client: TestClient, auth: dict[str, str], build: Build, db: Session
) -> None:
    """Редактирование обновляет существующую запись."""
    url = f"/builds/{build.id}"
    data = {"name": "Обновлённый ПК", "components": {"gpu": {"id": 2}}}

    result = client.put(url, headers=auth, json=data)

    db.refresh(build)
    assert result.status_code == HTTPStatus.OK
    assert build.name == data["name"]
    assert build.components == data["components"]


def test_update_invalid_build(
    client: TestClient, auth: dict[str, str], build: Build, db: Session
) -> None:
    """Ошибочные изменения не перезаписывают сборку."""
    url = f"/builds/{build.id}"
    old = build.name
    data = {"name": " ", "components": {"cpu": {"id": 1}}}

    result = client.put(url, headers=auth, json=data)

    db.refresh(build)
    assert result.status_code == HTTPStatus.BAD_REQUEST
    assert build.name == old


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_foreign_build_denied(
    client: TestClient, build: Build, other_user: User, method: str
) -> None:
    """Чужую сборку нельзя прочитать, изменить или удалить."""
    token = create_access_token({"sub": other_user.email})
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Чужая", "components": {"cpu": {"id": 1}}}

    result = client.request(method, f"/builds/{build.id}", headers=headers, json=data)

    assert result.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_missing_build(client: TestClient, auth: dict[str, str], method: str) -> None:
    """Операции с отсутствующей сборкой возвращают 404."""
    data = {"name": "ПК", "components": {"cpu": {"id": 1}}}

    result = client.request(method, "/builds/999", headers=auth, json=data)

    assert result.status_code == HTTPStatus.NOT_FOUND


def test_delete_build(
    client: TestClient, auth: dict[str, str], build: Build, db: Session
) -> None:
    """Удаление убирает запись из базы."""
    build_id = build.id

    result = client.delete(f"/builds/{build_id}", headers=auth)

    db.expire_all()
    assert result.status_code == HTTPStatus.OK
    assert db.get(Build, build_id) is None


@pytest.mark.parametrize("with_build", [True, False])
def test_build_list(
    client: TestClient,
    db: Session,
    user: User,
    other_user: User,
    *,
    with_build: bool,
) -> None:
    """Список содержит только свои сборки, в том числе бывает пустым."""
    db.add(Build(name="Чужая", components={}, user_id=other_user.id))
    if with_build:
        db.add(Build(name="Своя", components={}, user_id=user.id))
    db.commit()
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    result = client.get("/userbuilds", headers=headers)

    expected = ["Своя"] if with_build else []
    assert result.status_code == HTTPStatus.OK
    assert [item["name"] for item in result.json()] == expected


@pytest.mark.parametrize("with_history", [True, False])
def test_history_is_private(
    client: TestClient,
    db: Session,
    user: User,
    other_user: User,
    *,
    with_history: bool,
) -> None:
    """История показывает только сообщения текущего пользователя."""
    db.add(
        AIRequestChat(user_id=other_user.id, request_text="Чужое", response_text="Нет")
    )
    if with_history:
        db.add(AIRequestChat(user_id=user.id, request_text="Моё", response_text="Да"))
    db.commit()
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    result = client.get("/history", headers=headers)

    expected = ["Моё"] if with_history else []
    assert result.status_code == HTTPStatus.OK
    assert [item["request_text"] for item in result.json()] == expected


@pytest.mark.parametrize("origin", ["http://localhost:3000", "http://unknown.test"])
def test_cors(client: TestClient, origin: str) -> None:
    """Браузерные запросы разрешены только локальному интерфейсу."""
    headers = {"Origin": origin, "Access-Control-Request-Method": "POST"}

    result = client.options("/login", headers=headers)

    allowed = result.headers.get("access-control-allow-origin")
    assert (allowed == origin) == (origin == "http://localhost:3000")
