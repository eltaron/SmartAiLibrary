"""
tests/embedding/test_encoder.py
Tests for embedding encoder module.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestBookEncoder:
    """Test suite for BookEncoder class."""

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_encode_single_returns_768_vector(self, mock_st):
        """Test that encode_single returns 768-d vector."""
        from services.embedding.encoder import BookEncoder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_st.return_value = mock_model

        encoder = BookEncoder()
        result = encoder.encode_single("test text")

        assert result.shape == (768,)

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_encode_batch_returns_correct_shape(self, mock_st):
        """Test that encode_batch returns (N, 768) matrix."""
        from services.embedding.encoder import BookEncoder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(5, 768).astype(np.float32)
        mock_st.return_value = mock_model

        encoder = BookEncoder()
        texts = ["text1", "text2", "text3", "text4", "text5"]
        result = encoder.encode_batch(texts, batch_size=2)

        assert result.shape == (5, 768)

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_vectors_are_l2_normalized(self, mock_st):
        """Test that output vectors are L2-normalised."""
        from services.embedding.encoder import BookEncoder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(768).astype(np.float32)
        mock_st.return_value = mock_model

        encoder = BookEncoder()
        result = encoder.encode_single("test text")

        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 1e-5, f"Vector not normalized: norm={norm}"

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_identical_inputs_produce_identical_vectors(self, mock_st):
        """Test determinism of encoding."""
        from services.embedding.encoder import BookEncoder

        mock_model = MagicMock()
        base_vector = np.random.rand(768).astype(np.float32)
        mock_model.encode.return_value = base_vector
        mock_st.return_value = mock_model

        encoder = BookEncoder()
        text = "identical text"

        result1 = encoder.encode_single(text)
        result2 = encoder.encode_single(text)

        np.testing.assert_array_equal(result1, result2)

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_encode_single_dtype(self, mock_st):
        """Test that output dtype is float32."""
        from services.embedding.encoder import BookEncoder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(768)
        mock_st.return_value = mock_model

        encoder = BookEncoder()
        result = encoder.encode_single("test")

        assert result.dtype == np.float32

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_encode_batch_dtype(self, mock_st):
        """Test that batch output dtype is float32."""
        from services.embedding.encoder import BookEncoder

        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.rand(10, 768)
        mock_st.return_value = mock_model

        encoder = BookEncoder()
        texts = ["text"] * 10
        result = encoder.encode_batch(texts)

        assert result.dtype == np.float32


class TestEncoderProperties:
    """Test suite for encoder properties."""

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_embedding_dim_property(self, mock_st):
        """Test embedding_dim property."""
        from services.embedding.encoder import BookEncoder

        encoder = BookEncoder()
        assert encoder.embedding_dim == 768

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_model_name_property(self, mock_st):
        """Test model_name property."""
        from services.embedding.encoder import BookEncoder

        encoder = BookEncoder(model_name="test-model")
        assert encoder.model_name == "test-model"

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_device_property(self, mock_st):
        """Test device property."""
        from services.embedding.encoder import BookEncoder

        encoder = BookEncoder(device="cpu")
        assert encoder.device == "cpu"


class TestEncoderSingleton:
    """Test suite for encoder singleton."""

    def test_get_encoder_returns_singleton(self):
        """Test that get_encoder returns the same instance."""
        from services.embedding.encoder import get_encoder

        encoder1 = get_encoder()
        encoder2 = get_encoder()

        assert encoder1 is encoder2


class TestEncoderCUDA:
    """Test suite for CUDA detection."""

    @patch("services.embedding.encoder.torch.cuda.is_available")
    @patch("services.embedding.encoder.SentenceTransformer")
    def test_uses_cuda_when_available(self, mock_st, mock_cuda):
        """Test that encoder uses CUDA when available."""
        mock_cuda.return_value = True

        from services.embedding.encoder import BookEncoder

        encoder = BookEncoder(device=None)
        assert encoder.device == "cuda"

    @patch("services.embedding.encoder.torch.cuda.is_available")
    @patch("services.embedding.encoder.SentenceTransformer")
    def test_fallback_to_cpu_when_no_cuda(self, mock_st, mock_cuda):
        """Test that encoder falls back to CPU when CUDA not available."""
        mock_cuda.return_value = False

        from services.embedding.encoder import BookEncoder

        encoder = BookEncoder(device=None)
        assert encoder.device == "cpu"


class TestEncoderLazyLoading:
    """Test suite for lazy loading."""

    @patch("services.embedding.encoder.SentenceTransformer")
    def test_model_not_loaded_until_first_encode(self, mock_st):
        """Test that model is lazily loaded."""
        from services.embedding.encoder import BookEncoder

        encoder = BookEncoder()
        assert encoder._model is None

        encoder.encode_single("test")

        mock_st.assert_called_once()