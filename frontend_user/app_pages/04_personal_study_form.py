"""개인 학습 기록을 등록하거나 수정하는 입력 페이지입니다."""

from datetime import date
from typing import Any

import streamlit as st

from clients.personal_study_client import (
    create_record,
    get_record,
    update_record,
    upload_proof_image,
)
from core.api_client import BackendAPIError


MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}


def move_to_list() -> None:
    """개인 스터디 목록으로 이동합니다."""

    clear_form_state()
    st.session_state.pop("selected_record_id", None)
    st.switch_page("app_pages/03_personal_study_list.py")


def move_to_detail(record_id: str) -> None:
    """수정한 학습 기록의 상세 화면으로 이동합니다."""

    clear_form_state()
    st.session_state["selected_record_id"] = record_id
    st.switch_page("app_pages/05_personal_study_detail.py")


def clear_form_state() -> None:
    """학습 기록 폼에서 사용하는 세션 값을 제거합니다."""

    keys = [
        "personal_form_context",
        "personal_form_subject",
        "personal_form_minutes",
        "personal_form_date",
        "personal_form_content",
        "personal_form_existing_image",
        "personal_form_errors",
        "personal_form_saving",
    ]

    for key in keys:
        st.session_state.pop(key, None)


def parse_studied_on(value: Any) -> date:
    """API의 학습 날짜 값을 date 객체로 변환합니다."""

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass

    return date.today()


def initialize_create_form() -> None:
    """새 학습 기록 폼의 기본값을 설정합니다."""

    if st.session_state.get("personal_form_context") == "create":
        return

    clear_form_state()
    st.session_state["personal_form_context"] = "create"
    st.session_state["personal_form_subject"] = ""
    st.session_state["personal_form_minutes"] = 60
    st.session_state["personal_form_date"] = date.today()
    st.session_state["personal_form_content"] = ""
    st.session_state["personal_form_existing_image"] = None
    st.session_state["personal_form_errors"] = {}
    st.session_state["personal_form_saving"] = False


def initialize_edit_form(record_id: str, user_id: str) -> bool:
    """수정할 기록을 조회하고 기존 값을 폼에 설정합니다."""

    context = f"edit:{record_id}"

    if st.session_state.get("personal_form_context") == context:
        return True

    try:
        with st.spinner("학습 기록을 불러오는 중입니다."):
            record = get_record(
                record_id=record_id,
                user_id=user_id,
            )
    except BackendAPIError as error:
        if error.status_code == 404 or error.code == "RECORD_NOT_FOUND":
            st.warning("수정할 학습 기록을 찾을 수 없습니다.")
        else:
            st.error(error.message)

        if error.trace_id:
            st.caption(f"추적 ID: {error.trace_id}")

        if st.button("개인 스터디 목록으로"):
            move_to_list()

        return False

    if not isinstance(record, dict):
        st.error("학습 기록 응답 형식이 올바르지 않습니다.")
        return False

    clear_form_state()
    st.session_state["personal_form_context"] = context
    st.session_state["personal_form_subject"] = str(
        record.get("subject") or ""
    )
    st.session_state["personal_form_minutes"] = int(
        record.get("study_minutes") or 60
    )
    st.session_state["personal_form_date"] = parse_studied_on(
        record.get("studied_on")
    )
    st.session_state["personal_form_content"] = str(
        record.get("content") or ""
    )
    st.session_state["personal_form_existing_image"] = record.get(
        "proof_image_path"
    )
    st.session_state["personal_form_errors"] = {}
    st.session_state["personal_form_saving"] = False
    return True


def validate_image(uploaded_file: Any) -> str | None:
    """인증 사진의 확장자와 크기를 프론트엔드에서 먼저 검사합니다."""

    if uploaded_file is None:
        return None

    filename = str(uploaded_file.name)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return "인증 사진은 JPG, JPEG, PNG 파일만 등록할 수 있습니다."

    if uploaded_file.size > MAX_IMAGE_SIZE:
        return "인증 사진은 5MB 이하만 등록할 수 있습니다."

    return None


def validate_form() -> None:
    """학습 기록 입력값을 검사하고 필드별 오류를 저장합니다."""

    errors: dict[str, str] = {}
    subject = str(st.session_state.get("personal_form_subject") or "").strip()
    minutes = int(st.session_state.get("personal_form_minutes") or 0)
    studied_on = st.session_state.get("personal_form_date")
    content = str(st.session_state.get("personal_form_content") or "")
    uploaded_file = st.session_state.get("personal_form_image")

    if not subject:
        errors["subject"] = "과목을 입력해 주세요."
    elif len(subject) > 100:
        errors["subject"] = "과목은 100자 이하로 입력해 주세요."

    if minutes < 1 or minutes > 1440:
        errors["minutes"] = "공부 시간은 1분에서 1,440분 사이여야 합니다."

    if not isinstance(studied_on, date):
        errors["studied_on"] = "학습 날짜를 선택해 주세요."
    elif studied_on > date.today():
        errors["studied_on"] = "미래 날짜는 선택할 수 없습니다."

    if len(content) > 2000:
        errors["content"] = "학습 내용은 2,000자 이하로 입력해 주세요."

    image_error = validate_image(uploaded_file)
    if image_error:
        errors["image"] = image_error

    st.session_state["personal_form_errors"] = errors


