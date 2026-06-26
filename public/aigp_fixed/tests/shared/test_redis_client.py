"""
tests/shared/test_redis_client.py
Tests for shared Redis client using fakeredis.aioredis.
"""
import pytest
import fakeredis.aioredis


class TestRedisClient:
    """Test suite for Redis client."""

    @pytest.fixture
    async def redis(self):
        """Create a fake Redis client for testing."""
        client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, redis):
        """Test that get returns None for nonexistent key."""
        result = await redis.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, redis):
        """Test basic set and get operations."""
        await redis.set("test_key", "test_value")
        result = await redis.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_setex(self, redis):
        """Test setex (set with expiration)."""
        await redis.setex("expiry_key", 60, "expiry_value")
        result = await redis.get("expiry_key")
        assert result == "expiry_value"

    @pytest.mark.asyncio
    async def test_delete(self, redis):
        """Test delete operation."""
        await redis.set("delete_key", "delete_value")
        await redis.delete("delete_key")
        result = await redis.get("delete_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_incr(self, redis):
        """Test increment operation."""
        await redis.set("counter", "0")
        result = await redis.incr("counter")
        assert result == 1

    @pytest.mark.asyncio
    async def test_decr(self, redis):
        """Test decrement operation."""
        await redis.set("counter", "10")
        result = await redis.decr("counter")
        assert result == 9

    @pytest.mark.asyncio
    async def test_exists(self, redis):
        """Test exists check."""
        await redis.set("exists_key", "value")
        assert await redis.exists("exists_key") is True
        assert await redis.exists("nonexistent_key") is False

    @pytest.mark.asyncio
    async def test_expire(self, redis):
        """Test expire setting."""
        await redis.set("expire_key", "value")
        result = await redis.expire("expire_key", 60)
        assert result is True

    @pytest.mark.asyncio
    async def test_json_operations(self, redis):
        """Test JSON get/set operations."""
        import orjson

        test_data = {"key": "value", "number": 42}
        json_str = orjson.dumps(test_data).decode("utf-8")

        await redis.set("json_key", json_str)
        result = await redis.get("json_key")
        parsed = orjson.loads(result)

        assert parsed == test_data