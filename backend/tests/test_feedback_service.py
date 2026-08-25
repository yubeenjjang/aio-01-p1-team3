from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import feedback_service


class FeedbackQuery:
    def __init__(self, client):
        self.client = client
        self.mode = "select"

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def maybe_single(self):
        return self

    def upsert(self, values, *, on_conflict):
        self.mode = "upsert"
        self.client.upsert_values = values
        self.client.on_conflict = on_conflict
        return self

    def execute(self):
        if self.mode == "upsert":
            row = {
                "feedback_id": str(self.client.feedback_id),
                "created_at": "2026-08-11T00:00:00+00:00",
                **self.client.upsert_values,
            }
            return SimpleNamespace(data=[row])
        data = (
            {"feedback_id": str(self.client.feedback_id)}
            if self.client.has_existing
            else None
        )
        return SimpleNamespace(data=data)


class FeedbackClient:
    def __init__(self, has_existing):
        self.has_existing = has_existing
        self.feedback_id = uuid4()
        self.upsert_values = None
        self.on_conflict = None

    def table(self, table_name):
        assert table_name == "analysis_feedback"
        return FeedbackQuery(self)


@pytest.mark.parametrize(
    ("has_existing", "expected_created"),
    [(False, True), (True, False)],
)
def test_save_feedback_upserts_one_row_per_user_and_period(
    monkeypatch, has_existing, expected_created
):
    client = FeedbackClient(has_existing)
    payload = SimpleNamespace(
        user_id=uuid4(),
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 11),
        rating=5,
        comment="도움이 되었습니다.",
    )
    monkeypatch.setattr(feedback_service, "_require_study_records", lambda *_args: None)

    result, created = feedback_service.save_feedback(client, payload)

    assert created is expected_created
    assert client.on_conflict == "user_id,period_start,period_end"
    assert client.upsert_values["user_id"] == str(payload.user_id)
    assert result["feedback_id"] == str(client.feedback_id)
    assert result["rating"] == 5
