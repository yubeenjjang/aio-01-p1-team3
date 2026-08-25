"""관리자 콘솔의 공통 레이아웃과 내비게이션을 제공합니다."""

from collections.abc import Callable
from html import escape
from typing import Any

import streamlit as st


def apply_admin_shell() -> None:
    """Apply a single, restrained visual system to every admin page."""

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #172554 100%);
            border-right: 1px solid rgba(148, 163, 184, .22);
        }
        [data-testid="stSidebar"] * { color: #e2e8f0; }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            border-radius: 9px;
            padding: .5rem .6rem;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background: rgba(255, 255, 255, .1);
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
            background: #475569;
        }
        [data-testid="stSidebar"] div.stButton > button,
        [data-testid="stSidebar"] div.stButton > button * {
            color: #334155 !important;
            background: #f8fafc;
            border-color: #cbd5e1;
            font-weight: 800;
        }
        [data-testid="stSidebar"] div.stButton > button:hover,
        [data-testid="stSidebar"] div.stButton > button:hover * {
            color: #1e293b !important;
            background: #e2e8f0;
            border-color: #94a3b8;
        }
        [data-testid="stSidebar"] div.stButton > button:focus,
        [data-testid="stSidebar"] div.stButton > button:active {
            color: #1e293b !important;
            background: #cbd5e1;
            border-color: #64748b;
        }
        .admin-shell-kicker { color: #93c5fd; font-size: .68rem; font-weight: 800; letter-spacing: .12em; }
        .admin-shell-title { color: #ffffff; font-size: 1.35rem; font-weight: 800; letter-spacing: -.04em; margin: .2rem 0 .8rem; }
        .admin-shell-user { color: #ffffff; font-weight: 700; margin: 0; }
        .admin-shell-role { color: #94a3b8; font-size: .78rem; margin: .2rem 0 1rem; }
        .admin-page-eyebrow { color: #475569; font-size: .72rem; font-weight: 800; letter-spacing: .11em; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_admin_sidebar(
    dashboard_page: Any,
    logs_page: Any,
    feedback_page: Any,
    admin_name: str,
    on_logout: Callable[[], None],
) -> None:
    """Render the authoritative navigation shell shared by all admin pages."""

    st.markdown('<div class="admin-shell-kicker">STUDYMATE CONTROL</div>', unsafe_allow_html=True)
    st.markdown('<div class="admin-shell-title">관리자 콘솔</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="admin-shell-user">{escape(admin_name)}님</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<p class="admin-shell-role">권한 · 관리자</p>', unsafe_allow_html=True)

    st.page_link(dashboard_page, label="운영 대시보드", icon="📊")
    st.page_link(logs_page, label="운영 로그", icon="📋")
    st.page_link(feedback_page, label="AI 분석 평가", icon="⭐")

    st.divider()
    if st.button("로그아웃", use_container_width=True, key="admin_logout"):
        on_logout()


def render_admin_page_header(eyebrow: str, title: str, description: str) -> None:
    """Render the same clear hierarchy at the top of every admin page."""

    st.markdown(
        f'<div class="admin-page-eyebrow">{escape(eyebrow)}</div>',
        unsafe_allow_html=True,
    )
    st.title(title)
    st.caption(description)
