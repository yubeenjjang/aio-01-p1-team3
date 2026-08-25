# frontend_user/core/auth.py
"""사용자 로그인 정보와 Streamlit 세션 상태를 관리합니다."""

import json
from typing import Any

import streamlit as st
from streamlit_session_browser_storage import SessionStorage


AUTH_STORAGE_NAME = "login_session_storage"
AUTH_STORAGE_KEY = "current_user"
AUTH_CLEAR_KEY = "_auth_storage_clear_requested"


def get_auth_storage() -> SessionStorage:
    """현재 Streamlit 세션의 브라우저 sessionStorage를 반환합니다.

    ``SessionStorage`` 객체를 모듈 전역에 보관하면 새로고침으로 만들어진
    새 Streamlit 세션이 이전 세션의 저장소 스냅샷을 재사용할 수 있습니다.
    매 실행마다 현재 ``st.session_state``를 기준으로 객체를 구성합니다.
    """

    return SessionStorage(key=AUTH_STORAGE_NAME)


def load_auth_session() -> dict[str, Any] | None:
    """브라우저 sessionStorage의 로그인 정보를 읽습니다."""

    stored_value = get_auth_storage().getItem(
        AUTH_STORAGE_KEY
    )

    if not stored_value:
        return None

    if isinstance(stored_value, dict):
        user = stored_value
    else:
        try:
            user = json.loads(str(stored_value))
        except (TypeError, ValueError):
            return None

    required_values = [
        user.get("user_id"),
        user.get("name"),
        user.get("role"),
    ]

    if not all(required_values):
        return None

    return user


def init_state() -> None:
    """로그인 상태를 초기화하고 브라우저 저장값으로 복원합니다.

    브라우저 저장소 컴포넌트의 값은 첫 렌더보다 늦게 도착할 수 있으므로
    로그아웃 상태인 동안에는 매 실행에서 복원을 다시 시도합니다.
    """

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "user_id" not in st.session_state:
        st.session_state.user_id = ""

    if "name" not in st.session_state:
        st.session_state.name = ""

    if "role" not in st.session_state:
        st.session_state.role = ""

    if "email" not in st.session_state:
        st.session_state.email = ""

    should_restore = (
        not st.session_state.get("logged_in")
        and not st.session_state.get(AUTH_CLEAR_KEY)
    )

    if should_restore:
        stored_user = load_auth_session()

        if stored_user:
            st.session_state.logged_in = True
            st.session_state.user_id = str(
                stored_user["user_id"]
            )
            st.session_state.name = str(
                stored_user["name"]
            )
            st.session_state.role = str(
                stored_user["role"]
            )
            st.session_state.email = str(
                stored_user.get("email") or ""
            )


def sync_auth_session() -> None:
    """로그아웃 요청이 있으면 브라우저 로그인 정보를 비웁니다."""

    if st.session_state.get(AUTH_CLEAR_KEY):
        clear_auth_session()


def save_auth_session() -> None:
    """현재 로그인 정보를 브라우저 sessionStorage에 저장합니다."""

    if not st.session_state.get("logged_in"):
        return

    user = {
        "user_id": str(
            st.session_state.get("user_id") or ""
        ),
        "name": str(
            st.session_state.get("name") or ""
        ),
        "role": str(
            st.session_state.get("role") or ""
        ),
        "email": str(
            st.session_state.get("email") or ""
        ),
    }

    get_auth_storage().setItem(
        AUTH_STORAGE_KEY,
        json.dumps(user, ensure_ascii=False),
        key=f"save_auth_{user['user_id']}",
    )


def clear_auth_session() -> None:
    """브라우저 sessionStorage의 로그인 정보를 비웁니다."""

    auth_storage = get_auth_storage()
    auth_storage.deleteAll(key="clear_auth_session")


def clear_user_scoped_state() -> None:
    """로그아웃 시 현재 사용자에게만 속한 화면 상태를 제거합니다."""

    user_scoped_keys = [
        "selected_record_id",
        "selected_study_id",
        "confirm_delete_record",
        "analysis_result",
        "analysis_error",
        "analysis_result_start",
        "analysis_result_end",
        "analysis_period_start",
        "analysis_period_end",
        "feedback_loaded_period",
        "feedback_exists",
        "feedback_rating",
        "feedback_comment",
        "feedback_error",
        "feedback_saved",
        "feedback_saved_mode",
        "chat_conversations",
        "chat_selected_id",
        "chat_selected_id_widget",
        "chat_selection_sync_required",
        "chat_delete_confirm_reset_required",
        "chat_messages",
        "chat_messages_conversation_id",
        "chat_error",
        "chat_loaded",
        "chat_requesting",
        "chat_delete_confirm",
        "personal_form_context",
        "group_form_context",
    ]

    for key in user_scoped_keys:
        st.session_state.pop(key, None)


def login(user: dict[str, Any]) -> None:
    """로그인 API가 반환한 사용자 정보를 세션에 저장합니다."""

    user_id = user.get("user_id")
    name = user.get("name")
    role = user.get("role")

    if not user_id or not name or not role:
        raise ValueError("로그인 응답에 사용자 정보가 부족합니다.")

    st.session_state.logged_in = True
    st.session_state.user_id = str(user_id)
    st.session_state.name = str(name)
    st.session_state.role = str(role)
    st.session_state.pop(AUTH_CLEAR_KEY, None)

    # 회원가입 응답처럼 이메일이 함께 전달되는 경우 저장합니다.
    # MVP 로그인 응답에는 이메일이 없으므로 로그인 화면이 입력값을 저장합니다.
    if user.get("email"):
        st.session_state.email = str(user["email"])


def logout() -> None:
    """로그인 정보를 세션에서 초기화합니다."""

    clear_user_scoped_state()
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.name = ""
    st.session_state.role = ""
    st.session_state.email = ""
    st.session_state[AUTH_CLEAR_KEY] = True


def is_logged_in() -> bool:
    """현재 사용자의 로그인 여부를 반환합니다."""

    return bool(st.session_state.get("logged_in", False))


def is_admin() -> bool:
    """현재 로그인 사용자가 관리자인지 확인합니다."""

    return (
        is_logged_in()
        and st.session_state.get("role") == "admin"
    )


def get_current_user_id() -> str:
    """현재 로그인한 사용자의 user_id를 반환합니다."""

    return str(st.session_state.get("user_id", ""))


def get_current_user() -> dict[str, str]:
    """현재 로그인한 사용자 정보를 반환합니다."""

    return {
        "user_id": str(st.session_state.get("user_id", "")),
        "name": str(st.session_state.get("name", "")),
        "email": str(st.session_state.get("email", "")),
        "role": str(st.session_state.get("role", "")),
    }
