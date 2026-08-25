from types import SimpleNamespace

from app.core import log_utils
from app.services import event_service


class LogQuery:
    def __init__(self, client):
        self.client = client

    def insert(self, values):
        self.client.inserted = values
        return self

    def execute(self):
        return SimpleNamespace(data=[self.client.inserted])


class LogClient:
    def __init__(self):
        self.inserted = None

    def table(self, table_name):
        assert table_name == "operation_logs"
        return LogQuery(self)


def test_write_operation_log_publishes_sse_after_insert(monkeypatch):
    client = LogClient()
    published = []
    monkeypatch.setattr(
        event_service,
        "publish_admin_log_updated",
        lambda **values: published.append(values),
    )

    log_utils.write_operation_log(
        client,
        action="analysis.feedback.submit",
        status="success",
        trace_id="trace-id",
    )

    assert client.inserted["action"] == "analysis.feedback.submit"
    assert published == [
        {"action": "analysis.feedback.submit", "status": "success"}
    ]


def test_write_operation_log_ignores_redis_failure(monkeypatch):
    client = LogClient()

    def fail_publish(**_values):
        raise RuntimeError("Redis unavailable")

    monkeypatch.setattr(event_service, "publish_admin_log_updated", fail_publish)

    log_utils.write_operation_log(
        client,
        action="record.create",
        status="success",
        trace_id="trace-id",
    )

    assert client.inserted["action"] == "record.create"
    assert client.inserted["status"] == "success"
