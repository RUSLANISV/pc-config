"""Таблицы пользователей, сборок, истории и каталога."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base
from backend.db1 import Base1
from backend.schemas import Parts


class User(Base):
    """Пользователь сайта."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    requests: Mapped[list["AIRequestChat"]] = relationship(back_populates="user")
    builds: Mapped[list["Build"]] = relationship(back_populates="user")


class Component(Base1):
    """Запись каталога комплектующих."""

    __tablename__ = "components"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    price: Mapped[int]
    type: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String)


class AIRequestChat(Base):
    """Пара сообщений пользователя и ИИ."""

    __tablename__ = "ai_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    request_text: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    user: Mapped[User] = relationship(back_populates="requests")


class Build(Base):
    """Сборка, принадлежащая одному пользователю."""

    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    components: Mapped[Parts] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="builds")
