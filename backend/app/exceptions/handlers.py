"""FastAPI 예외를 프로젝트의 공통 오류 JSON 응답으로 바꿉니다."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.api_response import error_body


async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(detail.get("code", "HTTP_ERROR"), detail.get("message", "요청 처리에 실패했습니다."),
                           getattr(request.state, "trace_id", ""), detail.get("details")),
    )
