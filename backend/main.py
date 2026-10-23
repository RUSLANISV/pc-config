"""HTTP-интерфейс конфигуратора ПК."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import APIError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.ai_service import handle_ai_cot_request, handle_ai_request
from backend.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    register_user,
)
from backend.build_service import get_user_build, validate_build
from backend.db import Base, engine, get_db
from backend.db1 import Base1, engine1, get_db1
from backend.models import AIRequestChat, Build, Component, User
from backend.schemas import (
    AIHistory,
    AIRequestCreate,
    AIRequestResponse,
    BuildCreate,
    BuildOut,
    ComponentOut,
    FinalAnswer,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Создать отсутствующие таблицы при запуске сервера."""
    Base.metadata.create_all(bind=engine)
    Base1.metadata.create_all(bind=engine1)
    yield


app = FastAPI(title="Конфигуратор ПК", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/register")
def register(user: UserCreate, db: Annotated[Session, Depends(get_db)]) -> UserOut:
    """Зарегистрировать пользователя."""
    return UserOut.model_validate(register_user(db, user))


@app.post("/login")
def login(data: UserLogin, db: Annotated[Session, Depends(get_db)]) -> Token:
    """Проверить пароль и выдать токен."""
    user = authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(status_code=400, detail="Неверные данные")
    return Token(access_token=create_access_token({"sub": user.email}))


@app.get("/me")
def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    """Вернуть данные текущего пользователя."""
    return UserOut.model_validate(user)


@app.post("/ai")
def create_ai_request(
    request: AIRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AIRequestResponse:
    """Получить ответ ИИ и сохранить его в истории."""
    try:
        answer = handle_ai_request(request.query, user.id)
    except (APIError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail="ИИ-сервис не смог ответить. Попробуйте позже."
        ) from exc
    row = AIRequestChat(
        user_id=user.id,
        request_text=request.query,
        response_text=answer,
        created_at=datetime.now(UTC),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AIRequestResponse(
        id=row.id,
        query=request.query,
        response=answer,
        timestamp=row.created_at,
    )


@app.post("/ai_cot")
def ai_chain_of_thought(
    request: AIRequestCreate,
    db: Annotated[Session, Depends(get_db1)],
    _user: Annotated[User, Depends(get_current_user)],
) -> FinalAnswer:
    """Подобрать сборку из каталога с помощью ИИ."""
    try:
        return handle_ai_cot_request(request.query, db)
    except (APIError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail="ИИ-сервис не смог подобрать сборку."
        ) from exc


@app.get("/history")
def get_ai_history(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[AIHistory]:
    """Вернуть последние сто запросов текущего пользователя."""
    rows = db.scalars(
        select(AIRequestChat)
        .where(AIRequestChat.user_id == user.id)
        .order_by(AIRequestChat.created_at.desc(), AIRequestChat.id.desc())
        .limit(100)
    )
    result = []
    for row in rows:
        item = AIHistory.model_validate(row)
        result.append(item)
    return result


@app.get("/search_components")
def search_components(
    query: str,
    db: Annotated[Session, Depends(get_db1)],
    component_type: Annotated[str | None, Query(alias="type")] = None,
) -> list[ComponentOut]:
    """Найти комплектующие по названию и необязательному типу."""
    stmt = select(Component).where(Component.name.ilike(f"%{query}%"))
    if component_type is not None:
        stmt = stmt.where(Component.type == component_type)
    result = []
    for part in db.scalars(stmt.order_by(Component.id)):
        item = ComponentOut.model_validate(part)
        result.append(item)
    if not result:
        raise HTTPException(status_code=404, detail="Ничего не найдено")
    return result


@app.post("/builds")
def create_build(
    data: BuildCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuildOut:
    """Сохранить новую сборку пользователя."""
    validate_build(data)
    build = Build(name=data.name.strip(), components=data.components, user_id=user.id)
    db.add(build)
    db.commit()
    db.refresh(build)
    return BuildOut.model_validate(build)


@app.get("/builds/{build_id}")
def get_build(
    build_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuildOut:
    """Получить свою сборку по идентификатору."""
    return BuildOut.model_validate(get_user_build(db, build_id, user.id))


@app.put("/builds/{build_id}")
def update_build(
    build_id: int,
    data: BuildCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuildOut:
    """Обновить название и комплектующие своей сборки."""
    build = get_user_build(db, build_id, user.id)
    validate_build(data)
    build.name = data.name.strip()
    build.components = data.components
    db.commit()
    db.refresh(build)
    return BuildOut.model_validate(build)


@app.get("/userbuilds")
def get_builds(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[BuildOut]:
    """Вернуть последние двадцать сборок пользователя."""
    rows = db.scalars(
        select(Build)
        .where(Build.user_id == user.id)
        .order_by(Build.id.desc())
        .limit(20)
    )
    result = []
    for build in rows:
        item = BuildOut.model_validate(build)
        result.append(item)
    return result


@app.delete("/builds/{build_id}")
def delete_build(
    build_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Удалить свою сборку."""
    build = get_user_build(db, build_id, user.id)
    db.delete(build)
    db.commit()
    return {"status": "success", "message": "Build deleted"}
