"""관리자 운영 로그 SSE API 계약 테스트입니다."""

import asyncio
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.supabase_config import get_supabase
from app.routers.events_router import router
from app.services import admin_service, event_service


ADMIN_ID = uuid4()


@pytest.fixture
def client() -> TestClient:
    """Redis와 Supabase 없이 SSE 라우터만 검증하는 테스트 앱입니다."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(app)


def test_stream_rejects_non_admin(monkeypatch, client: TestClient) -> None:
    """관리자가 아닌 사용자는 SSE를 구독할 수 없습니다."""
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: False)

    response = client.get("/events/stream", params={"admin_user_id": str(ADMIN_ID)})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ADMIN_REQUIRED"


def test_stream_returns_sse_headers_and_event(monkeypatch, client: TestClient) -> None:
    """정상 구독은 SSE 헤더와 admin.log.updated 이벤트를 반환합니다."""
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: True)

    async def fake_subscribe():
        yield event_service.format_sse_event(
            "admin.log.updated",
            {"event_id": "event-1", "action": "analysis.request", "status": "success", "occurred_at": "2026-08-10T12:00:00+00:00"},
        )

    monkeypatch.setattr(event_service, "subscribe_admin_events", fake_subscribe)
    response = client.get("/events/stream", params={"admin_user_id": str(ADMIN_ID)})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert "event: admin.log.updated" in response.text
    assert '"event_id": "event-1"' in response.text


def test_stream_emits_error_event_when_redis_subscription_fails(monkeypatch, client: TestClient) -> None:
    """Redis 구독 실패는 HTTP 오류 대신 SSE error 이벤트로 전달합니다."""
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: True)

    async def failing_subscribe():
        raise RuntimeError("Redis unavailable")
        yield ""  # pragma: no cover - async generator 형식 유지

    monkeypatch.setattr(event_service, "subscribe_admin_events", failing_subscribe)
    response = client.get("/events/stream", params={"admin_user_id": str(ADMIN_ID)})

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "REDIS_UNAVAILABLE" in response.text


def test_event_service_formats_event_and_keep_alive(monkeypatch) -> None:
    """Redis 메시지와 유휴 시간은 문서의 SSE 형식으로 변환됩니다."""
    assert event_service.format_sse_event("admin.log.updated", {"action": "chat.message"}).endswith("\n\n")

    class FakePubSub:
        async def subscribe(self, _channel):
            return None

        async def get_message(self, **_kwargs):
            return None

        async def unsubscribe(self, _channel):
            return None

        async def aclose(self):
            return None

    class FakeRedis:
        def pubsub(self):
            return FakePubSub()

    monkeypatch.setattr(event_service, "get_async_redis", lambda: FakeRedis())

    async def first_item() -> str:
        stream = event_service.subscribe_admin_events(keep_alive_seconds=0)
        try:
            return await anext(stream)
        finally:
            await stream.aclose()

    assert asyncio.run(first_item()) == ": keep-alive\n\n"
