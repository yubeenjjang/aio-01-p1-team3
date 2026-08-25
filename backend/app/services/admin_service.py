"""서비스 전체 통계와 operation_logs 조회 결과를 만드는 기능입니다."""

from uuid import UUID


def _rows(result):
    return result.data or []


def is_admin(client, user_id: UUID) -> bool:
    """사용자 UUID가 관리자 역할인지 확인합니다."""
    result = client.table("users").select("role").eq("user_id", str(user_id)).maybe_single().execute()
    return bool((result.data or {}).get("role") == "admin")


def _count(client, table_name: str) -> int:
    result = client.table(table_name).select("*", count="exact").execute()
    if getattr(result, "count", None) is not None:
        return result.count
    return len(_rows(result))


def _group_counts(rows, key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        if value is not None:
            counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def get_dashboard(client):
    record_rows = _rows(client.table("study_records").select("subject,study_minutes").execute())
    subject_minutes: dict[str, int] = {}
    for row in record_rows:
        subject = row["subject"]
        subject_minutes[subject] = subject_minutes.get(subject, 0) + int(row["study_minutes"])

    study_rows = _rows(client.table("studies").select("status").execute())
    log_rows = _rows(client.table("operation_logs").select("action,status,latency_ms").execute())
    ai_logs = [row for row in log_rows if row.get("action") == "analysis.request"]
    success_count = sum(1 for row in ai_logs if row.get("status") == "success")
    failure_count = sum(1 for row in ai_logs if row.get("status") == "failure")
    latency_values = [int(row["latency_ms"]) for row in ai_logs if row.get("latency_ms") is not None]
    request_count = len(ai_logs)

    return {
        "user_count": _count(client, "users"),
        "study_count": _count(client, "studies"),
        "record_count": _count(client, "study_records"),
        "subject_minutes": [{"subject": subject, "minutes": minutes} for subject, minutes in sorted(subject_minutes.items())],
        "study_status_counts": _group_counts(study_rows, "status"),
        "action_counts": _group_counts(log_rows, "action"),
        "ai_metrics": {
            "request_count": request_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round(success_count / request_count * 100, 1) if request_count else 0.0,
            "failure_rate": round(failure_count / request_count * 100, 1) if request_count else 0.0,
            "average_latency_ms": round(sum(latency_values) / len(latency_values), 1) if latency_values else None,
        },
        "failure_count": sum(1 for row in log_rows if row.get("status") == "failure"),
    }


def list_operation_logs(client, *, status: str | None = None, action: str | None = None, limit: int = 50):
    query = client.table("operation_logs").select("log_id,created_at,user_id,action,status,message,latency_ms,trace_id,users(name)").order("created_at", desc=True).limit(limit)
    if status:
        query = query.eq("status", status)
    if action:
        query = query.eq("action", action)
    rows = _rows(query.execute())
    items = []
    for row in rows:
        user = row.get("users") or {}
        items.append({
            "log_id": row["log_id"],
            "created_at": row["created_at"],
            "user_id": row.get("user_id"),
            "user_name": user.get("name"),
            "action": row["action"],
            "status": row["status"],
            "message": row.get("message"),
            "latency_ms": row.get("latency_ms"),
            "trace_id": row["trace_id"],
        })
    return {"items": items, "total": len(items)}


