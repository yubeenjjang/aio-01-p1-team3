"""관리자 대시보드와 운영 로그 조회 API를 정의합니다."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.admin_schema import DashboardResponse, OperationLogListResponse
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])

# Query(...)는 URL 뒤의 ?user_id=... 같은 값을 받는 FastAPI 도구입니다.

def _log(client, request: Request, *, user_id, action: str, status: str, message: str | None):
    write_operation_log(
        client,
        user_id=user_id,
        action=action,
        status=status,
        message=message,
        trace_id=getattr(request.state, "trace_id", ""),
        # SSE 수신 뒤 조회한 로그가 다시 SSE를 발행하는 순환을 막습니다.
        publish_event=False,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(request: Request, user_id: UUID = Query(..., description="대시보드를 조회하는 사용자의 UUID"), client=Depends(get_supabase)):
    # 간소화 MVP에서는 user_id를 데이터 연결 및 운영 로그 식별에만 사용합니다.
    try:
        if not admin_service.is_admin(client, user_id):
            raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "관리자 권한이 필요합니다."})
        result = admin_service.get_dashboard(client)
        _log(client, request, user_id=user_id, action="admin.dashboard", status="success", message=None)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action="admin.dashboard", status="failure", message="관리자 대시보드 조회 실패")
        raise exc


@router.get("/logs", response_model=OperationLogListResponse)
def logs(
    request: Request,
    user_id: UUID = Query(..., description="운영 로그를 조회하는 사용자의 UUID"),
    status: str | None = Query(default=None, pattern="^(success|failure)$", description="성공 또는 실패 상태 필터"),
    action: str | None = Query(default=None, description="기능 action 필터. 예: analysis.request"),
    limit: int = Query(default=50, ge=1, le=200, description="반환할 최대 로그 개수"),
    client=Depends(get_supabase),
):
    # status/action은 선택 필터이며, 생략하면 최신 로그를 반환합니다.
    try:
        if not admin_service.is_admin(client, user_id):
            raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "관리자 권한이 필요합니다."})
        result = admin_service.list_operation_logs(client, status=status, action=action, limit=limit)
        _log(client, request, user_id=user_id, action="admin.logs", status="success", message=None)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action="admin.logs", status="failure", message="운영 로그 조회 실패")
        raise exc
