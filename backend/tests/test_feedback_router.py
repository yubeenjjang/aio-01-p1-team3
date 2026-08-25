"""분석 평가 라우터의 핵심 계약 테스트입니다."""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.supabase_config import get_supabase
from app import main as main_module
from app.routers.feedback_router import router
from app.services import admin_service, feedback_service


USER_ID = uuid4()
FEEDBACK_ID = uuid4()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(app)


def _feedback() -> dict:
    now = datetime(2026, 8, 10, tzinfo=timezone.utc).isoformat()
    return {"feedback_id": str(FEEDBACK_ID), "period_start": "2026-08-01", "period_end": "2026-08-10", "rating": 5,
            "comment": "도움이 되었습니다.", "created_at": now, "updated_at": now}


def test_save_feedback_returns_created_status(monkeypatch, client: TestClient) -> None:
    monkeypatch.setattr(feedback_service, "save_feedback", lambda _client, _payload: (_feedback(), True))
    response = client.post("/analyses/feedback", json={"user_id": str(USER_ID), "period_start": "2026-08-01", "period_end": "2026-08-10", "rating": 5})
    assert response.status_code == 201
    assert response.json()["rating"] == 5


def test_save_feedback_rejects_invalid_rating(client: TestClient) -> None:
    response = client.post("/analyses/feedback", json={"user_id": str(USER_ID), "period_start": "2026-08-01", "period_end": "2026-08-10", "rating": 6})
    assert response.status_code == 422


def test_admin_feedback_requires_admin(monkeypatch, client: TestClient) -> None:
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: False)
    response = client.get("/admin/analysis-feedback", params={"user_id": str(USER_ID)})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ADMIN_REQUIRED"


def test_admin_feedback_writes_documented_log_action(monkeypatch, client: TestClient) -> None:
    logged = []
    monkeypatch.setattr(admin_service, "is_admin", lambda _client, _user_id: True)
    monkeypatch.setattr(feedback_service, "list_admin_feedback", lambda _client, **_filters: {"items": [], "total": 0, "average_rating": None, "rating_distribution": {str(value): 0 for value in range(1, 6)}})
    monkeypatch.setattr("app.routers.feedback_router.write_operation_log", lambda _client, **kwargs: logged.append(kwargs))
    response = client.get("/admin/analysis-feedback", params={"user_id": str(USER_ID)})
    assert response.status_code == 200
    assert logged[0]["action"] == "admin.analysis_feedback.list"
    assert logged[0]["status"] == "success"
    assert logged[0]["publish_event"] is False


def test_get_feedback_rejects_reversed_period(client: TestClient) -> None:
    response = client.get("/analyses/feedback", params={"user_id": str(USER_ID), "period_start": "2026-08-10", "period_end": "2026-08-01"})
    assert response.status_code == 400


def test_get_feedback_treats_none_supabase_response_as_not_found() -> None:
    class Query:
        def select(self, *_args):
            return self

        def eq(self, *_args):
            return self

        def maybe_single(self):
            return self

        def execute(self):
            return None

    class FakeClient:
        def table(self, _name):
            return Query()

    with pytest.raises(Exception) as error:
        feedback_service.get_feedback(FakeClient(), USER_ID, date(2026, 8, 1), date(2026, 8, 10))

    assert getattr(error.value, "status_code", None) == 404


def test_feedback_validation_failure_writes_operation_log(monkeypatch) -> None:
    logged = []
    monkeypatch.setattr(main_module, "get_supabase", lambda: object())
    monkeypatch.setattr(main_module, "write_operation_log", lambda _client, **kwargs: logged.append(kwargs))
    with TestClient(main_module.app) as app_client:
        response = app_client.post("/analyses/feedback", json={"user_id": str(USER_ID), "period_start": "2026-08-01", "period_end": "2026-08-10", "rating": 6})
    assert response.status_code == 400
    assert logged[0]["action"] == "analysis.feedback.submit"
    assert logged[0]["status"] == "failure"
