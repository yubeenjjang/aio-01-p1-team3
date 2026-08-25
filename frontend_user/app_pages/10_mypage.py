"""로그인한 사용자의 세션 정보와 로그아웃 기능을 표시합니다."""

import os

import streamlit as st

from clients.auth_client import logout_user
from core.api_client import BackendAPIError
from core.auth import clear_user_scoped_state, init_state, is_logged_in, logout


USE_MOCK_LOGIN = os.getenv("MOCK_LOGIN", "false").lower() == "true"


def initialize_mock_user() -> None:
    """MOCK_LOGIN=true일 때 마이페이지 단독 테스트 사용자를 설정합니다."""

    if not USE_MOCK_LOGIN:
        return

    st.session_state.setdefault("logged_in", True)
    st.session_state.setdefault(
        "user_id",
        "00000000-0000-0000-0000-000000000001",
    )
    st.session_state.setdefault("name", "김학습")
    st.session_state.setdefault("email", "student@example.com")
    st.session_state.setdefault("role", "user")


def get_role_label(role: str) -> str:
    """로그인 응답의 역할 값을 화면 표시용 한글로 변환합니다."""

    labels = {
        "user": "사용자",
        "admin": "관리자",
    }
    return labels.get(role, role or "사용자")


def clear_user_page_state() -> None:
    """다른 사용자가 이전 사용자의 화면 데이터를 보지 않도록 제거합니다."""
    clear_user_scoped_state()


def process_logout(user_id: str) -> None:
    """백엔드 로그아웃 후 로컬 로그인 세션을 초기화합니다."""

    try:
        # 개발용 가짜 로그인은 백엔드 사용자 세션이 없습니다.
        if not USE_MOCK_LOGIN and user_id:
            with st.spinner("로그아웃하는 중입니다."):
                logout_user(user_id)

    except BackendAPIError:
        # 서버 요청이 실패해도 현재 브라우저의 로그인 정보는 제거합니다.
        pass

    finally:
        clear_user_page_state()
        logout()
        st.rerun()


def render_profile(user_name: str, role_label: str) -> None:
    """MVP 기본 프로필 이미지와 사용자 이름을 표시합니다."""

    with st.container(border=True):
        icon_column, information_column = st.columns([1, 5])

        with icon_column:
            # 실제 프로필 이미지는 GET /auth/me 확장 이후 교체합니다.
            st.markdown("# 👤")

        with information_column:
            st.subheader(user_name)
            st.caption(role_label)


def render_member_information(
    user_name: str,
    user_email: str,
    role_label: str,
    user_id: str,
) -> None:
    """설계서의 이름·이메일·역할과 로그아웃 버튼을 표시합니다."""

    with st.container(border=True):
        st.subheader("회원 정보")

        name_label, name_value = st.columns([1, 4])
        with name_label:
            st.markdown("**이름**")
        with name_value:
            st.write(user_name)

        st.divider()

        email_label, email_value = st.columns([1, 4])
        with email_label:
            st.markdown("**이메일**")
        with email_value:
            if user_email:
                st.write(user_email)
            else:
                st.caption("로그인 세션에 이메일 정보가 없습니다.")

        st.divider()

        role_name_column, role_value_column = st.columns([1, 4])
        with role_name_column:
            st.markdown("**역할**")
        with role_value_column:
            st.write(role_label)

        st.divider()

        if st.button(
            "로그아웃",
            type="primary",
            use_container_width=True,
        ):
            process_logout(user_id)


def main() -> None:
    """마이페이지를 실행합니다."""

    init_state()
    initialize_mock_user()

    if not is_logged_in():
        st.warning("로그인이 필요한 화면입니다.")
        st.stop()

    user_id = str(st.session_state.get("user_id") or "")
    user_name = str(st.session_state.get("name") or "사용자")
    user_email = str(st.session_state.get("email") or "")
    user_role = str(st.session_state.get("role") or "user")
    role_label = get_role_label(user_role)

    st.title("마이페이지")
    st.write("내 정보를 확인할 수 있어요.")

    st.write("")
    render_profile(user_name, role_label)

    st.write("")
    render_member_information(
        user_name=user_name,
        user_email=user_email,
        role_label=role_label,
        user_id=user_id,
    )


main()
