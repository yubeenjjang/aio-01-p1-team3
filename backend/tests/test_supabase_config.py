from app.core import supabase_config


def test_get_supabase_reuses_client(monkeypatch):
    created_clients = []
    expected_client = object()

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setattr(
        supabase_config,
        "create_client",
        lambda _url, _key: created_clients.append(expected_client) or expected_client,
    )
    supabase_config.get_supabase.cache_clear()

    try:
        first = supabase_config.get_supabase()
        second = supabase_config.get_supabase()
    finally:
        supabase_config.get_supabase.cache_clear()

    assert first is expected_client
    assert second is expected_client
    assert created_clients == [expected_client]
