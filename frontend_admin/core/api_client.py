# frontend_admin/core/api_client.py
"""관리자 프론트엔드에서 공통으로 사용하는 백엔드 API 요청 기능."""

import os
from typing import Any

import httpx


# 배포 환경에서는 BACKEND_URL 환경변수를 사용
# 환경변수가 없으면 로컬 FastAPI 서버를 사용
BACKEND_URL = (
    os.getenv("BACKEND_URL") or "http://127.0.0.1:8000"
).rstrip("/")

REQUEST_TIMEOUT = 15.0


class BackendAPIError(Exception):
    """백엔드 연결 또는 API 요청 실패 정보를 담는 예외입니다."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        details: Any = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        self.trace_id = trace_id

#GET, POST, PUT, DELETE 공통 요청
def request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
) -> Any:
    """백엔드 API를 호출하고 정상 응답의 JSON 데이터를 반환합니다."""

    url = f"{BACKEND_URL}/{path.lstrip('/')}"

    try:
        response = httpx.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            files=files,
            #Timeout 처리
            timeout=REQUEST_TIMEOUT,
        )

    
    #네트워크 오류 처리
    except httpx.TimeoutException as error:
        raise BackendAPIError(
            "백엔드 응답 시간이 초과되었습니다.",
            code="REQUEST_TIMEOUT",
        ) from error

    except httpx.RequestError as error:
        raise BackendAPIError(
            "백엔드 서버에 연결할 수 없습니다. 서버 실행 상태를 확인해 주세요.",
            code="CONNECTION_ERROR",
        ) from error

    # 로그아웃이나 삭제 성공처럼 응답 본문이 없는 경우
    if response.status_code == 204:
        return None

    #http 상태 코드가 오류인지 확인(백엔드 표준 오류 응답 파싱)
    if response.is_error:
        _raise_api_error(response)

    # 정상 응답이지만 본문이 없는 경우
    if not response.content:
        return None

    try:
        return response.json()

    except ValueError as error:
        raise BackendAPIError(
            "백엔드가 올바른 JSON 응답을 반환하지 않았습니다.",
            status_code=response.status_code,
            code="INVALID_RESPONSE",
        ) from error


def _raise_api_error(response: httpx.Response) -> None:
    """백엔드 표준 오류 응답을 BackendAPIError로 변환합니다."""

    try:
        error_payload = response.json()
    except ValueError:
        error_payload = {}

    if isinstance(error_payload, dict):
        code = error_payload.get("code")
        message = error_payload.get("message")
        details = error_payload.get("details")
        trace_id = error_payload.get("trace_id")

        # FastAPI 기본 오류 응답도 처리
        if not message:
            detail = error_payload.get("detail")
            if detail:
                message = str(detail)
    else:
        code = None
        message = None
        details = None
        trace_id = None

    if not message:
        message = response.text or "API 요청에 실패했습니다."

    raise BackendAPIError(
        message,
        status_code=response.status_code,
        code=code or f"HTTP_{response.status_code}",
        details=details,
        trace_id=trace_id,
    )