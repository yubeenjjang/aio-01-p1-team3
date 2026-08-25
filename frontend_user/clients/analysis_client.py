"""AI 학습 분석 API 호출 함수입니다."""

from datetime import date
from typing import Any

from core.api_client import request


def _date_value(value: date | str) -> str:
    """date 객체와 문자열 모두 API의 YYYY-MM-DD 형식으로 변환합니다."""
    return value.isoformat() if isinstance(value, date) else value


def request_analysis(
    *,
    user_id: str,
    period_start: date | str,
    period_end: date | str,
) -> dict[str, Any]:
    """선택한 기간의 학습 기록을 AI로 분석합니다."""
    return request(
        "POST",
        "/analyses",
        json={
            "user_id": user_id,
            "period_start": _date_value(period_start),
            "period_end": _date_value(period_end),
        },
    )


# 기존 화면 코드에서 읽기 쉬운 이름으로도 사용할 수 있게 둡니다.
create_analysis = request_analysis

# frontend_user/clients/analysis_client.py
"""사용자의 학습 기록을 기반으로 AI 분석을 요청하는 API 함수입니다."""

from datetime import date
from typing import Any

from core.api_client import request


def _date_value(value: date | str) -> str:
    """date 객체를 API 요청용 YYYY-MM-DD 문자열로 변환합니다."""

    if isinstance(value, date):
        return value.isoformat()

    return value


def create_analysis(
    user_id: str,
    period_start: date | str,
    period_end: date | str,
) -> dict[str, Any]:
    """지정한 기간의 학습 기록을 AI로 분석합니다.

    Args:
        user_id: 로그인한 사용자의 UUID
        period_start: 분석 시작일
        period_end: 분석 종료일

    Returns:
        summary, strengths, improvements, next_goal이 포함된 분석 결과
    """

    if not user_id:
        raise ValueError("사용자 ID가 필요합니다.")

    start_date = _date_value(period_start)
    end_date = _date_value(period_end)

    if start_date > end_date:
        raise ValueError("분석 시작일은 종료일보다 늦을 수 없습니다.")

    return request(
        "POST",
        "/analyses",
        json={
            "user_id": user_id,
            "period_start": start_date,
            "period_end": end_date,
        },
    )