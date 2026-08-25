"""AI 분석 평가 저장·조회 API입니다."""

from datetime import date
from time import perf_counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.feedback_schema import AdminFeedbackListResponse, FeedbackRequest, FeedbackResponse
from app.services import admin_service, feedback_service


router = APIRouter(tags=["feedback"])


def _log(client, request: Request, *, user_id: UUID, action: str, status: str, message: str | None, latency_ms: int,
         publish_event: bool = True) -> None:
    write_operation_log(client, user_id=user_id, action=action, status=status, message=message, latency_ms=latency_ms,
                        trace_id=getattr(request.state, "trace_id", ""), publish_event=publish_event)


@router.post("/analyses/feedback", response_model=FeedbackResponse)
def save_feedback(payload: FeedbackRequest, request: Request, client=Depends(get_supabase)) -> FeedbackResponse | JSONResponse:
    """분석 기간의 평가를 생성하거나 기존 평가를 수정합니다."""
    started = perf_counter()
    try:
        result, created = feedback_service.save_feedback(client, payload)
        _log(client, request, user_id=payload.user_id, action="analysis.feedback.submit", status="success", message=None,
             latency_ms=round((perf_counter() - started) * 1000))
        if created:
            return JSONResponse(status_code=201, content=FeedbackResponse.model_validate(result).model_dump(mode="json"))
        return FeedbackResponse.model_validate(result)
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="analysis.feedback.submit", status="failure", message="분석 평가 저장 실패",
             latency_ms=round((perf_counter() - started) * 1000))
        raise exc


@router.get("/analyses/feedback", response_model=FeedbackResponse)
def get_feedback(
    user_id: UUID = Query(..., description="평가를 조회할 사용자 UUID"),
    period_start: date = Query(..., description="분석 시작일"),
    period_end: date = Query(..., description="분석 종료일"),
    client=Depends(get_supabase),
) -> FeedbackResponse:
    """사용자의 특정 분석 기간 평가를 조회합니다."""
    if period_start > period_end:
        raise HTTPException(400, {"code": "VALIDATION_ERROR", "message": "분석 시작일은 종료일보다 늦을 수 없습니다."})
    return FeedbackResponse.model_validate(feedback_service.get_feedback(client, user_id, period_start, period_end))


@router.get("/admin/analysis-feedback", response_model=AdminFeedbackListResponse)
def list_admin_feedback(
    request: Request,
    user_id: UUID = Query(..., description="조회할 관리자 UUID"),
    rating: int | None = Query(default=None, ge=1, le=5, description="평점 필터"),
    from_date: date | None = Query(default=None, alias="from", description="평가 생성일 시작"),
    to_date: date | None = Query(default=None, alias="to", description="평가 생성일 종료"),
    limit: int = Query(default=50, ge=1, le=200, description="반환할 최대 개수"),
    offset: int = Query(default=0, ge=0, description="건너뛸 개수"),
    client=Depends(get_supabase),
) -> AdminFeedbackListResponse:
    """관리자가 전체 분석 평가와 평균 평점을 조회합니다."""
    started = perf_counter()
    try:
        if not admin_service.is_admin(client, user_id):
            raise HTTPException(403, {"code": "ADMIN_REQUIRED", "message": "관리자 권한이 필요합니다."})
        result = AdminFeedbackListResponse.model_validate(
            feedback_service.list_admin_feedback(client, rating=rating, from_date=from_date, to_date=to_date, limit=limit, offset=offset)
        )
        _log(client, request, user_id=user_id, action="admin.analysis_feedback.list", status="success", message=None,
             latency_ms=round((perf_counter() - started) * 1000), publish_event=False)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action="admin.analysis_feedback.list", status="failure", message="관리자 분석 평가 조회 실패",
             latency_ms=round((perf_counter() - started) * 1000), publish_event=False)
        raise exc
