"""관리자가 AI 분석 평가를 검토하는 화면입니다."""

from datetime import date, datetime
from typing import Any

import streamlit as st

from clients.admin_client import get_analysis_feedback
from clients.event_client import get_admin_events
from components.admin_shell import render_admin_page_header
from core.api_client import BackendAPIError
from core.auth import is_admin


def apply_feedback_style() -> None:
    st.markdown(
        """
        <style>
        .feedback-note { color: #64748b; font-size: .85rem; }
        .filter-label-spacer { height: 1.75rem; }
        div[data-testid="stMetric"] { padding: 1rem 1.1rem; border: 1px solid #e5eaf2; border-radius: 14px; background: #ffffff; box-shadow: 0 2px 10px rgba(15, 23, 42, .035); }
        div[data-testid="stDataFrame"] { border: 1px solid #e5eaf2; border-radius: 12px; overflow: hidden; background: #ffffff; }
        .feedback-live-note { margin: .25rem 0 .85rem; color: #64748b; font-size: .78rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_feedback(user_id: str, rating: int | None, date_from: date | None, date_to: date | None) -> dict[str, Any]:
    response = get_analysis_feedback(
        user_id,
        rating=rating,
        date_from=date_from,
        date_to=date_to,
    )
    return response if isinstance(response, dict) else {}


def render_feedback_summary(payload: dict[str, Any]) -> None:
    items = payload.get("items", [])
    items = items if isinstance(items, list) else []
    average_rating = float(payload.get("average_rating", 0) or 0)
    total = int(payload.get("total", len(items)) or 0)

    first, second, third = st.columns(3)
    first.metric("전체 평가", f"{total:,}건")
    second.metric("평균 평점", f"{average_rating:.1f} / 5.0")
    third.metric("5점 평가", f"{sum(1 for item in items if item.get('rating') == 5):,}건")


def render_feedback_table(payload: dict[str, Any]) -> None:
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        st.info("선택한 조건에 맞는 분석 평가가 없습니다.")
        return

    rows = [
        {
            "작성 시각": item.get("created_at", "-"),
            "사용자": item.get("user_name", "비공개"),
            "평점": f"{'★' * int(item.get('rating', 0) or 0)} ({item.get('rating', '-')})",
            "분석 기간": f"{item.get('period_start', '-')} ~ {item.get('period_end', '-')}",
            "의견": item.get("comment") or "-",
        }
        for item in items
        if isinstance(item, dict)
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def main() -> None:
    apply_feedback_style()
    if not is_admin():
        st.error("접근 권한이 없습니다.")
        st.stop()

    user_id = str(st.session_state.get("user_id") or "")
    render_admin_page_header(
        "ANALYSIS QUALITY",
        "AI 분석 평가",
        "사용자 평가와 의견을 검토해 AI 분석 품질을 관리하세요.",
    )

    with st.form("analysis_feedback_filter"):
        rating_column, from_column, to_column, submit_column = st.columns([2, 2, 2, 1])
        with rating_column:
            rating_label = st.selectbox("평점", ["전체", "5점", "4점", "3점", "2점", "1점"])
        with from_column:
            date_from = st.date_input("시작일", value=None)
        with to_column:
            date_to = st.date_input("종료일", value=None)
        with submit_column:
            st.markdown('<div class="filter-label-spacer"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button("조회", type="primary", use_container_width=True)

    if submitted:
        if date_from and date_to and date_from > date_to:
            st.error("시작일은 종료일보다 늦을 수 없습니다.")
        else:
            st.session_state.feedback_rating = (
                None if rating_label == "전체" else int(rating_label[0])
            )
            st.session_state.feedback_date_from = date_from
            st.session_state.feedback_date_to = date_to

    render_live_feedback(user_id)


@st.fragment(run_every="5s")
def render_live_feedback(user_id: str) -> None:
    """SSE 큐를 5초마다 확인하고 평가 이벤트가 있을 때만 API를 재조회합니다."""
    rating = st.session_state.get("feedback_rating")
    selected_from = st.session_state.get("feedback_date_from")
    selected_to = st.session_state.get("feedback_date_to")
    filter_key = (rating, selected_from, selected_to)
    events = get_admin_events(user_id)
    listener = st.session_state.get("admin_event_listener")
    if listener is not None and getattr(listener, "thread", None) is not None and listener.thread.is_alive():
        connection_label = "● SSE 연결됨"
    else:
        connection_label = "● SSE 재연결 중"
    st.markdown(
        f'<div class="feedback-live-note">{connection_label} · 마지막 확인 {datetime.now().strftime("%H:%M:%S")} · 이벤트 확인 5초</div>',
        unsafe_allow_html=True,
    )
    has_event = any(
        event.name == "admin.log.updated"
        and event.data.get("action") == "analysis.feedback.submit"
        for event in events
    )
    should_load = (
        "feedback_cache" not in st.session_state
        or st.session_state.get("feedback_cache_key") != filter_key
        or has_event
        or st.session_state.pop("feedback_force_refresh", False)
    )
    if has_event:
        st.toast("새 분석 평가를 반영했습니다.", icon="🔄")

    if should_load:
        try:
            with st.spinner("분석 평가를 불러오는 중입니다."):
                st.session_state.feedback_cache = load_feedback(
                    user_id, rating, selected_from, selected_to
                )
            st.session_state.feedback_cache_key = filter_key
            st.session_state.feedback_error = None
        except BackendAPIError as error:
            st.session_state.feedback_error = error
            st.session_state.feedback_cache_key = filter_key
        except Exception as error:
            st.session_state.feedback_error = error
            st.session_state.feedback_cache_key = filter_key

    feedback_error = st.session_state.get("feedback_error")
    if isinstance(feedback_error, BackendAPIError):
        st.error(feedback_error.message)
        if feedback_error.code:
            st.caption(f"오류 코드: {feedback_error.code}")
        if feedback_error.trace_id:
            st.caption(f"추적 ID: {feedback_error.trace_id}")
        if st.button("다시 시도", key="feedback_api_retry", type="primary"):
            st.session_state.feedback_force_refresh = True
            st.rerun(scope="fragment")
        return
    elif feedback_error is not None:
        st.error("분석 평가를 불러오지 못했습니다.")
        st.caption(str(feedback_error))
        if st.button("다시 시도", key="feedback_unknown_retry"):
            st.session_state.feedback_force_refresh = True
            st.rerun(scope="fragment")
        return

    payload = st.session_state.get("feedback_cache", {})
    render_feedback_summary(payload)
    st.divider()
    st.subheader("최근 사용자 의견")
    render_feedback_table(payload)


main()
