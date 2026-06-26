"""
shared/redis_client.py
Async Redis client wrapper for caching and state management.
"""
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from shared.config import settings


class RedisClient:
    """
    Async Redis client for caching and state management.
    Wraps redis.asyncio for proper async support.
    """

    def __init__(self, url: str | None = None) -> None:
        self._url = url or settings.REDIS_URL
        self._client: Redis | None = None

    async def connect(self) -> None:
        """Initialize the Redis connection."""
        if self._client is None:
            self._client = redis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> str | None:
        """
        Get a value by key.
        Returns None if key doesn't exist.
        """
        if self._client is None:
            await self.connect()
        return await self._client.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        """
        Set a key with expiration time (TTL in seconds).
        """
        if self._client is None:
            await self.connect()
        await self._client.setex(key, ttl, value)

    async def delete(self, key: str) -> None:
        """
        Delete a key.
        """
        if self._client is None:
            await self.connect()
        await self._client.delete(key)

    async def incr(self, key: str) -> int:
        """
        Increment a counter and return the new value.
        """
        if self._client is None:
            await self.connect()
        return await self._client.incr(key)

    async def decr(self, key: str) -> int:
        """
        Decrement a counter and return the new value.
        """
        if self._client is None:
            await self.connect()
        return await self._client.decr(key)

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        """
        if self._client is None:
            await self.connect()
        return await self._client.exists(key) > 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time on a key.
        """
        if self._client is None:
            await self.connect()
        return await self._client.expire(key, ttl)

    async def get_json(self, key: str) -> dict | None:
        """
        Get a JSON value by key.
        """
        import orjson

        value = await self.get(key)
        if value is not None:
            return orjson.loads(value)
        return None

    async def set_json(self, key: str, ttl: int, value: dict) -> None:
        """
        Set a JSON value with expiration.
        """
        import orjson

        await self.setex(key, ttl, orjson.dumps(value).decode("utf-8"))

    @property
    def client(self) -> Redis:
        """Get the underlying Redis client."""
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client


redis_client = RedisClient()