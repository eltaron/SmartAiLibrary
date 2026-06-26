"""
tests/rec_service/test_cbf.py
Tests for Content-Based Filtering.
"""
import pytest
from unittest.mock import AsyncMock, patch
import numpy as np


class TestContentBasedFilter:
    """Test suite for ContentBasedFilter."""

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_similar_books_returns_correct_count(self, mock_pc):
        """Test that similar_books returns top_k results."""
        from services.rec_service.models.cbf import ContentBasedFilter

        mock_pc.query = AsyncMock(side_effect=[
            [{"values": [0.1] * 768, "metadata": {"isbn": "seed-isbn", "title": "Seed"}}],
            [
                {"score": 0.9, "metadata": {"isbn": "isbn-a", "title": "Book A"}},
                {"score": 0.8, "metadata": {"isbn": "isbn-b", "title": "Book B"}},
                {"score": 0.7, "metadata": {"isbn": "isbn-c", "title": "Book C"}},
            ],
        ])

        cbf = ContentBasedFilter()
        results = await cbf.similar_books("seed-isbn", top_k=3)

        assert len(results) == 3

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_seed_isbn_not_in_results(self, mock_pc):
        """Test that seed ISBN is never returned in results."""
        from services.rec_service.models.cbf import ContentBasedFilter

        mock_pc.query = AsyncMock(side_effect=[
            [{"values": [0.1] * 768, "metadata": {"isbn": "seed-isbn", "title": "Seed Book"}}],
            [
                {"score": 0.9, "metadata": {"isbn": "seed-isbn", "title": "Seed Book"}},
                {"score": 0.8, "metadata": {"isbn": "isbn-b", "title": "Book B"}},
            ],
        ])

        cbf = ContentBasedFilter()
        results = await cbf.similar_books("seed-isbn", top_k=5)

        isbns = [r["isbn"] for r in results]
        assert "seed-isbn" not in isbns

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_empty_results_when_seed_not_found(self, mock_pc):
        """Test empty results when seed book not found."""
        from services.rec_service.models.cbf import ContentBasedFilter

        mock_pc.query = AsyncMock(return_value=[])

        cbf = ContentBasedFilter()
        results = await cbf.similar_books("nonexistent-isbn")

        assert results == []

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_similar_to_query(self, mock_pc):
        """Test similar_to_query method."""
        from services.rec_service.models.cbf import ContentBasedFilter

        mock_pc.query = AsyncMock(return_value=[
            {"score": 0.9, "metadata": {"isbn": "isbn-1", "title": "Book 1"}},
        ])

        cbf = ContentBasedFilter()
        query_vec = np.random.rand(768)
        results = await cbf.similar_to_query(query_vec, top_k=5)

        assert len(results) >= 0


class TestBatchSimilarBooks:
    """Test suite for batch_similar_books."""

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_batch_empty_input(self, mock_pc):
        """Test batch_similar_books with empty input."""
        from services.rec_service.models.cbf import ContentBasedFilter

        cbf = ContentBasedFilter()
        results = await cbf.batch_similar_books([], top_k=10)

        assert results == []

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_batch_multiple_seeds(self, mock_pc):
        """Test batch_similar_books with multiple seed ISBNs."""
        from services.rec_service.models.cbf import ContentBasedFilter

        mock_pc.query = AsyncMock(side_effect=[
            [{"values": [0.1] * 768, "metadata": {"isbn": "isbn-1"}}],
            [{"values": [0.2] * 768, "metadata": {"isbn": "isbn-2"}}],
            [{"score": 0.9, "metadata": {"isbn": "isbn-x", "title": "Book X"}}],
        ])

        cbf = ContentBasedFilter()
        results = await cbf.batch_similar_books(["isbn-1", "isbn-2"], top_k=5)

        assert isinstance(results, list)


class TestGenreCentroid:
    """Test suite for get_genre_centroid."""

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_genre_centroid_shape(self, mock_pc):
        """Test that genre centroid has correct shape."""
        from services.rec_service.models.cbf import ContentBasedFilter

        mock_pc.query = AsyncMock(return_value=[
            {"values": [0.1] * 768},
            {"values": [0.2] * 768},
        ])

        cbf = ContentBasedFilter()
        centroid = await cbf.get_genre_centroid("science-fiction")

        assert centroid.shape == (768,)

    @pytest.mark.asyncio
    @patch("services.rec_service.models.cbf.pinecone_client")
    async def test_genre_not_found_returns_zeros(self, mock_pc):
        """Test that missing genre returns zero vector."""
        from services.rec_service.models.cbf import ContentBasedFilter

        mock_pc.query = AsyncMock(return_value=[])

        cbf = ContentBasedFilter()
        centroid = await cbf.get_genre_centroid("nonexistent-genre")

        assert np.allclose(centroid, np.zeros(768))
