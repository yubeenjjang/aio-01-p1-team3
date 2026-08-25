"""기간별 학습 기록을 Gemini로 분석하는 API를 정의합니다."""

from time import perf_counter

from fastapi import APIRouter, Depends, Request

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from app.services import analysis_service

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _log(client, request: Request, *, user_id, status: str, message: str | None, latency_ms: int):
    write_operation_log(
        client,
        user_id=user_id,
        action="analysis.request",
        status=status,
        message=message,
        latency_ms=latency_ms,
        trace_id=getattr(request.state, "trace_id", ""),
    )


@router.post("", response_model=AnalysisResponse)
def create_analysis(payload: AnalysisRequest, request: Request, client=Depends(get_supabase)):
    started = perf_counter()
    try:
        result = analysis_service.analyze_records(client, payload)
        _log(client, request, user_id=payload.user_id, status="success", message="AI 분석 완료", latency_ms=round((perf_counter() - started) * 1000))
        return result
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, status="failure", message="AI 분석 실패", latency_ms=round((perf_counter() - started) * 1000))
        raise exc
