"""
services/rec_service/schemas.py
Pydantic schemas for recommendation service.
"""
from typing import Optional

from pydantic import BaseModel, Field


class RecRequest(BaseModel):
    """Request model for recommendations."""

    user_id: str = Field(..., description="User UUID or external_id")
    top_k: int = Field(10, description="Number of recommendations", ge=1, le=50)


class RecResponse(BaseModel):
    """Response model for recommendations."""

    user_id: str
    recommendations: list[dict] = Field(..., description="List of recommended books")
    source_tier: str = Field(..., description="User tier used for fusion")


class ColdStartRequest(BaseModel):
    """Request model for cold-start recommendations."""

    genre: Optional[str] = Field(None, description="Genre filter")
    limit: int = Field(10, description="Number of results", ge=1, le=50)


class ColdStartResponse(BaseModel):
    """Response model for cold-start recommendations."""

    recommendations: list[dict]
    source: str = "cold-start-cbf"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    message: str