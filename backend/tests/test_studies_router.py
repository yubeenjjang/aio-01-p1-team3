from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.supabase_config import get_supabase
from app.routers import studies_router
from app.routers.studies_router import router
from app.services import study_service


USER_ID = uuid4()
STUDY_ID = uuid4()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(app)


def test_create_study_returns_created_response_and_uses_request_user(monkeypatch, client):
    captured = {}

    def create(_client, payload):
        captured["user_id"] = payload.user_id
        return {"study_id": str(STUDY_ID), "title": "FastAPI 스터디", "status": "recruiting", "member_count": 1}

    monkeypatch.setattr(study_service, "create_study", create)
    response = client.post("/studies", json={
        "user_id": str(USER_ID), "title": "FastAPI 스터디", "category": "백엔드",
        "goal": "CRUD 완성", "schedule": "월·수 19:00", "capacity": 5,
    })

    assert response.status_code == 201
    assert response.json()["member_count"] == 1
    assert captured["user_id"] == USER_ID


def test_list_studies_forwards_search_conditions_and_uses_search_action(monkeypatch, client):
    captured = {}
    logged_actions = []

    def list_studies(_client, user_id, **filters):
        captured["user_id"] = user_id
        captured.update(filters)
        return {"items": [], "total": 0}

    def write_log(_client, **kwargs):
        logged_actions.append(kwargs["action"])

    monkeypatch.setattr(study_service, "list_studies", list_studies)
    monkeypatch.setattr(studies_router, "write_operation_log", write_log)
    response = client.get("/studies", params={
        "user_id": str(USER_ID), "keyword": "FastAPI", "category": "백엔드", "status": "recruiting", "source": "search",
    })

    assert response.status_code == 200
    assert captured == {"user_id": USER_ID, "keyword": "FastAPI", "category": "백엔드", "status": "recruiting"}
    assert logged_actions == ["study.search"]


@pytest.mark.parametrize("code", ["ALREADY_JOINED", "STUDY_FULL", "STUDY_CLOSED"])
def test_join_returns_conflict_for_join_rules(monkeypatch, client, code):
    def join(_client, _study_id, _user_id):
        raise HTTPException(status_code=409, detail={"code": code, "message": "참여할 수 없습니다."})

    monkeypatch.setattr(study_service, "join_study", join)
    response = client.post(f"/studies/{STUDY_ID}/join", json={"user_id": str(USER_ID)})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == code


def test_leave_rejects_owner(monkeypatch, client):
    def leave(_client, _study_id, _user_id):
        raise HTTPException(status_code=400, detail={"code": "OWNER_CANNOT_LEAVE", "message": "생성자는 탈퇴할 수 없습니다."})

    monkeypatch.setattr(study_service, "leave_study", leave)
    response = client.delete(f"/studies/{STUDY_ID}/join", params={"user_id": str(USER_ID)})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "OWNER_CANNOT_LEAVE"
