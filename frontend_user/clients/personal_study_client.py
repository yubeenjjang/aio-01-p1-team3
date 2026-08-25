# frontend_user/clients/personal_study_client.py

"""개인 학습 기록과 통계 API 호출 함수입니다."""

from datetime import date
from typing import Any


from core.api_client import request


def _date_value(value: date | str | None) -> str | None:
    """date 값을 API 요청에 사용할 문자열로 변환합니다."""

    if isinstance(value, date):
        return value.isoformat()

    return value


def _remove_none(params: dict[str, Any]) -> dict[str, Any]:
    """값이 None인 Query Parameter를 제거합니다."""

    return {
        key: value
        for key, value in params.items()
        if value is not None
    }


def get_records(
    user_id: str,
    date_from: date | str | None = None,
    date_to: date | str | None = None,
    subject: str | None = None,
):
    """사용자의 개인 학습 기록 목록을 조회합니다."""

    params = _remove_none(
        {
            "user_id": user_id,
            "from": _date_value(date_from),
            "to": _date_value(date_to),
            "subject": subject,
        }
    )

    return request(
        "GET",
        "/records",
        params=params,
    )


def get_record(
    record_id: str,
    user_id: str,
):
    """개인 학습 기록 상세 정보를 조회합니다."""

    return request(
        "GET",
        f"/records/{record_id}",
        params={
            "user_id": user_id,
        },
    )


def create_record(
    user_id: str,
    subject: str,
    study_minutes: int,
    studied_on: date | str,
    content: str | None = None,
    proof_image_path: str | None = None,
):
    """새로운 개인 학습 기록을 등록합니다."""

    return request(
        "POST",
        "/records",
        json={
            "user_id": user_id,
            "subject": subject,
            "content": content,
            "study_minutes": study_minutes,
            "studied_on": _date_value(studied_on),
            "proof_image_path": proof_image_path,
        },
    )


def update_record(
    record_id: str,
    user_id: str,
    subject: str,
    study_minutes: int,
    studied_on: date | str,
    content: str | None = None,
    proof_image_path: str | None = None,
):
    """기존 개인 학습 기록을 수정합니다."""

    return request(
        "PUT",
        f"/records/{record_id}",
        json={
            "user_id": user_id,
            "subject": subject,
            "content": content,
            "study_minutes": study_minutes,
            "studied_on": _date_value(studied_on),
            "proof_image_path": proof_image_path,
        },
    )


def delete_record(
    record_id: str,
    user_id: str,
):
    """개인 학습 기록을 삭제합니다."""

    return request(
        "DELETE",
        f"/records/{record_id}",
        params={
            "user_id": user_id,
        },
    )


def get_record_stats(
    user_id: str,
    date_from: date | str | None = None,
    date_to: date | str | None = None,
):
    """기간별 전체 및 과목별 학습 시간을 조회합니다."""

    params = _remove_none(
        {
            "user_id": user_id,
            "from": _date_value(date_from),
            "to": _date_value(date_to),
        }
    )

    return request(
        "GET",
        "/records/stats",
        params=params,
    )


def upload_proof_image(
    user_id: str,
    image: Any,
):
    """학습 인증 사진을 업로드하고 저장 경로를 반환합니다."""

    files = {
        "file": (
            image.name,
            image.getvalue(),
            image.type or "application/octet-stream",
        )
    }

    return request(
        "POST",
        "/uploads/proof-image",
        data={
            "user_id": user_id,
        },
        files=files,
    )