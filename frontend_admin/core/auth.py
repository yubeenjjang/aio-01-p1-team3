"""관리자 프론트엔드의 로그인 세션과 역할을 관리합니다."""

from typing import Any

import streamlit as st


def init_state() -> None:
    """관리자 로그인 세션의 기본값을 초기화합니다."""

    defaults = {
        "logged_in": False,
        "user_id": "",
        "name": "",
        "email": "",
        "role": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login(user: dict[str, Any], email: str = "") -> None:
    """관리자 로그인 응답을 세션에 저장합니다."""

    user_id = user.get("user_id")
    name = user.get("name")
    role = user.get("role")

    if not user_id or not name or not role:
        raise ValueError("로그인 응답에 사용자 정보가 부족합니다.")

    if role != "admin":
        raise PermissionError("관리자 계정만 접근할 수 있습니다.")

    st.session_state.logged_in = True
    st.session_state.user_id = str(user_id)
    st.session_state.name = str(name)
    st.session_state.email = email
    st.session_state.role = str(role)


def logout() -> None:
    """관리자 로그인 세션을 초기화합니다."""

    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.name = ""
    st.session_state.email = ""
    st.session_state.role = ""


def is_logged_in() -> bool:
    """현재 로그인 여부를 반환합니다."""

    return bool(st.session_state.get("logged_in", False))


def is_admin() -> bool:
    """현재 로그인 사용자가 관리자인지 확인합니다."""

    return is_logged_in() and st.session_state.get("role") == "admin"
