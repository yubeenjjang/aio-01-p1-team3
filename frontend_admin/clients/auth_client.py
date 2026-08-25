"""관리자 로그인·로그아웃 API 호출 함수입니다."""

from core.api_client import request


def login_admin(email: str, password: str):
    """이메일과 비밀번호로 로그인합니다."""

    return request(
        "POST",
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def logout_admin(user_id: str):
    """현재 관리자 사용자의 로그아웃을 요청합니다."""

    return request(
        "POST",
        "/auth/logout",
        params={"user_id": user_id},
    )
