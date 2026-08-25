"""관리자 역할을 확인하고 관리자 앱 로그인을 처리합니다."""

import os

import streamlit as st

from clients.auth_client import login_admin
from core.api_client import BackendAPIError
from core.auth import login


def process_login(email: str, password: str) -> None:
    """로그인 API 호출 후 admin 역할만 세션에 저장합니다."""

    try:
        with st.spinner("관리자 계정을 확인하는 중입니다."):
            response = login_admin(email, password)

        if not isinstance(response, dict):
            raise ValueError("로그인 응답 형식이 올바르지 않습니다.")

        login(response, email=email)
        st.rerun()

    except PermissionError:
        st.error("관리자 계정만 접근할 수 있습니다.")
    except BackendAPIError as error:
        st.error(error.message)

        if error.code:
            st.caption(f"오류 코드: {error.code}")

        if error.trace_id:
            st.caption(f"추적 ID: {error.trace_id}")
    except ValueError as error:
        st.error(str(error))


def main() -> None:
    """관리자 로그인 페이지를 실행합니다."""

    st.title("오케퐁터디 관리자")
    st.write("관리자 계정으로 로그인해 주세요.")

    with st.container(border=True):
        with st.form("admin_login_form"):
            email = st.text_input(
                "이메일",
                placeholder="admin@exam.com",
            )
            password = st.text_input(
                "비밀번호",
                type="password",
            )
            submitted = st.form_submit_button(
                "관리자 로그인",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if not email.strip():
                st.error("이메일을 입력해 주세요.")
            elif not password:
                st.error("비밀번호를 입력해 주세요.")
            else:
                process_login(email.strip(), password)

    if os.getenv("MOCK_ADMIN_LOGIN", "false").lower() == "true":
        st.divider()
        st.warning("개발용 관리자 로그인이 활성화되어 있습니다.")

        if st.button("테스트 관리자로 로그인", use_container_width=True):
            login(
                {
                    "user_id": "00000000-0000-0000-0000-000000000099",
                    "name": "테스트 관리자",
                    "role": "admin",
                },
                email="admin@example.com",
            )
            st.rerun()


main()
