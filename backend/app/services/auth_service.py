"""회원 정보를 Supabase에 저장하고 로그인 비밀번호를 검증합니다."""

from fastapi import HTTPException

from app.core.password import hash_password, verify_password


def _one(response):
    rows = response.data or []
    return rows[0] if rows else None


def _user_view(row):
    return {"user_id": row["user_id"], "email": row["email"], "name": row["name"], "role": row["role"]}


def signup(client, payload):
    existing = _one(client.table("users").select("user_id").eq("email", payload.email.lower()).limit(1).execute())
    if existing:
        raise HTTPException(409, {"code": "EMAIL_DUPLICATED", "message": "이미 사용 중인 이메일입니다."})
    row = _one(client.table("users").insert({
        "email": payload.email.lower(), "password_hash": hash_password(payload.password),
        "name": payload.name, "role": "user",
    }).execute())
    return _user_view(row)


def login(client, payload):
    row = _one(client.table("users").select("*").eq("email", payload.email.lower()).limit(1).execute())
    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(401, {"code": "LOGIN_FAILED", "message": "이메일 또는 비밀번호가 올바르지 않습니다."})
    return _user_view(row)
