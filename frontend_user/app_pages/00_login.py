"""오케퐁터디 사용자 로그인 화면입니다."""

import base64
import os
from pathlib import Path

import streamlit as st

from clients.auth_client import login_user
from core.api_client import BackendAPIError
from core.auth import login, save_auth_session


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


@st.cache_data
def image_data_uri(image_path: str) -> str:
    """원본 이미지를 브라우저가 직접 축소해 표시할 수 있는 데이터 URI로 변환합니다."""

    encoded_image = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def process_login(email: str, password: str) -> None:
    """로그인 API를 호출하고 사용자 정보를 세션에 저장합니다."""

    if not email.strip() or not password:
        st.error("이메일과 비밀번호를 입력해 주세요.")
        return

    try:
        with st.spinner("로그인 중입니다..."):
            user = login_user(
                email.strip(),
                password,
            )

        login(user)
        st.session_state.email = email.strip()
        save_auth_session()
        st.rerun()

    except BackendAPIError as error:
        st.error(error.message)

        if error.trace_id:
            st.caption(f"오류 추적 ID: {error.trace_id}")

    except ValueError as error:
        st.error(str(error))


def login_as_mock_user() -> None:
    """개발 환경에서 사용할 테스트 사용자로 로그인합니다."""

    fake_user = {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "name": "테스트 사용자",
        "role": "user",
    }

    login(fake_user)
    st.session_state.email = "test@example.com"
    save_auth_session()
    st.rerun()


def render_service_features() -> None:
    """서비스의 세 가지 핵심 기능을 세로로 쌓인 가로형 카드로 표시합니다."""

    st.markdown(
        '<div class="auth-section-title">오케퐁터디로 할 수 있어요</div>',
        unsafe_allow_html=True,
    )

    features = (
        (
            "login-personal-study.png",
            "개인 스터디",
            "학습 내용과 시간을 간편하게 기록하고<br>관리해요.",
        ),
        (
            "login-ai-analysis.png",
            "AI 분석",
            "학습 기록을 분석해 나에게 맞는<br>인사이트를 확인해요.",
        ),
        (
            "login-group-study.png",
            "그룹 스터디",
            "같은 목표를 가진 사람들과 함께 공부해요.",
        ),
    )

    feature_cards = "".join(
        f'<div class="auth-feature-card">'
        f'<img class="auth-feature-image" '
        f'src="{image_data_uri(str(ASSET_DIR / image_name))}" '
        f'alt="{title} 이미지" />'
        f'<div class="auth-feature-copy"><strong>{title}</strong>'
        f'<span>{description}</span></div></div>'
        for image_name, title, description in features
    )

    st.markdown(
        f'<div class="auth-feature-list">{feature_cards}</div>',
        unsafe_allow_html=True,
    )


def render_login_panel() -> None:
    """로그인과 회원가입 이동 영역을 표시합니다."""

    with st.container(border=True):
        st.markdown('<span class="auth-login-card-marker"></span>', unsafe_allow_html=True)
        st.markdown('<div class="auth-login-title">🔐 로그인</div>', unsafe_allow_html=True)
        st.caption("오케퐁터디 계정으로 시작해 보세요.")

        with st.form("login_form"):
            email = st.text_input(
                "이메일",
                placeholder="user@example.com",
            )

            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="비밀번호를 입력하세요",
            )

            login_submitted = st.form_submit_button(
                "로그인",
                type="primary",
                use_container_width=True,
            )

        if login_submitted:
            process_login(email, password)

        st.divider()

        if st.button(
            "처음이신가요? 회원가입",
            use_container_width=True,
        ):
            st.switch_page("app_pages/01_signup.py")

        mock_login_enabled = (
            os.getenv("MOCK_LOGIN", "false").lower()
            == "true"
        )

        if mock_login_enabled:
            if st.button(
                "테스트 사용자로 로그인",
                use_container_width=True,
            ):
                login_as_mock_user()


def main() -> None:
    """로그인 페이지를 실행합니다."""

    st.markdown(
        '<div class="auth-page-marker"></div>',
        unsafe_allow_html=True,
    )

    signup_success_message = st.session_state.pop(
        "signup_success_message",
        None,
    )

    if signup_success_message:
        st.markdown('<div class="auth-success-spacer"></div>', unsafe_allow_html=True)
        st.success(signup_success_message)

    st.title("오케퐁터디")
    st.markdown(
        '<div class="auth-subtitle">기록하고, 함께 공부하고, AI로 성장하는 학습 공간</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="auth-header-divider"></div>', unsafe_allow_html=True)

    feature_column, login_column = st.columns(
        [1.75, 1.05],
        gap="large",
        vertical_alignment="top",
    )

    with feature_column:
        render_service_features()

    with login_column:
        st.markdown('<div class="auth-login-offset"></div>', unsafe_allow_html=True)
        render_login_panel()


main()
