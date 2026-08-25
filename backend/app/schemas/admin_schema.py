"""관리자 대시보드와 운영 로그 API의 응답 데이터 형식을 정의합니다."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SubjectMinutes(BaseModel):
    subject: str
    minutes: int = Field(ge=0)


class AIMetrics(BaseModel):
    request_count: int = Field(ge=0)
    success_count: int = Field(ge=0)
    failure_count: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=100)
    failure_rate: float = Field(ge=0, le=100)
    average_latency_ms: float | None = Field(default=None, ge=0)


class DashboardResponse(BaseModel):
    user_count: int = Field(ge=0)
    study_count: int = Field(ge=0)
    record_count: int = Field(ge=0)
    subject_minutes: list[SubjectMinutes]
    study_status_counts: dict[str, int]
    action_counts: dict[str, int]
    ai_metrics: AIMetrics
    failure_count: int = Field(ge=0)


class OperationLogResponse(BaseModel):
    log_id: int
    created_at: datetime
    user_id: UUID | None = None
    user_name: str | None = None
    action: str
    status: str
    message: str | None = None
    latency_ms: int | None = None
    trace_id: UUID


class OperationLogListResponse(BaseModel):
    items: list[OperationLogResponse]
    total: int
