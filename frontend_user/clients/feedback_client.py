"""AI 분석 사용자 평가 API 호출 함수입니다."""

from datetime import date
from typing import Any

from core.api_client import request


def _date_text(value: date | str) -> str:
    return value.isoformat() if isinstance(value, date) else value


def get_analysis_feedback(
    user_id: str,
    period_start: date | str,
    period_end: date | str,
) -> dict[str, Any]:
    return request(
        "GET",
        "/analyses/feedback",
        params={
            "user_id": user_id,
            "period_start": _date_text(period_start),
            "period_end": _date_text(period_end),
        },
    )


def save_analysis_feedback(
    user_id: str,
    period_start: date | str,
    period_end: date | str,
    rating: int,
    comment: str = "",
) -> dict[str, Any]:
    if rating not in range(1, 6):
        raise ValueError("평점은 1점부터 5점까지 선택해 주세요.")
    if len(comment) > 1000:
        raise ValueError("의견은 1000자 이내로 입력해 주세요.")
    return request(
        "POST",
        "/analyses/feedback",
        json={
            "user_id": user_id,
            "period_start": _date_text(period_start),
            "period_end": _date_text(period_end),
            "rating": rating,
            "comment": comment.strip() or None,
        },
    )
