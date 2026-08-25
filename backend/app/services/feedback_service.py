"""AI 분석 평가의 저장·조회 기능입니다."""

from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException


def _rows(result) -> list[dict]:
    return result.data or []


def _require_study_records(client, user_id: UUID, period_start: date, period_end: date) -> None:
    records = _rows(
        client.table("study_records").select("record_id").eq("user_id", str(user_id))
        .gte("studied_on", period_start.isoformat()).lte("studied_on", period_end.isoformat()).limit(1).execute()
    )
    if not records:
        raise HTTPException(404, {"code": "NO_STUDY_RECORDS", "message": "평가할 분석 기간의 학습 기록이 없습니다."})


def save_feedback(client, payload) -> tuple[dict, bool]:
    """기간별 평가를 최초 생성하거나 기존 행을 수정합니다."""
    _require_study_records(client, payload.user_id, payload.period_start, payload.period_end)
    existing_result = client.table("analysis_feedback").select("feedback_id").eq("user_id", str(payload.user_id)) \
        .eq("period_start", payload.period_start.isoformat()).eq("period_end", payload.period_end.isoformat()).maybe_single().execute()
    # 현재 Supabase 클라이언트는 조회 결과가 없을 때 응답 객체 대신 None을 반환할 수 있습니다.
    existing = existing_result.data if existing_result else None
    values = {
        "user_id": str(payload.user_id),
        "period_start": payload.period_start.isoformat(),
        "period_end": payload.period_end.isoformat(),
        "rating": payload.rating,
        "comment": payload.comment,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    # UNIQUE 제약조건과 같은 키를 사용해 동시 저장 요청도 하나의 평가로 합칩니다.
    result = client.table("analysis_feedback").upsert(
        values,
        on_conflict="user_id,period_start,period_end",
    ).execute()
    return result.data[0], not bool(existing)


def get_feedback(client, user_id: UUID, period_start: date, period_end: date) -> dict:
    result = client.table("analysis_feedback").select("*").eq("user_id", str(user_id)) \
        .eq("period_start", period_start.isoformat()).eq("period_end", period_end.isoformat()).maybe_single().execute()
    # 평가가 아직 없으면 result 자체가 None인 Supabase 클라이언트 버전을 함께 처리합니다.
    feedback = result.data if result else None
    if not feedback:
        raise HTTPException(404, {"code": "FEEDBACK_NOT_FOUND", "message": "해당 기간의 평가가 없습니다."})
    return feedback


def list_admin_feedback(client, *, rating: int | None, from_date: date | None, to_date: date | None, limit: int, offset: int) -> dict:
    query = client.table("analysis_feedback").select("feedback_id,user_id,period_start,period_end,rating,comment,created_at,updated_at,users(name)", count="exact").order("created_at", desc=True).range(offset, offset + limit - 1)
    if rating is not None:
        query = query.eq("rating", rating)
    if from_date is not None:
        query = query.gte("created_at", from_date.isoformat())
    if to_date is not None:
        next_day = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc).isoformat()
        query = query.lt("created_at", next_day)
    result = query.execute()
    items = []
    for row in _rows(result):
        user = row.pop("users", None) or {}
        row["user_name"] = user.get("name")
        items.append(row)
    rating_query = client.table("analysis_feedback").select("rating")
    if rating is not None:
        rating_query = rating_query.eq("rating", rating)
    if from_date is not None:
        rating_query = rating_query.gte("created_at", from_date.isoformat())
    if to_date is not None:
        rating_query = rating_query.lt("created_at", datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc).isoformat())
    all_ratings = _rows(rating_query.execute())
    average = round(sum(int(row["rating"]) for row in all_ratings) / len(all_ratings), 2) if all_ratings else None
    distribution = {str(value): 0 for value in range(1, 6)}
    for row in all_ratings:
        distribution[str(row["rating"])] += 1
    return {
        "items": items,
        "total": result.count if result.count is not None else len(items),
        "average_rating": average,
        "rating_distribution": distribution,
    }
