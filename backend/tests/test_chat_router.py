"""멀티턴 채팅 라우터의 핵심 계약 테스트입니다."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.supabase_config import get_supabase
from app.routers.chat_router import router
from app.services import chat_service


USER_ID = uuid4()
CONVERSATION_ID = uuid4()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(app)


def _conversation() -> dict:
    now = datetime(2026, 8, 10, tzinfo=timezone.utc).isoformat()
    return {"conversation_id": str(CONVERSATION_ID), "title": "Python 질문", "created_at": now, "updated_at": now}


def test_create_conversation(monkeypatch, client: TestClient) -> None:
    monkeypatch.setattr(chat_service, "create_conversation", lambda _client, _payload: _conversation())
    response = client.post("/chat/conversations", json={"user_id": str(USER_ID), "title": "Python 질문"})
    assert response.status_code == 201
    assert response.json()["conversation_id"] == str(CONVERSATION_ID)


def test_list_messages_forwards_owner(monkeypatch, client: TestClient) -> None:
    captured = {}
    def list_messages(_client, conversation_id, user_id):
        captured.update({"conversation_id": conversation_id, "user_id": user_id})
        return {"items": [], "total": 0}
    monkeypatch.setattr(chat_service, "list_messages", list_messages)
    response = client.get(f"/chat/conversations/{CONVERSATION_ID}/messages", params={"user_id": str(USER_ID)})
    assert response.status_code == 200
    assert captured == {"conversation_id": CONVERSATION_ID, "user_id": USER_ID}


def test_message_rejects_blank_content(client: TestClient) -> None:
    response = client.post(f"/chat/conversations/{CONVERSATION_ID}/messages", json={"user_id": str(USER_ID), "content": "   "})
    assert response.status_code == 422
