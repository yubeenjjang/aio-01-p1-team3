"""개인 학습 기록과 인증 사진 API의 요청·응답 데이터 형식을 정의합니다."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

# Field의 min_length, ge, le 값은 잘못된 입력을 서버 진입 전에 막아 줍니다.

class RecordRequest(BaseModel):
    # proof_image_path는 업로드 API가 반환한 Storage 경로만 저장합니다.
    user_id: UUID = Field(..., description="학습 기록을 작성할 사용자의 UUID", examples=["123e4567-e89b-12d3-a456-426614174000"])
    subject: str = Field(..., min_length=1, max_length=100, description="학습 과목", examples=["Python"])
    content: str | None = Field(default=None, max_length=2000, description="학습한 내용", examples=["FastAPI 학습"])
    study_minutes: int = Field(..., ge=1, le=1440, description="학습 시간(분)", examples=[90])
    studied_on: date = Field(..., description="학습한 날짜", examples=["2026-08-10"])
    proof_image_path: str | None = Field(default=None, description="업로드한 인증 사진의 Storage 경로", examples=["records/user-id/proof.png"])


class RecordResponse(BaseModel):
    record_id: UUID
    subject: str
    content: str | None = None
    study_minutes: int
    studied_on: date
    proof_image_path: str | None = None
    proof_image_url: str | None = None


class RecordListResponse(BaseModel):
    items: list[RecordResponse]
    total: int


class SubjectStat(BaseModel):
    subject: str
    minutes: int


class RecordStatsResponse(BaseModel):
    total_minutes: int
    by_subject: list[SubjectStat]


class ProofImageUploadResponse(BaseModel):
    proof_image_path: str
