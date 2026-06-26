"""
services/embedding/batch_job.py
Batch job for consuming chunks from Kafka and upserting to Pinecone.
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import structlog

from services.embedding.encoder import get_encoder
from shared.kafka_consumer import KafkaConsumerWrapper
from shared.pinecone_client import pinecone_client
from shared.config import settings

log = structlog.get_logger(__name__)

UPSERT_BATCH_SIZE = settings.UPSERT_BATCH_SIZE


@dataclass
class ChunkData:
    """Data class for chunk messages from Kafka."""

    chunk_id: str
    isbn: str
    page_num: int
    text: str
    token_count: int


class EmbeddingBatchJob:
    """
    Batch job that consumes chunks from Kafka, embeds them,
    and upserts to Pinecone with dead-letter queue support.
    """

    def __init__(
        self,
        topic: Optional[str] = None,
        group_id: Optional[str] = None,
    ):
        self._topic = topic or settings.KAFKA_CHUNKS_TOPIC
        self._group_id = group_id or "embedding-service"
        self._encoder = get_encoder()
        self._buffer: list[dict] = []
        self._chunks_processed = 0
        self._start_time = time.monotonic()

    async def run(self) -> None:
        """Run the batch job continuously."""
        log.info("batch_job.starting", topic=self._topic, group_id=self._group_id)

        consumer = KafkaConsumerWrapper(
            topic=self._topic,
            group_id=self._group_id,
        )
        await consumer.start()

        try:
            async for msg in consumer.consume():
                try:
                    await self._process_message(msg["value"])
                except Exception as e:
                    log.error("chunk.process.failed", error=str(e), chunk_id=msg["value"].get("chunk_id"))
                    await self._handle_failure(msg["value"])
        finally:
            await self._flush_buffer()
            await consumer.stop()

        log.info(
            "batch_job.stopped",
            chunks_processed=self._chunks_processed,
            elapsed_sec=round(time.monotonic() - self._start_time, 1),
        )

    async def _process_message(self, chunk_data: dict) -> None:
        """Process a single chunk message."""
        chunk = ChunkData(
            chunk_id=chunk_data["chunk_id"],
            isbn=chunk_data["isbn"],
            page_num=chunk_data["page_num"],
            text=chunk_data["text"],
            token_count=chunk_data["token_count"],
        )

        vector = self._encoder.encode_single(chunk.text)

        vector_record = {
            "id": chunk.chunk_id,
            "values": vector.tolist(),
            "metadata": {
                "isbn": chunk.isbn,
                "page_num": chunk.page_num,
                "text": chunk.text[:500],
                "token_count": chunk.token_count,
            },
        }

        self._buffer.append(vector_record)
        self._chunks_processed += 1

        if len(self._buffer) >= UPSERT_BATCH_SIZE:
            await self._flush_buffer()
            self._log_throughput()

    async def _flush_buffer(self) -> None:
        """Flush the buffer to Pinecone."""
        if not self._buffer:
            return

        buffer_copy = self._buffer.copy()
        self._buffer.clear()

        isbn = buffer_copy[0]["metadata"]["isbn"]
        namespace = isbn

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                await pinecone_client.upsert(buffer_copy, namespace=namespace)
                log.info(
                    "pinecone.upsert.success",
                    isbn=isbn,
                    count=len(buffer_copy),
                )
                return
            except Exception as e:
                log.warning(
                    "pinecone.upsert.retry",
                    isbn=isbn,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    await self._send_to_dlq(buffer_copy, str(e))

    async def _send_to_dlq(self, vectors: list[dict], error: str) -> None:
        """Send failed batch to dead-letter queue."""
        from shared.kafka_producer import kafka_producer

        dlq_topic = f"{self._topic}.dlq"

        await kafka_producer.start()

        for vec in vectors:
            await kafka_producer.send(
                dlq_topic,
                {
                    "chunk_id": vec["id"],
                    "metadata": vec["metadata"],
                    "error": error,
                    "timestamp": time.time(),
                },
            )

        log.error(
            "pinecone.upsert.dlq",
            topic=dlq_topic,
            count=len(vectors),
            error=error,
        )

    async def _handle_failure(self, chunk_data: dict) -> None:
        """Handle individual chunk processing failure."""
        log.error(
            "chunk.failed",
            chunk_id=chunk_data.get("chunk_id"),
            isbn=chunk_data.get("isbn"),
        )

    def _log_throughput(self) -> None:
        """Log throughput every 1000 chunks."""
        elapsed = time.monotonic() - self._start_time
        if self._chunks_processed > 0 and self._chunks_processed % 1000 == 0:
            rate = self._chunks_processed / elapsed
            log.info(
                "embedding.throughput",
                chunks=self._chunks_processed,
                rate_chunks_per_sec=round(rate, 1),
            )


async def main() -> None:
    """Main entry point for the batch job."""
    job = EmbeddingBatchJob()
    await job.run()


if __name__ == "__main__":
    asyncio.run(main())