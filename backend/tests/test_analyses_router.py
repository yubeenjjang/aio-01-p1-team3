from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.core.supabase_config import get_supabase
from app.main import validation_error_handler
from app.routers import analyses_router
from app.routers.analyses_router import router
from app.services import analysis_service


USER_ID = uuid4()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(app)


def valid_payload():
    return {"user_id": str(USER_ID), "period_start": "2026-08-01", "period_end": "2026-08-31"}


def test_analysis_returns_gemini_result(monkeypatch, client):
    monkeypatch.setattr(analysis_service, "analyze_records", lambda _client, _payload: {
        "summary": "총 300분 학습했습니다.",
        "strengths": ["Python 학습이 꾸준합니다."],
        "improvements": ["SQL 학습 시간을 늘려보세요."],
        "next_goal": "다음 주 SQL 학습 120분",
    })

    response = client.post("/analyses", json=valid_payload())

    assert response.status_code == 200
    assert response.json()["summary"] == "총 300분 학습했습니다."


def test_analysis_returns_not_found_when_records_do_not_exist(monkeypatch, client):
    def analyze(_client, _payload):
        raise HTTPException(404, {"code": "NO_STUDY_RECORDS", "message": "분석할 학습 기록이 없습니다."})

    monkeypatch.setattr(analysis_service, "analyze_records", analyze)
    response = client.post("/analyses", json=valid_payload())

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NO_STUDY_RECORDS"


@pytest.mark.parametrize("status_code, code", [(429, "RATE_LIMITED"), (500, "GEMINI_REQUEST_FAILED"), (503, "GEMINI_UNAVAILABLE")])
def test_analysis_returns_gemini_error(monkeypatch, client, status_code, code):
    def analyze(_client, _payload):
        raise HTTPException(status_code, {"code": code, "message": "Gemini 요청 실패"})

    monkeypatch.setattr(analysis_service, "analyze_records", analyze)
    response = client.post("/analyses", json=valid_payload())

    assert response.status_code == status_code
    assert response.json()["detail"]["code"] == code


def test_analysis_rejects_reversed_period(client):
    payload = valid_payload()
    payload["period_start"] = "2026-08-31"
    payload["period_end"] = "2026-08-01"

    response = client.post("/analyses", json=payload)

    assert response.status_code == 400


def test_gemini_resource_exhausted_is_rate_limited():
    error = analysis_service._gemini_error(Exception("429 RESOURCE_EXHAUSTED: quota exceeded"))

    assert error.status_code == 429
    assert error.detail["code"] == "RATE_LIMITED"


def test_analysis_writes_success_operation_log(monkeypatch, client):
    logged = []
    monkeypatch.setattr(analysis_service, "analyze_records", lambda _client, _payload: {
        "summary": "학습 분석 결과", "strengths": [], "improvements": [], "next_goal": "다음 목표",
    })
    monkeypatch.setattr(analyses_router, "write_operation_log", lambda _client, **kwargs: logged.append(kwargs))

    response = client.post("/analyses", json=valid_payload())

    assert response.status_code == 200
    assert logged[0]["action"] == "analysis.request"
    assert logged[0]["status"] == "success"


def test_analysis_writes_failure_operation_log(monkeypatch, client):
    logged = []

    def analyze(_client, _payload):
        raise HTTPException(503, {"code": "GEMINI_UNAVAILABLE", "message": "Gemini 서비스 오류"})

    monkeypatch.setattr(analysis_service, "analyze_records", analyze)
    monkeypatch.setattr(analyses_router, "write_operation_log", lambda _client, **kwargs: logged.append(kwargs))

    response = client.post("/analyses", json=valid_payload())

    assert response.status_code == 503
    assert logged[0]["action"] == "analysis.request"
    assert logged[0]["status"] == "failure"
