"""
services/embedding/encoder.py
SentenceTransformer wrapper for embedding book text.
"""
from typing import Optional

import numpy as np
import structlog
import torch
from sentence_transformers import SentenceTransformer

from shared.config import settings

log = structlog.get_logger(__name__)


class BookEncoder:
    """
    Wraps SentenceTransformer for encoding book text.

    Output: L2-normalised 768-d float32 vectors (unit sphere →
    cosine similarity = dot product).
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model: Optional[SentenceTransformer] = None

    def _ensure_model(self) -> SentenceTransformer:
        """Lazy-load the model."""
        if self._model is None:
            log.info("encoder.loading", model=self._model_name, device=self._device)
            self._model = SentenceTransformer(self._model_name, device=self._device)
            self._model.eval()
            log.info("encoder.loaded", model=self._model_name)
        return self._model

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single text string.

        Args:
            text: Text to encode

        Returns:
            L2-normalised 768-d vector as float32 numpy array
        """
        model = self._ensure_model()

        with torch.no_grad():
            vec = model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

        return vec.astype(np.float32)

    def encode_batch(
        self,
        texts: list[str],
        batch_size: int = 64,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode a batch of text strings.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar

        Returns:
            L2-normalised matrix of shape (N, 768) as float32 numpy array
        """
        model = self._ensure_model()

        with torch.no_grad():
            vecs = model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=show_progress,
            )

        return vecs.astype(np.float32)

    @property
    def embedding_dim(self) -> int:
        """Get the embedding dimension."""
        return 768

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def device(self) -> str:
        """Get the device being used."""
        return self._device


encoder = BookEncoder()


def get_encoder() -> BookEncoder:
    """Get the singleton encoder instance."""
    return encoder