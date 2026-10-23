"""Подключение к каталогу комплектующих."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.settings import CATALOG_URL

engine1 = create_engine(CATALOG_URL, connect_args={"check_same_thread": False})
SessionLocal1 = sessionmaker(autoflush=False, bind=engine1)


class Base1(DeclarativeBase):
    """Общая основа таблиц каталога."""


def get_db1() -> Iterator[Session]:
    """Открыть сессию каталога на время запроса."""
    with SessionLocal1() as db:
        yield db
