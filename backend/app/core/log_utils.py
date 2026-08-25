"""요청 추적 ID를 만들고 operation_logs 테이블에 운영 로그를 저장합니다."""

from uuid import uuid4


def create_trace_id() -> str:
    return str(uuid4())


def write_operation_log(client, *, action: str, status: str, trace_id: str, user_id=None,
                        message: str | None = None, latency_ms: int | None = None,
                        publish_event: bool = True) -> None:
    """Best-effort audit logging. A logging outage must not hide the original result."""
    try:
        client.table("operation_logs").insert({
            "user_id": str(user_id) if user_id else None,
            "action": action,
            "status": status,
            "trace_id": trace_id,
            "message": message,
            "latency_ms": latency_ms,
        }).execute()
        if publish_event:
            try:
                from app.services.event_service import publish_admin_log_updated

                publish_admin_log_updated(action=action, status=status)
            except Exception:
                # Redis 장애는 이미 성공하거나 실패한 업무 처리 결과에 영향을 주지 않습니다.
                pass
    except Exception:
        pass
