"""
shared/kafka_consumer.py
Async Kafka consumer for processing messages from topics.
"""
import asyncio
from typing import AsyncGenerator, Any

import orjson
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from shared.config import settings


class KafkaConsumerWrapper:
    """
    Async Kafka consumer wrapper with orjson deserialization.
    Commits offsets only after successful processing.
    """

    def __init__(
        self,
        topic: str,
        group_id: str | None = None,
        bootstrap_servers: str | None = None,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = False,
    ) -> None:
        self._topic = topic
        self._group_id = group_id or settings.KAFKA_CONSUMER_GROUP
        self._bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self._auto_offset_reset = auto_offset_reset
        self._enable_auto_commit = enable_auto_commit
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                self._topic,
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._group_id,
                auto_offset_reset=self._auto_offset_reset,
                enable_auto_commit=self._enable_auto_commit,
                value_deserializer=lambda m: orjson.loads(m),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                max_poll_interval_ms=300000,
                max_poll_records=500,
                fetch_min_bytes=1,
                fetch_max_wait_ms=500,
            )
            await self._consumer.start()

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None

    async def consume(self) -> AsyncGenerator[dict[str, Any], None]:
        """
        Async generator that yields messages from the topic.
        Commits offset after successful processing.
        """
        if self._consumer is None:
            await self.start()

        async for msg in self._consumer:
            try:
                yield {
                    "key": msg.key,
                    "value": msg.value,
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "timestamp": msg.timestamp,
                }
                await self._consumer.commit()
            except Exception as e:
                # Log error but don't commit - message will be re-delivered
                import structlog

                log = structlog.get_logger(__name__)
                log.error(
                    "kafka.consume.error",
                    topic=msg.topic,
                    partition=msg.partition,
                    offset=msg.offset,
                    error=str(e),
                )
                raise

    async def __aiter__(self) -> AsyncGenerator[dict[str, Any], None]:
        """Allow using 'async for' syntax."""
        async for msg in self.consume():
            yield msg

    @property
    def consumer(self) -> AIOKafkaConsumer:
        """Get the underlying Kafka consumer."""
        if self._consumer is None:
            raise RuntimeError("Consumer not started. Call start() first.")
        return self._consumer


def create_consumer(
    topic: str,
    group_id: str | None = None,
) -> KafkaConsumerWrapper:
    """
    Factory function to create a Kafka consumer.

    Args:
        topic: Topic to consume from
        group_id: Consumer group ID
    """
    return KafkaConsumerWrapper(topic=topic, group_id=group_id)