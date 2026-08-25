"""Supabase에서 개인 학습 기록 CRUD와 과목별 통계를 처리합니다."""

from collections import defaultdict

from fastapi import HTTPException


PROOF_IMAGE_BUCKET = "proof-images"
SIGNED_URL_EXPIRES_IN = 60 * 60


def _rows(result):
    return result.data or []


def _one(result):
    rows = _rows(result)
    return rows[0] if rows else None


def _record_view(row):
    return {
        "record_id": row["record_id"],
        "subject": row["subject"],
        "content": row.get("content"),
        "study_minutes": row["study_minutes"],
        "studied_on": row["studied_on"],
        "proof_image_path": row.get("proof_image_path"),
    }


def _not_found(record_id):
    raise HTTPException(404, {"code": "RECORD_NOT_FOUND", "message": "학습 기록을 찾을 수 없습니다.", "details": {"record_id": str(record_id)}})


def _create_proof_image_url(client, image_path):
    """Storage 경로를 한 시간 동안 사용할 수 있는 이미지 URL로 변환합니다."""

    if not image_path:
        return None

    image_value = str(image_path)
    if image_value.startswith(("http://", "https://", "data:image")):
        return image_value

    try:
        response = (
            client.storage
            .from_(PROOF_IMAGE_BUCKET)
            .create_signed_url(
                image_value,
                SIGNED_URL_EXPIRES_IN,
            )
        )
    except Exception:
        return None

    if not isinstance(response, dict):
        return None

    return response.get("signedURL") or response.get("signedUrl")


def list_records(client, user_id, *, from_date=None, to_date=None, subject=None):
    query = client.table("study_records").select("*").eq("user_id", str(user_id)).order("studied_on", desc=True)
    if from_date:
        query = query.gte("studied_on", from_date.isoformat())
    if to_date:
        query = query.lte("studied_on", to_date.isoformat())
    if subject:
        query = query.eq("subject", subject)
    rows = [_record_view(row) for row in _rows(query.execute())]
    return {"items": rows, "total": len(rows)}


def get_record(client, record_id, user_id):
    row = _one(client.table("study_records").select("*").eq("record_id", str(record_id)).eq("user_id", str(user_id)).limit(1).execute())
    if not row:
        _not_found(record_id)
    record = _record_view(row)
    record["proof_image_url"] = _create_proof_image_url(
        client,
        record.get("proof_image_path"),
    )
    return record


def create_record(client, payload):
    row = _one(client.table("study_records").insert({key: (str(value) if key == "user_id" else value) for key, value in payload.model_dump(mode="json").items()}).execute())
    return _record_view(row)


def update_record(client, record_id, payload):
    values = payload.model_dump(mode="json", exclude={"user_id"})
    row = _one(client.table("study_records").update(values).eq("record_id", str(record_id)).eq("user_id", str(payload.user_id)).execute())
    if not row:
        _not_found(record_id)
    return _record_view(row)


def delete_record(client, record_id, user_id):
    rows = _rows(client.table("study_records").delete().eq("record_id", str(record_id)).eq("user_id", str(user_id)).execute())
    if not rows:
        _not_found(record_id)


def get_record_stats(client, user_id, *, from_date=None, to_date=None):
    query = client.table("study_records").select("subject,study_minutes").eq("user_id", str(user_id))
    if from_date:
        query = query.gte("studied_on", from_date.isoformat())
    if to_date:
        query = query.lte("studied_on", to_date.isoformat())
    totals = defaultdict(int)
    for row in _rows(query.execute()):
        totals[row["subject"]] += int(row["study_minutes"])
    return {"total_minutes": sum(totals.values()), "by_subject": [{"subject": subject, "minutes": minutes} for subject, minutes in sorted(totals.items())]}
