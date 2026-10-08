from collections.abc import AsyncIterator

import redis.asyncio as redis

from app.core.config import settings
from app.realtime.events import RealtimeEvent

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def publish_event(channel: str, event: RealtimeEvent) -> None:
    await get_redis().publish(channel, event.model_dump_json())


async def subscribe(channel: str) -> AsyncIterator[str]:
    pubsub = get_redis().pubsub()
    await pubsub.subscribe(channel)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
