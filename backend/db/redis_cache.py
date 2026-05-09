from __future__ import annotations

import logging
import json
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, url: str) -> None:
        self._url = url
        self._client: Redis | None = None

    async def connect(self) -> None:
        if self._client is None:
            self._client = Redis.from_url(self._url, decode_responses=False)
            logger.info("Redis client initialized")

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Redis client closed")

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            return bool(await self._client.ping())
        except Exception:
            logger.exception("Redis ping failed")
            return False

    async def get_json(self, key: str) -> Any | None:
        if self._client is None:
            return None
        raw = await self._client.get(key)
        if raw is None:
            return None
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Invalid cached JSON for key=%s", key)
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        if self._client is None:
            return
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        await self._client.set(name=key, value=payload, ex=ttl_seconds)
