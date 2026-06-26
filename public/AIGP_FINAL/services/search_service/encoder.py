"""
services/search_service/encoder.py
Bi-encoder for semantic search query encoding.
"""
from typing import Optional

import numpy as np
import structlog
import torch
from sentence_transformers import SentenceTransformer

from shared.config import settings

log = structlog.get_logger(__name__)

BI_ENCODER_MODEL = settings.EMBEDDING_MODEL


class QueryEncoder:
    """
    Bi-encoder for encoding search queries.

    Uses SentenceTransformer to encode queries into
    L2-normalised 768-d vectors for similarity search.
    """

    def __init__(self, model_path: Optional[str] = None):
        self._model_path = model_path or BI_ENCODER_MODEL
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model: Optional[SentenceTransformer] = None

    def _ensure_model(self) -> SentenceTransformer:
        """Lazy-load the model."""
        if self._model is None:
            log.info("query_encoder.loading", model=self._model_path, device=self._device)
            self._model = SentenceTransformer(self._model_path, device=self._device)
            self._model.eval()
            log.info("query_encoder.loaded", model=self._model_path)
        return self._model

    def encode(self, query: str) -> np.ndarray:
        """
        Encode a search query.

        Args:
            query: Search query string

        Returns:
            L2-normalised 768-d vector
        """
        model = self._ensure_model()

        with torch.no_grad():
            vec = model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

        return vec.astype(np.float32)

    @property
    def embedding_dim(self) -> int:
        return 768


query_encoder = QueryEncoder()


def get_encoder() -> QueryEncoder:
    """Get singleton query encoder."""
    return query_encoder