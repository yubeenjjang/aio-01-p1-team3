"""Supabase에서 그룹 스터디와 참여자 정보를 관리합니다."""

from collections import Counter

from fastapi import HTTPException


def _rows(result):
    return result.data or []


def _one(result):
    rows = _rows(result)
    return rows[0] if rows else None


def _not_found(study_id):
    raise HTTPException(
        status_code=404,
        detail={"code": "STUDY_NOT_FOUND", "message": "스터디를 찾을 수 없습니다.", "details": {"study_id": str(study_id)}},
    )


def _require_owner(study, user_id) -> None:
    if str(study["owner_user_id"]) != str(user_id):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "STUDY_OWNER_REQUIRED",
                "message": "스터디를 만든 사용자만 수정하거나 삭제할 수 있습니다.",
            },
        )


def _member_count(client, study_id) -> int:
    return len(_rows(client.table("study_members").select("study_member_id").eq("study_id", str(study_id)).execute()))


def _is_joined(client, study_id, user_id) -> bool:
    return bool(_one(client.table("study_members").select("study_member_id").eq("study_id", str(study_id)).eq("user_id", str(user_id)).limit(1).execute()))


def _owner_name(client, owner_user_id) -> str:
    owner = _one(
        client.table("users")
        .select("name")
        .eq("user_id", str(owner_user_id))
        .limit(1)
        .execute()
    )
    return str((owner or {}).get("name") or "알 수 없음")


def _study_response(client, study, user_id):
    return {
        "study_id": study["study_id"],
        "owner_user_id": study["owner_user_id"],
        "owner_name": _owner_name(client, study["owner_user_id"]),
        "title": study["title"],
        "category": study["category"],
        "goal": study["goal"],
        "schedule": study["schedule"],
        "capacity": study["capacity"],
        "member_count": _member_count(client, study["study_id"]),
        "status": study["status"],
        "is_joined": _is_joined(client, study["study_id"], user_id),
    }


def _study_list_responses(client, studies, user_id):
    """목록에 필요한 사용자·참여 정보를 일괄 조회해 응답을 조립합니다."""
    if not studies:
        return []

    study_ids = [str(study["study_id"]) for study in studies]
    owner_ids = list({str(study["owner_user_id"]) for study in studies})

    member_rows = _rows(
        client.table("study_members")
        .select("study_id,user_id")
        .in_("study_id", study_ids)
        .execute()
    )
    owner_rows = _rows(
        client.table("users")
        .select("user_id,name")
        .in_("user_id", owner_ids)
        .execute()
    )

    member_counts = Counter(str(member["study_id"]) for member in member_rows)
    joined_study_ids = {
        str(member["study_id"])
        for member in member_rows
        if str(member["user_id"]) == str(user_id)
    }
    owner_names = {
        str(owner["user_id"]): str(owner.get("name") or "알 수 없음")
        for owner in owner_rows
    }

    return [
        {
            "study_id": study["study_id"],
            "owner_user_id": study["owner_user_id"],
            "owner_name": owner_names.get(str(study["owner_user_id"]), "알 수 없음"),
            "title": study["title"],
            "category": study["category"],
            "goal": study["goal"],
            "schedule": study["schedule"],
            "capacity": study["capacity"],
            "member_count": member_counts.get(str(study["study_id"]), 0),
            "status": study["status"],
            "is_joined": str(study["study_id"]) in joined_study_ids,
        }
        for study in studies
    ]


def list_studies(client, user_id, *, keyword: str | None = None, category: str | None = None, status: str | None = None):
    query = client.table("studies").select("*").order("created_at", desc=True)
    if keyword:
        query = query.ilike("title", f"%{keyword}%")
    if category:
        query = query.eq("category", category)
    if status:
        query = query.eq("status", status)
    studies = _rows(query.execute())
    items = _study_list_responses(client, studies, user_id)
    return {"items": items, "total": len(items)}


