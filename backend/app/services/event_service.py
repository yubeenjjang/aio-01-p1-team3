"""관리자 운영 로그 SSE 이벤트의 Redis 발행·구독 기능입니다."""

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

from app.core.redis_config import get_async_redis, get_sync_redis


ADMIN_CHANNEL = "study-management:admin"


def build_admin_log_event(*, action: str, status: str) -> dict[str, str]:
    """민감정보를 제외한 관리자 로그 갱신 이벤트 데이터를 만듭니다."""
    return {
        "event_id": str(uuid4()),
        "action": action,
        "status": status,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


def publish_admin_log_updated(*, action: str, status: str) -> None:
    """관리자 채널에 로그 갱신 알림을 발행합니다."""
    payload = build_admin_log_event(action=action, status=status)
    get_sync_redis().publish(ADMIN_CHANNEL, json.dumps(payload, ensure_ascii=False))


def format_sse_event(event: str, data: dict[str, object]) -> str:
    """이벤트 하나를 SSE wire format 문자열로 변환합니다."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def subscribe_admin_events(keep_alive_seconds: float = 20.0) -> AsyncIterator[str]:
    """관리자 Redis 채널 메시지와 keep-alive 주석을 SSE 문자열로 반환합니다."""
    pubsub = get_async_redis().pubsub()
    try:
        await pubsub.subscribe(ADMIN_CHANNEL)
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=keep_alive_seconds,
            )
            if message is None:
                yield ": keep-alive\n\n"
                await asyncio.sleep(0)
                continue
            try:
                payload = json.loads(message.get("data"))
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                yield format_sse_event("admin.log.updated", payload)
    finally:
        await pubsub.unsubscribe(ADMIN_CHANNEL)
        await pubsub.aclose()
