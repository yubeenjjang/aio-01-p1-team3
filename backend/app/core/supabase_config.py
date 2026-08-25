"""환경변수로 Supabase 클라이언트를 만들고 API에서 주입할 수 있게 합니다."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


@lru_cache(maxsize=1)
def get_supabase():
    """애플리케이션에서 공유하는 Supabase 클라이언트를 반환합니다."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured.")
    return create_client(url, key)
