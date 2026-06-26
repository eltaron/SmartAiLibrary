"""
shared/kafka_producer.py
Async Kafka producer for publishing messages to topics.
"""
import asyncio
from typing import Any

import orjson
from aiokafka import AIOKafkaProducer

from shared.config import settings


class KafkaProducerWrapper:
    """
    Async Kafka producer wrapper with orjson serialization.
    """

    def __init__(self, bootstrap_servers: str | None = None) -> None:
        self._bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: orjson.dumps(v),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retry_backoff_ms=1000,
                max_batch_size=16384,
                linger_ms=10,
                api_version="2.5.0",
                request_timeout_ms=30000,
            )
            await self._producer.start()

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def send(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
    ) -> None:
        if self._producer is None:
            await self.start()

        await self._producer.send_and_wait(
            topic=topic,
            value=value,
            key=key,
        )

    async def send_batch(
        self,
        topic: str,
        values: list[dict[str, Any]],
    ) -> None:
        if self._producer is None:
            await self.start()

        for value in values:
            await self._producer.send_and_wait(topic, value)

    @property
    def producer(self) -> AIOKafkaProducer:
        if self._producer is None:
            raise RuntimeError("Producer not started. Call start() first.")
        return self._producer


kafka_producer = KafkaProducerWrapper()
