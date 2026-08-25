"""AI 분석 평가 API의 요청·응답 데이터 형식입니다."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class FeedbackRequest(BaseModel):
    user_id: UUID = Field(..., description="평가를 작성하는 사용자 UUID")
    period_start: date = Field(..., description="평가 대상 분석 시작일")
    period_end: date = Field(..., description="평가 대상 분석 종료일")
    rating: int = Field(..., ge=1, le=5, description="분석 만족도 평점")
    comment: str | None = Field(default=None, max_length=1000, description="선택 의견")

    @model_validator(mode="after")
    def validate_period(self) -> "FeedbackRequest":
        if self.period_start > self.period_end:
            raise ValueError("period_start must not be after period_end")
        return self


class FeedbackResponse(BaseModel):
    feedback_id: UUID = Field(..., description="평가 UUID")
    period_start: date = Field(..., description="평가 대상 분석 시작일")
    period_end: date = Field(..., description="평가 대상 분석 종료일")
    rating: int = Field(..., ge=1, le=5, description="분석 만족도 평점")
    comment: str | None = Field(default=None, description="선택 의견")
    created_at: datetime = Field(..., description="최초 작성 시각")
    updated_at: datetime = Field(..., description="마지막 수정 시각")


class AdminFeedbackItem(FeedbackResponse):
    user_id: UUID = Field(..., description="평가 작성자 UUID")
    user_name: str | None = Field(default=None, description="평가 작성자 이름")


class AdminFeedbackListResponse(BaseModel):
    items: list[AdminFeedbackItem] = Field(default_factory=list, description="관리자 평가 목록")
    total: int = Field(..., ge=0, description="전체 평가 수")
    average_rating: float | None = Field(default=None, ge=1, le=5, description="전체 평균 평점")
    rating_distribution: dict[str, int] = Field(default_factory=dict, description="현재 필터 기준 평점별 응답 수")
