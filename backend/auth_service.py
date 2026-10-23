"""Регистрация, проверка паролей и авторизация."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import User
from backend.schemas import UserCreate
from backend.settings import SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_PASSWORD_BYTES = 72


def verify_password(password: str, hashed: str) -> bool:
    """Проверить пароль по сохранённому bcrypt-хешу."""
    if len(password.encode()) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Создать bcrypt-хеш пароля."""
    if not password or len(password.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Найти пользователя и проверить его пароль."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict[str, str]) -> str:
    """Выпустить подписанный токен на один час."""
    payload: dict[str, str | int] = dict(data)
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = int(expire.timestamp())
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def register_user(db: Session, data: UserCreate) -> User:
    """Создать аккаунт с уникальными именем и почтой."""
    user = db.scalar(
        select(User).where(
            or_(User.email == data.email, User.username == data.username)
        )
    )
    if user is not None:
        raise HTTPException(status_code=400, detail="Имя или почта уже заняты")
    try:
        hashed = get_password_hash(data.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Пароль: от 1 до 72 байт") from exc
    user = User(username=data.username, email=data.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Получить пользователя по действующему токену."""
    error = HTTPException(
        status_code=401,
        detail="Невалидный токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise error from exc
    email = payload.get("sub")
    if not isinstance(email, str):
        raise error
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise error
    return user
