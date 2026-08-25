"""일반 사용자 계정을 생성하는 회원가입 페이지입니다."""

import re

import streamlit as st

from clients.auth_client import signup_user
from core.api_client import BackendAPIError


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def initialize_page_state() -> None:
    """회원가입 입력과 오류 상태를 초기화합니다."""

    defaults = {
        "signup_name": "",
        "signup_email": "",
        "signup_password": "",
        "signup_password_confirm": "",
        "signup_errors": {},
        "signup_general_error": "",
        "signup_submitting": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_signup_state() -> None:
    """회원가입 화면에서 사용한 세션 값을 제거합니다."""

    keys = [
        "signup_name",
        "signup_email",
        "signup_password",
        "signup_password_confirm",
        "signup_errors",
        "signup_general_error",
        "signup_submitting",
    ]

    for key in keys:
        st.session_state.pop(key, None)


def move_to_login() -> None:
    """로그인 화면으로 이동합니다."""

    clear_signup_state()
    st.switch_page("app_pages/00_login.py")


def validate_signup_form() -> None:
    """입력값을 검사하고 필드별 오류를 저장합니다."""

    errors: dict[str, str] = {}
    name = str(st.session_state.get("signup_name") or "").strip()
    email = str(st.session_state.get("signup_email") or "").strip()
    password = str(st.session_state.get("signup_password") or "")
    password_confirm = str(
        st.session_state.get("signup_password_confirm") or ""
    )

    if not name:
        errors["name"] = "이름을 입력해 주세요."
    elif len(name) > 50:
        errors["name"] = "이름은 50자 이하로 입력해 주세요."

    if not email:
        errors["email"] = "이메일을 입력해 주세요."
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "올바른 이메일 형식을 입력해 주세요."

    if not password:
        errors["password"] = "비밀번호를 입력해 주세요."
    elif len(password) < 8:
        errors["password"] = "비밀번호는 8자 이상 입력해 주세요."
    elif len(password) > 100:
        errors["password"] = "비밀번호는 100자 이하로 입력해 주세요."

    if not password_confirm:
        errors["password_confirm"] = "비밀번호를 한 번 더 입력해 주세요."
    elif password != password_confirm:
        errors["password_confirm"] = "비밀번호가 일치하지 않습니다."

    st.session_state["signup_errors"] = errors
    st.session_state["signup_general_error"] = ""


def render_field_error(field_name: str) -> None:
    """입력 필드 바로 아래에 오류 메시지를 표시합니다."""

    errors = st.session_state.get("signup_errors", {})
    message = errors.get(field_name)

    if message:
        st.error(message)


def process_signup() -> None:
    """회원가입 API를 호출하고 성공하면 로그인 화면으로 이동합니다."""

    if st.session_state.get("signup_errors"):
        return

    if st.session_state.get("signup_submitting"):
        return

    st.session_state["signup_submitting"] = True

    try:
        with st.spinner("회원가입을 처리하는 중입니다."):
            signup_user(
                name=st.session_state.signup_name.strip(),
                email=st.session_state.signup_email.strip(),
                password=st.session_state.signup_password,
            )

        st.session_state["signup_success_message"] = (
            "회원가입이 완료되었습니다. 로그인해 주세요."
        )
        move_to_login()

    except BackendAPIError as error:
        if error.code == "EMAIL_DUPLICATED" or error.status_code == 409:
            errors = dict(st.session_state.get("signup_errors", {}))
            errors["email"] = "이미 사용 중인 이메일입니다."
            st.session_state["signup_errors"] = errors
        else:
            st.session_state["signup_general_error"] = error.message

            if error.trace_id:
                st.session_state["signup_general_error"] += (
                    f" · 추적 ID: {error.trace_id}"
                )

        st.rerun()

    except Exception as error:
        st.session_state["signup_general_error"] = str(error)
        st.rerun()

    finally:
        st.session_state["signup_submitting"] = False


def main() -> None:
    """회원가입 페이지를 실행합니다."""

    initialize_page_state()

    st.markdown(
        '<div class="auth-page-marker"></div>',
        unsafe_allow_html=True,
    )

    st.title("회원가입")
    st.markdown(
        '<div class="auth-subtitle">오케퐁터디와 함께 학습 관리를 시작해 보세요</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    general_error = st.session_state.get("signup_general_error")
    if general_error:
        st.error(general_error)

    left_space, signup_area, right_space = st.columns(
        [1, 2, 1]
    )

    with signup_area:
        with st.container(border=True):
            st.subheader("계정 정보")
            st.caption("모든 항목을 입력해 주세요.")

            with st.form("standalone_signup_form"):
                st.text_input(
                    "이름",
                    key="signup_name",
                    max_chars=50,
                    placeholder="이름을 입력하세요",
                )
                render_field_error("name")

                st.text_input(
                    "이메일",
                    key="signup_email",
                    placeholder="user@example.com",
                )
                render_field_error("email")

                st.text_input(
                    "비밀번호",
                    type="password",
                    key="signup_password",
                    max_chars=100,
                    placeholder="8자 이상 입력하세요",
                )
                render_field_error("password")

                st.text_input(
                    "비밀번호 확인",
                    type="password",
                    key="signup_password_confirm",
                    max_chars=100,
                    placeholder="비밀번호를 다시 입력하세요",
                )
                render_field_error("password_confirm")

                cancel_column, signup_column = st.columns(2)

                with cancel_column:
                    cancelled = st.form_submit_button(
                        "취소",
                        use_container_width=True,
                    )

                with signup_column:
                    submitted = st.form_submit_button(
                        "회원가입",
                        type="primary",
                        use_container_width=True,
                        on_click=validate_signup_form,
                        disabled=st.session_state.signup_submitting,
                    )

    if cancelled:
        move_to_login()

    if submitted:
        process_signup()


main()
