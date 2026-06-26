"""
services/search_service/reranker.py
Cross-encoder re-ranker for search results.
"""
from typing import Optional

import structlog
from sentence_transformers import CrossEncoder

from shared.config import settings

log = structlog.get_logger(__name__)

CE_MODEL = settings.CE_MODEL
MAX_RERANK_CANDIDATES = 50


class CrossEncoderReranker:
    """
    Cross-encoder re-ranker for second-pass ranking.

    Re-ranks top-K bi-encoder candidates using a cross-encoder
    for higher accuracy. Limited to 50 candidates for latency.
    """

    def __init__(self, model_name: Optional[str] = None):
        self._model_name = model_name or CE_MODEL
        self._model: Optional[CrossEncoder] = None

    def _ensure_model(self) -> CrossEncoder:
        """Lazy-load the model."""
        if self._model is None:
            log.info("reranker.loading", model=self._model_name)
            self._model = CrossEncoder(self._model_name)
            log.info("reranker.loaded", model=self._model_name)
        return self._model

    def rerank(
        self,
        query: str,
        candidates: list[dict],
    ) -> list[dict]:
        """
        Re-rank candidates using cross-encoder.

        Args:
            query: Original search query
            candidates: List of candidate dicts with 'metadata.text'

        Returns:
            Re-ranked list with 'rerank_score' added
        """
        if not candidates:
            return []

        model = self._ensure_model()

        limited = candidates[:MAX_RERANK_CANDIDATES]

        pairs = [(query, c.get("metadata", {}).get("text", "")) for c in limited]

        scores = model.predict(pairs)

        for i, (cand, score) in enumerate(zip(limited, scores)):
            limited[i]["rerank_score"] = float(score)

        reranked = sorted(
            limited,
            key=lambda x: x.get("rerank_score", 0.0),
            reverse=True,
        )

        return reranked

    def score_pair(self, query: str, passage: str) -> float:
        """Score a single query-passage pair."""
        model = self._ensure_model()
        return float(model.predict([(query, passage)])[0])


reranker = CrossEncoderReranker()


def get_reranker() -> CrossEncoderReranker:
    """Get singleton reranker."""
    return reranker