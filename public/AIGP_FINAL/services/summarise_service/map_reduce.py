"""
services/summarise_service/map_reduce.py
Map-reduce pipeline for long book summarisation.
"""
from typing import Optional

import structlog

from services.summarise_service.summariser import Summariser, SummaryType, GenerationConfig, get_summariser
from shared.pinecone_client import pinecone_client
from shared.redis_client import RedisClient
from shared.config import settings

log = structlog.get_logger(__name__)

CHUNKS_PER_MAP_BATCH = settings.SUMMARY_BATCH_SIZE


class MapReducePipeline:
    """
    Map-reduce pipeline for summarising full books.

    MAP:    Summarise each batch of chunks independently (parallel)
    REDUCE: Summarise intermediate summaries into final summary
    """

    def __init__(self, summariser: Optional[Summariser] = None):
        self._summariser = summariser or get_summariser()
        self._redis = RedisClient()
        self._current_isbn: str = ""

    async def run(
        self,
        isbn: str,
        summary_type: SummaryType = SummaryType.SHORT,
    ) -> str:
        """
        Run map-reduce summarisation for a book.

        Args:
            isbn: Book ISBN
            summary_type: Type of summary to generate

        Returns:
            Final summary text
        """
        self._current_isbn = isbn
        await self._redis.connect()

        chunks = await self._fetch_chunks(isbn)

        if not chunks:
            log.warning("map_reduce.no_chunks", isbn=isbn)
            return ""

        await self._update_progress(isbn, 0, len(chunks))

        intermediate_summaries = await self._map_phase(chunks)

        final_summary = await self._reduce_phase(intermediate_summaries, summary_type)

        await self._update_progress(isbn, len(chunks), len(chunks))

        log.info("map_reduce.complete", isbn=isbn, summary_length=len(final_summary))

        return final_summary

    async def _fetch_chunks(self, isbn: str) -> list[dict]:
        """Fetch all chunks for a book from Pinecone."""
        try:
            matches = await pinecone_client.query(
                vector=[1e-6] * 768,
                top_k=10000,
                namespace=isbn,
                filter={"doc_type": {"$eq": "chunk"}},
            )

            chunks = sorted(matches, key=lambda x: x.get("metadata", {}).get("page_num", 0))
            return chunks

        except Exception as e:
            log.error("map_reduce.fetch_chunks.failed", isbn=isbn, error=str(e))
            return []

    async def _map_phase(self, chunks: list[dict]) -> list[str]:
        """MAP: Summarise each batch of chunks."""
        intermediate = []
        total_batches = (len(chunks) + CHUNKS_PER_MAP_BATCH - 1) // CHUNKS_PER_MAP_BATCH

        for batch_idx in range(total_batches):
            start = batch_idx * CHUNKS_PER_MAP_BATCH
            end = min(start + CHUNKS_PER_MAP_BATCH, len(chunks))
            batch = chunks[start:end]

            batch_text = " ".join(
                c.get("metadata", {}).get("text", "") for c in batch
            )

            summary = await self._summariser.summarise_async(
                batch_text,
                SummaryType.SHORT,
                GenerationConfig(max_new_tokens=80),
            )

            intermediate.append(summary)

            await self._update_progress_from_batch(batch_idx, total_batches, len(chunks))

            log.debug(
                "map_reduce.batch_complete",
                batch=batch_idx + 1,
                total=total_batches,
            )

        return intermediate

    async def _reduce_phase(
        self,
        intermediate_summaries: list[str],
        summary_type: SummaryType,
    ) -> str:
        """REDUCE: Summarise intermediate summaries into final summary."""
        if not intermediate_summaries:
            return ""

        if len(intermediate_summaries) == 1:
            return intermediate_summaries[0]

        combined = " ".join(intermediate_summaries)

        final_summary = await self._summariser.summarise_async(
            combined,
            summary_type,
            GenerationConfig(max_new_tokens=300),
        )

        return final_summary

    async def _update_progress(self, isbn: str, done: int, total: int) -> None:
        """Update progress in Redis."""
        key = f"summary:progress:{isbn}"
        await self._redis.set_json(key, 3600, {"done": done, "total": total})

    async def _update_progress_from_batch(
        self,
        batch_idx: int,
        total_batches: int,
        total_chunks: int,
    ) -> None:
        """Update progress based on batch completion."""
        if not self._current_isbn or total_batches == 0:
            return

        done = min(
            total_chunks,
            int((batch_idx + 1) / total_batches * total_chunks),
        )
        await self._update_progress(self._current_isbn, done, total_chunks)


async def map_reduce_summarise(isbn: str, summary_type: SummaryType = SummaryType.SHORT) -> str:
    """Convenience function for map-reduce summarisation."""
    pipeline = MapReducePipeline()
    return await pipeline.run(isbn, summary_type)
