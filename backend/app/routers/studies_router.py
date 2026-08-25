"""그룹 스터디의 목록, 생성, 수정, 참여, 탈퇴 API를 정의합니다."""

from time import perf_counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.study_schema import (
    StudyCreateRequest,
    StudyCreateResponse,
    StudyDetailResponse,
    StudyJoinRequest,
    StudyJoinResponse,
    StudyListResponse,
    StudyResponse,
    StudyUpdateRequest,
)
from app.services import study_service

router = APIRouter(prefix="/studies", tags=["studies"])


def _log(client, request: Request, *, user_id, action: str, status: str, message: str | None, started: float):
    write_operation_log(
        client,
        user_id=user_id,
        action=action,
        status=status,
        message=message,
        trace_id=getattr(request.state, "trace_id", ""),
    )


@router.get("", response_model=StudyListResponse)
def list_studies(
    request: Request,
    user_id: UUID,
    keyword: str | None = None,
    category: str | None = None,
    status: str | None = Query(default=None, pattern="^(recruiting|closed)$"),
    source: str = Query(default="list", pattern="^(list|search)$"),
    client=Depends(get_supabase),
):
    started = perf_counter()
    action = "study.search" if source == "search" else "study.list"
    try:
        result = study_service.list_studies(client, user_id, keyword=keyword, category=category, status=status)
        _log(client, request, user_id=user_id, action=action, status="success", message=None, started=started)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action=action, status="failure", message="스터디 목록 조회 실패", started=started)
        raise exc


@router.get("/{study_id}", response_model=StudyDetailResponse)
def get_study_detail(study_id: UUID, request: Request, user_id: UUID, client=Depends(get_supabase)):
    started = perf_counter()
    try:
        result = study_service.get_study_detail(client, study_id, user_id)
        _log(client, request, user_id=user_id, action="study.detail", status="success", message=None, started=started)
        return result
    except Exception as exc:
        _log(client, request, user_id=user_id, action="study.detail", status="failure", message="스터디 상세 조회 실패", started=started)
        raise exc


@router.post("", response_model=StudyCreateResponse, status_code=201)
def create_study(payload: StudyCreateRequest, request: Request, client=Depends(get_supabase)):
    started = perf_counter()
    try:
        result = study_service.create_study(client, payload)
        _log(client, request, user_id=payload.user_id, action="study.create", status="success", message="스터디 생성 완료", started=started)
        return result
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="study.create", status="failure", message="스터디 생성 실패", started=started)
        raise exc


@router.put("/{study_id}", response_model=StudyResponse)
def update_study(study_id: UUID, payload: StudyUpdateRequest, request: Request, client=Depends(get_supabase)):
    started = perf_counter()
    try:
        result = study_service.update_study(client, study_id, payload, payload.user_id)
        _log(client, request, user_id=payload.user_id, action="study.update", status="success", message="스터디 수정 완료", started=started)
        return result
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="study.update", status="failure", message="스터디 수정 실패", started=started)
        raise exc


@router.delete("/{study_id}", status_code=204)
def delete_study(study_id: UUID, request: Request, user_id: UUID, client=Depends(get_supabase)):
    started = perf_counter()
    try:
        study_service.delete_study(client, study_id, user_id)
        _log(client, request, user_id=user_id, action="study.delete", status="success", message="스터디 삭제 완료", started=started)
        return Response(status_code=204)
    except Exception as exc:
        _log(client, request, user_id=user_id, action="study.delete", status="failure", message="스터디 삭제 실패", started=started)
        raise exc


@router.post("/{study_id}/join", response_model=StudyJoinResponse, status_code=201)
def join_study(study_id: UUID, payload: StudyJoinRequest, request: Request, client=Depends(get_supabase)):
    started = perf_counter()
    try:
        result = study_service.join_study(client, study_id, payload.user_id)
        _log(client, request, user_id=payload.user_id, action="study.join", status="success", message="스터디 참여 완료", started=started)
        return result
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="study.join", status="failure", message="스터디 참여 실패", started=started)
        raise exc


@router.delete("/{study_id}/join", status_code=204)
def leave_study(study_id: UUID, request: Request, user_id: UUID, client=Depends(get_supabase)):
    started = perf_counter()
    try:
        study_service.leave_study(client, study_id, user_id)
        _log(client, request, user_id=user_id, action="study.leave", status="success", message="스터디 탈퇴 완료", started=started)
        return Response(status_code=204)
    except Exception as exc:
        _log(client, request, user_id=user_id, action="study.leave", status="failure", message="스터디 탈퇴 실패", started=started)
        raise exc
