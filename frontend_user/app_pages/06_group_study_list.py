# frontend_user/app_pages/06_group_study_list.py
"""참여 중인 그룹과 검색 가능한 그룹 스터디를 표시합니다."""

from datetime import datetime
from typing import Any

import streamlit as st

from clients.group_study_client import get_studies
from core.api_client import BackendAPIError


CATEGORY_OPTIONS = [
    "전체",
    "프론트엔드",
    "백엔드",
    "AI",
    "데이터",
    "알고리즘",
    "자격증",
    "기타",
]

STATUS_OPTIONS = [
    "모집 중",
    "모집 종료",
    "전체",
]


def apply_page_style() -> None:
    """그룹 카드의 버튼 행과 하단 여백을 간결하게 조정합니다."""

    st.markdown(
        """
        <style>
        div[class*="st-key-study_detail_"],
        div[class*="st-key-study_edit_"] {
            transform: translateY(-0.45rem);
            margin-bottom: -0.45rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_page_state() -> None:
    """그룹 스터디 검색 조건을 초기화합니다."""

    defaults = {
        "group_keyword": "",
        "group_category": "전체",
        "group_status": "모집 중",
        "group_keyword_input": "",
        "group_category_input": "전체",
        "group_status_input": "모집 중",
        "group_request_source": "list",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def move_to_create() -> None:
    """그룹 스터디 생성 화면으로 이동합니다."""

    st.session_state.pop("selected_study_id", None)
    st.session_state["group_study_form_mode"] = "create"
    st.switch_page("app_pages/07_group_study_form.py")


def move_to_detail(study_id: str) -> None:
    """선택한 그룹 스터디 상세 화면으로 이동합니다."""

    st.session_state["selected_study_id"] = study_id
    st.switch_page("app_pages/08_group_study_detail.py")


def move_to_edit(study_id: str) -> None:
    """스터디장이 목록 카드에서 바로 수정 화면으로 이동합니다."""

    st.session_state["selected_study_id"] = study_id
    st.session_state["group_study_form_mode"] = "edit"
    st.switch_page("app_pages/07_group_study_form.py")


def reset_filters() -> None:
    """검색 조건을 설계서 기본값으로 초기화합니다."""

    st.session_state["group_keyword"] = ""
    st.session_state["group_category"] = "전체"
    st.session_state["group_status"] = "모집 중"
    st.session_state["group_keyword_input"] = ""
    st.session_state["group_category_input"] = "전체"
    st.session_state["group_status_input"] = "모집 중"
    st.session_state["group_request_source"] = "list"


def convert_category(category_label: str) -> str | None:
    """전체 분야를 API 요청에서 제외합니다."""

    if category_label == "전체":
        return None

    return category_label


def convert_status(status_label: str) -> str | None:
    """한글 모집 상태를 API 값으로 변환합니다."""

    status_mapping = {
        "모집 중": "recruiting",
        "모집 종료": "closed",
        "전체": None,
    }

    return status_mapping.get(status_label)


def get_status_label(
    status: str,
    member_count: int = 0,
    capacity: int = 0,
) -> str:
    """API 모집 상태를 한글로 변환합니다."""

    if capacity > 0 and member_count >= capacity:
        return "🔴 모집 완료"

    status_mapping = {
        "recruiting": "🟢 모집 중",
        "closed": "⚪ 모집 종료",
    }

    return status_mapping.get(status, status or "상태 미정")


def load_joined_studies(user_id: str) -> list[dict[str, Any]]:
    """사용자가 참여 중인 모든 그룹 스터디를 조회합니다."""

    response = get_studies(
        user_id=user_id,
        source="list",
    )

    if not isinstance(response, dict):
        return []

    items = response.get("items", [])

    if not isinstance(items, list):
        return []

    return [
        study
        for study in items
        if isinstance(study, dict) and study.get("is_joined") is True
    ]


def load_explore_studies(user_id: str) -> list[dict[str, Any]]:
    """검색 조건에 맞는 그룹 스터디를 조회합니다."""

    source = st.session_state.get(
        "group_request_source",
        "list",
    )

    response = get_studies(
        user_id=user_id,
        keyword=st.session_state.group_keyword or None,
        category=convert_category(
            st.session_state.group_category
        ),
        status=convert_status(
            st.session_state.group_status
        ),
        source=source,
    )

    # 검색 버튼을 눌렀을 때만 source=search를 사용합니다.
    # 이후 자동·수동 갱신은 source=list로 요청합니다.
    st.session_state["group_request_source"] = "list"

    if not isinstance(response, dict):
        return []

    items = response.get("items", [])

    if not isinstance(items, list):
        return []

    # 참여 중인 그룹은 위의 별도 영역에서 표시합니다.
    return [
        study
        for study in items
        if isinstance(study, dict)
        and study.get("is_joined") is not True
    ]


def render_search_form() -> None:
    """그룹 탐색 검색 조건을 표시합니다."""

    st.subheader("그룹 탐색")

    time_column, refresh_column, create_column = st.columns(
        [3, 1, 1]
    )

    with time_column:
        st.caption(
            "마지막 조회: "
            f"{datetime.now().strftime('%H:%M:%S')}  \n"
            "2분마다 자동 갱신"
        )

    with refresh_column:
        if st.button(
            "새로고침",
            key="refresh_group_studies",
            use_container_width=True,
        ):
            st.session_state["group_request_source"] = "list"
            st.rerun(scope="fragment")

    with create_column:
        if st.button(
            "그룹 만들기",
            key="create_group_study",
            type="primary",
            use_container_width=True,
        ):
            move_to_create()

    with st.form("group_search_form"):
        keyword_column, category_column, status_column = (
            st.columns([2, 1, 1])
        )

        with keyword_column:
            keyword = st.text_input(
                "키워드",
                placeholder="그룹명 또는 공동 목표를 입력하세요",
                key="group_keyword_input",
            )

        with category_column:
            category = st.selectbox(
                "분야",
                options=CATEGORY_OPTIONS,
                key="group_category_input",
            )

        with status_column:
            status = st.selectbox(
                "상태",
                options=STATUS_OPTIONS,
                key="group_status_input",
            )

        search_column, reset_column = st.columns(2)

        with search_column:
            search_submitted = st.form_submit_button(
                "검색",
                type="primary",
                use_container_width=True,
            )

        with reset_column:
            st.form_submit_button(
                "검색 초기화",
                use_container_width=True,
                on_click=reset_filters,
            )

    if search_submitted:
        st.session_state["group_keyword"] = keyword.strip()
        st.session_state["group_category"] = category
        st.session_state["group_status"] = status

        # 사용자가 검색 버튼을 누른 경우에만 검색 로그를 남깁니다.
        st.session_state["group_request_source"] = "search"
        st.rerun()

def render_study_card(
    study: dict[str, Any],
    index: int,
    *,
    joined_section: bool,
    wide_layout: bool = True,
) -> None:
    """그룹 스터디 한 건을 카드로 표시합니다."""

    study_id = str(study.get("study_id") or "")
    title = study.get("title") or "제목 없음"
    category = study.get("category") or "분야 미지정"
    goal = study.get("goal") or "등록된 공동 목표가 없습니다."
    schedule = study.get("schedule") or "활동 일정 미정"
    member_count = int(study.get("member_count") or 0)
    capacity = int(study.get("capacity") or 0)
    status = str(study.get("status") or "")
    is_owner = str(study.get("owner_user_id") or "") == str(st.session_state.get("user_id") or "")
    owner_name = str(
        study.get("owner_name")
        or (st.session_state.get("name") if is_owner else "알 수 없음")
    )

    with st.container(border=True):
        if wide_layout:
            title_column, goal_column, status_column = st.columns([3, 3, 1])

            with title_column:
                st.markdown(f"### {title}")
                st.write(f"👑 스터디장 {owner_name}")
                st.caption(f"📅 {schedule}")

            with goal_column:
                st.markdown("**공동 목표**")
                st.write(goal)
                st.caption(f"🟣 {category}")

            with status_column:
                status_label = get_status_label(
                    status=status,
                    member_count=member_count,
                    capacity=capacity,
                )
                st.write(f"**{status_label}**")
                st.write(f"👥 참여 {member_count} / {capacity}명")

            if is_owner:
                _, detail_column, edit_column = st.columns(
                    [3, 1.4, 1.4],
                    vertical_alignment="bottom",
                )
            else:
                _, detail_column = st.columns(
                    [3, 2],
                    vertical_alignment="bottom",
                )

            with detail_column:
                open_detail = st.button(
                    "상세보기",
                    key=f"study_detail_{joined_section}_{study_id}_{index}",
                    use_container_width=True,
                )

            if is_owner:
                with edit_column:
                    if st.button(
                        "수정하기",
                        key=f"study_edit_{joined_section}_{study_id}_{index}",
                        use_container_width=True,
                    ):
                        move_to_edit(study_id)

            if open_detail:
                if not study_id:
                    st.error("스터디 ID가 없는 데이터입니다.")
                    return
                move_to_detail(study_id)
            return

        title_column, status_column = st.columns([4, 1])

        with title_column:
            st.markdown(f"### {title}")
            st.write(f"👑 스터디장 {owner_name}")
            st.caption(f"📅 {schedule}")

        with status_column:
            status_label = get_status_label(
                status=status,
                member_count=member_count,
                capacity=capacity,
            )
            st.write(f"**{status_label}**")
            st.write(f"👥 참여 {member_count} / {capacity}명")

        st.write(goal)
        st.caption(f"🟣 {category}")

        if joined_section:
            st.markdown("**🟣 참여 중인 그룹입니다.**")

        if is_owner:
            detail_column, edit_column = st.columns(2)
            with detail_column:
                open_detail = st.button(
                    "상세보기",
                    key=f"study_detail_{joined_section}_{study_id}_{index}",
                    use_container_width=True,
                )
            with edit_column:
                if st.button(
                    "수정하기",
                    key=f"study_edit_{joined_section}_{study_id}_{index}",
                    use_container_width=True,
                ):
                    move_to_edit(study_id)
        else:
            open_detail = st.button(
                "상세보기",
                key=f"study_detail_{joined_section}_{study_id}_{index}",
                use_container_width=True,
            )

        if open_detail:
            if not study_id:
                st.error("스터디 ID가 없는 데이터입니다.")
                return

            move_to_detail(study_id)



def render_joined_section(
    joined_studies: list[dict[str, Any]],
) -> None:
    """참여 중인 그룹을 별도 영역에 표시합니다."""

    st.subheader("참여 중인 그룹")
    st.caption("함께 학습하고 있는 그룹을 확인해 보세요.")

    if not joined_studies:
        st.info("현재 참여 중인 그룹 스터디가 없습니다.")
        return

    for index, study in enumerate(joined_studies):
        render_study_card(
            study,
            index,
            joined_section=True,
        )


def render_explore_section(
    studies: list[dict[str, Any]],
) -> None:
    """검색 가능한 그룹 스터디 목록을 표시합니다."""

    if not studies:
        with st.container(border=True):
            st.subheader("검색 결과가 없습니다.")
            st.write(
                "검색 조건을 변경하거나 새로운 스터디를 만들어 보세요."
            )

            if st.button(
                "스터디 생성",
                key="empty_create_study",
                type="primary",
            ):
                move_to_create()

        return

    st.caption(f"🟣 검색 결과 {len(studies)}개")

    for index, study in enumerate(studies):
        render_study_card(
            study,
            index,
            joined_section=False,
        )


def render_api_error(error: BackendAPIError) -> None:
    """표준 백엔드 오류를 표시합니다."""

    st.error(error.message)

    if error.code:
        st.caption(f"오류 코드: {error.code}")

    if error.trace_id:
        st.caption(f"추적 ID: {error.trace_id}")

    if st.button(
        "다시 시도",
        key="group_api_retry",
        type="primary",
    ):
        st.session_state["group_request_source"] = "list"
        st.rerun()


@st.fragment(run_every="120s")
def render_auto_refresh_content(user_id: str) -> None:
    """목록을 2분마다 자동으로 다시 조회합니다."""

    try:
        with st.spinner("그룹 스터디를 불러오는 중입니다."):
            joined_studies = load_joined_studies(user_id)
            explore_studies = load_explore_studies(user_id)

    except BackendAPIError as error:
        render_api_error(error)
        return

    except Exception as error:
        st.error("그룹 스터디를 불러오지 못했습니다.")
        st.caption(str(error))

        if st.button(
            "다시 시도",
            key="group_unknown_retry",
        ):
            st.rerun(scope="fragment")

        return

    render_joined_section(joined_studies)
    st.divider()

    render_search_form()
    st.divider()

    render_explore_section(explore_studies)


def main() -> None:
    """그룹 스터디 목록 페이지를 실행합니다."""

    apply_page_style()
    initialize_page_state()

    user_id = st.session_state.get("user_id")

    if not user_id:
        st.warning("로그인 정보가 없습니다. 다시 로그인해 주세요.")
        st.stop()

    st.title("그룹 스터디")
    st.write("함께 공부할 그룹 스터디를 찾아보세요.")

    st.divider()

    render_auto_refresh_content(str(user_id))


main()

