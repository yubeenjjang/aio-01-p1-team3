from types import SimpleNamespace
from uuid import uuid4

from app.services import study_service


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name

    def select(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def ilike(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def execute(self):
        self.client.executed_tables.append(self.table_name)
        return SimpleNamespace(data=self.client.rows[self.table_name])


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.executed_tables = []

    def table(self, table_name):
        return FakeQuery(self, table_name)


def test_list_studies_loads_related_data_in_bulk():
    user_id = uuid4()
    other_user_id = uuid4()
    owner_id = uuid4()
    first_study_id = uuid4()
    second_study_id = uuid4()
    common = {
        "owner_user_id": str(owner_id),
        "category": "백엔드",
        "goal": "API 완성",
        "schedule": "월·수 19:00",
        "capacity": 5,
        "status": "recruiting",
    }
    client = FakeClient(
        {
            "studies": [
                {**common, "study_id": str(first_study_id), "title": "FastAPI"},
                {**common, "study_id": str(second_study_id), "title": "Supabase"},
            ],
            "study_members": [
                {"study_id": str(first_study_id), "user_id": str(user_id)},
                {"study_id": str(first_study_id), "user_id": str(other_user_id)},
                {"study_id": str(second_study_id), "user_id": str(other_user_id)},
            ],
            "users": [{"user_id": str(owner_id), "name": "스터디장"}],
        }
    )

    result = study_service.list_studies(client, user_id)

    assert client.executed_tables == ["studies", "study_members", "users"]
    assert result["total"] == 2
    assert result["items"][0]["owner_name"] == "스터디장"
    assert result["items"][0]["member_count"] == 2
    assert result["items"][0]["is_joined"] is True
    assert result["items"][1]["member_count"] == 1
    assert result["items"][1]["is_joined"] is False
