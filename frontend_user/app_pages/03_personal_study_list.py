"""개인 학습 기록을 검색하고 상세 화면으로 이동하는 페이지입니다.

페이지는 화면 상태만 처리합니다. 실제 API 요청은 전공자가 관리하는
``personal_study_client``를 통해서만 수행합니다.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

import streamlit as st

from clients import personal_study_client


PRIMARY_COLOR = "#6D45F5"


def _apply_page_style() -> None:
    """학습 목록 카드와 상태 배지의 공통 화면 톤을 적용합니다."""
    st.markdown(
        f"""
        <style>
            .list-title {{ color: #1B2035; font-size: 1.75rem; font-weight: 800; margin-bottom: .2rem; }}
            .list-subtitle {{ color: #7A8298; margin-bottom: 1.25rem; }}
            .stDateInput label, .stTextInput label {{
                min-height: 1.5rem;
                line-height: 1.5rem;
                align-items: center;
            }}
            .stDateInput div[data-baseweb="input"],
            .stTextInput div[data-baseweb="input"] {{
                box-sizing: border-box;
                height: 3rem !important;
                min-height: 3rem !important;
            }}
            .stDateInput input, .stTextInput input {{
                box-sizing: border-box;
                height: 3rem !important;
                min-height: 3rem !important;
            }}
            .stFormSubmitButton button {{
                box-sizing: border-box;
                height: 3rem !important;
                min-height: 3rem !important;
            }}
            .record-card {{ background: white; border: 1px solid #ECEAF4; border-radius: 14px; padding: .9rem 1rem; margin-bottom: .6rem; }}
            .record-subject {{ color: {PRIMARY_COLOR}; font-weight: 800; }}
            .empty-list {{ text-align: center; background: #FBFAFF; border: 1px dashed #CEC5FF; border-radius: 18px; padding: 3rem 1rem; color: #69738A; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _find_client_function(*names: str) -> Callable[..., Any]:
    """목록 조회를 담당하는 client 함수를 찾습니다."""
    for name in names:
        function = getattr(personal_study_client, name, None)
        if callable(function):
            return function
    expected = " 또는 ".join(f"{name}()" for name in names)
    raise RuntimeError(f"학습 기록 client에 {expected} 함수가 아직 준비되지 않았습니다.")


def _load_records(user_id: str, start_date: date, end_date: date, subject: str) -> list[dict[str, Any]]:
    """선택한 기간과 과목 조건으로 목록을 조회합니다.

    client 구현에서는 ``from_date``와 ``to_date``를 API 명세의 ``from``과
    ``to`` Query Parameter로 변환합니다.
    """
    get_records = _find_client_function("get_records", "list_records")
    response = get_records(
        user_id=user_id,
        date_from=start_date.isoformat(),
        date_to=end_date.isoformat(),
        subject=subject or None,
    )
    if isinstance(response, dict):
        items = response.get("items", [])
    else:
        items = response
    return items if isinstance(items, list) else []


def _format_minutes(minutes: Any) -> str:
    """API의 분 단위 시간을 읽기 쉬운 문자열로 바꿉니다."""
    try:
        value = int(minutes or 0)
    except (TypeError, ValueError):
        value = 0
    hours, remaining = divmod(value, 60)
    return f"{hours}시간 {remaining}분" if hours else f"{remaining}분"


def _move_to_form() -> None:
    """새 학습 기록 작성 화면으로 이동합니다."""

    # 이전에 수정하거나 조회했던 기록 ID가 남아 있으면 폼이 수정 모드로
    # 열리므로, 새 기록 작성 전 반드시 제거합니다.
    st.session_state.pop("selected_record_id", None)
    st.switch_page("app_pages/04_personal_study_form.py")


def _move_to_detail(record_id: str) -> None:
    """선택한 학습 기록의 상세 화면으로 이동합니다."""

    st.session_state["selected_record_id"] = record_id
    st.switch_page("app_pages/05_personal_study_detail.py")


def _render_filters() -> tuple[date, date, str]:
    """기간·과목 필터 UI를 그리고 선택값을 반환합니다."""
    default_end = date.today()
    default_start = default_end - timedelta(days=30)
    with st.form("personal_study_filters"):
        period_column, subject_column, search_column = st.columns(
            3,
            vertical_alignment="bottom",
        )
        with period_column:
            selected_period = st.date_input(
                "학습 기간 검색",
                value=(default_start, default_end),
                max_value=default_end,
                help="조회할 학습 기록의 시작일과 종료일을 선택하세요.",
            )
        with subject_column:
            subject = st.text_input(
                "과목 검색",
                placeholder="과목명으로 검색 (예: Python, 영어)",
            )
        with search_column:
            st.form_submit_button(
                "검색",
                type="primary",
                use_container_width=True,
            )

    if isinstance(selected_period, tuple) and len(selected_period) == 2:
        start_date, end_date = selected_period
    else:
        start_date = end_date = selected_period
    return start_date, end_date, subject.strip()


def _render_empty_state() -> None:
    """필터 결과가 없을 때 등록 행동을 안내합니다."""
    st.markdown(
        """<div class="empty-list">
            <div style="font-size:2rem;">📚</div>
            <h3 style="color:#252B40; margin:.45rem 0;">학습 기록이 없어요</h3>
            <p>기간 또는 과목 조건을 바꾸거나 새로운 학습 기록을 남겨 보세요.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("학습 기록 등록하기", key="empty_create", type="primary"):
        _move_to_form()


def _render_records(records: list[dict[str, Any]]) -> None:
    """학습 기록 카드와 상세 이동 버튼을 표시합니다."""
    if not records:
        _render_empty_state()
        return

    st.caption(f"총 {len(records)}건의 학습 기록")
    for index, record in enumerate(records):
        record_id = str(record.get("record_id", ""))
        with st.container(border=True):
            date_column, subject_column, time_column, button_column = st.columns([1.2, 3.4, 1.1, 1])
            with date_column:
                st.caption("학습 날짜")
                st.markdown(f"**{record.get('studied_on', '-')}**")
            with subject_column:
                st.caption("학습 과목")
                st.markdown(f"<span class='record-subject'>{record.get('subject', '미분류')}</span>", unsafe_allow_html=True)
            with time_column:
                st.caption("학습 시간")
                st.markdown(f"**{_format_minutes(record.get('study_minutes', 0))}**")
            with button_column:
                st.write("")
                if st.button("상세 보기", key=f"detail_{record_id or index}", use_container_width=True):
                    _move_to_detail(record_id)


def _render_error(error: Exception) -> None:
    """API 호출 실패 시 오류 메시지와 재시도 행동을 표시합니다."""
    st.error("개인 학습 기록을 불러오지 못했습니다.")
    st.caption(f"오류 내용: {error}")
    if st.button("다시 시도", type="primary"):
        st.rerun()


def main() -> None:
    """개인 학습 기록 목록 화면을 렌더링합니다."""
    _apply_page_style()
    st.markdown('<h1 class="list-title">개인 학습 기록</h1>', unsafe_allow_html=True)
    st.markdown('<p class="list-subtitle">기간과 과목으로 기록을 찾아보고 학습 흐름을 확인하세요.</p>', unsafe_allow_html=True)

    _, create_column = st.columns([5, 1])
    with create_column:
        if st.button("+ 새 기록 작성", type="primary", use_container_width=True):
            _move_to_form()

    start_date, end_date, subject = _render_filters()
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("로그인 정보를 찾을 수 없습니다. 다시 로그인해 주세요.")
        return

    try:
        with st.spinner("개인 학습 기록을 불러오는 중입니다..."):
            records = _load_records(str(user_id), start_date, end_date, subject)
    except Exception as error:  # client의 표준 API 오류를 화면에서 보여 줍니다.
        _render_error(error)
        return

    _render_records(records)


main()
