"""선택한 개인 학습 기록을 조회·수정·삭제하는 상세 페이지입니다."""

from typing import Any

import streamlit as st

from clients.personal_study_client import delete_record, get_record
from core.api_client import BackendAPIError


def move_to_list() -> None:
    """개인 스터디 목록으로 이동합니다."""

    st.session_state.pop("selected_record_id", None)
    st.switch_page("app_pages/03_personal_study_list.py")


def move_to_edit(record_id: str) -> None:
    """현재 학습 기록의 수정 폼으로 이동합니다."""

    st.session_state["selected_record_id"] = record_id
    st.session_state.pop("personal_form_context", None)
    st.switch_page("app_pages/04_personal_study_form.py")


def format_minutes(value: Any) -> str:
    """분 단위 학습 시간을 읽기 쉬운 문자열로 변환합니다."""

    try:
        minutes = int(value or 0)
    except (TypeError, ValueError):
        minutes = 0

    hours, remaining = divmod(minutes, 60)

    if hours and remaining:
        return f"{hours}시간 {remaining}분"
    if hours:
        return f"{hours}시간"
    return f"{remaining}분"


def load_record(record_id: str, user_id: str) -> dict[str, Any]:
    """백엔드에서 선택한 학습 기록을 조회합니다."""

    response = get_record(
        record_id=record_id,
        user_id=user_id,
    )

    if not isinstance(response, dict):
        raise ValueError("학습 기록 응답 형식이 올바르지 않습니다.")

    return response


def render_image_preview(image_url: Any, image_path: Any) -> None:
    """백엔드가 반환한 인증 사진 URL을 화면에 표시합니다."""

    st.subheader("인증 사진")

    if not image_path:
        st.caption("등록된 인증 사진이 없습니다.")
        return

    image_value = str(image_url or image_path)

    if image_value.startswith(("http://", "https://", "data:image")):
        left_space, image_column, right_space = st.columns(
            [1, 2, 1]
        )

        with image_column:
            st.image(
                image_value,
                caption="학습 인증 사진",
                use_container_width=True,
            )
    else:
        st.warning("인증 사진을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")


def render_record(record: dict[str, Any], record_id: str, user_id: str) -> None:
    """설계서에 맞춰 학습 기록 상세 정보를 표시합니다."""

    subject = record.get("subject") or "과목 없음"
    studied_on = record.get("studied_on") or "-"
    study_minutes = format_minutes(record.get("study_minutes"))
    content = record.get("content") or "작성된 학습 내용이 없습니다."

    st.title(f"{subject} 학습 기록")

    with st.container(border=True):
        date_column, time_column = st.columns(2)

        with date_column:
            st.caption("학습 날짜")
            st.subheader(str(studied_on))

        with time_column:
            st.caption("학습 시간")
            st.subheader(study_minutes)

        st.divider()
        st.subheader("학습 내용")
        st.write(content)

        st.divider()
        render_image_preview(
            record.get("proof_image_url"),
            record.get("proof_image_path"),
        )

    edit_column, delete_column = st.columns(2)

    with edit_column:
        if st.button(
            "수정",
            type="primary",
            use_container_width=True,
        ):
            move_to_edit(record_id)

    with delete_column:
        if st.button(
            "삭제",
            use_container_width=True,
        ):
            render_delete_confirmation(record_id, user_id)


@st.dialog("학습 기록 삭제")
def render_delete_confirmation(record_id: str, user_id: str) -> None:
    """팝업에서 삭제 확인을 받고 성공하면 목록으로 이동합니다."""

    st.warning("학습 기록을 삭제할까요? 삭제한 기록은 복구할 수 없습니다.")

    cancel_column, confirm_column = st.columns(2)

    with cancel_column:
        if st.button(
            "취소",
            key="cancel_record_delete",
            use_container_width=True,
        ):
            st.rerun()

    with confirm_column:
        if st.button(
            "삭제 확인",
            key="confirm_record_delete",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner("학습 기록을 삭제하는 중입니다."):
                    delete_record(
                        record_id=record_id,
                        user_id=user_id,
                    )
            except BackendAPIError as error:
                st.error(error.message)

                if error.code:
                    st.caption(f"오류 코드: {error.code}")

                if error.trace_id:
                    st.caption(f"추적 ID: {error.trace_id}")

                return
            except Exception as error:
                st.error("학습 기록을 삭제하지 못했습니다.")
                st.caption(str(error))
                return

            st.session_state["personal_list_message"] = (
                "학습 기록이 삭제되었습니다."
            )
            move_to_list()


def render_load_error(error: BackendAPIError) -> None:
    """상세 조회 오류를 설계서의 상태 처리에 맞춰 표시합니다."""

    if error.status_code == 404 or error.code == "RECORD_NOT_FOUND":
        st.session_state["personal_list_message"] = (
            "요청한 학습 기록을 찾을 수 없습니다."
        )
        move_to_list()

    st.error(error.message)

    if error.code:
        st.caption(f"오류 코드: {error.code}")

    if error.trace_id:
        st.caption(f"추적 ID: {error.trace_id}")

    retry_column, list_column = st.columns(2)

    with retry_column:
        if st.button("다시 시도", type="primary", use_container_width=True):
            st.rerun()

    with list_column:
        if st.button("목록으로", use_container_width=True):
            move_to_list()


def main() -> None:
    """개인 학습 기록 상세 페이지를 실행합니다."""

    user_id = str(st.session_state.get("user_id") or "")
    record_id = str(st.session_state.get("selected_record_id") or "")

    if not user_id:
        st.warning("로그인 정보가 없습니다. 다시 로그인해 주세요.")
        st.stop()

    if st.button("← 개인 스터디"):
        move_to_list()

    message = st.session_state.pop("personal_detail_message", None)
    if message:
        st.success(message)

    if not record_id:
        st.info("선택된 학습 기록이 없습니다.")

        if st.button("학습 기록 목록으로 이동"):
            move_to_list()

        st.stop()

    try:
        with st.spinner("학습 기록을 불러오는 중입니다."):
            record = load_record(record_id, user_id)
    except BackendAPIError as error:
        render_load_error(error)
        return
    except Exception as error:
        st.error("학습 기록을 불러오지 못했습니다.")
        st.caption(str(error))

        if st.button("목록으로 돌아가기"):
            move_to_list()

        return

    render_record(record, record_id, user_id)


main()
