"""회원가입, 로그인, 로그아웃 요청을 처리하는 API 경로를 정의합니다."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.auth_schema import LoginRequest, SignupRequest, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _log(client, request: Request, *, user_id, action: str, status: str, message: str):
    write_operation_log(client, user_id=user_id, action=action, status=status, message=message,
                        trace_id=getattr(request.state, "trace_id", ""))


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(payload: SignupRequest, request: Request, client=Depends(get_supabase)):
    return auth_service.signup(client, payload)


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, request: Request, client=Depends(get_supabase)):
    try:
        user = auth_service.login(client, payload)
    except Exception as exc:
        _log(client, request, user_id=None, action="auth.login", status="failure", message="로그인 실패")
        raise
    _log(client, request, user_id=user["user_id"], action="auth.login", status="success", message="로그인 성공")
    return user


@router.post("/logout", status_code=204)
def logout(user_id: UUID, request: Request, client=Depends(get_supabase)):
    _log(client, request, user_id=user_id, action="auth.logout", status="success", message="로그아웃 완료")
    return Response(status_code=204)
