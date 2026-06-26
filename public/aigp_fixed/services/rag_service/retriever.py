"""
services/rag_service/retriever.py
Pinecone retriever for RAG with similarity threshold.
"""
from typing import Optional

import structlog
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
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

    _pc = None
    _encoder = None

    def __init__(self, isbn: str, top_k: int = 5):
        super().__init__(isbn=isbn, top_k=top_k)
        self._pc = pinecone_client
        self._encoder = get_encoder()

    def _get_relevant_documents(self, query: str) -> list[Document]:
        """Synchronous document retrieval."""
        query_vec = self._encoder.encode_single(query).tolist()

        try:
            matches = self._pc.query(
                vector=query_vec,
                top_k=self.top_k,
                namespace=self.isbn,
            )
        except Exception as e:
            log.error("retriever.query_failed", isbn=self.isbn, error=str(e))
            return []

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
                page_content=m["metadata"]["text"],
                metadata={
                    "isbn": self.isbn,
                    "page_num": m["metadata"].get("page_num"),
                    "score": round(m["score"], 4),
                },
            )
            for m in matches
            if m["score"] >= MIN_SIMILARITY_THRESHOLD
        ]

    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        """Async wrapper using run_in_executor."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_relevant_documents, query)


retriever = PineconeBookRetriever


def get_retriever(isbn: str, top_k: int = 5) -> PineconeBookRetriever:
    """Factory function to create retriever for a book."""
    return PineconeBookRetriever(isbn=isbn, top_k=top_k)