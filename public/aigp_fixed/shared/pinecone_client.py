"""
shared/pinecone_client.py
Pinecone vector database client for semantic search and retrieval.
"""
import asyncio
from typing import Any

from pinecone import Pinecone as PineconeSDK

from shared.config import settings


class PineconeClient:
    """
    Async Pinecone client wrapper for vector operations.
    Uses run_in_executor for blocking SDK calls.
    """

    def __init__(self) -> None:
        self._pc: PineconeSDK | None = None
        self._index = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def init(self) -> None:
        """Initialize Pinecone connection."""
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not configured")

        self._pc = PineconeSDK(api_key=settings.PINECONE_API_KEY)
        self._index = self._pc.Index(
            settings.PINECONE_INDEX,
            pool_threads=10,
        )
        self._loop = asyncio.get_event_loop()

    @property
    def index(self):
        """Get the Pinecone index."""
        if self._index is None:
            self.init()
        return self._index

    async def upsert(
        self,
        vectors: list[dict[str, Any]],
        namespace: str = "",
    ) -> dict:
        if self._index is None:
            self.init()

        def _upsert() -> dict:
            return self._index.upsert(
                vectors=vectors,
                namespace=namespace,
            )

        return await asyncio.get_event_loop().run_in_executor(None, _upsert)

    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = "",
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
        include_values: bool = False,
    ) -> list[dict[str, Any]]:
        if self._index is None:
            self.init()

        def _query() -> dict:
            return self._index.query(
                vector=vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=include_metadata,
                include_values=include_values,
            )

        result = await asyncio.get_event_loop().run_in_executor(None, _query)
        # Pinecone v3 returns an object with .matches
        matches = result.get("matches", []) if isinstance(result, dict) else result.matches
        return [m.to_dict() if hasattr(m, "to_dict") else dict(m) for m in matches]

    async def query_global(
        self,
        vector: list[float],
        top_k: int = 10,
        filter: dict[str, Any] | None = None,
        include_metadata: bool = True,
        include_values: bool = False,
    ) -> list[dict[str, Any]]:
        if self._index is None:
            self.init()

        def _query() -> dict:
            return self._index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                include_metadata=include_metadata,
                include_values=include_values,
            )

        result = await asyncio.get_event_loop().run_in_executor(None, _query)
        matches = result.get("matches", []) if isinstance(result, dict) else result.matches
        return [m.to_dict() if hasattr(m, "to_dict") else dict(m) for m in matches]

    async def fetch(
        self,
        ids: list[str],
        namespace: str = "",
    ) -> dict[str, Any]:
        if self._index is None:
            self.init()

        def _fetch() -> dict:
            return self._index.fetch(ids=ids, namespace=namespace)

        return await asyncio.get_event_loop().run_in_executor(None, _fetch)

    async def delete(
        self,
        ids: list[str] | None = None,
        namespace: str = "",
        delete_all: bool = False,
    ) -> None:
        if self._index is None:
            self.init()

        def _delete() -> None:
            if delete_all:
                self._index.delete(delete_all=True, namespace=namespace)
            elif ids:
                self._index.delete(ids=ids, namespace=namespace)

        await asyncio.get_event_loop().run_in_executor(None, _delete)

    async def describe_index_stats(self) -> dict[str, Any]:
        """Get index statistics."""
        if self._index is None:
            self.init()

        def _stats() -> dict:
            return self._index.describe_index_stats()

        return await asyncio.get_event_loop().run_in_executor(None, _stats)


pinecone_client = PineconeClient()
