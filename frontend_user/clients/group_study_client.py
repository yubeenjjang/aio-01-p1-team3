# frontend_user/clients/group_study_client.py
"""그룹 스터디 조회·생성·수정·참여 API 호출 함수입니다."""

from typing import Any, Literal

from core.api_client import request


StudyStatus = Literal["recruiting", "closed"]
StudySource = Literal["list", "search"]


def _remove_none(params: dict[str, Any]) -> dict[str, Any]:
    """값이 None인 Query Parameter를 제거합니다."""

    return {
        key: value
        for key, value in params.items()
        if value is not None
    }


def get_studies(
    user_id: str,
    keyword: str | None = None,
    category: str | None = None,
    status: StudyStatus | None = None,
    source: StudySource = "list",
):
    """그룹 스터디 목록을 조회합니다.

    일반 목록과 폴링 조회는 source='list'를 사용합니다.
    사용자가 검색 버튼을 누른 경우 source='search'를 사용합니다.
    """

    params = _remove_none(
        {
            "user_id": user_id,
            "keyword": keyword,
            "category": category,
            "status": status,
            "source": source,
        }
    )

    return request(
        "GET",
        "/studies",
        params=params,
    )


def search_studies(
    user_id: str,
    keyword: str | None = None,
    category: str | None = None,
    status: StudyStatus | None = None,
):
    """사용자가 입력한 조건으로 그룹 스터디를 검색합니다."""

    return get_studies(
        user_id=user_id,
        keyword=keyword,
        category=category,
        status=status,
        source="search",
    )


def get_study(
    study_id: str,
    user_id: str,
):
    """그룹 스터디 상세 정보와 참여자 목록을 조회합니다."""

    return request(
        "GET",
        f"/studies/{study_id}",
        params={
            "user_id": user_id,
        },
    )


def create_study(
    user_id: str,
    title: str,
    category: str,
    goal: str,
    schedule: str,
    capacity: int,
):
    """새로운 그룹 스터디를 생성합니다.

    스터디장은 백엔드에서 자동으로 참여자로 등록됩니다.
    생성 시 기본 모집 상태는 recruiting입니다.
    """

    return request(
        "POST",
        "/studies",
        json={
            "user_id": user_id,
            "title": title,
            "category": category,
            "goal": goal,
            "schedule": schedule,
            "capacity": capacity,
        },
    )


def update_study(
    study_id: str,
    user_id: str,
    title: str,
    category: str,
    goal: str,
    schedule: str,
    capacity: int,
    status: StudyStatus,
):
    """기존 그룹 스터디 정보를 수정합니다."""

    return request(
        "PUT",
        f"/studies/{study_id}",
        json={
            "user_id": user_id,
            "title": title,
            "category": category,
            "goal": goal,
            "schedule": schedule,
            "capacity": capacity,
            "status": status,
        },
    )


def join_study(
    study_id: str,
    user_id: str,
):
    """그룹 스터디에 참여합니다."""

    return request(
        "POST",
        f"/studies/{study_id}/join",
        json={
            "user_id": user_id,
        },
    )


def leave_study(
    study_id: str,
    user_id: str,
):
    """참여 중인 그룹 스터디에서 탈퇴합니다."""

    return request(
        "DELETE",
        f"/studies/{study_id}/join",
        params={
            "user_id": user_id,
        },
    )


def delete_study(study_id: str, user_id: str):
    """스터디장이 자신의 스터디를 삭제합니다."""

    return request(
        "DELETE",
        f"/studies/{study_id}",
        params={"user_id": user_id},
    )
