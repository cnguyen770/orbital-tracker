
import json
import logging
from typing import Optional
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await _redis_client.ping()
            logger.info("Redis connected at %s", settings.REDIS_URL)
        except Exception as e:
            logger.warning("Redis unavailable (%s) — caching disabled", e)
            _redis_client = None
    return _redis_client


async def cache_get(key: str) -> Optional[dict]:
    client = await get_redis()
    if client is None:
        return None
    try:
        value = await client.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.warning("Cache get failed for %s: %s", key, e)
        return None


async def cache_set(key: str, value: dict, ttl_seconds: int = 10) -> None:
    client = await get_redis()
    if client is None:
        return
    try:
        await client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as e:
        logger.warning("Cache set failed for %s: %s", key, e)