# frontend_user/app_pages/07_group_study_form.py

# frontend_user/app_pages/07_group_study_form.py
"""그룹 스터디를 생성하거나 수정하는 입력 페이지입니다."""

import re
from typing import Any

import streamlit as st

from clients.group_study_client import (
    create_study,
    get_study,
    update_study,
)
from core.api_client import BackendAPIError


CATEGORY_OPTIONS = [
    "프론트엔드",
    "백엔드",
    "AI",
    "데이터",
    "알고리즘",
    "자격증",
    "기타",
]

STATUS_OPTIONS = [
    "모집 중",
    "모집 종료",
]

WEEKDAY_OPTIONS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
PERIOD_OPTIONS = ["오전", "오후"]
HOUR_OPTIONS = list(range(1, 13))


def build_schedule() -> str:
    """선택한 요일과 시작·종료 시각을 API에 저장할 일정 문구로 만듭니다."""

    days = st.session_state.get("group_form_days", [])
    start_period = st.session_state.get("group_form_start_period", "오후")
    start_hour = int(st.session_state.get("group_form_start_hour", 7))
    end_period = st.session_state.get("group_form_end_period", "오후")
    end_hour = int(st.session_state.get("group_form_end_hour", 9))

    if not days:
        return ""

    day_text = " · ".join(day.replace("요일", "") for day in days)
    return f"{day_text} | {start_period} {start_hour}시 ~ {end_period} {end_hour}시"


def load_schedule_selection(schedule: str) -> None:
    """기존 일정 문구에서 가능한 범위의 값을 폼 선택값으로 복원합니다."""

    st.session_state["group_form_days"] = [
        day for day in WEEKDAY_OPTIONS if day[0] in schedule
    ]
    if not st.session_state["group_form_days"]:
        st.session_state["group_form_days"] = ["월요일"]

    matches = re.findall(r"(오전|오후)\s*(\d{1,2})", schedule)
    if len(matches) >= 2:
        start_period, start_hour = matches[0]
        end_period, end_hour = matches[1]
        st.session_state["group_form_start_period"] = start_period
        st.session_state["group_form_start_hour"] = int(start_hour) if int(start_hour) in HOUR_OPTIONS else 7
        st.session_state["group_form_end_period"] = end_period
        st.session_state["group_form_end_hour"] = int(end_hour) if int(end_hour) in HOUR_OPTIONS else 9
    else:
        st.session_state["group_form_start_period"] = "오후"
        st.session_state["group_form_start_hour"] = 7
        st.session_state["group_form_end_period"] = "오후"
        st.session_state["group_form_end_hour"] = 9


def get_status_label(status: str) -> str:
    """API 모집 상태를 화면 표시 값으로 변환합니다."""

    status_mapping = {
        "recruiting": "모집 중",
        "closed": "모집 종료",
    }

    return status_mapping.get(status, "모집 중")


def get_status_value(status_label: str) -> str:
    """화면 모집 상태를 API 요청 값으로 변환합니다."""

    status_mapping = {
        "모집 중": "recruiting",
        "모집 종료": "closed",
    }

    return status_mapping.get(status_label, "recruiting")


def clear_form_state() -> None:
    """그룹 스터디 입력 화면에서 사용한 세션 값을 제거합니다."""

    keys = [
        "group_form_context",
        "group_form_title",
        "group_form_category",
        "group_form_goal",
        "group_form_schedule",
        "group_form_days",
        "group_form_start_period",
        "group_form_start_hour",
        "group_form_end_period",
        "group_form_end_hour",
        "group_form_capacity",
        "group_form_status",
        "group_form_owner_user_id",
        "group_form_errors",
    ]

    for key in keys:
        st.session_state.pop(key, None)


def initialize_create_form() -> None:
    """그룹 생성 화면의 기본값을 설정합니다."""

    if st.session_state.get("group_form_context") == "create":
        return

    clear_form_state()

    st.session_state["group_form_context"] = "create"
    st.session_state["group_form_title"] = ""
    st.session_state["group_form_category"] = CATEGORY_OPTIONS[0]
    st.session_state["group_form_goal"] = ""
    st.session_state["group_form_schedule"] = ""
    load_schedule_selection("")
    st.session_state["group_form_capacity"] = 2
    st.session_state["group_form_status"] = "모집 중"
    st.session_state["group_form_owner_user_id"] = ""
    st.session_state["group_form_errors"] = {}


