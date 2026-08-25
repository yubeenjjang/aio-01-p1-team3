"""인증 사진의 형식·크기를 검사하고 Supabase Storage에 저장합니다."""

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException


ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE = 5 * 1024 * 1024
BUCKET_NAME = "proof-images"


def upload_proof_image(client, user_id, filename: str | None, content_type: str | None, content: bytes) -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, {"code": "INVALID_FILE_TYPE", "message": "JPG, JPEG, PNG 파일만 업로드할 수 있습니다."})
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, {"code": "FILE_TOO_LARGE", "message": "파일 크기는 5MB 이하여야 합니다."})

    extension = Path(filename or "upload").suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png"}:
        raise HTTPException(400, {"code": "INVALID_FILE_TYPE", "message": "JPG, JPEG, PNG 파일만 업로드할 수 있습니다."})
    path = f"records/{user_id}/{uuid4()}{extension}"
    try:
        client.storage.from_(BUCKET_NAME).upload(path, content, {"content-type": content_type, "upsert": "false"})
    except Exception as exc:
        raise HTTPException(500, {"code": "IMAGE_UPLOAD_FAILED", "message": "인증 사진 업로드에 실패했습니다."}) from exc
    return path
