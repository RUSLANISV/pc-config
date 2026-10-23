"""Подключение к базе аккаунтов и сборок."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.settings import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Общая основа таблиц пользовательских данных."""


def get_db() -> Iterator[Session]:
    """Открыть сессию пользовательской базы на время запроса."""
    with SessionLocal() as db:
        yield db
