"""AI 학습 분석 API의 요청·응답 데이터 형식을 정의합니다."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

# model_validator는 여러 입력값의 관계를 함께 검사할 때 사용합니다.

class AnalysisRequest(BaseModel):
    # 종료일이 시작일보다 빠른 경우 아래 validator가 입력 오류로 처리합니다.
    user_id: UUID = Field(..., description="분석할 사용자의 UUID", examples=["123e4567-e89b-12d3-a456-426614174000"])
    period_start: date = Field(..., description="분석 시작일", examples=["2026-08-01"])
    period_end: date = Field(..., description="분석 종료일", examples=["2026-08-31"])

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_start > self.period_end:
            raise ValueError("period_start must not be after period_end")
        return self


class AnalysisResponse(BaseModel):
    summary: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    next_goal: str
