"""
tests/search_service/test_main.py
Tests for search service.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestSearchEndpoint:
    """Test suite for /search endpoint."""

    @patch("services.search_service.main.get_encoder")
    @patch("services.search_service.main.get_reranker")
    @patch("services.search_service.main.pinecone_client")
    @patch("services.search_service.main.redis_client")
    def test_search_returns_top_k_results(self, mock_redis, mock_pc, mock_reranker, mock_encoder):
        """Test that search returns top_k results."""
        from services.search_service.main import app

        mock_encoder.return_value.encode.return_value = MagicMock(tolist=lambda: [0.1] * 768)

        mock_pc.query_global.return_value = [
            {"metadata": {"isbn": f"isbn-{i}", "title": f"Book {i}"}, "score": 0.9 - i * 0.1}
            for i in range(20)
        ]

        mock_reranker.return_value.rerank.return_value = [
            {"metadata": {"isbn": f"isbn-{i}", "title": f"Book {i}"}, "rerank_score": 0.9 - i * 0.1}
            for i in range(10)
        ]

        mock_redis.get.return_value = None

        with TestClient(app) as client:
            response = client.post("/search", json={"query": "test query", "top_k": 10})

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 10

    @patch("services.search_service.main.pinecone_client")
    @patch("services.search_service.main.redis_client")
    def test_empty_pinecone_results_returns_empty_list(self, mock_redis, mock_pc):
        """Test that empty Pinecone results returns empty list."""
        from services.search_service.main import app

        mock_pc.query_global.return_value = []
        mock_redis.get.return_value = None

        with TestClient(app) as client:
            response = client.post("/search", json={"query": "test", "top_k": 10})

            assert response.status_code == 200
            assert response.json() == []


class TestSimilarEndpoint:
    """Test suite for /search/similar/{isbn} endpoint."""

    @patch("services.search_service.main.get_cbf")
    @patch("services.search_service.main.redis_client")
    def test_similar_returns_results(self, mock_redis, mock_cbf):
        """Test similar books endpoint."""
        from services.search_service.main import app

        mock_cbf.return_value.similar_books.return_value = [
            {"isbn": "isbn-1", "title": "Book 1", "score": 0.9},
            {"isbn": "isbn-2", "title": "Book 2", "score": 0.8},
        ]

        mock_redis.get.return_value = None

        with TestClient(app) as client:
            response = client.post("/search/similar/978-0-123456-78-9?top_k=10")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2


class TestHealthEndpoint:
    """Test suite for health endpoint."""

    def test_health_returns_ok(self):
        """Test health endpoint."""
        from services.search_service.main import app

        with TestClient(app) as client:
            response = client.get("/health")

            assert response.status_code == 200
            assert response.json()["status"] == "ok"


class TestRerankerLimit:
    """Test that reranker is called with at most 50 candidates."""

    @patch("services.search_service.main.get_encoder")
    @patch("services.search_service.main.get_reranker")
    @patch("services.search_service.main.pinecone_client")
    @patch("services.search_service.main.redis_client")
    def test_reranker_max_50_candidates(self, mock_redis, mock_pc, mock_reranker, mock_encoder):
        """Test reranker is limited to 50 candidates."""
        from services.search_service.main import app

        mock_encoder.return_value.encode.return_value = MagicMock(tolist=lambda: [0.1] * 768)

        mock_pc.query_global.return_value = [
            {"metadata": {"isbn": f"isbn-{i}", "text": f"text {i}"}, "score": 0.9}
            for i in range(100)
        ]

        mock_redis.get.return_value = None

        with TestClient(app) as client:
            client.post("/search", json={"query": "test", "top_k": 10})

            call_args = mock_reranker.return_value.rerank.call_args
            candidates = call_args[0][1]
            assert len(candidates) <= 50