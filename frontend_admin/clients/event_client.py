"""관리자 운영 로그 SSE 이벤트를 수신합니다."""

from __future__ import annotations

import json
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any, Iterator

import httpx
import streamlit as st

from core.api_client import BACKEND_URL, BackendAPIError


def receive_admin_events(
    admin_user_id: str,
) -> Iterator[tuple[str, dict[str, Any]]]:
    """관리자 SSE에 연결해 event와 data를 순서대로 반환합니다."""

    try:
        with httpx.stream(
            "GET",
            f"{BACKEND_URL}/events/stream",
            params={"admin_user_id": admin_user_id},
            headers={"Accept": "text/event-stream"},
            timeout=None,
        ) as response:
            response.raise_for_status()
            event_name = "message"

            for line in response.iter_lines():
                if line.startswith("event:"):
                    event_name = line.removeprefix("event:").strip() or "message"
                elif line.startswith(":"):
                    yield "keep-alive", {}
                elif line.startswith("data:"):
                    data = _parse_event_data(line.removeprefix("data:").strip())
                    if data is not None:
                        yield event_name, data
                    event_name = "message"
    except (httpx.HTTPError, ValueError) as error:
        raise BackendAPIError(
            "관리자 실시간 연결에 실패했습니다.",
            code="SSE_CONNECTION_ERROR",
        ) from error


@dataclass(frozen=True)
class AdminEvent:
    """관리자 화면 갱신에 필요한 SSE 이벤트 정보입니다."""

    name: str
    data: dict[str, Any]


class AdminEventListener:
    """SSE 연결을 백그라운드에서 유지하고 이벤트를 큐에 전달합니다."""

    def __init__(self, admin_user_id: str) -> None:
        self.admin_user_id = admin_user_id
        self.events: Queue[AdminEvent] = Queue()
        self._stop_event = Event()
        self.thread = Thread(
            target=self._listen,
            daemon=True,
            name="admin-sse-listener",
        )
        self.thread.start()

    def _listen(self) -> None:
        url = f"{BACKEND_URL}/events/stream"

        while not self._stop_event.is_set():
            try:
                with httpx.stream(
                    "GET",
                    url,
                    params={"admin_user_id": self.admin_user_id},
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache",
                    },
                    timeout=httpx.Timeout(
                        connect=5.0,
                        read=45.0,
                        write=5.0,
                        pool=5.0,
                    ),
                ) as response:
                    response.raise_for_status()
                    event_name = "message"

                    for line in response.iter_lines():
                        if self._stop_event.is_set():
                            return
                        if line.startswith("event:"):
                            event_name = (
                                line.removeprefix("event:").strip()
                                or "message"
                            )
                        elif line.startswith("data:"):
                            payload = _parse_event_data(
                                line.removeprefix("data:").strip()
                            )
                            if payload is not None:
                                self.events.put(AdminEvent(event_name, payload))
                            event_name = "message"
            except (httpx.HTTPError, ValueError):
                self._stop_event.wait(5.0)

    def stop(self) -> None:
        """현재 SSE 재연결 작업을 중지합니다."""

        self._stop_event.set()

    def drain(self) -> list[AdminEvent]:
        """큐에 쌓인 이벤트를 모두 반환합니다."""

        received: list[AdminEvent] = []
        while True:
            try:
                received.append(self.events.get_nowait())
            except Empty:
                return received


def _parse_event_data(raw_data: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw_data)
    except (TypeError, ValueError):
        return None

    return payload if isinstance(payload, dict) else None


def get_admin_events(admin_user_id: str) -> list[AdminEvent]:
    """Streamlit 세션별 리스너를 만들고 대기 중인 이벤트를 반환합니다."""

    listener = st.session_state.get("admin_event_listener")
    if not isinstance(listener, AdminEventListener) or (
        listener.admin_user_id != admin_user_id
    ):
        if isinstance(listener, AdminEventListener):
            listener.stop()
        listener = AdminEventListener(admin_user_id)
        st.session_state.admin_event_listener = listener

    return listener.drain()
