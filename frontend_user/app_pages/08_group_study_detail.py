# frontend_user/app_pages/08_group_study_detail.py
"""그룹 스터디 상세 정보와 참여자를 조회하고 참여 상태를 관리합니다."""

from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from clients.group_study_client import delete_study, get_study, join_study, leave_study
from core.api_client import BackendAPIError


def apply_page_style() -> None:
    """상세 제목과 분야 사이의 간격을 간결하게 조정합니다."""

    st.markdown(
        """
        <style>
        .group-detail-title {
            color: #182033;
            font-size: 2.75rem;
            font-weight: 700;
            line-height: 1.2;
            margin: 0 0 0.2rem;
        }
        .group-detail-category {
            color: #7a8298;
            font-size: 0.875rem;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def move_to_list() -> None:
    """그룹 스터디 목록 화면으로 이동합니다."""

    st.session_state.pop("selected_study_id", None)
    st.switch_page("app_pages/06_group_study_list.py")


def move_to_edit(study_id: str) -> None:
    """현재 그룹 스터디를 수정하는 화면으로 이동합니다."""

    st.session_state["selected_study_id"] = study_id
    st.session_state["group_study_form_mode"] = "edit"
    st.switch_page("app_pages/07_group_study_form.py")


def get_status_label(status: str) -> str:
    """API 모집 상태를 화면 표시용 한글로 변환합니다."""

    labels = {
        "recruiting": "🟢 모집 중",
        "closed": "⚪ 모집 종료",
    }
    return labels.get(status, status or "상태 미정")


def format_joined_at(value: Any) -> str:
    """참여 시각을 읽기 쉬운 문자열로 변환합니다."""

    if not value:
        return ""

    text = str(value)

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return text


def load_detail(study_id: str, user_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """그룹 스터디 상세 정보와 참여자 목록을 조회합니다."""

    response = get_study(
        study_id=study_id,
        user_id=user_id,
    )

    if not isinstance(response, dict):
        raise ValueError("그룹 스터디 응답 형식이 올바르지 않습니다.")

    study = response.get("study")
    members = response.get("members", [])

    if not isinstance(study, dict):
        raise ValueError("그룹 스터디 상세 정보가 없습니다.")

    if not isinstance(members, list):
        members = []

    valid_members = [
        member
        for member in members
        if isinstance(member, dict)
    ]

    return study, valid_members


def render_members(members: list[dict[str, Any]], owner_user_id: str) -> None:
    """참여자 목록과 스터디장 표시를 출력합니다."""

    st.subheader("참여자")

    if not members:
        st.info("표시할 참여자가 없습니다.")
        return

    for member in members:
        member_user_id = str(member.get("user_id") or "")
        member_name = member.get("name") or "이름 없음"
        joined_at = format_joined_at(member.get("joined_at"))

        with st.container(border=True):
            name_column, date_column = st.columns([2, 1])

            with name_column:
                if member_user_id == owner_user_id:
                    st.markdown(f"**👑 {member_name} · 스터디장**")
                else:
                    st.markdown(f"**👤 {member_name}**")

            with date_column:
                if joined_at:
                    st.caption(f"참여일 {joined_at}")


def render_action_error(error: BackendAPIError) -> None:
    """참여·탈퇴 API 오류를 표준 형식으로 표시합니다."""

    if error.code == "STUDY_FULL":
        st.error("스터디 정원이 모두 찼습니다.")
    elif error.code == "STUDY_CLOSED":
        st.error("모집이 종료된 스터디입니다.")
    elif error.code == "ALREADY_JOINED":
        st.warning("이미 참여 중인 스터디입니다.")
    else:
        st.error(error.message)

    if error.code:
        st.caption(f"오류 코드: {error.code}")

    if error.trace_id:
        st.caption(f"추적 ID: {error.trace_id}")


def request_join(study_id: str, user_id: str) -> None:
    """현재 사용자의 그룹 스터디 참여를 요청합니다."""

    try:
        with st.spinner("스터디에 참여하는 중입니다."):
            join_study(
                study_id=study_id,
                user_id=user_id,
            )
    except BackendAPIError as error:
        render_action_error(error)
        return

    st.session_state["group_detail_message"] = "스터디에 참여했습니다."
    st.rerun(scope="fragment")


def request_leave(study_id: str, user_id: str) -> None:
    """현재 사용자의 그룹 스터디 탈퇴를 요청합니다."""

    try:
        with st.spinner("스터디에서 탈퇴하는 중입니다."):
            leave_study(
                study_id=study_id,
                user_id=user_id,
            )
    except BackendAPIError as error:
        render_action_error(error)
        return

    st.session_state["group_detail_message"] = "스터디에서 탈퇴했습니다."
    st.rerun()


@st.dialog("그룹 스터디 탈퇴")
def render_leave_confirmation(study_id: str, user_id: str) -> None:
    """팝업에서 그룹 스터디 탈퇴 여부를 확인합니다."""

    st.warning("그룹 스터디에서 탈퇴할까요?")
    st.caption("탈퇴 후 다시 참여하려면 모집 중이고 정원에 여유가 있어야 합니다.")

    cancel_column, confirm_column = st.columns(2)

    with cancel_column:
        if st.button(
            "취소",
            key="cancel_leave_study",
            use_container_width=True,
        ):
            st.rerun()

    with confirm_column:
        if st.button(
            "탈퇴 확인",
            key="confirm_leave_study",
            type="primary",
            use_container_width=True,
        ):
            request_leave(study_id, user_id)


def request_delete(study_id: str, user_id: str) -> None:
    try:
        with st.spinner("스터디를 삭제하는 중입니다."):
            delete_study(study_id, user_id)
    except BackendAPIError as error:
        render_action_error(error)
        return

    st.session_state.pop("selected_study_id", None)
    st.session_state.pop("confirm_delete_study", None)
    st.session_state["group_success_message"] = "스터디를 삭제했습니다."
    st.switch_page("app_pages/06_group_study_list.py")


def render_study_detail(
    study: dict[str, Any],
    members: list[dict[str, Any]],
    study_id: str,
    user_id: str,
) -> None:
    """설계서에 맞춰 그룹 상세 정보와 사용자 액션을 표시합니다."""

    title = study.get("title") or "제목 없음"
    category = study.get("category") or "분야 미지정"
    goal = study.get("goal") or "등록된 공동 목표가 없습니다."
    schedule = study.get("schedule") or "활동 일정 미정"
    status = str(study.get("status") or "")
    capacity = int(study.get("capacity") or 0)
    member_count = int(study.get("member_count") or len(members))
    owner_user_id = str(study.get("owner_user_id") or "")
    is_joined = bool(study.get("is_joined"))
    is_owner = owner_user_id == user_id

    title_column, status_column = st.columns([4, 1])

    with title_column:
        st.markdown(
            f'<h1 class="group-detail-title">{escape(str(title))}</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p class="group-detail-category">분야 · {escape(str(category))}</p>',
            unsafe_allow_html=True,
        )

    with status_column:
        st.write(f"**{get_status_label(status)}**")
        st.write(f"**참여 {member_count} / {capacity}명**")

    st.divider()

    with st.container(border=True):
        st.subheader("공동 목표")
        st.write(goal)

    with st.container(border=True):
        st.subheader("진행 일정")
        st.write(schedule)

    # description, start_date, end_date는 현재 MVP 응답에 없으므로
    # 설계서의 확장 항목에 따라 화면에서 표시하지 않습니다.

    st.divider()

    if is_owner:
        st.success("내가 스터디장인 그룹 스터디입니다.")
        edit_column, delete_column = st.columns(2)

        with edit_column:
            if st.button(
                "그룹 수정",
                key=f"edit_{study_id}",
                use_container_width=True,
            ):
                move_to_edit(study_id)

        with delete_column:
            if st.button(
                "스터디 삭제",
                key=f"delete_{study_id}",
                use_container_width=True,
            ):
                st.session_state["confirm_delete_study"] = True
    elif is_joined:
        if st.button(
            "탈퇴하기",
            key=f"leave_{study_id}",
            use_container_width=True,
        ):
            render_leave_confirmation(study_id, user_id)
    elif status == "closed":
        st.button(
            "모집이 종료되었습니다",
            key=f"closed_{study_id}",
            disabled=True,
            use_container_width=True,
        )
    elif member_count >= capacity:
        st.button(
            "정원이 모두 찼습니다",
            key=f"full_{study_id}",
            disabled=True,
            use_container_width=True,
        )
    elif st.button(
        "참여하기",
        key=f"join_{study_id}",
        type="primary",
        use_container_width=True,
    ):
        request_join(study_id, user_id)

    if is_owner and st.session_state.get("confirm_delete_study"):
        st.warning("삭제하면 참여자 정보도 함께 삭제되며 되돌릴 수 없습니다.")
        cancel_column, confirm_column = st.columns(2)
        with cancel_column:
            if st.button("취소", key=f"cancel_delete_{study_id}", use_container_width=True):
                st.session_state["confirm_delete_study"] = False
                st.rerun(scope="fragment")
        with confirm_column:
            if st.button("삭제 확인", key=f"confirm_delete_{study_id}", type="primary", use_container_width=True):
                request_delete(study_id, user_id)

    st.divider()
    render_members(members, owner_user_id)


@st.fragment(run_every="120s")
def render_auto_refresh_detail(study_id: str, user_id: str) -> None:
    """상세 정보와 참여자 목록을 2분마다 다시 조회합니다."""

    message = st.session_state.pop("group_detail_message", None)

    if message:
        st.success(message)

    back_column, info_column, refresh_column = st.columns(
        [4, 1.6, 1],
        vertical_alignment="center",
    )

    with back_column:
        if st.button("← 그룹 스터디", key="back_to_group_list"):
            move_to_list()

    with info_column:
        st.caption(
            "마지막 조회: "
            f"{datetime.now().strftime('%H:%M:%S')}  \n"
            "2분마다 자동 갱신"
        )

    with refresh_column:
        if st.button(
            "새로고침",
            key="refresh_group_detail",
            use_container_width=True,
        ):
            st.rerun(scope="fragment")

    st.divider()


    try:
        with st.spinner("그룹 스터디 상세 정보를 불러오는 중입니다."):
            study, members = load_detail(study_id, user_id)

    except BackendAPIError as error:
        if error.status_code == 404 or error.code == "STUDY_NOT_FOUND":
            st.session_state.pop("selected_study_id", None)
            st.switch_page("app_pages/06_group_study_list.py")

        st.error(error.message)

        if error.code:
            st.caption(f"오류 코드: {error.code}")

        if error.trace_id:
            st.caption(f"추적 ID: {error.trace_id}")

        if st.button("다시 시도", key="detail_retry"):
            st.rerun(scope="fragment")

        return

    except Exception as error:
        st.error("그룹 스터디 상세 정보를 불러오지 못했습니다.")
        st.caption(str(error))

        if st.button("다시 시도", key="detail_unknown_retry"):
            st.rerun(scope="fragment")

        return

    render_study_detail(
        study=study,
        members=members,
        study_id=study_id,
        user_id=user_id,
    )


def main() -> None:
    """그룹 스터디 상세 페이지를 실행합니다."""

    apply_page_style()
    user_id = str(st.session_state.get("user_id") or "")
    study_id = str(st.session_state.get("selected_study_id") or "")

    if not user_id:
        st.warning("로그인 정보가 없습니다. 다시 로그인해 주세요.")
        st.stop()

    if not study_id:
        st.warning("선택된 그룹 스터디가 없습니다.")

        if st.button("그룹 스터디 목록으로 이동"):
            move_to_list()

        st.stop()

    success_message = st.session_state.pop("group_success_message", None)

    if success_message:
        st.success(success_message)

    render_auto_refresh_detail(study_id, user_id)


main()
