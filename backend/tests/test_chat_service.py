from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core import gemini_config
from app.services import chat_service


class HistoryQuery:
    def __init__(self, rows):
        self.rows = rows
        self.limit_value = None

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows[: self.limit_value])


class HistoryClient:
    def __init__(self, rows):
        self.query = HistoryQuery(rows)

    def table(self, table_name):
        assert table_name == "chat_messages"
        return self.query


def test_recent_contents_limits_and_restores_chronological_order():
    descending_rows = [
        {"role": "user", "content": f"질문 {index}"}
        for index in range(25, 0, -1)
    ]
    client = HistoryClient(descending_rows)

    contents = chat_service._recent_contents(client, uuid4())

    assert client.query.limit_value == 20
    assert len(contents) == 20
    assert contents[0] == {"role": "user", "parts": [{"text": "질문 6"}]}
    assert contents[-1] == {"role": "user", "parts": [{"text": "질문 25"}]}


class MessageQuery:
    def __init__(self, table_name, stored):
        self.table_name = table_name
        self.stored = stored

    def insert(self, values):
        self.values = values
        return self

    def update(self, _values):
        return self

    def eq(self, *_args):
        return self

    def execute(self):
        if hasattr(self, "values"):
            message = {
                "message_id": str(uuid4()),
                "created_at": "2026-08-11T00:00:00+00:00",
                **self.values,
            }
            self.stored.append(message)
            return SimpleNamespace(data=[message])
        return SimpleNamespace(data=[])


class MessageClient:
    def __init__(self):
        self.stored = []

    def table(self, table_name):
        return MessageQuery(table_name, self.stored)


def test_create_message_passes_recent_user_model_history_to_gemini(monkeypatch):
    conversation_id = uuid4()
    user_id = uuid4()
    payload = SimpleNamespace(user_id=user_id, content="두 번째 질문")
    recent_contents = [
        {"role": "user", "parts": [{"text": "첫 번째 질문"}]},
        {"role": "model", "parts": [{"text": "첫 번째 답변"}]},
        {"role": "user", "parts": [{"text": "두 번째 질문"}]},
    ]
    captured = {}
    client = MessageClient()

    monkeypatch.setattr(chat_service, "_conversation_or_404", lambda *_args: {})
    monkeypatch.setattr(chat_service, "_recent_contents", lambda *_args: recent_contents)

    def generate(contents, system_instruction):
        captured["contents"] = contents
        captured["system_instruction"] = system_instruction
        return "두 번째 답변"

    monkeypatch.setattr(gemini_config, "generate_gemini_contents", generate)

    result = chat_service.create_message(client, conversation_id, payload)

    assert captured["contents"] == recent_contents
    assert captured["system_instruction"] == chat_service.SYSTEM_INSTRUCTION
    assert result["user_message"]["role"] == "user"
    assert result["model_message"]["role"] == "model"
    assert result["model_message"]["content"] == "두 번째 답변"


class ConversationQuery:
    def __init__(self):
        self.filters = []

    def select(self, *_args):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return SimpleNamespace(data=None)


class ConversationClient:
    def __init__(self):
        self.query = ConversationQuery()

    def table(self, table_name):
        assert table_name == "chat_conversations"
        return self.query


def test_conversation_lookup_hides_other_users_resource():
    client = ConversationClient()
    conversation_id = uuid4()
    user_id = uuid4()

    with pytest.raises(HTTPException) as error:
        chat_service._conversation_or_404(client, conversation_id, user_id)

    assert error.value.status_code == 404
    assert error.value.detail["code"] == "CONVERSATION_NOT_FOUND"
    assert client.query.filters == [
        ("conversation_id", str(conversation_id)),
        ("user_id", str(user_id)),
    ]


@pytest.mark.parametrize(
    ("status_code", "expected_status", "expected_code"),
    [
        (429, 429, "RATE_LIMITED"),
        (503, 503, "GEMINI_UNAVAILABLE"),
        (500, 500, "GEMINI_REQUEST_FAILED"),
    ],
)
def test_gemini_errors_follow_chat_api_contract(
    status_code, expected_status, expected_code
):
    source_error = RuntimeError("Gemini error")
    source_error.status_code = status_code

    error = chat_service._gemini_error(source_error)

    assert error.status_code == expected_status
    assert error.detail["code"] == expected_code
