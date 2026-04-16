"""Redis pub/sub bridge for pushing events from Celery workers to WebSocket clients.

Celery tasks run in separate processes and cannot call WebSocket broadcast directly.
They publish JSON messages to a per-campaign Redis channel; the FastAPI process
subscribes on startup and forwards messages to connected WebSocket clients.
"""
import asyncio
import json
import logging

from redis import Redis as SyncRedis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import settings

logger = logging.getLogger(__name__)

CAMPAIGN_CHANNEL_PREFIX = "campaign:"

_sync_redis: SyncRedis | None = None


def _get_sync_redis() -> SyncRedis:
    global _sync_redis
    if _sync_redis is None:
        _sync_redis = SyncRedis.from_url(settings.REDIS_URL, decode_responses=True)
    return _sync_redis


def publish_campaign_event(campaign_id: int, message: dict) -> None:
    """Sync publish — safe to call from Celery tasks."""
    try:
        _get_sync_redis().publish(
            f"{CAMPAIGN_CHANNEL_PREFIX}{campaign_id}",
            json.dumps(message, default=str),
        )
    except Exception:
        logger.exception("Failed to publish campaign event")


async def campaign_event_listener(ws_manager) -> None:
    """Long-running coroutine: subscribes to campaign:* and forwards to WS clients."""
    async_redis = AsyncRedis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = async_redis.pubsub()
    await pubsub.psubscribe(f"{CAMPAIGN_CHANNEL_PREFIX}*")

    try:
        async for raw in pubsub.listen():
            if raw.get("type") != "pmessage":
                continue
            channel = raw.get("channel", "")
            try:
                campaign_id = int(channel.split(":", 1)[1])
            except (ValueError, IndexError):
                continue
            try:
                data = json.loads(raw.get("data", "{}"))
            except json.JSONDecodeError:
                continue
            await ws_manager.broadcast(campaign_id, data)
    except asyncio.CancelledError:
        raise
    finally:
        try:
            await pubsub.aclose()
        except Exception:
            pass
        try:
            await async_redis.aclose()
        except Exception:
            pass
