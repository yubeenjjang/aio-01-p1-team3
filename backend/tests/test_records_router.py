from datetime import date
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.core.supabase_config import get_supabase
from app.main import validation_error_handler
from app.routers.records_router import router
from app.services import record_service, upload_service


USER_ID = uuid4()
RECORD_ID = uuid4()


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.dependency_overrides[get_supabase] = lambda: object()
    return TestClient(app)


def payload():
    return {"user_id": str(USER_ID), "subject": "Python", "content": "FastAPI 학습", "study_minutes": 90, "studied_on": "2026-08-10", "proof_image_path": None}


def test_create_record(monkeypatch, client):
    monkeypatch.setattr(record_service, "create_record", lambda _client, _payload: {"record_id": str(RECORD_ID), **{key: value for key, value in payload().items() if key != "user_id"}})
    response = client.post("/records", json=payload())
    assert response.status_code == 201
    assert response.json()["record_id"] == str(RECORD_ID)


def test_list_records_forwards_filters(monkeypatch, client):
    captured = {}

    def list_records(_client, user_id, **filters):
        captured["user_id"] = user_id
        captured.update(filters)
        return {"items": [], "total": 0}

    monkeypatch.setattr(record_service, "list_records", list_records)
    response = client.get("/records", params={"user_id": str(USER_ID), "from": "2026-08-01", "to": "2026-08-10", "subject": "Python"})

    assert response.status_code == 200
    assert captured == {"user_id": USER_ID, "from_date": date(2026, 8, 1), "to_date": date(2026, 8, 10), "subject": "Python"}


def test_update_record_returns_updated_record(monkeypatch, client):
    updated = payload()
    updated["subject"] = "SQL"
    monkeypatch.setattr(record_service, "update_record", lambda _client, _record_id, _payload: {"record_id": str(RECORD_ID), **{key: value for key, value in updated.items() if key != "user_id"}})

    response = client.put(f"/records/{RECORD_ID}", json=updated)

    assert response.status_code == 200
    assert response.json()["subject"] == "SQL"


def test_delete_record_returns_no_content(monkeypatch, client):
    captured = {}

    def delete_record(_client, record_id, user_id):
        captured.update({"record_id": record_id, "user_id": user_id})

    monkeypatch.setattr(record_service, "delete_record", delete_record)
    response = client.delete(f"/records/{RECORD_ID}", params={"user_id": str(USER_ID)})

    assert response.status_code == 204
    assert captured == {"record_id": RECORD_ID, "user_id": USER_ID}


def test_record_stats_returns_subject_totals(monkeypatch, client):
    monkeypatch.setattr(record_service, "get_record_stats", lambda _client, _user_id, **_filters: {
        "total_minutes": 150,
        "by_subject": [{"subject": "Python", "minutes": 90}, {"subject": "SQL", "minutes": 60}],
    })

    response = client.get("/records/stats", params={"user_id": str(USER_ID)})

    assert response.status_code == 200
    assert response.json()["total_minutes"] == 150


def test_proof_image_rejects_invalid_file_type():
    with pytest.raises(HTTPException) as error:
        upload_service.upload_proof_image(object(), USER_ID, "proof.gif", "image/gif", b"image")

    assert error.value.status_code == 400
    assert error.value.detail["code"] == "INVALID_FILE_TYPE"


def test_proof_image_rejects_file_larger_than_five_mb():
    # 큰 파일 내용은 parametrized 값이 아니라 테스트 실행 시 만들어 pytest 테스트명이 커지지 않게 합니다.
    too_large_image = b"x" * (upload_service.MAX_FILE_SIZE + 1)

    with pytest.raises(HTTPException) as error:
        upload_service.upload_proof_image(object(), USER_ID, "proof.png", "image/png", too_large_image)

    assert error.value.status_code == 400
    assert error.value.detail["code"] == "FILE_TOO_LARGE"


def test_proof_image_path_is_converted_to_signed_url():
    captured = {}

    class Bucket:
        def create_signed_url(self, path, expires_in):
            captured["path"] = path
            captured["expires_in"] = expires_in
            return {"signedURL": "https://example.com/proof.png?token=test"}

    class Storage:
        def from_(self, bucket_name):
            captured["bucket_name"] = bucket_name
            return Bucket()

    class Client:
        storage = Storage()

    image_url = record_service._create_proof_image_url(
        Client(),
        "records/user-id/proof.png",
    )

    assert image_url == "https://example.com/proof.png?token=test"
    assert captured == {
        "bucket_name": "proof-images",
        "path": "records/user-id/proof.png",
        "expires_in": 3600,
    }


def test_record_not_found(monkeypatch, client):
    def get_record(_client, _record_id, _user_id):
        raise HTTPException(404, {"code": "RECORD_NOT_FOUND", "message": "학습 기록을 찾을 수 없습니다."})

    monkeypatch.setattr(record_service, "get_record", get_record)
    response = client.get(f"/records/{RECORD_ID}", params={"user_id": str(USER_ID)})
    assert response.status_code == 404


def test_record_rejects_invalid_minutes(client):
    invalid = payload()
    invalid["study_minutes"] = 0
    response = client.post("/records", json=invalid)
    assert response.status_code == 400
