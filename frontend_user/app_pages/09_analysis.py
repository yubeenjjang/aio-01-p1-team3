# frontend_user/app_pages/09_analysis.py
"""선택한 기간의 학습 기록을 AI로 분석하고 결과를 표시합니다."""

from datetime import date
from typing import Any

import streamlit as st

from clients.analysis_client import create_analysis
from clients.chat_client import (
    create_conversation,
    delete_conversation,
    get_conversations,
    get_messages,
    send_message,
)
from clients.feedback_client import (
    get_analysis_feedback,
    save_analysis_feedback,
)
from core.api_client import BackendAPIError


def initialize_page_state() -> None:
    """AI 분석 페이지에서 사용하는 세션 값을 초기화합니다."""

    today = date.today()
    first_day = today.replace(day=1)

    defaults = {
        "analysis_period_start": first_day,
        "analysis_period_end": today,
        "analysis_result": None,
        "analysis_error": None,
        "analysis_result_start": None,
        "analysis_result_end": None,
        "analysis_requesting": False,
        "feedback_loaded_period": None,
        "feedback_exists": False,
        "feedback_rating": 5,
        "feedback_comment": "",
        "feedback_error": None,
        "feedback_saved": False,
        "feedback_saved_mode": None,
        "chat_conversations": [],
        "chat_selected_id": "",
        "chat_selected_id_widget": "",
        "chat_selection_sync_required": False,
        "chat_delete_confirm_reset_required": False,
        "chat_messages": [],
        "chat_messages_conversation_id": "",
        "chat_error": None,
        "chat_loaded": False,
        "chat_requesting": False,
        "chat_delete_confirm": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def move_to_record_form() -> None:
    """개인 학습 기록 등록 화면으로 이동합니다."""

    st.session_state.pop("selected_record_id", None)
    st.switch_page("app_pages/04_personal_study_form.py")


def normalize_text_list(value: Any) -> list[str]:
    """분석 결과를 화면에서 반복 출력할 수 있는 문자열 목록으로 변환합니다."""

    if isinstance(value, list):
        return [str(item) for item in value if item]

    if value:
        return [str(value)]

    return []


def save_api_error(error: BackendAPIError) -> None:
    """표준 백엔드 오류를 화면 표시용 세션 값으로 저장합니다."""

    st.session_state["analysis_error"] = {
        "message": error.message,
        "status_code": error.status_code,
        "code": error.code,
        "details": error.details,
        "trace_id": error.trace_id,
    }


def request_analysis(
    user_id: str,
    period_start: date,
    period_end: date,
) -> None:
    """선택한 기간으로 AI 분석 API를 호출합니다."""

    st.session_state["analysis_result"] = None
    st.session_state["analysis_error"] = None
    st.session_state["analysis_requesting"] = True

    try:
        with st.spinner("학습 기록을 AI로 분석하는 중입니다."):
            response = create_analysis(
                user_id=user_id,
                period_start=period_start,
                period_end=period_end,
            )

        if not isinstance(response, dict):
            raise ValueError("AI 분석 응답 형식이 올바르지 않습니다.")

        st.session_state["analysis_result"] = response
        st.session_state["analysis_result_start"] = period_start
        st.session_state["analysis_result_end"] = period_end
        st.session_state["feedback_loaded_period"] = None
        st.session_state["feedback_saved"] = False

    except BackendAPIError as error:
        save_api_error(error)

    except Exception as error:
        st.session_state["analysis_error"] = {
            "message": str(error),
            "status_code": None,
            "code": "ANALYSIS_REQUEST_ERROR",
            "details": None,
            "trace_id": None,
        }

    finally:
        st.session_state["analysis_requesting"] = False


def render_analysis_form(user_id: str) -> None:
    """분석 기간 선택과 요청 버튼을 표시합니다."""

    with st.container(border=True):
        st.subheader("분석 기간")

        with st.form("analysis_period_form"):
            start_column, end_column = st.columns(2)

            with start_column:
                period_start = st.date_input(
                    "시작일",
                    key="analysis_period_start",
                    max_value=date.today(),
                )

            with end_column:
                period_end = st.date_input(
                    "종료일",
                    key="analysis_period_end",
                    max_value=date.today(),
                )

            submitted = st.form_submit_button(
                "분석 요청",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.analysis_requesting,
            )

    if not submitted:
        return

    if period_start > period_end:
        st.error("분석 시작일은 종료일보다 늦을 수 없습니다.")
        return

    request_analysis(
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
    )


def render_result_section(result: dict[str, Any]) -> None:
    """AI 분석의 요약·강점·개선점·다음 목표를 표시합니다."""

    result_start = st.session_state.get("analysis_result_start")
    result_end = st.session_state.get("analysis_result_end")

    st.divider()
    st.subheader("AI 분석 결과")

    if result_start and result_end:
        st.caption(f"분석 기간: {result_start} ~ {result_end}")

    with st.container(border=True):
        st.markdown("### 요약")
        st.write(result.get("summary") or "요약 결과가 없습니다.")

    strengths = normalize_text_list(result.get("strengths"))

    with st.container(border=True):
        st.markdown("### 강점")

        if strengths:
            for strength in strengths:
                st.write(f"- {strength}")
        else:
            st.write("분석된 강점이 없습니다.")

    improvements = normalize_text_list(result.get("improvements"))

    with st.container(border=True):
        st.markdown("### 개선할 점")

        if improvements:
            for improvement in improvements:
                st.write(f"- {improvement}")
        else:
            st.write("분석된 개선점이 없습니다.")

    with st.container(border=True):
        st.markdown("### 다음 목표")
        st.write(result.get("next_goal") or "추천된 다음 목표가 없습니다.")


def render_error_section(user_id: str) -> None:
    """학습 기록 없음과 Gemini 오류를 설계서에 맞게 처리합니다."""

    error = st.session_state.get("analysis_error")

    if not isinstance(error, dict):
        return

    code = error.get("code")
    status_code = error.get("status_code")
    message = error.get("message") or "AI 분석 요청에 실패했습니다."
    trace_id = error.get("trace_id")

    st.divider()

    if code == "NO_STUDY_RECORDS" or status_code == 404:
        st.warning("선택한 기간에 분석할 학습 기록이 없습니다.")
        st.write("먼저 학습 기록을 등록한 후 다시 분석해 주세요.")

        if st.button(
            "학습 기록 등록",
            key="analysis_create_record",
            type="primary",
        ):
            move_to_record_form()

        return

    if code in {"GEMINI_REQUEST_FAILED", "GEMINI_UNAVAILABLE"} or status_code in {500, 503}:
        st.error("AI 분석을 완료하지 못했습니다.")
    else:
        st.error(message)

    if code:
        st.caption(f"오류 코드: {code}")

    if trace_id:
        st.caption(f"추적 ID: {trace_id}")

    if st.button(
        "다시 분석하기",
        key="analysis_retry",
        type="primary",
    ):
        request_analysis(
            user_id=user_id,
            period_start=st.session_state.analysis_period_start,
            period_end=st.session_state.analysis_period_end,
        )
        st.rerun()


def render_small_error(error: Exception) -> None:
    """분석의 다른 영역을 가리지 않는 API 오류를 표시합니다."""

    if isinstance(error, BackendAPIError):
        st.error(error.message)
        if error.code:
            st.caption(f"오류 코드: {error.code}")
        if error.trace_id:
            st.caption(f"추적 ID: {error.trace_id}")
    else:
        st.error(str(error))


def load_feedback(user_id: str) -> None:
    """현재 분석 기간의 기존 평가를 복원합니다."""

    period_start = st.session_state.get("analysis_result_start")
    period_end = st.session_state.get("analysis_result_end")
    period_key = f"{period_start}:{period_end}"

    if not period_start or not period_end:
        return
    if st.session_state.feedback_loaded_period == period_key:
        return

    st.session_state.feedback_error = None
    st.session_state.feedback_exists = False
    st.session_state.feedback_rating = 5
    st.session_state.feedback_comment = ""
    st.session_state.feedback_saved = False
    st.session_state.feedback_saved_mode = None

    try:
        feedback = get_analysis_feedback(
            user_id, period_start, period_end
        )
        if isinstance(feedback, dict):
            st.session_state.feedback_exists = True
            st.session_state.feedback_rating = int(
                feedback.get("rating") or 5
            )
            st.session_state.feedback_comment = str(
                feedback.get("comment") or ""
            )
    except BackendAPIError as error:
        if error.status_code != 404:
            st.session_state.feedback_error = error
    finally:
        st.session_state.feedback_loaded_period = period_key


def render_feedback_panel(user_id: str) -> None:
    """분석 결과에 대한 평점과 의견 입력을 표시합니다."""

    load_feedback(user_id)

    with st.container(border=True):
        st.subheader("분석 평가")
        st.write("이번 분석이 학습에 얼마나 도움이 되었나요?")
        st.caption("평가 내용은 서비스 개선을 위해 관리자에게 공유될 수 있습니다.")

        with st.form("analysis_feedback_form"):
            rating = st.select_slider(
                "평점",
                options=[1, 2, 3, 4, 5],
                value=st.session_state.feedback_rating,
                format_func=lambda value: f"{value}점",
            )
            comment = st.text_area(
                "의견 (선택)",
                value=st.session_state.feedback_comment,
                max_chars=1000,
            )
            submitted = st.form_submit_button(
                "평가 수정" if st.session_state.feedback_exists else "평가 저장",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            feedback_was_existing = st.session_state.feedback_exists
            try:
                saved = save_analysis_feedback(
                    user_id=user_id,
                    period_start=st.session_state.analysis_result_start,
                    period_end=st.session_state.analysis_result_end,
                    rating=int(rating),
                    comment=comment,
                )
                st.session_state.feedback_rating = int(rating)
                st.session_state.feedback_comment = comment
                st.session_state.feedback_exists = True
                st.session_state.feedback_saved = True
                st.session_state.feedback_saved_mode = (
                    "updated" if feedback_was_existing else "created"
                )
                st.session_state.feedback_error = None
                if isinstance(saved, dict) and saved.get("updated_at"):
                    st.caption(f"저장 시각: {saved['updated_at']}")
            except Exception as error:
                st.session_state.feedback_error = error

        if st.session_state.feedback_saved:
            message = (
                "평가가 수정되었습니다."
                if st.session_state.feedback_saved_mode == "updated"
                else "평가가 저장되었습니다."
            )
            st.success(message)
        if st.session_state.feedback_error:
            render_small_error(st.session_state.feedback_error)


def load_chat_conversations(
    user_id: str,
    *,
    select_first_if_missing: bool = False,
) -> None:
    """사용자의 대화방 목록을 불러옵니다."""

    response = get_conversations(user_id)
    items = response.get("items", []) if isinstance(response, dict) else []
    st.session_state.chat_conversations = [
        item for item in items if isinstance(item, dict)
    ]
    ids = [
        str(item.get("conversation_id") or "")
        for item in st.session_state.chat_conversations
    ]
    widget_selected_id = st.session_state.get("chat_selected_id_widget", "")
    if st.session_state.get("chat_selection_sync_required"):
        requested_id = st.session_state.get("chat_selected_id", "")
        widget_selected_id = requested_id if requested_id in ids else ""
    elif widget_selected_id not in ids:
        widget_selected_id = ids[0] if ids and select_first_if_missing else ""
    if st.session_state.get("chat_selection_sync_required") or widget_selected_id not in ids:
        st.session_state.chat_selected_id_widget = widget_selected_id
        st.session_state.chat_selection_sync_required = False
    st.session_state.chat_selected_id = widget_selected_id
    st.session_state.chat_loaded = True


def load_chat_messages(user_id: str, conversation_id: str) -> None:
    response = get_messages(conversation_id, user_id)
    items = response.get("items", []) if isinstance(response, dict) else []
    st.session_state.chat_messages = [
        item for item in items if isinstance(item, dict)
    ]
    st.session_state.chat_messages_conversation_id = conversation_id


def render_chat_panel(user_id: str) -> None:
    """멀티턴 학습 코치 대화방과 메시지를 표시합니다."""

    st.subheader("일반 학습 코치")
    st.caption("이전 대화를 참고해 학습 질문에 답변합니다.")

    if not st.session_state.chat_loaded:
        try:
            load_chat_conversations(user_id, select_first_if_missing=True)
        except Exception as error:
            st.session_state.chat_error = error
            st.session_state.chat_loaded = True

    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("새 대화", type="primary", use_container_width=True):
            try:
                created = create_conversation(user_id)
                st.session_state.chat_selected_id = str(
                    created.get("conversation_id") or ""
                )
                st.session_state.chat_selection_sync_required = True
                load_chat_conversations(user_id)
                st.session_state.chat_messages = []
                st.session_state.chat_messages_conversation_id = ""
                st.session_state.chat_error = None
                st.session_state.chat_delete_confirm = False
                st.rerun()
            except Exception as error:
                st.session_state.chat_error = error
    with action_right:
        if st.button("대화 목록 새로고침", use_container_width=True):
            st.session_state.chat_loaded = False
            st.session_state.chat_error = None
            st.rerun()

    conversations = st.session_state.chat_conversations
    if conversations:
        title_by_id = {}
        for index, item in enumerate(conversations, start=1):
            conversation_id = str(item.get("conversation_id") or "")
            title = str(item.get("title") or "새 학습 코치 대화")
            title_by_id[conversation_id] = f"대화 {index} · {title}"

        ids = list(title_by_id)
        if st.session_state.get("chat_delete_confirm_reset_required"):
            st.session_state.chat_delete_confirm = False
            st.session_state.chat_delete_confirm_reset_required = False
        options = [""] + ids
        selected_id = st.selectbox(
            "대화방",
            options,
            key="chat_selected_id_widget",
            format_func=lambda value: (
                "대화방을 선택하세요" if not value else title_by_id[value]
            ),
        )
        if selected_id != st.session_state.chat_selected_id:
            st.session_state.chat_selected_id = selected_id
            st.session_state.chat_messages = []
            st.session_state.chat_messages_conversation_id = ""
            st.session_state.chat_delete_confirm = False

        if selected_id:
            delete_check = st.checkbox(
                "선택한 대화방 삭제 확인",
                key="chat_delete_confirm",
                disabled=st.session_state.chat_requesting,
            )
            if st.button(
                "대화방 삭제",
                disabled=not delete_check or st.session_state.chat_requesting,
                use_container_width=True,
            ):
                deleted_id = selected_id
                try:
                    delete_conversation(deleted_id, user_id)
                    st.session_state.chat_selected_id = ""
                    st.session_state.chat_selection_sync_required = True
                    st.session_state.chat_messages = []
                    st.session_state.chat_messages_conversation_id = ""
                    st.session_state.chat_loaded = False
                    st.session_state.chat_delete_confirm_reset_required = True
                    st.toast("대화방을 삭제했습니다.", icon="🗑️")
                    st.rerun()
                except Exception as error:
                    st.session_state.chat_error = error

            if (
                st.session_state.chat_messages_conversation_id
                != selected_id
            ):
                try:
                    load_chat_messages(user_id, selected_id)
                except Exception as error:
                    st.session_state.chat_error = error

            with st.container(border=True):
                if not st.session_state.chat_messages:
                    st.info("아직 메시지가 없습니다. 첫 질문을 입력해 보세요.")
                for message in st.session_state.chat_messages:
                    role = "assistant" if message.get("role") == "model" else "user"
                    with st.chat_message(role):
                        st.write(message.get("content") or "")

            with st.form("chat_question_form", clear_on_submit=True):
                question = st.text_area(
                    "질문",
                    placeholder="학습과 관련된 질문을 입력하세요.",
                )
                sent = st.form_submit_button(
                    "전송",
                    type="primary",
                    use_container_width=True,
                    disabled=st.session_state.chat_requesting,
                )
            if sent:
                if not question.strip():
                    st.warning("질문 내용을 입력하세요.")
                else:
                    st.session_state.chat_requesting = True
                    try:
                        send_message(selected_id, user_id, question)
                        load_chat_messages(user_id, selected_id)
                        load_chat_conversations(user_id)
                        st.session_state.chat_error = None
                        st.session_state.chat_requesting = False
                        st.rerun()
                    except Exception as error:
                        st.session_state.chat_error = error
                    finally:
                        st.session_state.chat_requesting = False
        else:
            st.info("대화를 선택하거나 새 대화를 만들어 주세요.")
    else:
        st.info("대화방이 없습니다. 새 대화를 만들어 주세요.")

    if st.session_state.chat_error:
        render_small_error(st.session_state.chat_error)
        if st.button("채팅 다시 시도", use_container_width=True):
            st.session_state.chat_loaded = False
            st.session_state.chat_error = None
            st.rerun()


def main() -> None:
    """AI 학습 분석 페이지를 실행합니다."""

    initialize_page_state()

    user_id = str(st.session_state.get("user_id") or "")

    if not user_id:
        st.warning("로그인 정보가 없습니다. 다시 로그인해 주세요.")
        st.stop()

    st.title("AI 학습 분석")
    st.write("AI 분석과 일반 학습 코치를 원하는 탭에서 이용해 보세요.")

    st.markdown(
        '<div class="analysis-tabs-marker"></div>',
        unsafe_allow_html=True,
    )

    analysis_tab, coach_tab = st.tabs(
        ["📊 AI 분석", "💬 일반 학습 코치"]
    )

    with analysis_tab:
        render_analysis_form(user_id)
        result = st.session_state.get("analysis_result")
        if isinstance(result, dict):
            render_result_section(result)
            render_feedback_panel(user_id)
        else:
            render_error_section(user_id)

    with coach_tab:
        render_chat_panel(user_id)


main()
