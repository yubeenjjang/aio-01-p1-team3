"""성공·실패 API 응답에서 공통으로 사용하는 JSON 형태를 만드는 파일입니다."""

from typing import Any


def error_body(code: str, message: str, trace_id: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details or {}, "trace_id": trace_id}
