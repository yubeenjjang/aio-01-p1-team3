"""학습 인증 사진 파일을 Supabase Storage에 업로드하는 API를 정의합니다."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.core.log_utils import write_operation_log
from app.core.supabase_config import get_supabase
from app.schemas.record_schema import ProofImageUploadResponse
from app.services import upload_service

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Form은 일반 입력칸, File은 사용자가 선택한 파일을 받습니다.

@router.post("/proof-image", response_model=ProofImageUploadResponse)
async def upload_proof_image(
    request: Request,
    user_id: UUID = Form(..., description="인증 사진을 업로드할 사용자의 UUID"),
    file: UploadFile = File(..., description="JPG, JPEG, PNG 형식의 5MB 이하 인증 사진"),
    client=Depends(get_supabase),
):
    # 파일 형식과 5MB 제한 검증은 upload_service에서 수행합니다.
    try:
        path = upload_service.upload_proof_image(client, user_id, file.filename, file.content_type, await file.read())
        write_operation_log(client, user_id=user_id, action="record.image_upload", status="success", message="인증 사진 업로드 완료",
                            trace_id=getattr(request.state, "trace_id", ""))
        return {"proof_image_path": path}
    except Exception as exc:
        write_operation_log(client, user_id=user_id, action="record.image_upload", status="failure", message="인증 사진 업로드 실패",
                            trace_id=getattr(request.state, "trace_id", ""))
        raise exc
