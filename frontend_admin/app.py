"""로그인 역할에 따라 관리자 페이지 접근과 메뉴를 구성합니다."""

import streamlit as st

from clients.auth_client import logout_admin
from components.admin_shell import apply_admin_shell, render_admin_sidebar
from core.api_client import BackendAPIError
from core.auth import init_state, is_admin, is_logged_in, logout


st.set_page_config(
    page_title="오케퐁터디 관리자",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()
apply_admin_shell()


login_page = st.Page(
    "app_pages/00_login.py",
    title="관리자 로그인",
    icon="🔐",
    default=True,
)

dashboard_page = st.Page(
    "app_pages/01_dashboard.py",
    title="관리자 대시보드",
    icon="📊",
    default=True,
)

logs_page = st.Page(
    "app_pages/02_logs.py",
    title="운영 로그",
    icon="📋",
)

feedback_page = st.Page(
    "app_pages/03_analysis_feedback.py",
    title="AI 분석 평가",
    icon="⭐",
)


def process_logout() -> None:
    """백엔드와 관리자 화면의 로그아웃을 처리합니다."""

    user_id = str(st.session_state.get("user_id") or "")

    try:
        if user_id:
            logout_admin(user_id)
    except BackendAPIError:
        # 서버 로그아웃 실패 여부와 관계없이 로컬 관리자 세션은 종료합니다.
        pass
    finally:
        logout()
        st.rerun()


if is_logged_in() and not is_admin():
    # 일반 사용자 정보가 관리자 앱 세션에 남아 있어도 접근을 허용하지 않습니다.
    logout()


if not is_admin():
    # 로그아웃 뒤에도 이전 Streamlit sidebar 컨테이너가 남지 않도록 숨깁니다.
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    navigation = st.navigation(
        [login_page],
        position="hidden",
    )
else:
    navigation = st.navigation(
        [dashboard_page, logs_page, feedback_page],
        position="hidden",
    )

    with st.sidebar:
        render_admin_sidebar(
            dashboard_page,
            logs_page,
            feedback_page,
            str(st.session_state.get("name") or "관리자"),
            process_logout,
        )


navigation.run()
