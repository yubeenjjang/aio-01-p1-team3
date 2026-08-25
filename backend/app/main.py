"""FastAPI 앱을 만들고, 공통 설정과 모든 API router를 등록하는 시작 파일입니다."""

from contextlib import asynccontextmanager
import json

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.core.api_response import error_body
from app.exceptions.handlers import http_exception_handler
from app.core.log_utils import create_trace_id, write_operation_log
from app.core.redis_config import close_redis_connections
from app.core.supabase_config import get_supabase
from app.routers import admin_router, analyses_router, auth_router, chat_router, events_router, feedback_router, records_router, studies_router, uploads_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """앱 종료 시 SSE용 Redis 연결을 정리합니다."""
    yield
    await close_redis_connections()


app = FastAPI(title="Study Management API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://127.0.0.1:8502", "http://localhost:8501", "http://localhost:8502"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    request.state.trace_id = create_trace_id()
    response = await call_next(request)
    response.headers["X-Trace-Id"] = request.state.trace_id
    return response


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "서버 오류가 발생했습니다.", getattr(request.state, "trace_id", "")))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    await _write_validation_failure_log(request)
    return JSONResponse(status_code=400, content=error_body("VALIDATION_ERROR", "요청값이 올바르지 않습니다.", getattr(request.state, "trace_id", ""), {"errors": jsonable_encoder(exc.errors())}))


async def _write_validation_failure_log(request: Request) -> None:
    """확장 API의 Pydantic 검증 실패도 문서의 운영 로그 규칙에 맞춰 기록합니다."""
    action_by_request = {
        ("POST", "/analyses/feedback"): ("analysis.feedback.submit", True),
        ("POST", "/chat/conversations"): ("chat.conversation.create", True),
        ("GET", "/admin/analysis-feedback"): ("admin.analysis_feedback.list", False),
    }
    action_info = action_by_request.get((request.method, request.url.path))
    if action_info is None and request.method == "POST" and request.url.path.startswith("/chat/conversations/") and request.url.path.endswith("/messages"):
        action_info = ("chat.message", True)
    if action_info is None and request.method == "DELETE" and request.url.path.startswith("/chat/conversations/"):
        action_info = ("chat.conversation.delete", True)
    if action_info is None:
        return

    user_id = request.query_params.get("user_id")
    if not user_id:
        try:
            body = json.loads((await request.body()) or b"{}")
            user_id = body.get("user_id") if isinstance(body, dict) else None
        except (TypeError, ValueError):
            user_id = None
    action, publish_event = action_info
    try:
        write_operation_log(
            get_supabase(),
            user_id=user_id,
            action=action,
            status="failure",
            message="요청값 검증 실패",
            trace_id=getattr(request.state, "trace_id", ""),
            publish_event=publish_event,
        )
    except Exception:
        # 로그 인프라가 없어도 원래의 400 검증 응답은 그대로 반환합니다.
        pass


from fastapi import HTTPException
app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(auth_router.router)
app.include_router(records_router.router)
app.include_router(uploads_router.router)
app.include_router(studies_router.router)
app.include_router(analyses_router.router)
app.include_router(admin_router.router)
app.include_router(events_router.router)
app.include_router(chat_router.router)
app.include_router(feedback_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
