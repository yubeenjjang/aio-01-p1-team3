"""Gemini 멀티턴 학습 코치 대화방·메시지 API입니다."""

from time import perf_counter
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.chat_schema import (
    ChatMessageCreateRequest,
    ChatMessageCreateResponse,
    ChatMessageListResponse,
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
)
from app.services import chat_service


router = APIRouter(prefix="/chat/conversations", tags=["chat"])


def _log(client, request: Request, *, user_id: UUID, action: str, status: str, message: str | None, latency_ms: int) -> None:
    write_operation_log(client, user_id=user_id, action=action, status=status, message=message, latency_ms=latency_ms,
                        trace_id=getattr(request.state, "trace_id", ""))


@router.post("", response_model=ConversationResponse, status_code=201)
def create_conversation(payload: ConversationCreateRequest, request: Request, client=Depends(get_supabase)) -> ConversationResponse:
    """빈 멀티턴 학습 코치 대화방을 생성합니다."""
    started = perf_counter()
    try:
        result = chat_service.create_conversation(client, payload)
        _log(client, request, user_id=payload.user_id, action="chat.conversation.create", status="success", message=None,
             latency_ms=round((perf_counter() - started) * 1000))
        return ConversationResponse.model_validate(result)
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="chat.conversation.create", status="failure", message="대화방 생성 실패",
             latency_ms=round((perf_counter() - started) * 1000))
        raise exc


@router.get("", response_model=ConversationListResponse)
def list_conversations(user_id: UUID = Query(..., description="대화방을 조회할 사용자 UUID"), client=Depends(get_supabase)) -> ConversationListResponse:
    """사용자 대화방을 최근 수정 순으로 조회합니다."""
    return ConversationListResponse.model_validate(chat_service.list_conversations(client, user_id))


@router.get("/{conversation_id}/messages", response_model=ChatMessageListResponse)
def list_messages(conversation_id: UUID, user_id: UUID = Query(..., description="대화방 소유자 UUID"), client=Depends(get_supabase)) -> ChatMessageListResponse:
    """대화방 메시지를 시간순으로 조회합니다."""
    return ChatMessageListResponse.model_validate(chat_service.list_messages(client, conversation_id, user_id))


@router.post("/{conversation_id}/messages", response_model=ChatMessageCreateResponse, status_code=201)
def create_message(conversation_id: UUID, payload: ChatMessageCreateRequest, request: Request, client=Depends(get_supabase)) -> ChatMessageCreateResponse:
    """질문을 저장하고 이전 문맥을 포함한 Gemini 답변을 생성합니다."""
    started = perf_counter()
    try:
        result = chat_service.create_message(client, conversation_id, payload)
        _log(client, request, user_id=payload.user_id, action="chat.message", status="success", message=None,
             latency_ms=round((perf_counter() - started) * 1000))
        return ChatMessageCreateResponse.model_validate(result)
    except Exception as exc:
        _log(client, request, user_id=payload.user_id, action="chat.message", status="failure", message="Gemini 채팅 요청 실패",
             latency_ms=round((perf_counter() - started) * 1000))
        raise exc


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: UUID, request: Request, user_id: UUID = Query(..., description="대화방 소유자 UUID"),
                        client=Depends(get_supabase)) -> Response:
    """소유자 대화방과 CASCADE 설정된 메시지를 함께 삭제합니다."""
    started = perf_counter()
    try:
        chat_service.delete_conversation(client, conversation_id, user_id)
        _log(client, request, user_id=user_id, action="chat.conversation.delete", status="success", message=None,
             latency_ms=round((perf_counter() - started) * 1000))
        return Response(status_code=204)
    except Exception as exc:
        _log(client, request, user_id=user_id, action="chat.conversation.delete", status="failure", message="대화방 삭제 실패",
             latency_ms=round((perf_counter() - started) * 1000))
        raise exc
