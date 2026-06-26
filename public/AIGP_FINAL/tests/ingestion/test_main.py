"""
tests/ingestion/test_main.py
Tests for ingestion FastAPI service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("services.ingestion.main.redis_client") as mock:
        mock.connect = AsyncMock()
        mock.set_json = AsyncMock()
        mock.get_json = AsyncMock(return_value={"isbn": "978-0-123456-78-9", "status": "done", "chunk_count": 10})
        yield mock


@pytest.fixture
def mock_process_book():
    """Mock the background task function."""
    with patch("services.ingestion.main.process_book", new_callable=AsyncMock) as mock:
        mock.return_value = 10
        yield mock


class TestHealthEndpoint:
    """Test suite for /health endpoint."""

    def test_health_returns_ok(self):
        """Test that health endpoint returns correct response."""
        from services.ingestion.main import app

        with TestClient(app) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["service"] == "ingestion"


class TestIngestEndpoint:
    """Test suite for /ingest endpoint."""

    def test_ingest_requires_file(self):
        """Test that file is required."""
        from services.ingestion.main import app

        with TestClient(app) as client:
            response = client.post("/ingest", data={"isbn": "123", "title": "Test", "author": "Author"})

            assert response.status_code == 422

    @patch("services.ingestion.main.process_book")
    def test_ingest_queued(self, mock_process):
        """Test that ingestion is queued correctly."""
        from services.ingestion.main import app

        with TestClient(app) as client:
            response = client.post(
                "/ingest",
                files={"file": ("test.pdf", b"fake pdf content", "application/pdf")},
                data={
                    "isbn": "978-0-123456-78-9",
                    "title": "Test Book",
                    "author": "Test Author",
                },
            )

            assert response.status_code == 202
            data = response.json()
            assert data["isbn"] == "978-0-123456-78-9"
            assert data["status"] == "queued"
            assert "job_id" in data


class TestIngestStatusEndpoint:
    """Test suite for /ingest/{isbn}/status endpoint."""

    def test_status_returns_data(self, mock_redis):
        """Test that status endpoint returns correct data."""
        from services.ingestion.main import app

        with TestClient(app) as client:
            response = client.get("/ingest/978-0-123456-78-9/status")

            assert response.status_code == 200
            data = response.json()
            assert data["isbn"] == "978-0-123456-78-9"
            assert data["status"] == "done"
            assert data["chunk_count"] == 10

    def test_status_404_for_unknown_isbn(self, mock_redis):
        """Test that status returns 404 for unknown ISBN."""
        from services.ingestion.main import app

        mock_redis.get_json.return_value = None

        with TestClient(app) as client:
            response = client.get("/ingest/000-0-000000-00-0/status")

            assert response.status_code == 404


class TestErrorHandling:
    """Test suite for error handling."""

    @patch("services.ingestion.main.process_book")
    def test_process_book_failure(self, mock_process, mock_redis):
        """Test that failed processing is handled correctly."""
        from services.ingestion.main import app

        mock_process.side_effect = Exception("Test error")

        with TestClient(app) as client:
            with patch("builtins.open", MagicMock()):
                response = client.post(
                    "/ingest",
                    files={"file": ("test.pdf", b"content", "application/pdf")},
                    data={
                        "isbn": "978-0-123456-78-9",
                        "title": "Test",
                        "author": "Author",
                    },
                )

                assert response.status_code == 202


class TestSchemaValidation:
    """Test suite for request/response schemas."""

    def test_ingest_response_schema(self):
        """Test IngestResponse schema."""
        from services.ingestion.schemas import IngestResponse

        response = IngestResponse(job_id="test-123", isbn="978-0-123456-78-9", status="queued")

        assert response.job_id == "test-123"
        assert response.isbn == "978-0-123456-78-9"
        assert response.status == "queued"

    def test_ingest_status_response_schema(self):
        """Test IngestStatusResponse schema."""
        from services.ingestion.schemas import IngestStatusResponse

        response = IngestStatusResponse(isbn="978-0-123456-78-9", status="done", chunk_count=50)

        assert response.isbn == "978-0-123456-78-9"
        assert response.status == "done"
        assert response.chunk_count == 50

    def test_health_response_schema(self):
        """Test HealthResponse schema."""
        from services.ingestion.schemas import HealthResponse

        response = HealthResponse(status="ok", service="ingestion")

        assert response.status == "ok"
        assert response.service == "ingestion"