def initialize_edit_form(
    study_id: str,
    user_id: str,
) -> bool:
    """기존 그룹 스터디를 조회하여 수정 화면에 표시합니다."""

    context = f"edit:{study_id}"

    if st.session_state.get("group_form_context") == context:
        return True

    try:
        with st.spinner("그룹 스터디 정보를 불러오는 중입니다."):
            response = get_study(
                study_id=study_id,
                user_id=user_id,
            )

    except BackendAPIError as error:
        st.error(error.message)

        if error.code:
            st.caption(f"오류 코드: {error.code}")

        if error.trace_id:
            st.caption(f"추적 ID: {error.trace_id}")

        if st.button("그룹 목록으로 돌아가기"):
            clear_form_state()
            st.switch_page("app_pages/06_group_study_list.py")

        return False

    if not isinstance(response, dict):
        st.error("그룹 스터디 응답 형식이 올바르지 않습니다.")
        return False

    study = response.get("study", response)

    if not isinstance(study, dict):
        st.error("그룹 스터디 정보를 확인할 수 없습니다.")
        return False

    owner_user_id = str(study.get("owner_user_id") or "")

    # 설계서 기준으로 그룹 스터디장만 수정할 수 있습니다.
    if owner_user_id and owner_user_id != user_id:
        st.error("그룹 스터디장만 스터디를 수정할 수 있습니다.")

        if st.button("그룹 상세로 돌아가기"):
            st.switch_page("app_pages/08_group_study_detail.py")

        return False

    category = str(study.get("category") or "기타")

    # 백엔드에 기존 선택지 외의 분야가 저장된 경우에도 표시합니다.
    if category not in CATEGORY_OPTIONS:
        CATEGORY_OPTIONS.append(category)

    clear_form_state()

    st.session_state["group_form_context"] = context
    st.session_state["group_form_title"] = str(
        study.get("title") or ""
    )
    st.session_state["group_form_category"] = category
    st.session_state["group_form_goal"] = str(
        study.get("goal") or ""
    )
    st.session_state["group_form_schedule"] = str(
        study.get("schedule") or ""
    )
    load_schedule_selection(st.session_state["group_form_schedule"])
    st.session_state["group_form_capacity"] = int(
        study.get("capacity") or 2
    )
    st.session_state["group_form_status"] = get_status_label(
        str(study.get("status") or "recruiting")
    )
    st.session_state["group_form_owner_user_id"] = owner_user_id
    st.session_state["group_form_errors"] = {}

    return True


def validate_form() -> None:
    """입력값을 검사하고 필드별 오류를 세션에 저장합니다."""

    errors: dict[str, str] = {}

    title = str(
        st.session_state.get("group_form_title") or ""
    ).strip()

    category = str(
        st.session_state.get("group_form_category") or ""
    ).strip()

    goal = str(
        st.session_state.get("group_form_goal") or ""
    ).strip()

    schedule = build_schedule()
    st.session_state["group_form_schedule"] = schedule

    capacity = int(
        st.session_state.get("group_form_capacity") or 0
    )

    if not title:
        errors["title"] = "그룹명을 입력해 주세요."
    elif len(title) > 100:
        errors["title"] = "그룹명은 100자 이하로 입력해 주세요."

    if not category:
        errors["category"] = "분야를 선택해 주세요."

    if not goal:
        errors["goal"] = "공동 목표를 입력해 주세요."

    if not schedule:
        errors["schedule"] = "활동 일정을 입력해 주세요."

    if capacity < 2:
        errors["capacity"] = "모집 인원은 최소 2명입니다."
    elif capacity > 20:
        errors["capacity"] = "모집 인원은 최대 20명입니다."

    st.session_state["group_form_errors"] = errors


def render_field_error(field_name: str) -> None:
    """해당 입력 필드 아래에 검증 오류를 표시합니다."""

    errors = st.session_state.get(
        "group_form_errors",
        {},
    )

    message = errors.get(field_name)

    if message:
        st.error(message)


def move_to_list() -> None:
    """그룹 스터디 목록으로 이동합니다."""

    clear_form_state()
    st.session_state["group_study_form_mode"] = "create"
    st.switch_page("app_pages/06_group_study_list.py")


def move_to_detail(study_id: str) -> None:
    """저장한 그룹 스터디 상세 화면으로 이동합니다."""

    clear_form_state()
    st.session_state["selected_study_id"] = study_id
    st.session_state["group_study_form_mode"] = "create"
    st.switch_page("app_pages/08_group_study_detail.py")


def save_study(
    *,
    is_edit_mode: bool,
    study_id: str | None,
    user_id: str,
) -> None:
    """검증을 통과한 그룹 스터디를 생성하거나 수정합니다."""

    errors = st.session_state.get(
        "group_form_errors",
        {},
    )

    if errors:
        return

    title = st.session_state.group_form_title.strip()
    category = st.session_state.group_form_category
    goal = st.session_state.group_form_goal.strip()
    schedule = build_schedule()
    capacity = int(st.session_state.group_form_capacity)

    try:
        with st.spinner("그룹 스터디를 저장하는 중입니다."):
            if is_edit_mode:
                if not study_id:
                    st.error("수정할 그룹 스터디 ID가 없습니다.")
                    return

                response = update_study(
                    study_id=study_id,
                    user_id=user_id,
                    title=title,
                    category=category,
                    goal=goal,
                    schedule=schedule,
                    capacity=capacity,
                    status=get_status_value(
                        st.session_state.group_form_status
                    ),
                )

                saved_study_id = study_id

            else:
                response = create_study(
                    user_id=user_id,
                    title=title,
                    category=category,
                    goal=goal,
                    schedule=schedule,
                    capacity=capacity,
                )

                if not isinstance(response, dict):
                    st.error("그룹 생성 응답 형식이 올바르지 않습니다.")
                    return

                saved_study_id = str(
                    response.get("study_id") or ""
                )

                if not saved_study_id:
                    st.error("생성된 그룹 스터디 ID가 없습니다.")
                    return

    except BackendAPIError as error:
        st.error(error.message)

        if error.code:
            st.caption(f"오류 코드: {error.code}")

        if error.trace_id:
            st.caption(f"추적 ID: {error.trace_id}")

        return

    except Exception as error:
        st.error("그룹 스터디를 저장하지 못했습니다.")
        st.caption(str(error))
        return

    st.session_state["group_success_message"] = (
        "그룹 스터디가 수정되었습니다."
        if is_edit_mode
        else "그룹 스터디가 생성되었습니다."
    )

    move_to_detail(saved_study_id)