def render_field_error(field_name: str) -> None:
    """해당 입력 필드 바로 아래에 오류를 표시합니다."""

    errors = st.session_state.get("personal_form_errors", {})
    message = errors.get(field_name)

    if message:
        st.error(message)


def render_api_error(error: BackendAPIError) -> None:
    """백엔드 표준 오류 응답을 표시합니다."""

    st.error(error.message)

    if error.code:
        st.caption(f"오류 코드: {error.code}")

    if error.trace_id:
        st.caption(f"추적 ID: {error.trace_id}")


def save_record(record_id: str | None, user_id: str) -> None:
    """사진을 업로드한 후 학습 기록을 생성하거나 수정합니다."""

    if st.session_state.get("personal_form_errors"):
        return

    if st.session_state.get("personal_form_saving"):
        st.warning("저장 요청을 처리하고 있습니다.")
        return

    st.session_state["personal_form_saving"] = True
    uploaded_file = st.session_state.get("personal_form_image")
    proof_image_path = st.session_state.get("personal_form_existing_image")

    try:
        if uploaded_file is not None:
            with st.spinner("인증 사진을 업로드하는 중입니다."):
                upload_response = upload_proof_image(
                    user_id=user_id,
                    image=uploaded_file,
                )

            if not isinstance(upload_response, dict) or not upload_response.get(
                "proof_image_path"
            ):
                raise ValueError("인증 사진 업로드 결과를 확인할 수 없습니다.")

            proof_image_path = str(upload_response["proof_image_path"])

        payload = {
            "user_id": user_id,
            "subject": st.session_state.personal_form_subject.strip(),
            "study_minutes": int(st.session_state.personal_form_minutes),
            "studied_on": st.session_state.personal_form_date,
            "content": st.session_state.personal_form_content.strip() or None,
            "proof_image_path": proof_image_path,
        }

        with st.spinner("학습 기록을 저장하는 중입니다."):
            if record_id:
                update_record(record_id=record_id, **payload)
                st.session_state["personal_detail_message"] = (
                    "학습 기록이 수정되었습니다."
                )
                move_to_detail(record_id)
            else:
                create_record(**payload)
                st.session_state["personal_list_message"] = (
                    "학습 기록이 등록되었습니다."
                )
                move_to_list()

    except BackendAPIError as error:
        render_api_error(error)
    except Exception as error:
        st.error("학습 기록을 저장하지 못했습니다.")
        st.caption(str(error))
    finally:
        st.session_state["personal_form_saving"] = False


def render_form(record_id: str | None, user_id: str) -> None:
    """설계서의 개인 학습 기록 등록·수정 폼을 표시합니다."""

    is_edit_mode = bool(record_id)
    st.title("학습 기록 수정" if is_edit_mode else "학습 기록 등록")

    with st.form("personal_study_form"):
        st.text_input(
            "과목",
            key="personal_form_subject",
            max_chars=100,
            placeholder="예: Python",
        )
        render_field_error("subject")

        st.number_input(
            "공부 시간(분)",
            min_value=1,
            max_value=1440,
            step=10,
            key="personal_form_minutes",
        )
        render_field_error("minutes")

        st.date_input(
            "학습 날짜",
            max_value=date.today(),
            key="personal_form_date",
        )
        render_field_error("studied_on")

        st.text_area(
            "학습 내용",
            key="personal_form_content",
            max_chars=2000,
            height=160,
            placeholder="학습한 내용을 입력하세요",
        )
        render_field_error("content")

        existing_image = st.session_state.get("personal_form_existing_image")
        if existing_image:
            st.info("기존 인증 사진이 있습니다. 새 파일을 선택하면 교체됩니다.")
            st.caption(str(existing_image))

        st.file_uploader(
            "인증 사진",
            type=["jpg", "jpeg", "png"],
            key="personal_form_image",
            help="JPG, JPEG, PNG 형식 · 최대 5MB",
        )
        render_field_error("image")

        cancel_column, save_column = st.columns(2)

        with cancel_column:
            cancelled = st.form_submit_button(
                "취소",
                use_container_width=True,
            )

        with save_column:
            submitted = st.form_submit_button(
                "저장",
                type="primary",
                use_container_width=True,
                on_click=validate_form,
                disabled=st.session_state.personal_form_saving,
            )

    if cancelled:
        if record_id:
            move_to_detail(record_id)
        else:
            move_to_list()

    if submitted:
        save_record(record_id, user_id)


def main() -> None:
    """개인 학습 기록 등록·수정 페이지를 실행합니다."""

    user_id = str(st.session_state.get("user_id") or "")
    record_id = str(st.session_state.get("selected_record_id") or "")

    if not user_id:
        st.warning("로그인 정보가 없습니다. 다시 로그인해 주세요.")
        st.stop()

    if record_id:
        if not initialize_edit_form(record_id, user_id):
            return
    else:
        initialize_create_form()

    if st.button("← 개인 스터디 목록"):
        move_to_list()

    render_form(record_id or None, user_id)


main()
