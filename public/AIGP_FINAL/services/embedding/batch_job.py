"""
services/embedding/batch_job.py
Batch job for consuming chunks from Kafka and upserting to Pinecone.
"""
import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np
import structlog

from services.embedding.encoder import get_encoder
from shared.kafka_consumer import KafkaConsumerWrapper
from shared.pinecone_client import pinecone_client
from shared.config import settings

log = structlog.get_logger(__name__)

UPSERT_BATCH_SIZE = settings.UPSERT_BATCH_SIZE
GLOBAL_NAMESPACE = settings.PINECONE_GLOBAL_NAMESPACE
SYNOPSES_NAMESPACE = settings.PINECONE_SYNOPSES_NAMESPACE


@dataclass
class ChunkData:
    """Data class for chunk messages from Kafka."""

    chunk_id: str
    isbn: str
    page_num: int
    text: str
    token_count: int
    title: str = ""
    author: str = ""
    genre_tags: list[str] | None = None


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
        self._buffer: dict[str, list[dict]] = defaultdict(list)
        self._synopsis_vectors: dict[str, list[list[float]]] = defaultdict(list)
        self._book_metadata: dict[str, dict] = {}
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
                await self._process_message(msg["value"])
        finally:
            await self._flush_all_buffers()
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
            title=chunk_data.get("title", ""),
            author=chunk_data.get("author", ""),
            genre_tags=chunk_data.get("genre_tags") or [],
        )

        vector = self._encoder.encode_single(chunk.text)

        primary_genre = chunk.genre_tags[0] if chunk.genre_tags else ""

        metadata = {
            "chunk_id": chunk.chunk_id,
            "isbn": chunk.isbn,
            "page_num": chunk.page_num,
            "text": chunk.text,
            "token_count": chunk.token_count,
            "title": chunk.title,
            "author": chunk.author,
            "genre": primary_genre,
            "genre_tags": chunk.genre_tags,
            "doc_type": "chunk",
        }

        vector_record = {
            "id": chunk.chunk_id,
            "values": vector.tolist(),
            "metadata": metadata,
        }

        self._buffer[chunk.isbn].append(vector_record)
        self._synopsis_vectors[chunk.isbn].append(vector.tolist())
        self._book_metadata[chunk.isbn] = {
            "title": chunk.title,
            "author": chunk.author,
            "genre": primary_genre,
        }

        self._chunks_processed += 1

        total_buffered = sum(len(v) for v in self._buffer.values())
        if total_buffered >= UPSERT_BATCH_SIZE:
            await self._flush_all_buffers()

    async def _flush_all_buffers(self) -> None:
        """Flush all per-ISBN buffers to Pinecone."""
        for isbn in list(self._buffer.keys()):
            if self._buffer[isbn]:
                await self._flush_isbn_buffer(isbn)

    async def _flush_isbn_buffer(self, isbn: str) -> None:
        """Flush a single ISBN buffer to Pinecone (per-book + global namespaces)."""
        buffer_copy = self._buffer[isbn]
        self._buffer[isbn] = []

        if not buffer_copy:
            return

        global_records = [
            {
                **record,
                "id": f"global_{record['id']}",
            }
            for record in buffer_copy
        ]

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                await pinecone_client.upsert(buffer_copy, namespace=isbn)
                await pinecone_client.upsert(global_records, namespace=GLOBAL_NAMESPACE)
                log.info(
                    "pinecone.upsert.success",
                    isbn=isbn,
                    count=len(buffer_copy),
                )
                await self._upsert_synopsis(isbn)
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
                    await self._send_to_dlq(buffer_copy + global_records, str(e))
                    raise

    async def _upsert_synopsis(self, isbn: str) -> None:
        """Upsert or refresh the book synopsis vector in the synopses namespace."""
        vectors = self._synopsis_vectors.pop(isbn, [])
        meta = self._book_metadata.get(isbn, {})

        if not vectors:
            return

        avg = np.mean(vectors, axis=0)
        norm = np.linalg.norm(avg)
        if norm > 0:
            avg = avg / norm

        synopsis_record = [{
            "id": f"synopsis_{isbn}",
            "values": avg.tolist(),
            "metadata": {
                "isbn": isbn,
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "genre": meta.get("genre", ""),
                "doc_type": "synopsis",
            },
        }]

        await pinecone_client.upsert(synopsis_record, namespace=SYNOPSES_NAMESPACE)

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


async def main() -> None:
    """Main entry point for the batch job."""
    job = EmbeddingBatchJob()
    await job.run()


if __name__ == "__main__":
    asyncio.run(main())
