"""회원가입·로그인 API에서 주고받는 데이터 형식을 정의합니다."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# BaseModel은 API가 받을 JSON 데이터의 모양과 검증 규칙을 정의합니다.

class SignupRequest(BaseModel):
    # Field 설명과 examples는 Swagger의 요청 예시 및 도움말에 표시됩니다.
    # `...`는 이 값이 반드시 필요하다는 뜻입니다.
    email: str = Field(..., min_length=3, max_length=255, description="회원가입에 사용할 이메일", examples=["user@example.com"])
    password: str = Field(..., min_length=8, max_length=100, description="8자 이상 100자 이하의 비밀번호", examples=["password123"])
    name: str = Field(..., min_length=1, max_length=50, description="화면에 표시할 사용자 이름", examples=["홍길동"])


class LoginRequest(BaseModel):
    # 로그인에서는 비밀번호 길이를 제한하지 않고 인증 실패를 401로 반환합니다.
    email: str = Field(..., min_length=3, max_length=255, description="가입한 이메일", examples=["user@example.com"])
    password: str = Field(..., min_length=1, max_length=100, description="가입 시 설정한 비밀번호", examples=["password123"])


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    name: str
    role: Literal["user", "admin"]
