"""사용자 홈 대시보드 화면입니다."""

import os
from datetime import date, timedelta
from typing import Any

import streamlit as st

from clients.group_study_client import get_studies
from clients.personal_study_client import (
    get_record_stats,
    get_records,
)
from core.api_client import BackendAPIError


# 가짜 로그인 또는 가짜 데이터 모드에서는 API를 호출하지 않습니다.
USE_MOCK_DATA = (
    os.getenv("MOCK_LOGIN", "false").lower() == "true"
    or os.getenv("MOCK_DATA", "false").lower() == "true"
)

SUBJECT_CHART_BASE_MINUTES = 10 * 60


def format_minutes(minutes: Any) -> str:
    """분을 시간과 분 형식으로 변환합니다."""

    try:
        total_minutes = int(minutes or 0)
    except (TypeError, ValueError):
        total_minutes = 0

    hours, remaining_minutes = divmod(
        total_minutes,
        60,
    )

    if hours and remaining_minutes:
        return f"{hours}시간 {remaining_minutes}분"

    if hours:
        return f"{hours}시간"

    return f"{remaining_minutes}분"


def initialize_mock_user() -> None:
    """단독 화면 테스트용 사용자를 설정합니다."""

    if not USE_MOCK_DATA:
        return

    st.session_state.setdefault(
        "user_id",
        "00000000-0000-0000-0000-000000000001",
    )

    st.session_state.setdefault(
        "name",
        "김민지",
    )

    st.session_state.setdefault(
        "role",
        "user",
    )


def get_mock_records() -> list[dict[str, Any]]:
    """화면 테스트용 학습 기록을 반환합니다."""

    today = date.today()

    records = [
        {
            "record_id": "mock-record-001",
            "subject": "Python",
            "content": "함수와 클래스 정리",
            "study_minutes": 80,
            "studied_on": today.isoformat(),
            "proof_image_path": None,
        },
        {
            "record_id": "mock-record-002",
            "subject": "영어",
            "content": "독해와 빈칸 추론 문제",
            "study_minutes": 50,
            "studied_on": today.isoformat(),
            "proof_image_path": None,
        },
        {
            "record_id": "mock-record-003",
            "subject": "물리학",
            "content": "역학과 운동량 보존 법칙",
            "study_minutes": 70,
            "studied_on": (
                today - timedelta(days=1)
            ).isoformat(),
            "proof_image_path": None,
        },
        {
            "record_id": "mock-record-004",
            "subject": "SQL",
            "content": "JOIN과 서브쿼리 학습",
            "study_minutes": 65,
            "studied_on": (
                today - timedelta(days=2)
            ).isoformat(),
            "proof_image_path": None,
        },
        {
            "record_id": "mock-record-005",
            "subject": "Python",
            "content": "자료구조와 알고리즘 복습",
            "study_minutes": 95,
            "studied_on": (
                today - timedelta(days=4)
            ).isoformat(),
            "proof_image_path": None,
        },
        {
            "record_id": "mock-record-006",
            "subject": "영어",
            "content": "영어 단어와 문법 복습",
            "study_minutes": 45,
            "studied_on": (
                today - timedelta(days=6)
            ).isoformat(),
            "proof_image_path": None,
        },
    ]

    deleted_ids = set(
        st.session_state.get(
            "mock_deleted_record_ids",
            [],
        )
    )

    return [
        record
        for record in records
        if record["record_id"] not in deleted_ids
    ]


