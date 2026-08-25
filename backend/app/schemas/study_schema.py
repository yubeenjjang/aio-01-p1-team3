"""그룹 스터디 API의 요청·응답 데이터 형식을 정의합니다."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Literal은 정해진 문자열 값 중 하나만 입력받도록 제한합니다.

StudyStatus = Literal["recruiting", "closed"]


class StudyCreateRequest(BaseModel):
    # 수정 요청도 이 모델을 상속하므로 생성·수정 입력 형식이 동일합니다.
    user_id: UUID = Field(..., description="스터디를 생성하거나 수정하는 사용자의 UUID", examples=["123e4567-e89b-12d3-a456-426614174000"])
    title: str = Field(..., min_length=1, max_length=100, description="스터디 제목", examples=["FastAPI 스터디"])
    category: str = Field(..., min_length=1, max_length=100, description="스터디 분야 또는 과목", examples=["백엔드"])
    goal: str = Field(..., min_length=1, description="공동 학습 목표", examples=["CRUD 완성"])
    schedule: str = Field(..., min_length=1, max_length=200, description="스터디 활동 일정", examples=["월·수 19:00"])
    capacity: int = Field(..., ge=2, le=20, description="최대 참여 인원", examples=[5])
    status: StudyStatus = Field(default="recruiting", description="모집 상태", examples=["recruiting"])


class StudyUpdateRequest(StudyCreateRequest):
    pass


class StudyJoinRequest(BaseModel):
    # 참여 요청에는 참여할 사용자 식별자만 필요합니다.
    user_id: UUID = Field(..., description="스터디에 참여할 사용자의 UUID", examples=["123e4567-e89b-12d3-a456-426614174000"])


class StudyMemberResponse(BaseModel):
    user_id: UUID
    name: str
    joined_at: datetime


class StudyResponse(BaseModel):
    study_id: UUID
    owner_user_id: UUID
    owner_name: str = "알 수 없음"
    title: str
    category: str
    goal: str
    schedule: str
    capacity: int
    member_count: int
    status: StudyStatus
    is_joined: bool


class StudyListResponse(BaseModel):
    items: list[StudyResponse]
    total: int


class StudyDetailResponse(BaseModel):
    study: StudyResponse
    members: list[StudyMemberResponse]


class StudyCreateResponse(BaseModel):
    study_id: UUID
    title: str
    status: StudyStatus
    member_count: int


class StudyJoinResponse(BaseModel):
    message: str
