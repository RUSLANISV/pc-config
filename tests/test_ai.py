"""Проверки ИИ без внешних запросов и оплаты."""

import json
from collections.abc import Callable
from http import HTTPStatus

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend import ai_service, settings
from backend.ai_service import (
    get_client,
    get_complects_from_db,
    handle_ai_cot_request,
    handle_ai_request,
    make_complects_string,
)
from backend.models import Component
from backend.schemas import Complect, FinalAnswer

type MockAI = Callable[[dict[str, object], int], None]


@pytest.fixture
def chat_response() -> dict[str, object]:
    """Подготовить ответ в формате Chat Completions."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1,
        "model": "test",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Ответ"},
                "finish_reason": "stop",
            }
        ],
    }


@pytest.fixture
def build_response(chat_response: dict[str, object]) -> dict[str, object]:
    """Подготовить структурированный ответ Chat Completions."""
    answer = FinalAnswer(thoughts=[], choosen_complect=[], final_answer="Сборка")
    chat_response["choices"] = [
        {
            "index": 0,
            "message": {"role": "assistant", "content": answer.model_dump_json()},
            "finish_reason": "stop",
        }
    ]
    return chat_response


def test_client_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Без ключа ИИ возвращает понятную ошибку настройки."""
    monkeypatch.setattr(settings, "AI_API_KEY", "")

    with pytest.raises(HTTPException) as error:
        get_client()

    assert error.value.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_client_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Клиент использует адрес и ключ из настроек."""
    monkeypatch.setattr(settings, "AI_API_KEY", "test")
    monkeypatch.setattr(settings, "AI_BASE_URL", "https://ai.example.test/v1")

    with get_client() as result:
        assert str(result.base_url) == "https://ai.example.test/v1/"
        assert result.api_key == "test"


def test_catalog_empty(db: Session) -> None:
    """Пустая база даёт пустой список для ИИ."""
    session = db

    result = get_complects_from_db(session)

    assert result == []


def test_catalog_values(db: Session, catalog: list[Component]) -> None:
    """Данные каталога передаются без потери цены и описания."""
    expected = catalog[0]

    result = get_complects_from_db(db)

    assert result[0].name == expected.name
    assert result[0].price == expected.price
    assert result[0].description == expected.description


def test_catalog_text_empty() -> None:
    """Пустой список превращается в пустую строку."""
    parts: list[Complect] = []

    result = make_complects_string(parts)

    assert result == ""


def test_catalog_text_values() -> None:
    """Описание содержит идентификатор, тип и цену."""
    parts = [Complect(id=1, type="cpu", name="Intel", price=100, description="CPU")]

    result = make_complects_string(parts)

    assert result == "1) cpu: Intel, 100 руб, CPU"


def test_chat_success(
    ai_mock: MockAI,
    chat_response: dict[str, object],
    requests: list[httpx.Request],
) -> None:
    """Ответ SDK сохраняется вместе с сообщением пользователя."""
    ai_service.user_messages.clear()
    ai_mock(chat_response, HTTPStatus.OK)

    result = handle_ai_request("Подбери ПК", 1)

    payload = json.loads(requests[0].content)
    assert result == "Ответ"
    assert payload["messages"][-1]["content"] == "Подбери ПК"
    assert ai_service.user_messages[1][-1]["role"] == "assistant"


def test_chat_history_isolated(
    ai_mock: MockAI,
    chat_response: dict[str, object],
    requests: list[httpx.Request],
) -> None:
    """История другого пользователя не попадает в запрос."""
    ai_service.user_messages.clear()
    ai_service.user_messages[2] = [{"role": "user", "content": "Чужая история"}]
    ai_mock(chat_response, HTTPStatus.OK)

    handle_ai_request("Мой вопрос", 1)

    assert "Чужая история" not in requests[0].content.decode()


def test_chat_empty_answer(ai_mock: MockAI, chat_response: dict[str, object]) -> None:
    """Пустой ответ не сохраняется в истории."""
    ai_service.user_messages.clear()
    chat_response["choices"] = []
    ai_mock(chat_response, HTTPStatus.OK)

    with pytest.raises(ValueError, match=r"^$"):
        handle_ai_request("Вопрос", 1)

    assert 1 not in ai_service.user_messages


@pytest.mark.usefixtures("catalog")
def test_build_ai_success(
    db: Session,
    ai_mock: MockAI,
    build_response: dict[str, object],
    requests: list[httpx.Request],
) -> None:
    """SDK разбирает структурированный ответ и отправляет каталог."""
    ai_mock(build_response, HTTPStatus.OK)

    result = handle_ai_cot_request("До 50000", db)

    payload = json.loads(requests[0].content)
    assert result.final_answer == "Сборка"
    assert requests[0].url.path == "/v1/chat/completions"
    assert payload["response_format"]["type"] == "json_schema"
    assert "Intel Core" in payload["messages"][0]["content"]
    assert payload["messages"][1]["content"] == "До 50000"


def test_build_ai_empty_catalog(db: Session) -> None:
    """Без комплектующих запрос во внешний сервис не выполняется."""
    prompt = "Подбери ПК"

    with pytest.raises(HTTPException) as error:
        handle_ai_cot_request(prompt, db)

    assert error.value.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures("catalog")
def test_build_ai_empty_answer(
    db: Session, ai_mock: MockAI, build_response: dict[str, object]
) -> None:
    """Ответ без результата не считается успешной сборкой."""
    build_response["choices"] = []
    ai_mock(build_response, HTTPStatus.OK)

    with pytest.raises(ValueError, match=r"^$"):
        handle_ai_cot_request("Подбери ПК", db)


def test_chat_api_saves_history(
    client: TestClient,
    auth: dict[str, str],
    ai_mock: MockAI,
    chat_response: dict[str, object],
) -> None:
    """HTTP-запрос сохраняет полученный ответ в истории."""
    ai_mock(chat_response, HTTPStatus.OK)

    result = client.post("/ai", headers=auth, json={"query": "Вопрос"})

    assert result.status_code == HTTPStatus.OK
    assert result.json()["response"] == "Ответ"
    history = client.get("/history", headers=auth).json()
    assert history[0]["response_text"] == "Ответ"


@pytest.mark.usefixtures("catalog")
def test_build_ai_api(
    client: TestClient,
    auth: dict[str, str],
    ai_mock: MockAI,
    build_response: dict[str, object],
) -> None:
    """Маршрут подбора сборки возвращает ожидаемый формат."""
    ai_mock(build_response, HTTPStatus.OK)

    result = client.post("/ai_cot", headers=auth, json={"query": "Подбери ПК"})

    assert result.status_code == HTTPStatus.OK
    assert result.json()["final_answer"] == "Сборка"


@pytest.mark.usefixtures("catalog")
@pytest.mark.parametrize("path", ["/ai", "/ai_cot"])
def test_ai_api_provider_failure(
    client: TestClient, auth: dict[str, str], ai_mock: MockAI, path: str
) -> None:
    """Ошибка провайдера превращается в понятный ответ API."""
    ai_mock({"error": {"message": "not available"}}, HTTPStatus.INTERNAL_SERVER_ERROR)

    result = client.post(path, headers=auth, json={"query": "Вопрос"})

    assert result.status_code == HTTPStatus.BAD_GATEWAY
    assert "not available" not in result.text


@pytest.mark.usefixtures("catalog")
@pytest.mark.parametrize("path", ["/ai", "/ai_cot"])
def test_ai_api_missing_key(
    client: TestClient, auth: dict[str, str], monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    """Отсутствующий ключ не мешает работе сайта и объясняется пользователю."""
    monkeypatch.setattr(settings, "AI_API_KEY", "")

    result = client.post(path, headers=auth, json={"query": "Вопрос"})

    assert result.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert "AI_API_KEY" in result.json()["detail"]


def test_chat_continues_own_history(
    ai_mock: MockAI,
    chat_response: dict[str, object],
    requests: list[httpx.Request],
) -> None:
    """Следующий запрос включает предыдущие сообщения владельца."""
    ai_service.user_messages.clear()
    ai_service.user_messages[1] = [
        {"role": "system", "content": "Помоги собрать ПК"},
        {"role": "user", "content": "Мой бюджет"},
        {"role": "assistant", "content": "Уточните сумму"},
    ]
    ai_mock(chat_response, HTTPStatus.OK)

    result = handle_ai_request("50000", 1)

    payload = json.loads(requests[0].content)
    assert result == "Ответ"
    assert payload["messages"][1]["content"] == "Мой бюджет"
    assert payload["messages"][-1]["content"] == "50000"
