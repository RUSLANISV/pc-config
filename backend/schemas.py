"""Форматы входных данных и ответов API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

type Parts = dict[str, dict[str, str | int | float | None]]


class UserCreate(BaseModel):
    """Данные регистрации."""

    username: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    """Публичные данные аккаунта."""

    model_config = ConfigDict(from_attributes=True)
    username: str
    id: int
    email: str


class Token(BaseModel):
    """Токен для авторизации запросов."""

    access_token: str
    token_type: str = Field(default="bearer")


class UserLogin(BaseModel):
    """Данные для входа."""

    email: str
    password: str


class ComponentOut(BaseModel):
    """Комплектующее из каталога."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    name: str
    price: int
    description: str


class AIHistory(BaseModel):
    """Сохранённый обмен сообщениями с ИИ."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    request_text: str
    response_text: str
    created_at: datetime


class AIRequestCreate(BaseModel):
    """Сообщение пользователя для ИИ."""

    query: str = Field(min_length=1, max_length=10000)


class AIRequestResponse(BaseModel):
    """Ответ на сообщение пользователя."""

    id: int
    query: str
    response: str
    timestamp: datetime


class BuildCreate(BaseModel):
    """Данные для сохранения сборки."""

    name: str = Field(min_length=1, max_length=100)
    components: Parts


class BuildOut(BaseModel):
    """Сохранённая сборка."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    components: Parts
    user_id: int


class Complect(BaseModel):
    """Комплектующее, доступное ИИ для выбора."""

    id: int
    type: str
    name: str
    price: int
    description: str


class Think(BaseModel):
    """Краткое объяснение выбора комплектующего."""

    explanation: str
    output: str


class FinalAnswer(BaseModel):
    """Рекомендованная ИИ сборка с объяснениями."""

    thoughts: list[Think]
    choosen_complect: list[Complect]
    final_answer: str
