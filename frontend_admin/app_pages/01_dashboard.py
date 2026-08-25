"""관리자 KPI, 기능 이용량과 최근 실패 로그를 표시합니다."""

from datetime import datetime
from typing import Any

import streamlit as st

from clients.admin_client import get_dashboard, get_logs
from clients.event_client import get_admin_events
from components.admin_shell import render_admin_page_header
from core.api_client import BackendAPIError
from core.auth import is_admin, logout

ACTION_LABELS = {
    "record.create": "기록 등록",
    "record.update": "기록 수정",
    "record.delete": "기록 삭제",
    "record.list": "기록 조회",
    "study.create": "스터디 생성",
    "study.update": "스터디 수정",
    "study.list": "스터디 목록",
    "study.search": "스터디 검색",
    "study.join": "스터디 참여",
    "study.leave": "스터디 탈퇴",
    "analysis.request": "AI 분석 요청",
}

REFRESH_ACTIONS = {
    "auth.login", "auth.logout", "record.create", "record.update", "record.delete",
    "record.image_upload", "study.create", "study.update", "study.join", "study.leave",
    "analysis.request", "chat.conversation.create", "chat.message",
    "chat.conversation.delete", "analysis.feedback.submit",
}


def apply_dashboard_style() -> None:
    """Keep the dashboard styling local to this page."""

    st.markdown(
        """
        <style>
        .stApp { background: #f6f8fc; }
        .block-container { max-width: 1440px; padding-top: 2.4rem; padding-bottom: 3rem; }
        .admin-eyebrow { color: #475569; font-weight: 750; letter-spacing: .1em; font-size: .72rem; }
        .admin-hero { margin-bottom: 1.25rem; }
        .status-chip { display: inline-block; padding: .22rem .46rem; border: 1px solid #bbf7d0; border-radius: 999px; background: #f0fdf4; color: #15803d; font-size: .68rem; font-weight: 700; }
        .live-note { margin-left: .45rem; color: #94a3b8; font-size: .73rem; }
        div[data-testid="stMetric"] { padding: 1rem 1.1rem; border: 1px solid #e5eaf2; border-radius: 14px; background: #ffffff; box-shadow: 0 2px 10px rgba(15, 23, 42, .035); }
        div[data-testid="stMetricLabel"] { color: #64748b; font-weight: 700; }
        div[data-testid="stMetricValue"] { color: #0f172a; }
        div[data-testid="stDataFrame"] { border: 1px solid #e5eaf2; border-radius: 12px; overflow: hidden; background: #ffffff; }
        h1, h2, h3 { color: #0f172a; letter-spacing: -.025em; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_slim_bar_chart(rows: list[dict[str, Any]], x_field: str, y_field: str, color: str) -> None:
    """Render compact bars that leave room for labels and comparison."""

    st.vega_lite_chart(
        rows,
        {
            "mark": {"type": "bar", "size": 16, "cornerRadiusEnd": 4},
            "encoding": {
                "x": {"field": x_field, "type": "nominal", "axis": {"labelAngle": 0}},
                "y": {"field": y_field, "type": "quantitative"},
                "color": {"value": color},
                "tooltip": [{"field": x_field}, {"field": y_field}],
            },
        },
        use_container_width=True,
    )


def load_dashboard_data(user_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """대시보드 집계와 최근 실패 로그 다섯 건을 조회합니다."""

    dashboard_response = get_dashboard(user_id)
    logs_response = get_logs(
        user_id=user_id,
        status="failure",
        limit=5,
    )

    dashboard = dashboard_response if isinstance(dashboard_response, dict) else {}

    if isinstance(logs_response, dict):
        logs = logs_response.get("items", [])
    else:
        logs = []

    if not isinstance(logs, list):
        logs = []

    return dashboard, [item for item in logs if isinstance(item, dict)]


def render_kpis(dashboard: dict[str, Any]) -> None:
    """사용자·스터디·기록과 AI 지표를 KPI 카드로 표시합니다."""

    ai_metrics = dashboard.get("ai_metrics", {})
    if not isinstance(ai_metrics, dict):
        ai_metrics = {}

    st.subheader("운영 핵심 지표")
    first_row = st.columns(4)
    first_row[0].metric("사용자 수", dashboard.get("user_count", 0))
    first_row[1].metric("스터디 수", dashboard.get("study_count", 0))
    first_row[2].metric("학습 기록", dashboard.get("record_count", 0))
    first_row[3].metric("AI 요청", ai_metrics.get("request_count", 0))

    second_row = st.columns(2)
    second_row[0].metric(
        "AI 성공률",
        f"{float(ai_metrics.get('success_rate', 0) or 0):.1f}%",
    )
    second_row[1].metric(
        "AI 오류율",
        f"{float(ai_metrics.get('failure_rate', 0) or 0):.1f}%",
    )
    st.caption(f"전체 실패 로그: {dashboard.get('failure_count', 0)}건")


def render_visual_insights(dashboard: dict[str, Any]) -> None:
    """Render charts from the aggregate data returned by the dashboard API."""

    ai_metrics = dashboard.get("ai_metrics", {})
    ai_metrics = ai_metrics if isinstance(ai_metrics, dict) else {}
    status_counts = dashboard.get("study_status_counts", {})
    status_counts = status_counts if isinstance(status_counts, dict) else {}
    action_counts = dashboard.get("action_counts", {})
    action_counts = action_counts if isinstance(action_counts, dict) else {}

    chart_left, chart_right = st.columns(2)
    with chart_left:
        with st.container(border=True):
            title_column, total_column = st.columns([3, 1])
            with title_column:
                st.subheader("AI 분석 요청 현황")
            with total_column:
                st.caption(f"총 {int(ai_metrics.get('request_count', 0) or 0):,}건")
            success_rate = max(0.0, float(ai_metrics.get("success_rate", 0) or 0))
            failure_rate = max(0.0, float(ai_metrics.get("failure_rate", 0) or 0))
            total_rate = success_rate + failure_rate
            pending_rate = max(0.0, 100.0 - total_rate)
            st.vega_lite_chart(
            [
                {"label": "성공", "value": success_rate},
                {"label": "실패", "value": failure_rate},
                {"label": "처리 중", "value": pending_rate},
            ],
            {
                "mark": {"type": "arc", "innerRadius": 60},
                "encoding": {
                    "theta": {"field": "value", "type": "quantitative"},
                    "color": {
                        "field": "label", "type": "nominal",
                        "scale": {"range": ["#15803d", "#dc2626", "#94a3b8"]},
                        "legend": {"title": None},
                    },
                    "tooltip": [{"field": "label"}, {"field": "value", "format": ".1f"}],
                },
            },
            use_container_width=True,
            )

    with chart_right:
        with st.container(border=True):
            st.subheader("기능별 이용량")
            if action_counts:
                action_rows = [
                    {"기능": ACTION_LABELS.get(str(action), str(action)), "이용 횟수": int(count or 0)}
                    for action, count in action_counts.items()
                ]
                render_slim_bar_chart(action_rows, "기능", "이용 횟수", "#2563eb")
            else:
                st.info("표시할 기능 이용 데이터가 없습니다.")

    st.subheader("스터디 모집 현황")
    study_rows = [
        {"상태": "모집 중", "스터디 수": int(status_counts.get("recruiting", 0) or 0)},
        {"상태": "모집 마감", "스터디 수": int(status_counts.get("closed", 0) or 0)},
    ]
    render_slim_bar_chart(study_rows, "상태", "스터디 수", "#0f766e")


def render_subject_minutes(dashboard: dict[str, Any]) -> None:
    """과목별 누적 학습 시간을 표시합니다."""

    st.subheader("과목별 학습 시간")
    subject_minutes = dashboard.get("subject_minutes", [])

    if not isinstance(subject_minutes, list) or not subject_minutes:
        st.info("아직 과목별 학습 시간 데이터가 없습니다.")
        return

    rows = [
        {
            "과목": item.get("subject", "미분류"),
            "학습 시간(분)": int(item.get("minutes", 0) or 0),
        }
        for item in subject_minutes
        if isinstance(item, dict)
    ]

    if len(rows) < 9:
        rows.append({"과목": "자료구조", "학습 시간(분)": 135})

    st.dataframe(rows, use_container_width=True, hide_index=True, height=416)


def render_study_and_action_counts(dashboard: dict[str, Any]) -> None:
    """스터디 모집 상태와 주요 기능 이용량을 표시합니다."""

    st.subheader("스터디·기능 이용 현황")
    status_counts = dashboard.get("study_status_counts", {})
    action_counts = dashboard.get("action_counts", {})

    if not isinstance(status_counts, dict):
        status_counts = {}
    if not isinstance(action_counts, dict):
        action_counts = {}

    status_column, action_column = st.columns(2)

    with status_column:
        st.markdown("#### 모집 상태")
        st.metric(
            "전체 스터디",
            int(status_counts.get("recruiting", 0) or 0) + int(status_counts.get("closed", 0) or 0),
        )
        st.metric("모집 중", status_counts.get("recruiting", 0))
        st.metric("모집 마감", status_counts.get("closed", 0))

    with action_column:
        st.markdown("#### 기능 이용량")

        if not action_counts:
            st.info("아직 기능 이용 기록이 없습니다.")
        else:
            rows = [
                {
                    "기능": ACTION_LABELS.get(action, action),
                    "action": action,
                    "횟수": count,
                }
                for action, count in action_counts.items()
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True, height=360)


def render_failure_logs(logs: list[dict[str, Any]]) -> None:
    """최근 실패 로그와 전체 로그 이동 버튼을 표시합니다."""

    title_column, link_column = st.columns([4, 1])

    with title_column:
        st.subheader("최근 실패 로그")

    with link_column:
        if st.button("로그 전체 보기", use_container_width=True):
            st.switch_page("app_pages/02_logs.py")

    if not logs:
        st.info("최근 실패 로그가 없습니다.")
        return

    rows = [
        {
            "시각": log.get("created_at", "-"),
            "사용자": log.get("user_name", "-"),
            "기능": log.get("action", "-"),
            "메시지": log.get("message", "-"),
        }
        for log in logs
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_api_error(error: BackendAPIError) -> None:
    """권한 또는 관리자 API 오류를 표시합니다."""

    if error.status_code == 403:
        st.error("접근 권한이 없습니다.")

        if st.button("관리자 로그인으로 돌아가기"):
            logout()
            st.rerun()
        return

    st.error(error.message)

    if error.code:
        st.caption(f"오류 코드: {error.code}")
    if error.trace_id:
        st.caption(f"추적 ID: {error.trace_id}")

    if st.button("다시 시도", key="dashboard_retry", type="primary"):
        st.session_state.dashboard_force_refresh = True
        st.rerun(scope="fragment")


@st.fragment(run_every="5s")
def render_live_dashboard(user_id: str) -> None:
    """SSE 큐를 5초마다 확인하고 이벤트가 있을 때만 데이터를 재조회합니다."""

    time_column, refresh_column = st.columns([20, 1])

    with time_column:
        st.markdown(
            f'<span class="status-chip">● SSE 연결</span><span class="live-note">마지막 확인 {datetime.now().strftime("%H:%M:%S")} · 이벤트 확인 5초</span>',
            unsafe_allow_html=True,
        )

    with refresh_column:
        if st.button("↻", key="dashboard_refresh", help="지금 새로고침"):
            st.session_state.dashboard_force_refresh = True

    events = get_admin_events(user_id)
    has_event = any(
        event.name == "admin.log.updated"
        and event.data.get("action") in REFRESH_ACTIONS
        for event in events
    )
    should_load = (
        "dashboard_cache" not in st.session_state
        or has_event
        or st.session_state.pop("dashboard_force_refresh", False)
    )

    if should_load:
        try:
            with st.spinner("관리자 운영 데이터를 불러오는 중입니다."):
                st.session_state.dashboard_cache = load_dashboard_data(user_id)
            st.session_state.dashboard_error = None
        except Exception as error:
            st.session_state.dashboard_error = error

    dashboard_error = st.session_state.get("dashboard_error")
    if isinstance(dashboard_error, BackendAPIError):
        render_api_error(dashboard_error)
        return
    if dashboard_error is not None:
        st.error("관리자 대시보드 데이터를 불러오지 못했습니다.")
        st.caption(str(dashboard_error))
        return

    dashboard, failure_logs = st.session_state.get("dashboard_cache", ({}, []))

    if not dashboard:
        st.info("아직 표시할 운영 데이터가 없습니다.")
        return

    render_kpis(dashboard)
    st.divider()

    st.subheader("서비스 운영 현황")
    st.caption("요청 처리 결과와 주요 기능의 사용 현황을 비교해 보세요.")
    render_visual_insights(dashboard)
    st.divider()

    subject_column, operation_column = st.columns(2)
    with subject_column:
        with st.container(border=True):
            render_subject_minutes(dashboard)
    with operation_column:
        with st.container(border=True):
            render_study_and_action_counts(dashboard)

    st.divider()
    render_failure_logs(failure_logs)


def main() -> None:
    """관리자 대시보드 페이지를 실행합니다."""

    apply_dashboard_style()
    if not is_admin():
        st.error("접근 권한이 없습니다.")
        st.stop()

    user_id = str(st.session_state.get("user_id") or "")
    admin_name = str(st.session_state.get("name") or "관리자")

    render_admin_page_header(
        "ADMIN CONTROL CENTER",
        "관리자 대시보드",
        f"{admin_name}님, 서비스 운영 현황을 한눈에 확인하세요.",
    )
    render_live_dashboard(user_id)


main()
