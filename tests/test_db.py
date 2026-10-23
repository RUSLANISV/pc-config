"""Проверки открытия и освобождения сессий базы."""

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import sessionmaker

from backend import db, db1


@pytest.mark.parametrize("module", ["users", "catalog"])
def test_session_dependency(
    engine: Engine, monkeypatch: pytest.MonkeyPatch, module: str
) -> None:
    """Каждая зависимость предоставляет рабочую сессию."""
    factory = sessionmaker(bind=engine)
    if module == "users":
        monkeypatch.setattr(db, "SessionLocal", factory)
        source = db.get_db()
    else:
        monkeypatch.setattr(db1, "SessionLocal1", factory)
        source = db1.get_db1()

    session = next(source)
    result = session.scalar(select(1))

    assert result == 1
    assert next(source, None) is None
