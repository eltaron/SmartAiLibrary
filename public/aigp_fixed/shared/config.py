"""
shared/config.py
Centralized configuration for Smart AI Library using pydantic-settings.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main settings class - all config via environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/smartailibrary",
        description="PostgreSQL connection URL",
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Pinecone
    PINECONE_API_KEY: str = Field(default="", description="Pinecone API key")
    PINECONE_ENV: str = Field(default="us-west1-gcp", description="Pinecone environment")
    PINECONE_INDEX: str = Field(default="smart-library-books", description="Pinecone index name")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    KAFKA_CHUNKS_TOPIC: str = Field(default="book.chunks", description="Kafka topic for book chunks")
    KAFKA_EVENTS_TOPIC: str = Field(
        default="user.events",
        description="Kafka topic for user events",
    )
    KAFKA_CONSUMER_GROUP: str = Field(
        default="smart-ai-library",
        description="Kafka consumer group",
    )

    # Ingestion
    INGEST_API_KEY: str = Field(
        default="development-key",
        description="API key for ingestion service",
    )
    CHUNK_SIZE: int = Field(default=512, description="Token count per chunk")
    CHUNK_OVERLAP: int = Field(default=50, description="Token overlap between chunks")
    UPSERT_BATCH_SIZE: int = Field(default=100, description="Pinecone upsert batch size")

    # Embedding
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        description="Sentence transformer model for embeddings",
    )
    EMBEDDING_DEVICE: Literal["cuda", "cpu"] = Field(
        default="cuda",
        description="Device for embedding model (cuda or cpu)",
    )

    # Search
    ANN_TOP_K: int = Field(
        default=50,
        description="Top-K results from ANN retrieval before re-ranking",
    )
    FINAL_TOP_K: int = Field(
        default=10,
        description="Final top-K results returned after re-ranking",
    )
    CE_MODEL: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Cross-encoder model for re-ranking",
    )

    # Recommendation
    NCF_EMB_DIM: int = Field(default=64, description="Embedding dimension for NCF model")
    NCF_MLP_LAYERS: list[int] = Field(
        default=[128, 64, 32],
        description="MLP layer sizes for NCF",
    )
    NCF_DROPOUT: float = Field(default=0.2, description="Dropout rate for NCF")

    # Summarisation
    FLAN_MODEL: str = Field(
        default="google/flan-t5-large",
        description="FLAN-T5 model for summarisation",
    )
    FLAN_DEVICE: Literal["cuda", "cpu"] = Field(
        default="cuda",
        description="Device for FLAN model",
    )
    MAX_INPUT_TOKENS: int = Field(
        default=900,
        description="Max input tokens for summarisation",
    )
    SUMMARY_BATCH_SIZE: int = Field(
        default=5,
        description="Chunks per map batch for map-reduce",
    )

    # RAG
    RAG_LLM_MODEL: str = Field(
        default="gpt-4o-mini",
        description="LLM model for RAG Q&A",
    )
    RAG_SIMILARITY_THRESHOLD: float = Field(
        default=0.60,
        description="Minimum similarity threshold for RAG retrieval",
    )
    RAG_TOP_K: int = Field(default=5, description="Top-K chunks to retrieve for RAG")
    RAG_MAX_CONTEXT_TOKENS: int = Field(
        default=3800,
        description="Max tokens in RAG context before budget guard triggers",
    )

    # Caching
    REDIS_TTL_REC: int = Field(
        default=300,
        description="TTL for recommendation cache (seconds)",
    )
    REDIS_TTL_SUMMARY: int = Field(
        default=86400,
        description="TTL for summary cache (seconds)",
    )
    REDIS_TTL_SEARCH: int = Field(
        default=60,
        description="TTL for search cache (seconds)",
    )

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Rate limiting
    REC_RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Max recommendation requests per user per minute",
    )
    SUMMARISE_MAX_CONCURRENT: int = Field(
        default=4,
        description="Max concurrent summarisation jobs (GPU queue limit)",
    )

    # OpenAI
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()