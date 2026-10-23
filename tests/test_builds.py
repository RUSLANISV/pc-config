"""Проверки данных сборок и доступа к ним."""

from http import HTTPStatus

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.build_service import get_user_build, validate_build
from backend.models import Build, User
from backend.schemas import BuildCreate, Parts


@pytest.mark.parametrize(
    "kind", ["cpu", "gpu", "motherboard", "ram", "storage", "psu", "cpucool", "case"]
)
def test_validate_supported_type(kind: str) -> None:
    """Разрешённый тип комплектующего принимается."""
    data = BuildCreate(name="ПК", components={kind: {"id": 1}})

    validate_build(data)

    assert data.components == {kind: {"id": 1}}


@pytest.mark.parametrize(
    ("name", "parts"),
    [(" ", {"cpu": {"id": 1}}), ("ПК", {}), ("ПК", {"wrong": {"id": 1}})],
)
def test_validate_bad_build(name: str, parts: Parts) -> None:
    """Пустые данные и неизвестные типы отклоняются."""
    data = BuildCreate(name=name, components=parts)

    with pytest.raises(HTTPException) as error:
        validate_build(data)

    assert error.value.status_code == HTTPStatus.BAD_REQUEST


def test_get_own_build(db: Session, user: User, build: Build) -> None:
    """Владелец получает свою сборку."""
    build_id = build.id

    result = get_user_build(db, build_id, user.id)

    assert result is build


def test_get_foreign_build(db: Session, other_user: User, build: Build) -> None:
    """Другой пользователь не получает чужую сборку."""
    build_id = build.id

    with pytest.raises(HTTPException) as error:
        get_user_build(db, build_id, other_user.id)

    assert error.value.status_code == HTTPStatus.NOT_FOUND


def test_get_missing_build(db: Session, user: User) -> None:
    """Несуществующая сборка даёт понятную ошибку."""
    build_id = 999

    with pytest.raises(HTTPException) as error:
        get_user_build(db, build_id, user.id)

    assert error.value.status_code == HTTPStatus.NOT_FOUND
