"""학습 기록을 모아 Gemini에 전달하고 분석 결과를 검증합니다."""

import json
from collections import defaultdict

from fastapi import HTTPException


def _rows(result):
    return result.data or []


def _build_prompt(records, period_start, period_end) -> str:
    subject_minutes = defaultdict(int)
    total_minutes = 0
    record_lines = []
    for record in records:
        minutes = int(record["study_minutes"])
        subject_minutes[record["subject"]] += minutes
        total_minutes += minutes
        content = record.get("content") or ""
        record_lines.append(f"- {record['studied_on']} | {record['subject']} | {minutes}분 | {content}")

    subject_summary = ", ".join(f"{subject}: {minutes}분" for subject, minutes in subject_minutes.items())
    return f"""당신은 학습 코치입니다. 아래 학습 기록을 분석하세요.

분석 기간: {period_start} ~ {period_end}
총 학습 시간: {total_minutes}분
과목별 학습 시간: {subject_summary}
학습 기록:
{chr(10).join(record_lines)}

반드시 아래 JSON 객체만 반환하세요. Markdown 코드 블록은 사용하지 마세요.
{{
  \"summary\": \"학습 요약\",
  \"strengths\": [\"강점\"],
  \"improvements\": [\"개선점\"],
  \"next_goal\": \"다음 목표\"
}}"""


def _parse_analysis(text: str) -> dict:
    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "GEMINI_REQUEST_FAILED", "message": "Gemini 응답을 처리하지 못했습니다."},
        ) from exc

    required = ("summary", "strengths", "improvements", "next_goal")
    if not isinstance(payload, dict) or any(key not in payload for key in required):
        raise HTTPException(
            status_code=500,
            detail={"code": "GEMINI_REQUEST_FAILED", "message": "Gemini 응답 형식이 올바르지 않습니다."},
        )
    if not isinstance(payload["summary"], str) or not isinstance(payload["next_goal"], str):
        raise HTTPException(500, {"code": "GEMINI_REQUEST_FAILED", "message": "Gemini 응답 형식이 올바르지 않습니다."})
    if not all(isinstance(item, str) for item in payload["strengths"]) or not all(isinstance(item, str) for item in payload["improvements"]):
        raise HTTPException(500, {"code": "GEMINI_REQUEST_FAILED", "message": "Gemini 응답 형식이 올바르지 않습니다."})
    return payload


def _generate_text(prompt: str) -> str:
    """Import lazily so the analysis router remains testable until A adds Gemini configuration."""
    from app.core.gemini_config import generate_gemini_text

    return generate_gemini_text(prompt)


def _gemini_error(exc: Exception) -> HTTPException:
    """Gemini SDK 오류를 API 명세의 상태 코드와 오류 코드로 바꿉니다."""
    status_code = getattr(exc, "status_code", None)
    message = str(exc)

    # Gemini SDK는 무료 할당량 초과 시 `429 RESOURCE_EXHAUSTED`를 반환합니다.
    if status_code == 429 or "RESOURCE_EXHAUSTED" in message or "429" in message:
        return HTTPException(
            status_code=429,
            detail={"code": "RATE_LIMITED", "message": "Gemini API 호출 한도를 초과했습니다. 잠시 후 다시 시도하세요."},
        )

    if status_code == 503 or "UNAVAILABLE" in message:
        return HTTPException(
            status_code=503,
            detail={"code": "GEMINI_UNAVAILABLE", "message": "Gemini 서비스를 사용할 수 없습니다."},
        )

    return HTTPException(
        status_code=500,
        detail={"code": "GEMINI_REQUEST_FAILED", "message": "Gemini 분석 요청에 실패했습니다."},
    )


def analyze_records(client, payload):
    records = _rows(
        client.table("study_records")
        .select("subject,content,study_minutes,studied_on")
        .eq("user_id", str(payload.user_id))
        .gte("studied_on", payload.period_start.isoformat())
        .lte("studied_on", payload.period_end.isoformat())
        .order("studied_on")
        .execute()
    )
    if not records:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_STUDY_RECORDS", "message": "분석할 학습 기록이 없습니다."},
        )

    prompt = _build_prompt(records, payload.period_start, payload.period_end)
    try:
        response_text = _generate_text(prompt)
    except (TimeoutError, ConnectionError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "GEMINI_UNAVAILABLE", "message": "Gemini 서비스를 사용할 수 없습니다."},
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise _gemini_error(exc) from exc
    return _parse_analysis(response_text)
