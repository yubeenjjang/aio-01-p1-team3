"""로그인, 회원가입, 로그아웃 API 호출 함수입니다."""

from core.api_client import request


def login_user(email: str, password: str):
    """이메일과 비밀번호로 로그인합니다."""

    return request(
        "POST",
        "/auth/login",
        json={"email": email, "password": password},
    )


def signup_user(name: str, email: str, password: str):
    """일반 사용자 계정을 생성합니다."""

    return request(
        "POST",
        "/auth/signup",
        json={"name": name, "email": email, "password": password},
    )


def logout_user(user_id: str):
    """현재 사용자의 로그아웃을 백엔드에 요청합니다."""

    return request(
        "POST",
        "/auth/logout",
        params={"user_id": user_id},
    )
