from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.password import hash_password, verify_password
from app.core.supabase_config import get_supabase
from app.main import app
from app.routers.auth_router import router
from app.services import auth_service


USER_ID = uuid4()


@pytest.fixture
def client():
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(test_app)


def user_response():
    return {"user_id": str(USER_ID), "email": "user@example.com", "name": "테스트 사용자", "role": "user"}


def test_password_hash_is_verifiable_and_not_plaintext():
    password_hash = hash_password("password123")
    assert password_hash != "password123"
    assert verify_password("password123", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_signup_returns_created_user(monkeypatch, client):
    monkeypatch.setattr(auth_service, "signup", lambda _client, _payload: user_response())

    response = client.post("/auth/signup", json={"email": "user@example.com", "password": "password123", "name": "테스트 사용자"})

    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_signup_returns_conflict_for_duplicate_email(monkeypatch, client):
    def signup(_client, _payload):
        raise HTTPException(409, {"code": "EMAIL_DUPLICATED", "message": "이미 가입된 이메일입니다."})

    monkeypatch.setattr(auth_service, "signup", signup)
    response = client.post("/auth/signup", json={"email": "user@example.com", "password": "password123", "name": "테스트 사용자"})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "EMAIL_DUPLICATED"


def test_login_returns_user_when_credentials_are_valid(monkeypatch, client):
    monkeypatch.setattr(auth_service, "login", lambda _client, _payload: user_response())

    response = client.post("/auth/login", json={"email": "user@example.com", "password": "password123"})

    assert response.status_code == 200
    assert response.json()["user_id"] == str(USER_ID)


def test_login_returns_unauthorized_for_invalid_credentials(monkeypatch, client):
    def login(_client, _payload):
        raise HTTPException(401, {"code": "LOGIN_FAILED", "message": "이메일 또는 비밀번호를 확인하세요."})

    monkeypatch.setattr(auth_service, "login", login)
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "LOGIN_FAILED"


def test_logout_returns_no_content(client):
    response = client.post("/auth/logout", params={"user_id": str(USER_ID)})

    assert response.status_code == 204


def test_auth_routes_are_registered():
    # FastAPI는 실제 엔드포인트 외에 include한 router 객체도 함께 보관할 수 있습니다.
    # 포함 router는 `original_router.routes`에서 실제 경로를 읽습니다.
    paths = set()
    for route in app.routes:
        if hasattr(route, "path"):
            paths.add(route.path)
        elif hasattr(route, "original_router"):
            paths.update(child.path for child in route.original_router.routes if hasattr(child, "path"))
    assert {"/auth/signup", "/auth/login", "/auth/logout"} <= paths
