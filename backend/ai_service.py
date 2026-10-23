"""Обращения к ИИ и подготовка каталога для подбора сборки."""

from fastapi import HTTPException
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend import settings
from backend.models import Component
from backend.schemas import Complect, FinalAnswer

user_messages: dict[int, list[ChatCompletionMessageParam]] = {}
SYSTEM_PROMPT = (
    "Ты ассистент по компьютерам, комплектующим, сборке и апгрейду ПК. "
    "На вопросы по другим темам отвечай вежливым отказом."
)


def get_client() -> OpenAI:
    """Создать клиент при наличии ключа внешнего сервиса."""
    if not settings.AI_API_KEY:
        raise HTTPException(
            status_code=503, detail="ИИ не настроен: задайте AI_API_KEY"
        )
    return OpenAI(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL,
        timeout=30,
        max_retries=1,
    )


def get_complects_from_db(db: Session) -> list[Complect]:
    """Прочитать доступные комплектующие из каталога."""
    result = []
    for part in db.scalars(select(Component).order_by(Component.id)):
        item = Complect(
            id=part.id,
            type=part.type,
            name=part.name,
            price=part.price,
            description=part.description,
        )
        result.append(item)
    return result


def make_complects_string(parts: list[Complect]) -> str:
    """Подготовить текстовое описание каталога."""
    lines = []
    for part in parts:
        line = f"{part.id}) {part.type}: {part.name}, {part.price} руб"
        line += f", {part.description}"
        lines.append(line)
    return "\n".join(lines)


def handle_ai_cot_request(prompt: str, db: Session) -> FinalAnswer:
    """Получить сборку с краткими объяснениями выбора деталей."""
    parts = get_complects_from_db(db)
    if not parts:
        raise HTTPException(status_code=404, detail="Каталог комплектующих пуст")
    catalog = make_complects_string(parts)
    instruction = (
        "Подбери сборку ПК по запросу пользователя. "
        "Используй только комплектующие из каталога ниже. "
        "Учитывай бюджет и совместимость. Дай краткие объяснения выбора "
        "и итоговую рекомендацию.\n" + catalog
    )
    with get_client() as client:
        result = client.beta.chat.completions.parse(
            model=settings.AI_BUILD_MODEL,
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": prompt},
            ],
            response_format=FinalAnswer,
            max_tokens=2048,
        )
    if not result.choices or result.choices[0].message.parsed is None:
        raise ValueError
    return result.choices[0].message.parsed


def handle_ai_request(prompt: str, user_id: int) -> str:
    """Ответить пользователю с учётом его предыдущих сообщений."""
    messages = user_messages.get(user_id, []).copy()
    if not messages:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": prompt})
    with get_client() as client:
        result = client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=messages,
            max_tokens=1024,
        )
    if not result.choices or not result.choices[0].message.content:
        raise ValueError
    answer = result.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})
    user_messages[user_id] = messages
    return answer
