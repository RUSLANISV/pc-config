"""Проверки паролей, регистрации и токенов."""

from datetime import UTC, datetime
from http import HTTPStatus

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from backend.auth_service import (
    ALGORITHM,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    register_user,
    verify_password,
)
from backend.models import User
from backend.schemas import UserCreate
from backend.settings import SECRET_KEY


@pytest.mark.parametrize("text", ["simple-password", "пароль"])
def test_password_roundtrip(text: str) -> None:
    """Хеш подходит только исходному паролю."""
    source = text

    result = get_password_hash(source)

    assert result != source
    assert verify_password(source, result)
    assert not verify_password(source + "x", result)


@pytest.mark.parametrize("text", ["", "x" * 73, "я" * 37])
def test_password_invalid_length(text: str) -> None:
    """Пустой и слишком длинный пароль отклоняются."""
    source = text

    with pytest.raises(ValueError, match=r"^$"):
        get_password_hash(source)


@pytest.mark.parametrize("text", ["short", "x" * 73])
def test_verify_invalid_hash(text: str) -> None:
    """Повреждённый хеш и длинный пароль дают отказ."""
    hashed = "broken-hash"

    result = verify_password(text, hashed)

    assert not result


@pytest.mark.parametrize("valid", [True, False])
def test_authenticate_password(
    db: Session, user: User, password: str, *, valid: bool
) -> None:
    """Пользователь входит только с правильным паролем."""
    text = password if valid else password + "x"

    result = authenticate_user(db, user.email, text)

    assert (result is user) == valid


def test_authenticate_missing(db: Session, password: str) -> None:
    """Неизвестный адрес не даёт авторизацию."""
    email = "missing@example.com"

    result = authenticate_user(db, email, password)

    assert result is None


@pytest.mark.parametrize("email", ["one@example.com", "two@example.com"])
def test_token_subject_and_expiration(email: str) -> None:
    """Токен содержит адрес и ограничен одним часом."""
    data = {"sub": email}
    now = datetime.now(UTC).timestamp()
    duration = 60 * 60

    token = create_access_token(data)

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == email
    assert now + duration - 2 <= payload["exp"] <= now + duration + 2
    assert data == {"sub": email}


def test_register_new(db: Session, password: str) -> None:
    """Регистрация сохраняет хеш вместо открытого пароля."""
    data = UserCreate(username="new", email="new@example.com", password=password)

    result = register_user(db, data)

    assert result.username == data.username
    assert result.hashed_password != password
    assert verify_password(password, result.hashed_password)
    assert db.get(User, result.id) is result


@pytest.mark.parametrize("field", ["username", "email"])
def test_register_duplicate(db: Session, user: User, password: str, field: str) -> None:
    """Повтор имени или адреса отклоняется."""
    data = UserCreate(username="new", email="new@example.com", password=password)
    setattr(data, field, getattr(user, field))

    with pytest.raises(HTTPException) as error:
        register_user(db, data)

    assert error.value.status_code == HTTPStatus.BAD_REQUEST


def test_register_multibyte_password(db: Session) -> None:
    """Ограничение bcrypt считается в байтах, а не символах."""
    data = UserCreate(username="new", email="new@example.com", password="я" * 37)

    with pytest.raises(HTTPException) as error:
        register_user(db, data)

    assert error.value.status_code == HTTPStatus.BAD_REQUEST


def test_current_user_valid(db: Session, user: User) -> None:
    """Подписанный токен возвращает владельца."""
    token = create_access_token({"sub": user.email})

    result = get_current_user(token, db)

    assert result is user


@pytest.mark.parametrize(
    "data",
    [{}, {"sub": "missing@example.com"}, {"sub": "student@example.com", "exp": 1}],
)
def test_current_user_invalid_claims(db: Session, data: dict[str, str | int]) -> None:
    """Токены без владельца и с истёкшим сроком отклоняются."""
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as error:
        get_current_user(token, db)

    assert error.value.status_code == HTTPStatus.UNAUTHORIZED


def test_current_user_bad_signature(db: Session, user: User) -> None:
    """Подделанный токен не проходит проверку подписи."""
    token = create_access_token({"sub": user.email}) + "changed"

    with pytest.raises(HTTPException) as error:
        get_current_user(token, db)

    assert error.value.status_code == HTTPStatus.UNAUTHORIZED
