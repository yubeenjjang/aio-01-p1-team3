from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.core.supabase_config import get_supabase
from app.main import validation_error_handler
from app.routers.admin_router import router
from app.services import admin_service


USER_ID = uuid4()


@pytest.fixture
def client():
    app = FastAPI()
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.include_router(router)
    app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(app)


def test_admin_dashboard_returns_kpis(monkeypatch, client):
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: True)
    monkeypatch.setattr(admin_service, "get_dashboard", lambda _client: {
        "user_count": 20,
        "study_count": 5,
        "record_count": 100,
        "subject_minutes": [{"subject": "Python", "minutes": 1800}],
        "study_status_counts": {"recruiting": 3, "closed": 2},
        "action_counts": {"analysis.request": 8},
        "ai_metrics": {"request_count": 8, "success_count": 6, "failure_count": 2, "success_rate": 75.0, "failure_rate": 25.0, "average_latency_ms": 1250.0},
        "failure_count": 2,
    })

    response = client.get("/admin/dashboard", params={"user_id": str(USER_ID)})

    assert response.status_code == 200
    assert response.json()["ai_metrics"]["success_rate"] == 75.0


def test_admin_logs_forwards_filters(monkeypatch, client):
    captured = {}
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: True)

    def list_logs(_client, **kwargs):
        captured.update(kwargs)
        return {"items": [], "total": 0}

    monkeypatch.setattr(admin_service, "list_operation_logs", list_logs)
    response = client.get("/admin/logs", params={"user_id": str(USER_ID), "status": "failure", "action": "analysis.request", "limit": 20})

    assert response.status_code == 200
    assert captured == {"status": "failure", "action": "analysis.request", "limit": 20}


def test_admin_logs_rejects_invalid_status(client):
    response = client.get("/admin/logs", params={"user_id": str(USER_ID), "status": "invalid"})

    assert response.status_code == 400


def test_admin_logs_returns_trace_id(monkeypatch, client):
    trace_id = uuid4()
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: True)
    monkeypatch.setattr(admin_service, "list_operation_logs", lambda _client, **_filters: {
        "items": [{
            "log_id": 1,
            "created_at": datetime(2026, 8, 10, tzinfo=timezone.utc).isoformat(),
            "user_id": str(USER_ID),
            "user_name": "테스트 사용자",
            "action": "study.search",
            "status": "success",
            "message": None,
            "latency_ms": 10,
            "trace_id": str(trace_id),
        }],
        "total": 1,
    })

    response = client.get("/admin/logs", params={"user_id": str(USER_ID)})

    assert response.status_code == 200
    assert response.json()["items"][0]["trace_id"] == str(trace_id)


def test_admin_logs_rejects_non_admin(monkeypatch, client):
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: False)
    response = client.get("/admin/logs", params={"user_id": str(USER_ID)})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ADMIN_REQUIRED"
