"""Проверка сборок и прав доступа к ним."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Build
from backend.schemas import BuildCreate

PART_TYPES = {"cpu", "gpu", "motherboard", "ram", "storage", "psu", "cpucool", "case"}


def validate_build(build: BuildCreate) -> None:
    """Проверить название сборки и типы её комплектующих."""
    if not build.name.strip() or not build.components:
        raise HTTPException(status_code=400, detail="Укажите название и комплектующие")
    for kind in build.components:
        if kind not in PART_TYPES:
            raise HTTPException(status_code=400, detail=f"Неизвестный тип: {kind}")


def get_user_build(db: Session, build_id: int, user_id: int) -> Build:
    """Найти сборку, доступную указанному пользователю."""
    build = db.scalar(
        select(Build).where(Build.id == build_id, Build.user_id == user_id)
    )
    if build is None:
        raise HTTPException(status_code=404, detail="Сборка не найдена")
    return build
