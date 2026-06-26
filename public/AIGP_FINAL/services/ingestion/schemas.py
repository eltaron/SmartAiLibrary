"""
services/ingestion/schemas.py
Pydantic schemas for ingestion service requests and responses.
"""
from typing import Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Request model for book ingestion."""

    isbn: str = Field(..., description="ISBN of the book", min_length=10, max_length=13)
    title: str = Field(..., description="Title of the book", min_length=1, max_length=500)
    author: str = Field(..., description="Author of the book", min_length=1, max_length=300)


class IngestResponse(BaseModel):
    """Response model for ingestion job submission."""

    job_id: str = Field(..., description="Unique job identifier")
    isbn: str = Field(..., description="ISBN of the ingested book")
    status: str = Field(..., description="Job status", pattern="^(queued|processing|done|failed)$")


class IngestStatusResponse(BaseModel):
    """Response model for ingestion job status."""

    isbn: str = Field(..., description="ISBN of the book")
    status: str = Field(..., description="Job status")
    chunk_count: Optional[int] = Field(None, description="Number of chunks processed")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")


class ErrorResponse(BaseModel):
    """Response model for error responses."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")