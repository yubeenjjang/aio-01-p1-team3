"""관리자 운영 로그를 필터링하고 선택한 로그의 상세를 표시합니다."""

from datetime import datetime
from typing import Any

import streamlit as st

from clients.admin_client import get_logs
from clients.event_client import get_admin_events
from components.admin_shell import render_admin_page_header
from core.api_client import BackendAPIError
from core.auth import is_admin, logout

STATUS_OPTIONS = ["전체", "성공", "실패"]
ACTION_OPTIONS = [
    "전체",
    "auth.login",
    "auth.logout",
    "record.create",
    "record.update",
    "record.delete",
    "record.list",
    "record.image_upload",
    "study.create",
    "study.update",
    "study.list",
    "study.search",
    "study.detail",
    "study.join",
    "study.leave",
    "analysis.request",
    "chat.conversation.create",
    "chat.message",
    "chat.conversation.delete",
    "analysis.feedback.submit",
    "admin.analysis_feedback.list",
]

LOG_REFRESH_ACTIONS = set(ACTION_OPTIONS[1:])


def apply_logs_style() -> None:
    """Use a compact operations-console look without shared UI helpers."""

    st.markdown(
        """
        <style>
        .stApp { background: #f6f8fc; }
        .block-container { max-width: 1440px; padding-top: 2.4rem; padding-bottom: 3rem; }
        .logs-eyebrow { color: #475569; font-weight: 750; letter-spacing: .1em; font-size: .72rem; }
        .status-chip { display: inline-block; padding: .22rem .46rem; border: 1px solid #bbf7d0; border-radius: 999px; background: #f0fdf4; color: #15803d; font-size: .68rem; font-weight: 700; }
        .live-note { margin-left: .45rem; color: #94a3b8; font-size: .73rem; }
        div[data-testid="stMetric"] { padding: 1rem 1.1rem; border: 1px solid #e5eaf2; border-radius: 14px; background: #ffffff; box-shadow: 0 2px 10px rgba(15, 23, 42, .035); }
        div[data-testid="stForm"] { border: 1px solid #e5eaf2; border-radius: 14px; background: #ffffff; padding: 1rem 1.1rem; }
        div[data-testid="stDataFrame"] { border: 1px solid #e5eaf2; border-radius: 12px; overflow: hidden; background: #ffffff; }
        h1, h2, h3 { color: #0f172a; letter-spacing: -.025em; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_slim_bar_chart(rows: list[dict[str, Any]]) -> None:
    """Render compact event bars for quick comparison."""

    st.vega_lite_chart(
        rows,
        {
            "mark": {"type": "bar", "size": 16, "cornerRadiusEnd": 4},
            "encoding": {
                "x": {"field": "기능", "type": "nominal", "axis": {"labelAngle": 0}},
                "y": {"field": "이벤트", "type": "quantitative"},
                "color": {"value": "#2563eb"},
                "tooltip": [{"field": "기능"}, {"field": "이벤트"}],
            },
        },
        use_container_width=True,
    )


def render_log_overview(logs: list[dict[str, Any]]) -> None:
    """Show at-a-glance metrics and charts for the loaded log set."""

    success_logs = [log for log in logs if log.get("status") == "success"]
    failure_logs = [log for log in logs if log.get("status") == "failure"]
    latency_values = [float(log.get("latency_ms", 0) or 0) for log in logs]
    average_latency = sum(latency_values) / len(latency_values) if latency_values else 0
    error_rate = (len(failure_logs) / len(logs) * 100) if logs else 0

    metric_columns = st.columns(4)
    metric_columns[0].metric("조회 로그", f"{len(logs):,}건")
    metric_columns[1].metric("성공", f"{len(success_logs):,}건")
    metric_columns[2].metric("실패율", f"{error_rate:.1f}%")
    metric_columns[3].metric("평균 처리 시간", f"{average_latency:,.0f}ms")

    action_counts: dict[str, int] = {}
    for log in logs:
        action = str(log.get("action") or "기타")
        action_counts[action] = action_counts.get(action, 0) + 1

    chart_left, chart_right = st.columns(2)
    with chart_left:
        with st.container(border=True):
            st.subheader("처리 결과 분포")
            st.vega_lite_chart(
            [{"상태": "성공", "건수": len(success_logs)}, {"상태": "실패", "건수": len(failure_logs)}],
            {
                "mark": {"type": "arc", "innerRadius": 55},
                "encoding": {
                    "theta": {"field": "건수", "type": "quantitative"},
                    "color": {
                        "field": "상태",
                        "type": "nominal",
                        "scale": {
                            "domain": ["성공", "실패"],
                            "range": ["#15803d", "#dc2626"],
                        },
                    },
                    "tooltip": [{"field": "상태"}, {"field": "건수"}],
                },
            },
            use_container_width=True,
            )
    with chart_right:
        with st.container(border=True):
            st.subheader("기능별 이벤트")
            if action_counts:
                render_slim_bar_chart(
                    [{"기능": action, "이벤트": count} for action, count in action_counts.items()]
                )
            else:
                st.info("표시할 로그 데이터가 없습니다.")


def initialize_filter_state() -> None:
    """적용된 운영 로그 필터를 초기화합니다."""

    defaults = {
        "admin_log_status": "전체",
        "admin_log_action": "전체",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def invalidate_logs_cache() -> None:
    """필터 변경 뒤 이전 조회 결과가 화면에 남지 않도록 캐시를 비웁니다."""

    st.session_state.pop("logs_cache", None)
    st.session_state.pop("logs_cache_key", None)
    st.session_state.pop("logs_error", None)
    st.session_state.logs_force_refresh = True


def status_to_api(status_label: str) -> str | None:
    """한글 상태 필터를 API Query 값으로 변환합니다."""

    values = {
        "전체": None,
        "성공": "success",
        "실패": "failure",
    }
    return values.get(status_label)


def status_label(status: Any) -> str:
    """API 로그 상태를 한글로 변환합니다."""

    labels = {
        "success": "성공",
        "failure": "실패",
    }
    return labels.get(str(status), str(status or "-"))


def load_logs(user_id: str) -> list[dict[str, Any]]:
    """현재 적용된 상태와 action 필터로 운영 로그를 조회합니다."""

    selected_action = st.session_state.admin_log_action
    response = get_logs(
        user_id=user_id,
        status=status_to_api(st.session_state.admin_log_status),
        action=None if selected_action == "전체" else selected_action,
        limit=50,
    )

    if not isinstance(response, dict):
        return []

    items = response.get("items", [])
    if not isinstance(items, list):
        return []

    return [item for item in items if isinstance(item, dict)]


def render_filters() -> None:
    """상태·기능 필터와 검색 버튼을 표시합니다."""

    with st.form("admin_log_filter_form"):
        status_column, action_column = st.columns(2)

        with status_column:
            selected_status = st.selectbox(
                "상태",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(st.session_state.admin_log_status),
            )

        with action_column:
            selected_action = st.selectbox(
                "기능",
                ACTION_OPTIONS,
                index=ACTION_OPTIONS.index(st.session_state.admin_log_action),
            )

        search_column, reset_column = st.columns(2)

        with search_column:
            search_submitted = st.form_submit_button(
                "검색",
                type="primary",
                use_container_width=True,
            )

        with reset_column:
            reset_submitted = st.form_submit_button(
                "필터 초기화",
                use_container_width=True,
            )

    if search_submitted:
        st.session_state.admin_log_status = selected_status
        st.session_state.admin_log_action = selected_action
        invalidate_logs_cache()
        st.rerun()

    if reset_submitted:
        st.session_state.admin_log_status = "전체"
        st.session_state.admin_log_action = "전체"
        invalidate_logs_cache()
        st.rerun()


def render_log_detail(log: dict[str, Any]) -> None:
    """선택한 로그의 처리 시간·trace ID·오류 상세를 표시합니다."""

    st.subheader("로그 상세")

    with st.container(border=True):
        first_row = st.columns(3)
        first_row[0].metric("상태", status_label(log.get("status")))
        first_row[1].metric("처리 시간", f"{log.get('latency_ms', 0)}ms")
        first_row[2].metric("사용자", log.get("user_name", "-"))

        st.markdown("**Action**")
        st.code(str(log.get("action", "-")), language=None)

        st.markdown("**Trace ID**")
        st.code(str(log.get("trace_id", "-")), language=None)

        st.markdown("**메시지**")
        st.write(log.get("message", "-"))

        error_details = log.get("details") or log.get("error_details")
        if error_details:
            st.markdown("**오류 상세**")
            st.json(error_details)


def render_log_table(logs: list[dict[str, Any]]) -> None:
    """로그 목록을 표시하고 선택한 행의 상세를 연결합니다."""

    if not logs:
        st.info("선택한 조건에 맞는 운영 로그가 없습니다.")
        return

    rows = [
        {
            "시각": log.get("created_at", "-"),
            "사용자": log.get("user_name", "-"),
            "action": log.get("action", "-"),
            "상태": status_label(log.get("status")),
            "메시지": log.get("message", "-"),
        }
        for log in logs
    ]

    event = st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="admin_logs_table",
    )

    selected_rows = event.selection.rows
    if selected_rows:
        selected_index = selected_rows[0]

        if 0 <= selected_index < len(logs):
            render_log_detail(logs[selected_index])
    else:
        st.caption("로그 행을 선택하면 처리 시간과 trace ID가 표시됩니다.")


def render_api_error(error: BackendAPIError) -> None:
    """권한 오류 또는 운영 로그 API 오류를 표시합니다."""

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

    if st.button("다시 시도", key="logs_retry", type="primary"):
        st.session_state.logs_force_refresh = True
        st.rerun(scope="fragment")


@st.fragment(run_every="5s")
def render_live_logs(user_id: str) -> None:
    """SSE 큐를 5초마다 확인하고 이벤트가 있을 때만 운영 로그를 재조회합니다."""

    time_column, refresh_column = st.columns([20, 1])

    with time_column:
        st.markdown(
            f'<span class="status-chip">● SSE 연결</span><span class="live-note">마지막 확인 {datetime.now().strftime("%H:%M:%S")} · 이벤트 확인 5초</span>',
            unsafe_allow_html=True,
        )

    with refresh_column:
        if st.button("↻", key="logs_refresh", help="지금 새로고침"):
            st.session_state.logs_force_refresh = True

    events = get_admin_events(user_id)
    has_event = any(
        event.name == "admin.log.updated"
        and event.data.get("action") in LOG_REFRESH_ACTIONS
        for event in events
    )
    filter_key = (
        st.session_state.admin_log_status,
        st.session_state.admin_log_action,
    )
    force_refresh = st.session_state.pop("logs_force_refresh", False)
    should_load = (
        "logs_cache" not in st.session_state
        or st.session_state.get("logs_cache_key") != filter_key
        or has_event
        or force_refresh
    )
    if has_event:
        st.toast("새 운영 로그를 반영했습니다.", icon="🔄")

    if should_load:
        try:
            with st.spinner("운영 로그를 불러오는 중입니다."):
                st.session_state.logs_cache = load_logs(user_id)
            st.session_state.logs_cache_key = filter_key
            st.session_state.logs_error = None
        except Exception as error:
            st.session_state.logs_error = error

    logs_error = st.session_state.get("logs_error")
    if isinstance(logs_error, BackendAPIError):
        render_api_error(logs_error)
        return
    if logs_error is not None:
        st.error("운영 로그를 불러오지 못했습니다.")
        st.caption(str(logs_error))
        return

    logs = st.session_state.get("logs_cache", [])

    render_log_overview(logs)
    st.divider()
    render_log_table(logs)


def main() -> None:
    """운영 로그 페이지를 실행합니다."""

    apply_logs_style()
    if not is_admin():
        st.error("접근 권한이 없습니다.")
        st.stop()

    initialize_filter_state()
    user_id = str(st.session_state.get("user_id") or "")

    render_admin_page_header(
        "LIVE OPERATIONS",
        "운영 로그",
        "서비스 이벤트를 필터링하고, 오류 추이와 처리 결과를 빠르게 확인하세요.",
    )

    render_filters()
    st.divider()
    render_live_logs(user_id)


main()
