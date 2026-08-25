"""Redis 연결을 만들고 FastAPI 종료 시 안전하게 정리합니다."""

import os

from redis import Redis
from redis.asyncio import Redis as AsyncRedis


_sync_redis: Redis | None = None
_async_redis: AsyncRedis | None = None


def _redis_url() -> str:
    """필수 Redis 접속 URL을 반환합니다."""
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL must be configured.")
    return redis_url


def get_sync_redis() -> Redis:
    """운영 로그 발행에 쓰는 동기 Redis 클라이언트를 반환합니다."""
    global _sync_redis
    if _sync_redis is None:
        _sync_redis = Redis.from_url(_redis_url(), decode_responses=True)
    return _sync_redis


def get_async_redis() -> AsyncRedis:
    """SSE Pub/Sub 구독에 쓰는 비동기 Redis 클라이언트를 반환합니다."""
    global _async_redis
    if _async_redis is None:
        _async_redis = AsyncRedis.from_url(_redis_url(), decode_responses=True)
    return _async_redis


async def close_redis_connections() -> None:
    """생성된 Redis 연결을 애플리케이션 종료 시 닫습니다."""
    global _sync_redis, _async_redis
    if _async_redis is not None:
        await _async_redis.aclose()
        _async_redis = None
    if _sync_redis is not None:
        _sync_redis.close()
        _sync_redis = None
