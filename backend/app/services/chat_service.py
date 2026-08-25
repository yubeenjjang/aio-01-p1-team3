"""대화방·메시지 저장과 Gemini 멀티턴 호출 기능입니다."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException


DEFAULT_TITLE = "새 학습 코치 대화"
SYSTEM_INSTRUCTION = "당신은 친절한 학습 코치입니다. 학습 질문에 한국어로 정확하고 실천적인 답변을 제공하세요."


def _rows(result) -> list[dict]:
    return result.data or []


def _conversation_or_404(client, conversation_id: UUID, user_id: UUID) -> dict:
    result = client.table("chat_conversations").select("*").eq("conversation_id", str(conversation_id)) \
        .eq("user_id", str(user_id)).maybe_single().execute()
    if not result.data:
        raise HTTPException(404, {"code": "CONVERSATION_NOT_FOUND", "message": "대화방을 찾을 수 없습니다."})
    return result.data


def create_conversation(client, payload) -> dict:
    values = {"user_id": str(payload.user_id), "title": payload.title or DEFAULT_TITLE}
    return client.table("chat_conversations").insert(values).execute().data[0]


def list_conversations(client, user_id: UUID) -> dict:
    rows = _rows(client.table("chat_conversations").select("conversation_id,title,updated_at,chat_messages(count)")
                 .eq("user_id", str(user_id)).order("updated_at", desc=True).execute())
    items = []
    for row in rows:
        counts = row.get("chat_messages") or []
        row["message_count"] = int(counts[0].get("count", 0)) if counts else 0
        row.pop("chat_messages", None)
        items.append(row)
    return {"items": items, "total": len(items)}


def list_messages(client, conversation_id: UUID, user_id: UUID) -> dict:
    _conversation_or_404(client, conversation_id, user_id)
    rows = _rows(client.table("chat_messages").select("message_id,role,content,created_at").eq("conversation_id", str(conversation_id))
                 .order("created_at").order("message_id").execute())
    return {"items": rows, "total": len(rows)}


def _recent_contents(client, conversation_id: UUID, history_limit: int = 20) -> list[dict[str, object]]:
    rows = _rows(client.table("chat_messages").select("role,content").eq("conversation_id", str(conversation_id))
                 .order("created_at", desc=True).order("message_id", desc=True).limit(history_limit).execute())
    rows.reverse()
    return [{"role": row["role"], "parts": [{"text": row["content"]}]} for row in rows]


def _gemini_error(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", None)
    message = str(exc)
    if status_code == 429 or "RESOURCE_EXHAUSTED" in message or "429" in message:
        return HTTPException(429, {"code": "RATE_LIMITED", "message": "Gemini API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요."})
    if status_code == 503 or "UNAVAILABLE" in message:
        return HTTPException(503, {"code": "GEMINI_UNAVAILABLE", "message": "Gemini 서비스를 사용할 수 없습니다."})
    return HTTPException(500, {"code": "GEMINI_REQUEST_FAILED", "message": "Gemini 채팅 요청에 실패했습니다."})


def create_message(client, conversation_id: UUID, payload) -> dict:
    _conversation_or_404(client, conversation_id, payload.user_id)
    user_message = client.table("chat_messages").insert({"conversation_id": str(conversation_id), "role": "user", "content": payload.content}).execute().data[0]
    # Gemini 호출이 실패해도 사용자가 보낸 새 질문은 대화방 최신 순서에 반영합니다.
    client.table("chat_conversations").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq("conversation_id", str(conversation_id)).execute()
    try:
        from app.core.gemini_config import generate_gemini_contents

        answer = generate_gemini_contents(_recent_contents(client, conversation_id), SYSTEM_INSTRUCTION)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(503, {"code": "GEMINI_UNAVAILABLE", "message": "Gemini 서비스를 사용할 수 없습니다."}) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise _gemini_error(exc) from exc
    model_message = client.table("chat_messages").insert({"conversation_id": str(conversation_id), "role": "model", "content": answer}).execute().data[0]
    client.table("chat_conversations").update({"updated_at": datetime.now(timezone.utc).isoformat()}).eq("conversation_id", str(conversation_id)).execute()
    return {"user_message": user_message, "model_message": model_message}


def delete_conversation(client, conversation_id: UUID, user_id: UUID) -> None:
    _conversation_or_404(client, conversation_id, user_id)
    client.table("chat_conversations").delete().eq("conversation_id", str(conversation_id)).execute()
