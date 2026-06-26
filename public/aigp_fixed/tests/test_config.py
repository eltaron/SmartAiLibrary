"""
tests/test_config.py
Tests for shared configuration module.
"""
import pytest
from unittest.mock import patch
from pydantic import ValidationError


class TestSettings:
    """Test suite for Settings configuration."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        from shared.config import Settings

        settings = Settings()
        assert settings.EMBEDDING_MODEL == "sentence-transformers/all-mpnet-base-v2"
        assert settings.CHUNK_SIZE == 512
        assert settings.CHUNK_OVERLAP == 50
        assert settings.UPSERT_BATCH_SIZE == 100
        assert settings.ANN_TOP_K == 50
        assert settings.FINAL_TOP_K == 10
        assert settings.CE_MODEL == "cross-encoder/ms-marco-MiniLM-L-6-v2"
        assert settings.FLAN_MODEL == "google/flan-t5-large"
        assert settings.RAG_LLM_MODEL == "gpt-4o-mini"
        assert settings.RAG_SIMILARITY_THRESHOLD == 0.60
        assert settings.REDIS_TTL_REC == 300
        assert settings.REDIS_TTL_SUMMARY == 86400
        assert settings.KAFKA_CHUNKS_TOPIC == "book.chunks"
        assert settings.KAFKA_EVENTS_TOPIC == "user.events"
        assert settings.LOG_LEVEL == "INFO"

    def test_custom_values_from_env(self, monkeypatch):
        """Test that custom values can be set via environment variables."""
        from shared.config import Settings

        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
        monkeypatch.setenv("PINECONE_API_KEY", "test-api-key")
        monkeypatch.setenv("CHUNK_SIZE", "1024")

        # Clear cached settings
        import shared.config
        shared.config.get_settings.cache_clear()

        settings = Settings()
        assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        assert settings.REDIS_URL == "redis://localhost:6379/1"
        assert settings.PINECONE_API_KEY == "test-api-key"
        assert settings.CHUNK_SIZE == 1024

    def test_pydantic_validation(self):
        """Test that pydantic validates types correctly."""
        from shared.config import Settings

        with pytest.raises(ValidationError):
            Settings(CHUNK_SIZE="invalid")  # type: ignore

    def test_log_level_enum(self):
        """Test that log level accepts only valid values."""
        from shared.config import Settings

        settings = Settings(LOG_LEVEL="DEBUG")
        assert settings.LOG_LEVEL == "DEBUG"

        settings = Settings(LOG_LEVEL="ERROR")
        assert settings.LOG_LEVEL == "ERROR"

    def test_get_settings_singleton(self):
        """Test that get_settings returns a cached instance."""
        import shared.config

        settings1 = shared.config.get_settings()
        settings2 = shared.config.get_settings()
        assert settings1 is settings2

    def test_health_endpoint_fields(self):
        """Test required fields for health endpoint."""
        from shared.config import Settings

        settings = Settings()
        assert settings.KAFKA_BOOTSTRAP_SERVERS is not None
        assert settings.INGEST_API_KEY is not None

    def test_model_config(self):
        """Test that model_config is set correctly."""
        from shared.config import Settings

        settings = Settings()
        assert settings.model_config["extra"] == "ignore"