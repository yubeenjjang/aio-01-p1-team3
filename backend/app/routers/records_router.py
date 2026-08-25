"""개인 학습 기록의 조회, 등록, 수정, 삭제, 통계 API를 정의합니다."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.record_schema import RecordListResponse, RecordRequest, RecordResponse, RecordStatsResponse
from app.services import record_service

router = APIRouter(prefix="/records", tags=["records"])


def _log(client, request: Request, *, user_id, action: str, status: str, message: str | None):
    write_operation_log(client, user_id=user_id, action=action, status=status, message=message,
                        trace_id=getattr(request.state, "trace_id", ""))


@router.get("", response_model=RecordListResponse)
def list_records(request: Request, user_id: UUID, from_date: date | None = Query(default=None, alias="from"), to: date | None = None,
                 subject: str | None = None, client=Depends(get_supabase)):
    try:
        result = record_service.list_records(client, user_id, from_date=from_date, to_date=to, subject=subject)
        _log(client, request, user_id=user_id, action="record.list", status="success", message=None)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action="record.list", status="failure", message="학습 기록 목록 조회 실패")
        raise exc


@router.get("/stats", response_model=RecordStatsResponse)
def record_stats(request: Request, user_id: UUID, from_date: date | None = Query(default=None, alias="from"), to: date | None = None, client=Depends(get_supabase)):
    try:
        result = record_service.get_record_stats(client, user_id, from_date=from_date, to_date=to)
        _log(client, request, user_id=user_id, action="record.list", status="success", message=None)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action="record.list", status="failure", message="학습 통계 조회 실패")
        raise exc


@router.get("/{record_id}", response_model=RecordResponse)
def get_record(record_id: UUID, request: Request, user_id: UUID, client=Depends(get_supabase)):
    try:
        result = record_service.get_record(client, record_id, user_id)
        _log(client, request, user_id=user_id, action="record.list", status="success", message=None)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action="record.list", status="failure", message="학습 기록 상세 조회 실패")
        raise exc


@router.post("", response_model=RecordResponse, status_code=201)
def create_record(payload: RecordRequest, request: Request, client=Depends(get_supabase)):
    try:
        result = record_service.create_record(client, payload)
        _log(client, request, user_id=payload.user_id, action="record.create", status="success", message="학습 기록 등록 완료")
        return result
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="record.create", status="failure", message="학습 기록 등록 실패")
        raise exc


@router.put("/{record_id}", response_model=RecordResponse)
def update_record(record_id: UUID, payload: RecordRequest, request: Request, client=Depends(get_supabase)):
    try:
        result = record_service.update_record(client, record_id, payload)
        _log(client, request, user_id=payload.user_id, action="record.update", status="success", message="학습 기록 수정 완료")
        return result
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="record.update", status="failure", message="학습 기록 수정 실패")
        raise exc


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: UUID, user_id: UUID, request: Request, client=Depends(get_supabase)):
    try:
        record_service.delete_record(client, record_id, user_id)
        _log(client, request, user_id=user_id, action="record.delete", status="success", message="학습 기록 삭제 완료")
        return Response(status_code=204)
    except Exception as exc:
        _log(client, request, user_id=user_id, action="record.delete", status="failure", message="학습 기록 삭제 실패")
        raise exc
