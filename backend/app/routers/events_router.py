"""관리자 운영 로그 화면용 Server-Sent Events API입니다."""

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.services import admin_service, event_service


router = APIRouter(prefix="/events", tags=["events"])


def _require_admin(client, admin_user_id: UUID) -> None:
    """요청한 사용자가 관리자가 아니면 표준 권한 오류를 발생시킵니다."""
    if not admin_service.is_admin(client, admin_user_id):
        raise HTTPException(
            status_code=403,
            detail={"code": "ADMIN_REQUIRED", "message": "관리자 권한이 필요합니다."},
        )


@router.get("/stream")
async def stream_events(
    request: Request,
    admin_user_id: UUID = Query(..., description="SSE를 구독할 관리자 UUID"),
    client=Depends(get_supabase),
) -> StreamingResponse:
    """관리자 운영 로그 변경을 SSE로 전달합니다."""
    _require_admin(client, admin_user_id)

    async def generate() -> AsyncIterator[str]:
        try:
            async for event in event_service.subscribe_admin_events():
                yield event
        except Exception:
            write_operation_log(
                client,
                user_id=admin_user_id,
                action="events.stream",
                status="failure",
                message="Redis SSE 구독 연결 실패",
                trace_id=getattr(request.state, "trace_id", ""),
                publish_event=False,
            )
            yield event_service.format_sse_event(
                "error",
                {
                    "code": "REDIS_UNAVAILABLE",
                    "message": "실시간 운영 로그 연결에 실패했습니다.",
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                },
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
