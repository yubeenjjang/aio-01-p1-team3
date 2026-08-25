"""멀티턴 학습 코치 대화 API의 요청·응답 데이터 형식입니다."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


ChatRole = Literal["user", "model"]


class ConversationCreateRequest(BaseModel):
    user_id: UUID = Field(..., description="대화방 소유자 UUID")
    title: str | None = Field(default=None, min_length=1, max_length=100, description="선택 대화방 제목")


class ConversationResponse(BaseModel):
    conversation_id: UUID = Field(..., description="대화방 UUID")
    title: str = Field(..., description="대화방 제목")
    created_at: datetime = Field(..., description="대화방 생성 시각")
    updated_at: datetime = Field(..., description="대화방 마지막 수정 시각")


class ConversationListItem(BaseModel):
    conversation_id: UUID = Field(..., description="대화방 UUID")
    title: str = Field(..., description="대화방 제목")
    updated_at: datetime = Field(..., description="대화방 마지막 수정 시각")
    message_count: int = Field(..., ge=0, description="대화방 메시지 수")


class ConversationListResponse(BaseModel):
    items: list[ConversationListItem] = Field(default_factory=list, description="대화방 목록")
    total: int = Field(..., ge=0, description="전체 대화방 수")


class ChatMessageResponse(BaseModel):
    message_id: UUID = Field(..., description="메시지 UUID")
    role: ChatRole = Field(..., description="메시지 작성 주체")
    content: str = Field(..., description="메시지 본문")
    created_at: datetime = Field(..., description="메시지 작성 시각")


class ChatMessageListResponse(BaseModel):
    items: list[ChatMessageResponse] = Field(default_factory=list, description="시간순 메시지 목록")
    total: int = Field(..., ge=0, description="전체 메시지 수")


class ChatMessageCreateRequest(BaseModel):
    user_id: UUID = Field(..., description="질문을 보내는 사용자 UUID")
    content: str = Field(..., min_length=1, max_length=5000, description="학습 관련 질문")

    @field_validator("content")
    @classmethod
    def validate_non_blank_content(cls, value: str) -> str:
        """공백만 입력한 질문은 저장하거나 Gemini에 전달하지 않습니다."""
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("content must not be blank")
        return stripped_value


class ChatMessageCreateResponse(BaseModel):
    user_message: ChatMessageResponse = Field(..., description="저장된 사용자 질문")
    model_message: ChatMessageResponse = Field(..., description="저장된 Gemini 답변")
