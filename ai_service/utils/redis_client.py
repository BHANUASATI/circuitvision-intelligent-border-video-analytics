"""
Redis client — async, used for alert publishing and stream state.
"""
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from ai_service.configs.settings import settings
from ai_service.utils.logger import logger

_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def publish_alert(channel: str, payload: dict) -> None:
    """Publish a JSON alert to a Redis pub/sub channel."""
    r = await get_redis()
    try:
        await r.publish(channel, json.dumps(payload))
    except Exception as exc:
        logger.error(f"Redis publish failed: {exc}")


async def set_stream_state(camera_id: str, state: dict, ttl: int = 300) -> None:
    r = await get_redis()
    await r.setex(f"stream:state:{camera_id}", ttl, json.dumps(state))


async def get_stream_state(camera_id: str) -> Optional[dict]:
    r = await get_redis()
    raw = await r.get(f"stream:state:{camera_id}")
    return json.loads(raw) if raw else None


async def close_redis() -> None:
    global _pool
    if _pool:
        await _pool.aclose()
        _pool = None