def get_study_detail(client, study_id, user_id):
    study = _one(client.table("studies").select("*").eq("study_id", str(study_id)).limit(1).execute())
    if not study:
        _not_found(study_id)

    member_rows = _rows(
        client.table("study_members")
        .select("user_id,joined_at,users(name)")
        .eq("study_id", str(study_id))
        .order("joined_at")
        .execute()
    )
    members = []
    for member in member_rows:
        user = member.get("users") or {}
        members.append({
            "user_id": member["user_id"],
            "name": user.get("name") or "알 수 없음",
            "joined_at": member["joined_at"],
        })
    return {"study": _study_response(client, study, user_id), "members": members}


def create_study(client, payload):
    data = payload.model_dump()
    owner_user_id = data.pop("user_id")
    study = _one(client.table("studies").insert({**data, "owner_user_id": str(owner_user_id)}).execute())
    if not study:
        raise HTTPException(500, {"code": "STUDY_CREATE_FAILED", "message": "스터디 생성에 실패했습니다."})
    try:
        client.table("study_members").insert({"study_id": study["study_id"], "user_id": str(owner_user_id)}).execute()
    except Exception:
        client.table("studies").delete().eq("study_id", study["study_id"]).execute()
        raise HTTPException(500, {"code": "STUDY_CREATE_FAILED", "message": "스터디 생성에 실패했습니다."})
    return {"study_id": study["study_id"], "title": study["title"], "status": study["status"], "member_count": 1}


def update_study(client, study_id, payload, user_id):
    existing = _one(client.table("studies").select("study_id,owner_user_id").eq("study_id", str(study_id)).limit(1).execute())
    if not existing:
        _not_found(study_id)
    _require_owner(existing, user_id)
    update_data = payload.model_dump(exclude={"user_id"})
    study = _one(client.table("studies").update(update_data).eq("study_id", str(study_id)).execute())
    return _study_response(client, study, user_id)


def delete_study(client, study_id, user_id) -> None:
    study = _one(client.table("studies").select("study_id,owner_user_id").eq("study_id", str(study_id)).limit(1).execute())
    if not study:
        _not_found(study_id)
    _require_owner(study, user_id)

    client.table("study_members").delete().eq("study_id", str(study_id)).execute()
    client.table("studies").delete().eq("study_id", str(study_id)).execute()


def join_study(client, study_id, user_id):
    study = _one(client.table("studies").select("*").eq("study_id", str(study_id)).limit(1).execute())
    if not study:
        _not_found(study_id)
    if study["status"] != "recruiting":
        raise HTTPException(409, {"code": "STUDY_CLOSED", "message": "모집이 종료된 스터디입니다."})
    if _is_joined(client, study_id, user_id):
        raise HTTPException(409, {"code": "ALREADY_JOINED", "message": "이미 참여 중인 스터디입니다."})
    if _member_count(client, study_id) >= study["capacity"]:
        raise HTTPException(409, {"code": "STUDY_FULL", "message": "스터디 정원이 가득 찼습니다.", "details": {"capacity": study["capacity"]}})
    try:
        client.table("study_members").insert({"study_id": str(study_id), "user_id": str(user_id)}).execute()
    except Exception as exc:
        # The database unique constraint is the final guard against concurrent duplicate joins.
        raise HTTPException(409, {"code": "ALREADY_JOINED", "message": "이미 참여 중인 스터디입니다."}) from exc
    return {"message": "스터디에 참여했습니다."}


def leave_study(client, study_id, user_id):
    study = _one(client.table("studies").select("owner_user_id").eq("study_id", str(study_id)).limit(1).execute())
    if not study:
        _not_found(study_id)
    if str(study["owner_user_id"]) == str(user_id):
        raise HTTPException(400, {"code": "OWNER_CANNOT_LEAVE", "message": "스터디장은 스터디를 탈퇴할 수 없습니다."})
    result = _rows(client.table("study_members").delete().eq("study_id", str(study_id)).eq("user_id", str(user_id)).execute())
    if not result:
        raise HTTPException(404, {"code": "STUDY_MEMBER_NOT_FOUND", "message": "참여 중인 스터디가 아닙니다."})
