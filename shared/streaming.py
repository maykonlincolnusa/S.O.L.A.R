from __future__ import annotations

import json
import os
from typing import Any

try:
    import redis
except Exception:  # pragma: no cover - optional dependency at runtime
    redis = None

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
STREAM_NAME = os.getenv("STREAM_NAME", "solar:events")


def get_redis_client():
    if redis is None:
        return None
    try:
        return redis.Redis.from_url(REDIS_URL, decode_responses=True)
    except Exception:
        return None


def publish_event(event: dict[str, Any]) -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        payload = json.dumps(event, ensure_ascii=True, default=str)
        client.xadd(STREAM_NAME, {"event": payload}, maxlen=50_000, approximate=True)
        return True
    except Exception:
        return False


def stream_health() -> dict[str, Any]:
    client = get_redis_client()
    if client is None:
        return {"enabled": False, "connected": False, "stream": STREAM_NAME}
    try:
        pong = bool(client.ping())
        return {"enabled": True, "connected": pong, "stream": STREAM_NAME}
    except Exception:
        return {"enabled": True, "connected": False, "stream": STREAM_NAME}

