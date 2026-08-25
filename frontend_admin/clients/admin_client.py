"""관리자 대시보드·운영 로그·분석 평가 API 호출 함수입니다."""

from datetime import date
from typing import Literal

from core.api_client import request


LogStatus = Literal["success", "failure"]


def get_dashboard(user_id: str):
    """서비스 운영 KPI와 집계 데이터를 조회합니다."""

    return request(
        "GET",
        "/admin/dashboard",
        params={"user_id": user_id},
    )


def get_logs(
    user_id: str,
    status: LogStatus | None = None,
    action: str | None = None,
    limit: int = 50,
):
    """상태와 action 조건으로 운영 로그를 조회합니다."""

    params = {
        "user_id": user_id,
        "limit": limit,
    }

    if status is not None:
        params["status"] = status

    if action is not None:
        params["action"] = action

    return request(
        "GET",
        "/admin/logs",
        params=params,
    )


def get_analysis_feedback(
    user_id: str,
    rating: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """사용자 AI 분석 평가 목록과 평균 평점을 조회합니다."""

    params = {
        "user_id": user_id,
        "limit": limit,
        "offset": offset,
    }
    if rating is not None:
        params["rating"] = rating
    if date_from is not None:
        params["from"] = date_from.isoformat()
    if date_to is not None:
        params["to"] = date_to.isoformat()

    return request(
        "GET",
        "/admin/analysis-feedback",
        params=params,
    )