def render_form(
    *,
    is_edit_mode: bool,
    study_id: str | None,
    user_id: str,
) -> None:
    """그룹 생성·수정 입력 화면을 표시합니다."""

    page_title = (
        "그룹 수정"
        if is_edit_mode
        else "그룹 생성"
    )

    st.title(page_title)
    st.write("그룹 스터디 정보를 입력해 주세요.")

    with st.form("group_study_form"):
        st.text_input(
            "그룹명",
            key="group_form_title",
            max_chars=100,
            placeholder="그룹 스터디 이름을 입력하세요",
        )
        render_field_error("title")

        st.selectbox(
            "분야",
            options=CATEGORY_OPTIONS,
            key="group_form_category",
        )
        render_field_error("category")

        st.text_area(
            "공동 목표",
            key="group_form_goal",
            placeholder="함께 달성할 목표를 입력하세요",
            height=120,
        )
        render_field_error("goal")

        st.multiselect(
            "활동 요일",
            options=WEEKDAY_OPTIONS,
            key="group_form_days",
            placeholder="활동할 요일을 선택하세요",
        )

        start_period_column, start_hour_column, end_period_column, end_hour_column = st.columns(4)
        with start_period_column:
            st.selectbox("시작", options=PERIOD_OPTIONS, key="group_form_start_period")
        with start_hour_column:
            st.selectbox("시작 시각", options=HOUR_OPTIONS, key="group_form_start_hour", format_func=lambda hour: f"{hour}시")
        with end_period_column:
            st.selectbox("종료", options=PERIOD_OPTIONS, key="group_form_end_period")
        with end_hour_column:
            st.selectbox("종료 시각", options=HOUR_OPTIONS, key="group_form_end_hour", format_func=lambda hour: f"{hour}시")

        st.caption(f"선택된 일정: {build_schedule() or '요일을 선택해 주세요.'}")
        render_field_error("schedule")


        st.number_input(
            "모집 인원",
            min_value=2,
            max_value=20,
            step=1,
            key="group_form_capacity",
        )
        render_field_error("capacity")

        if is_edit_mode:
            st.selectbox(
                "모집 상태",
                options=STATUS_OPTIONS,
                key="group_form_status",
            )
        else:
            st.selectbox(
                "모집 상태",
                options=["모집 중"],
                key="group_form_status",
                disabled=True,
                help="새 그룹은 모집 중 상태로 생성됩니다.",
            )

        cancel_column, save_column = st.columns(2)

        with cancel_column:
            cancel_submitted = st.form_submit_button(
                "취소",
                use_container_width=True,
            )

        with save_column:
            save_submitted = st.form_submit_button(
                "저장",
                type="primary",
                use_container_width=True,
                on_click=validate_form,
            )

    if cancel_submitted:
        if is_edit_mode and study_id:
            clear_form_state()
            st.session_state["selected_study_id"] = study_id
            st.switch_page("app_pages/08_group_study_detail.py")
        else:
            move_to_list()

    if save_submitted:
        save_study(
            is_edit_mode=is_edit_mode,
            study_id=study_id,
            user_id=user_id,
        )


def main() -> None:
    """그룹 생성·수정 페이지를 실행합니다."""

    user_id = str(
        st.session_state.get("user_id") or ""
    )

    if not user_id:
        st.warning("로그인 정보가 없습니다. 다시 로그인해 주세요.")
        st.stop()

    mode = st.session_state.get(
        "group_study_form_mode",
        "create",
    )

    selected_study_id = str(
        st.session_state.get("selected_study_id") or ""
    )

    is_edit_mode = (
        mode == "edit"
        and bool(selected_study_id)
    )

    if is_edit_mode:
        initialized = initialize_edit_form(
            study_id=selected_study_id,
            user_id=user_id,
        )

        if not initialized:
            return

    else:
        initialize_create_form()

    render_form(
        is_edit_mode=is_edit_mode,
        study_id=(
            selected_study_id
            if is_edit_mode
            else None
        ),
        user_id=user_id,
    )


main()