def build_mock_stats(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """가짜 기록으로 통계를 생성합니다."""

    subject_minutes: dict[str, int] = {}

    for record in records:
        subject = str(
            record.get(
                "subject",
                "미분류",
            )
        )

        study_minutes = int(
            record.get(
                "study_minutes",
                0,
            )
            or 0
        )

        subject_minutes[subject] = (
            subject_minutes.get(subject, 0)
            + study_minutes
        )

    return {
        "total_minutes": sum(
            subject_minutes.values()
        ),
        "by_subject": [
            {
                "subject": subject,
                "minutes": minutes,
            }
            for subject, minutes
            in subject_minutes.items()
        ],
    }


def load_home_data(
    user_id: str,
    period_start: date,
    period_end: date,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """기간별 기록과 통계를 조회합니다."""

    if USE_MOCK_DATA:
        all_records = get_mock_records()
        filtered_records = []

        for record in all_records:
            studied_on = date.fromisoformat(
                str(record["studied_on"])
            )

            if period_start <= studied_on <= period_end:
                filtered_records.append(record)

        return (
            filtered_records,
            build_mock_stats(filtered_records),
        )

    records_response = get_records(
        user_id=user_id,
        date_from=period_start,
        date_to=period_end,
    )

    stats_response = get_record_stats(
        user_id=user_id,
        date_from=period_start,
        date_to=period_end,
    )

    if isinstance(records_response, dict):
        records = records_response.get(
            "items",
            [],
        )
    else:
        records = records_response or []

    if not isinstance(records, list):
        records = []

    if not isinstance(stats_response, dict):
        stats_response = {
            "total_minutes": 0,
            "by_subject": [],
        }

    return records, stats_response


def get_mock_joined_studies() -> list[dict[str, Any]]:
    """화면 테스트용 참여 그룹 목록을 반환합니다."""

    return [
        {
            "study_id": "mock-study-001",
            "title": "매일 Python 스터디",
            "category": "프로그래밍",
            "goal": "매일 한 시간씩 Python 문제를 풀어요.",
            "schedule": "평일 오후 8시",
            "capacity": 6,
            "member_count": 4,
            "status": "recruiting",
            "is_joined": True,
        },
        {
            "study_id": "mock-study-002",
            "title": "영어 단어 함께 외우기",
            "category": "영어",
            "goal": "하루에 단어 30개를 함께 공부해요.",
            "schedule": "매일 오후 9시",
            "capacity": 8,
            "member_count": 8,
            "status": "closed",
            "is_joined": True,
        },
    ]


def load_joined_studies(
    user_id: str,
) -> list[dict[str, Any]]:
    """사용자가 참여 중인 그룹 스터디를 조회합니다."""

    if USE_MOCK_DATA:
        return get_mock_joined_studies()

    response = get_studies(
        user_id=user_id,
        source="list",
    )

    if not isinstance(response, dict):
        return []

    studies = response.get("items", [])

    if not isinstance(studies, list):
        return []

    return [
        study
        for study in studies
        if isinstance(study, dict)
        and study.get("is_joined") is True
    ]


def calculate_today_minutes(
    records: list[dict[str, Any]],
) -> int:
    """오늘 공부 시간을 계산합니다."""

    today_text = date.today().isoformat()

    return sum(
        int(record.get("study_minutes", 0) or 0)
        for record in records
        if str(record.get("studied_on")) == today_text
    )


def calculate_week_minutes(
    records: list[dict[str, Any]],
) -> int:
    """이번 주 공부 시간을 계산합니다."""

    today = date.today()

    week_start = today - timedelta(
        days=today.weekday()
    )

    total_minutes = 0

    for record in records:
        try:
            studied_on = date.fromisoformat(
                str(record.get("studied_on"))
            )
        except (TypeError, ValueError):
            continue

        if week_start <= studied_on <= today:
            total_minutes += int(
                record.get(
                    "study_minutes",
                    0,
                )
                or 0
            )

    return total_minutes


def render_header(user_name: str) -> None:
    """상단 환영 영역을 표시합니다."""

    st.title(f"{user_name}님, 환영합니다! ")
    st.write(
        "오늘도 꾸준한 학습으로 목표를 향해 나아가요!"
    )


def render_summary_cards(
    records: list[dict[str, Any]],
    stats: dict[str, Any],
) -> None:
    """상단 학습 시간 카드 3개를 표시합니다."""

    today_minutes = calculate_today_minutes(
        records
    )

    week_minutes = calculate_week_minutes(
        records
    )

    total_minutes = int(
        stats.get(
            "total_minutes",
            0,
        )
        or 0
    )

    today_record_count = sum(
        1
        for record in records
        if str(record.get("studied_on")) == date.today().isoformat()
    )

    today_column, week_column, total_column = (
        st.columns(
            3
        )
    )

    with today_column:
        with st.container(border=True):
            st.metric(
                "⏱️ 오늘 공부 시간",
                format_minutes(today_minutes),
            )
            st.caption(f"오늘 기록 {today_record_count}개")

    with week_column:
        with st.container(border=True):
            st.metric(
                "🗓️ 이번 주 공부 시간",
                format_minutes(week_minutes),
            )
            st.caption("이번 주 누적 학습 시간")

    with total_column:
        with st.container(border=True):
            st.metric(
                "📊 총 공부 시간",
                format_minutes(total_minutes),
            )
            st.caption("선택한 기간 기준")


def render_subject_chart(
    stats: dict[str, Any],
) -> None:
    """과목별 학습 시간을 가로 막대로 표시합니다."""

    st.subheader("과목별 공부 시간")
    st.caption("단위: 분")

    by_subject = stats.get(
        "by_subject",
        [],
    )

    if not isinstance(by_subject, list):
        by_subject = []

    if not by_subject:
        st.info(
            "표시할 과목별 학습 기록이 없습니다."
        )
        return

    valid_items = [
        item
        for item in by_subject
        if isinstance(item, dict)
    ]

    if not valid_items:
        st.info(
            "표시할 과목별 학습 기록이 없습니다."
        )
        return

    maximum_minutes = max(
        int(item.get("minutes", 0) or 0)
        for item in valid_items
    )

    if maximum_minutes <= 0:
        maximum_minutes = 1

    chart_maximum_minutes = max(
        maximum_minutes,
        SUBJECT_CHART_BASE_MINUTES,
    )

    sorted_items = sorted(
        valid_items,
        key=lambda item: int(
            item.get(
                "minutes",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    for item in sorted_items:
        subject = str(
            item.get(
                "subject",
                "미분류",
            )
        )

        minutes = int(
            item.get(
                "minutes",
                0,
            )
            or 0
        )

        label_column, bar_column, time_column = (
            st.columns(
                [1, 4, 1.4]
            )
        )

        with label_column:
            st.write(subject)

        with bar_column:
            progress_value = int(
                minutes
                / chart_maximum_minutes
                * 100
            )

            st.progress(progress_value)

        with time_column:
            st.write(
                format_minutes(minutes)
            )


def go_to_group_list() -> None:
    """그룹 스터디 목록으로 이동합니다."""

    st.switch_page(
        "app_pages/06_group_study_list.py"
    )


def go_to_group_detail(study_id: str) -> None:
    """선택한 그룹 스터디 상세 화면으로 이동합니다."""

    st.session_state[
        "selected_study_id"
    ] = study_id

    st.switch_page(
        "app_pages/08_group_study_detail.py"
    )


def get_group_status_label(
    status: Any,
    member_count: int = 0,
    capacity: int = 0,
) -> str:
    """그룹 모집 상태를 화면용 문구로 변환합니다."""

    if capacity > 0 and member_count >= capacity:
        return "🔴 모집 완료"

    labels = {
        "recruiting": "🟢 모집 중",
        "closed": "⚪ 모집 종료",
    }

    return labels.get(str(status), "상태 확인 필요")


def render_joined_group_studies(
    studies: list[dict[str, Any]],
) -> None:
    """사용자가 참여 중인 그룹 스터디를 표시합니다."""

    st.markdown(
        """
        <style>
        div[class*="st-key-home_group_detail_"] {
            transform: translateY(-0.45rem);
            margin-bottom: -0.45rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    title_column, list_column = st.columns(
        [4, 1]
    )

    with title_column:
        st.subheader("가입된 그룹 스터디")
        st.caption(
            "현재 참여 중인 그룹을 확인해 보세요."
        )

    with list_column:
        if st.button(
            "바로가기",
            use_container_width=True,
        ):
            go_to_group_list()

    if not studies:
        st.info(
            "아직 가입된 그룹 스터디가 없습니다."
        )

        if st.button(
            "그룹 스터디 찾기",
            type="primary",
            use_container_width=True,
        ):
            go_to_group_list()

        return

    visible_studies = studies[:3]

    for index, study in enumerate(
        visible_studies
    ):
        study_id = str(
            study.get("study_id", "")
        )
        title = str(
            study.get("title")
            or "제목 없는 그룹"
        )
        category = str(
            study.get("category")
            or "미분류"
        )
        goal = str(
            study.get("goal")
            or "등록된 목표가 없습니다."
        )
        schedule = str(
            study.get("schedule")
            or "일정 미정"
        )
        member_count = int(
            study.get("member_count", 0)
            or 0
        )
        capacity = int(
            study.get("capacity", 0)
            or 0
        )
        is_owner = str(
            study.get("owner_user_id") or ""
        ) == str(st.session_state.get("user_id") or "")
        owner_name = str(
            study.get("owner_name")
            or (
                st.session_state.get("name")
                if is_owner
                else "알 수 없음"
            )
        )

        with st.container(border=True):
            title_column, goal_column, status_column = st.columns([3, 3, 1])

            with title_column:
                st.subheader(title)
                st.write(f"👑 스터디장 {owner_name}")
                st.caption(f"📅 {schedule}")

            with goal_column:
                st.markdown("**공동 목표**")
                st.write(goal)
                st.caption(f"🟣 {category}")

            with status_column:
                status_label = get_group_status_label(
                    study.get("status"),
                    member_count=member_count,
                    capacity=capacity,
                )
                st.write(f"**{status_label}**")
                if capacity:
                    st.write(f"👥 참여 {member_count} / {capacity}명")
                else:
                    st.write(f"👥 참여 {member_count}명")

            _, detail_column = st.columns([3, 2])

            with detail_column:
                if st.button(
                    "상세보기",
                    key=(
                        "home_group_detail_"
                        f"{study_id or index}"
                    ),
                    type="primary",
                    use_container_width=True,
                ):
                    go_to_group_detail(study_id)


def render_error(error: Exception) -> None:
    """API 조회 오류를 표시합니다."""

    if isinstance(error, BackendAPIError):
        st.error(error.message)

        if error.trace_id:
            st.caption(
                f"오류 추적 ID: {error.trace_id}"
            )

    else:
        st.error(
            "학습 현황을 불러오지 못했습니다."
        )

        st.caption(str(error))

    if st.button(
        "다시 시도",
        type="primary",
    ):
        st.rerun()


def main() -> None:
    """홈 대시보드를 표시합니다."""

    initialize_mock_user()

    user_id = str(
        st.session_state.get(
            "user_id",
            "",
        )
    )

    user_name = str(
        st.session_state.get(
            "name",
            "사용자",
        )
    )

    if not user_id:
        st.warning(
            "로그인 정보가 없습니다."
        )

        st.info(
            "app.py에서 로그인한 후 다시 확인해 주세요."
        )

        st.stop()

    render_header(user_name)

    today = date.today()
    month_start = today.replace(day=1)

    with st.expander(
        "조회 기간 설정",
        expanded=False,
    ):
        start_column, end_column = st.columns(
            2
        )

        with start_column:
            period_start = st.date_input(
                "시작일",
                value=month_start,
                max_value=today,
            )

        with end_column:
            period_end = st.date_input(
                "종료일",
                value=today,
                max_value=today,
            )

    if period_start > period_end:
        st.error(
            "시작일은 종료일보다 늦을 수 없습니다."
        )

        st.stop()

    try:
        with st.spinner(
            "학습 현황을 불러오는 중입니다..."
        ):
            records, stats = load_home_data(
                user_id=user_id,
                period_start=period_start,
                period_end=period_end,
            )

            joined_studies = load_joined_studies(
                user_id=user_id,
            )

    except Exception as error:
        render_error(error)
        st.stop()

    st.caption(
        f"조회 기간: {period_start} ~ {period_end}"
    )

    render_summary_cards(
        records=records,
        stats=stats,
    )

    st.write("")

    with st.container(border=True):
        render_subject_chart(stats)

    st.write("")

    with st.container(border=True):
        render_joined_group_studies(
            studies=joined_studies,
        )


main()
