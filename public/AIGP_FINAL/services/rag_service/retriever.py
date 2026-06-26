"""
services/rag_service/retriever.py
Pinecone retriever for RAG with similarity threshold.
"""
import asyncio
from typing import Optional

import structlog
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from pydantic.v1 import PrivateAttr
import numpy as np

from shared.pinecone_client import pinecone_client
from shared.config import settings
from services.embedding.encoder import get_encoder

log = structlog.get_logger(__name__)

MIN_SIMILARITY_THRESHOLD = settings.RAG_SIMILARITY_THRESHOLD


class PineconeBookRetriever(BaseRetriever):
    """
    LangChain-compatible retriever for book content from Pinecone.

    Enforces similarity threshold to prevent hallucination.
    """

    isbn: str
    top_k: int = settings.RAG_TOP_K

    _pc: object = PrivateAttr(default=None)
    _encoder: object = PrivateAttr(default=None)

    def __init__(self, isbn: str, top_k: int = 5):
        super().__init__(isbn=isbn, top_k=top_k)
        self._pc = pinecone_client
        self._encoder = get_encoder()

    def _search_sync(self, query: str) -> list[Document]:
        """Synchronous Pinecone search using the raw SDK index (thread-safe)."""
        query_vec = self._encoder.encode_single(query).tolist()

        try:
            if self._pc.index is None:
                self._pc.init()

            raw_result = self._pc.index.query(
                vector=query_vec,
                top_k=self.top_k,
                namespace=self.isbn,
                include_metadata=True,
            )
            raw_matches = (
                raw_result.get("matches", [])
                if isinstance(raw_result, dict)
                else raw_result.matches
            )
            matches = [
                m.to_dict() if hasattr(m, "to_dict") else dict(m)
                for m in raw_matches
            ]
        except Exception as e:
            log.error("retriever.query_failed", isbn=self.isbn, error=str(e))
            return []

        return self._matches_to_documents(matches, query)

    async def _search_async(self, query: str) -> list[Document]:
        """Async Pinecone search using the native async client (event-loop safe)."""
        query_vec = (await asyncio.to_thread(self._encoder.encode_single, query)).tolist()

        try:
            matches = await self._pc.query(
                vector=query_vec,
                top_k=self.top_k,
                namespace=self.isbn,
                filter={"doc_type": {"$eq": "chunk"}},
            )
        except Exception as e:
            log.error("retriever.query_failed", isbn=self.isbn, error=str(e))
            return []

        return self._matches_to_documents(matches, query)

    def _matches_to_documents(self, matches: list, query: str) -> list[Document]:
        """Apply similarity threshold and convert Pinecone matches to Documents."""
        if not matches:
            log.info("retriever.no_matches", isbn=self.isbn, query=query[:50])
            return []

        top_score = matches[0]["score"]
        log.info(
            "retriever.retrieved",
            isbn=self.isbn,
            chunks=len(matches),
            top_score=round(top_score, 3),
        )

        if top_score < MIN_SIMILARITY_THRESHOLD:
            log.info(
                "retriever.threshold_triggered",
                isbn=self.isbn,
                top_score=round(top_score, 3),
                threshold=MIN_SIMILARITY_THRESHOLD,
            )
            return []

        return [
            Document(
                page_content=m["metadata"].get("text", ""),
                metadata={
                    "isbn": self.isbn,
                    "page_num": m["metadata"].get("page_num"),
                    "score": round(m["score"], 4),
                },
            )
            for m in matches
            if m["score"] >= MIN_SIMILARITY_THRESHOLD and m.get("metadata", {}).get("text")
        ]

    def _get_relevant_documents(self, query: str) -> list[Document]:
        """Synchronous document retrieval."""
        return self._search_sync(query)

    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        """Async document retrieval using the native async Pinecone client."""
        return await self._search_async(query)


retriever = PineconeBookRetriever


def get_retriever(isbn: str, top_k: int = 5) -> PineconeBookRetriever:
    """Factory function to create retriever for a book."""
    return PineconeBookRetriever(isbn=isbn, top_k=top_k)