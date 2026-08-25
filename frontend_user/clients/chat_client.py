"""멀티턴 학습 코치 API 호출 함수입니다."""

from typing import Any

from core.api_client import request


def create_conversation(
    user_id: str,
    title: str | None = None,
) -> dict[str, Any]:
    payload = {"user_id": user_id}
    if title and title.strip():
        payload["title"] = title.strip()
    return request("POST", "/chat/conversations", json=payload)


def get_conversations(user_id: str) -> dict[str, Any]:
    return request(
        "GET",
        "/chat/conversations",
        params={"user_id": user_id},
    )


def get_messages(
    conversation_id: str,
    user_id: str,
) -> dict[str, Any]:
    return request(
        "GET",
        f"/chat/conversations/{conversation_id}/messages",
        params={"user_id": user_id},
    )


def send_message(
    conversation_id: str,
    user_id: str,
    content: str,
) -> dict[str, Any]:
    if not content.strip():
        raise ValueError("질문 내용을 입력해 주세요.")
    return request(
        "POST",
        f"/chat/conversations/{conversation_id}/messages",
        json={
            "user_id": user_id,
            "content": content.strip(),
        },
    )


def delete_conversation(
    conversation_id: str,
    user_id: str,
) -> None:
    request(
        "DELETE",
        f"/chat/conversations/{conversation_id}",
        params={"user_id": user_id},
    )
