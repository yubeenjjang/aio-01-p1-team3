# frontend_user/app.py
"""로그인 상태에 따라 사용자 앱의 메뉴와 페이지를 구성합니다."""

import streamlit as st

from core.auth import (
    init_state,
    is_logged_in,
    logout,
    sync_auth_session,
)

st.set_page_config(
    page_title="오케퐁터디",
    page_icon="📚",
    layout="wide",
)


def apply_custom_css() -> None:
    """오케퐁터디의 보라색 공통 디자인을 적용합니다."""

    st.markdown(
        """
        <style>
        :root {
            --study-purple: #6d45f5;
            --study-purple-dark: #5930dc;
            --study-purple-light: #f3efff;
            --study-border: #e3dcf8;
            --study-text: #182033;
        }

        [data-testid="stAppViewContainer"] {
            background:
                linear-gradient(180deg, #f3edff 0, #faf8ff 34px, #ffffff 150px);
        }

        [data-testid="stHeader"] {
            background: rgba(248, 245, 255, 0.92);
        }

        .stMainBlockContainer {
            max-width: 1320px;
            padding-top: 3rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f7f3ff 0%, #ffffff 72%);
            border-right: 1px solid var(--study-border);
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] {
            border-radius: 12px;
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.2rem;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
            background: #eee7ff;
            color: var(--study-purple-dark);
        }

        [data-testid="stSidebar"] .st-key-sidebar_mypage button {
            background: #eee7ff;
            border-color: rgba(109, 69, 245, 0.22);
            color: var(--study-purple-dark);
        }

        [data-testid="stSidebar"] .st-key-sidebar_mypage button:hover {
            background: #e5dcff;
            border-color: rgba(109, 69, 245, 0.34);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--study-border);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 10px 28px rgba(75, 53, 126, 0.08);
        }

        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input,
        div[data-baseweb="select"] > div {
            border-color: #ded7f3 !important;
            border-radius: 10px !important;
            background: #fcfbff !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus {
            border-color: var(--study-purple) !important;
            box-shadow: 0 0 0 2px rgba(109, 69, 245, 0.14) !important;
        }

        .stButton button,
        .stFormSubmitButton button {
            border-radius: 10px;
            min-height: 2.75rem;
            font-weight: 650;
        }

        .stButton button[kind="primary"],
        .stFormSubmitButton button[kind="primary"] {
            border: 0;
            color: white;
            background: linear-gradient(100deg, var(--study-purple-dark), #824cff);
            box-shadow: 0 8px 18px rgba(109, 69, 245, 0.22);
        }

        .stButton button[kind="primary"]:hover,
        .stFormSubmitButton button[kind="primary"]:hover {
            background: linear-gradient(100deg, #4f27d0, #7340ee);
            transform: translateY(-1px);
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .stMainBlockContainer {
            max-width: 1200px;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stVerticalBlock"]:has(
            > [data-testid="stElementContainer"] .auth-page-marker
        ) {
            gap: 0.45rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker) h1 {
            text-align: center;
            font-size: clamp(2.25rem, 3.5vw, 2.8rem);
            line-height: 1.1;
            letter-spacing: -0.04em;
            margin: 0 0 0.15rem;
            background: linear-gradient(100deg, #5a32db, #8a4fff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-subtitle {
            text-align: center;
            color: var(--study-text);
            font-size: 1rem;
            font-weight: 650;
            margin: 0;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-header-divider {
            width: 100%;
            height: 1px;
            margin: 0;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(109, 69, 245, 0.3) 12%,
                rgba(109, 69, 245, 0.3) 88%,
                transparent
            );
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-success-spacer {
            height: 2rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stElementContainer"]:has(.auth-header-divider) {
            padding: 0.8rem 0;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-section-title {
            color: var(--study-text);
            font-size: 1rem;
            font-weight: 800;
            margin: 0 0 0.35rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-login-title {
            color: var(--study-text);
            font-size: 1.65rem;
            font-weight: 800;
            line-height: 1.2;
            margin: 0.1rem 0 0.8rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-feature-list {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            width: 100%;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-feature-card {
            box-sizing: border-box;
            display: flex;
            align-items: center;
            gap: 1rem;
            width: 100%;
            height: 164px;
            padding: 0.2rem 1rem;
            overflow: hidden;
            border: 1px solid rgba(142, 118, 194, 0.24);
            border-radius: 16px;
            background: linear-gradient(135deg, #ffffff, #fbf9ff);
            box-shadow: 0 8px 22px rgba(75, 53, 126, 0.08);
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-feature-image {
            flex: 0 0 260px;
            width: 260px;
            height: 156px;
            object-fit: contain;
            border-radius: 12px;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-feature-copy {
            min-width: 0;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-feature-copy strong {
            display: block;
            color: var(--study-text);
            font-size: 1.05rem;
            line-height: 1.35;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-feature-copy span {
            display: block;
            margin-top: 0.22rem;
            color: #747b8f;
            font-size: 0.84rem;
            line-height: 1.45;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stVerticalBlock"]:has(
            > [data-testid="stElementContainer"] .auth-login-card-marker
        ) {
            border-radius: 20px;
            box-shadow: 0 14px 36px rgba(75, 53, 126, 0.12);
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stVerticalBlock"]:has(
            > [data-testid="stElementContainer"] .auth-login-card-marker
        ) {
            gap: 0.42rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stVerticalBlock"]:has(
            > [data-testid="stElementContainer"] .auth-login-card-marker
        )
        .stTextInput input {
            min-height: 2.4rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stVerticalBlock"]:has(
            > [data-testid="stElementContainer"] .auth-login-card-marker
        )
        .stButton button,
        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stVerticalBlock"]:has(
            > [data-testid="stElementContainer"] .auth-login-card-marker
        )
        .stFormSubmitButton button {
            min-height: 2.4rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        .auth-login-offset {
            height: 3.2rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stDivider"] {
            margin: 0.2rem 0 0.3rem;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        div[data-testid="stVerticalBlockBorderWrapper"] {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 14px 34px rgba(75, 53, 126, 0.13);
        }

        [data-testid="stAppViewContainer"]:has(.auth-page-marker)
        [data-testid="stForm"] {
            border: 0;
            padding: 0;
        }

        [data-testid="stAppViewContainer"]:has(.analysis-tabs-marker)
        [data-baseweb="tab-list"] {
            gap: 0.6rem;
            padding: 0.45rem;
            border: 1px solid var(--study-border);
            border-radius: 14px;
            background: var(--study-purple-light);
        }

        [data-testid="stAppViewContainer"]:has(.analysis-tabs-marker)
        [role="tab"] {
            min-height: 3.25rem;
            padding: 0.7rem 1.5rem;
            border: 1px solid #cfc3f5;
            border-radius: 10px;
            color: #594d72;
            font-size: 1.05rem;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 3px 9px rgba(89, 48, 220, 0.08);
        }

        [data-testid="stAppViewContainer"]:has(.analysis-tabs-marker)
        [role="tab"]:hover {
            color: var(--study-purple-dark);
            background: rgba(255, 255, 255, 0.72);
        }

        [data-testid="stAppViewContainer"]:has(.analysis-tabs-marker)
        [role="tab"][aria-selected="true"] {
            border-color: transparent;
            color: white;
            background: linear-gradient(100deg, var(--study-purple-dark), #824cff);
            box-shadow: 0 7px 16px rgba(109, 69, 245, 0.22);
        }

        [data-testid="stAppViewContainer"]:has(.analysis-tabs-marker)
        [data-baseweb="tab-highlight"] {
            display: none;
        }

        [data-testid="stAppViewContainer"]:has(.analysis-tabs-marker)
        [data-testid="stTabContent"] {
            padding-top: 1.5rem;
        }

        @media (max-width: 768px) {
            .stMainBlockContainer {
                padding: 2rem 1rem 3rem;
            }

            [data-testid="stAppViewContainer"]:has(.auth-page-marker) h1 {
                font-size: 2.3rem;
            }

            [data-testid="stAppViewContainer"]:has(.auth-page-marker)
            .stMainBlockContainer {
                padding-top: 1rem;
            }

            [data-testid="stAppViewContainer"]:has(.auth-page-marker)
            .auth-feature-card {
                height: 142px;
                padding: 0.7rem;
                gap: 0.75rem;
            }

            [data-testid="stAppViewContainer"]:has(.auth-page-marker)
            .auth-feature-image {
                flex-basis: 190px;
                width: 190px;
                height: 122px;
            }

            [data-testid="stAppViewContainer"]:has(.auth-page-marker)
            .auth-login-offset {
                display: none;
            }

            [data-testid="stAppViewContainer"]:has(.analysis-tabs-marker)
            [role="tab"] {
                padding: 0.65rem 0.8rem;
                font-size: 0.95rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_custom_css()

# 로그인 관련 세션 값을 초기화합니다.
init_state()
sync_auth_session()


# 로그인 전 페이지
login_page = st.Page(
    "app_pages/00_login.py",
    title="로그인",
    icon="🔐",
    default=True,
)

signup_page = st.Page(
    "app_pages/01_signup.py",
    title="회원가입",
    icon="✍️",
)


# 로그인 후 주요 페이지
home_page = st.Page(
    "app_pages/02_home.py",
    title="메인",
    icon="🏠",
    default=True,
)

personal_study_list_page = st.Page(
    "app_pages/03_personal_study_list.py",
    title="개인 스터디",
    icon="📝",
)

group_study_list_page = st.Page(
    "app_pages/06_group_study_list.py",
    title="그룹 스터디",
    icon="👥",
)

analysis_page = st.Page(
    "app_pages/09_analysis.py",
    title="AI 분석",
    icon="📊",
)

mypage = st.Page(
    "app_pages/10_mypage.py",
    title="마이페이지",
    icon="👤",
)


# 목록에서 이동하는 등록·수정·상세 페이지
personal_study_form_page = st.Page(
    "app_pages/04_personal_study_form.py",
    title="학습 기록 등록·수정",
)

personal_study_detail_page = st.Page(
    "app_pages/05_personal_study_detail.py",
    title="학습 기록 상세",
)

group_study_form_page = st.Page(
    "app_pages/07_group_study_form.py",
    title="그룹 스터디 등록·수정",
)

group_study_detail_page = st.Page(
    "app_pages/08_group_study_detail.py",
    title="그룹 스터디 상세",
)


if not is_logged_in():
    # 로그인 전에는 로그인과 회원가입 페이지에만 접근할 수 있습니다.
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
        [login_page, signup_page],
        position="hidden",
    )

else:
    # 로그인한 사용자는 모든 사용자 기능 페이지에 접근할 수 있습니다.
    navigation = st.navigation(
        [
            home_page,
            personal_study_list_page,
            personal_study_form_page,
            personal_study_detail_page,
            group_study_list_page,
            group_study_form_page,
            group_study_detail_page,
            analysis_page,
            mypage,
        ],
        position="hidden",
    )

    with st.sidebar:
        st.markdown("# 📚 오케퐁터디")
        st.markdown(
            '<div class="sidebar-service-copy">'
            '함께 기록하고 성장하는<br />학습 관리 서비스'
            '</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown("## 메뉴")
        st.page_link(home_page)
        st.page_link(personal_study_list_page)
        st.page_link(group_study_list_page)
        st.page_link(analysis_page)

        st.divider()
        st.markdown(
            f"### 👤 {st.session_state.name}님"
        )
        st.write(f"역할: {st.session_state.role}")

        if st.button(
            "마이페이지",
            key="sidebar_mypage",
            use_container_width=True,
        ):
            st.switch_page(mypage)

        st.button(
            "로그아웃",
            use_container_width=True,
            on_click=logout,
        )


navigation.run()
