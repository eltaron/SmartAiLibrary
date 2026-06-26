"""
services/ingestion/main.py
FastAPI service for book ingestion pipeline.
"""
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
import structlog

from services.ingestion.extractor import extract_text
from services.ingestion.chunker import chunk_page
from services.ingestion.schemas import (
    ErrorResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    IngestStatusResponse,
)
from shared.redis_client import RedisClient
from shared.kafka_producer import kafka_producer
from shared.config import settings

log = structlog.get_logger(__name__)

app = FastAPI(
    title="Ingestion Service",
    description="Book ingestion and text processing pipeline",
    version="1.0.0",
)

redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency for Redis client."""
    await redis_client.connect()
    return redis_client


async def process_book(
    isbn: str,
    title: str,
    author: str,
    file_path: Path,
    redis: RedisClient,
) -> int:
    """
    Background task to process a book through the ingestion pipeline.

    Pipeline: extract → clean → chunk → Kafka

    Args:
        isbn: ISBN of the book
        title: Title of the book
        author: Author of the book
        file_path: Path to the uploaded file
        redis: Redis client for state management

    Returns:
        Total number of chunks produced
    """
    try:
        status_key = f"ingest:status:{isbn}"

        await redis.set_json(
            status_key,
            settings.REDIS_TTL_REC,
            {"isbn": isbn, "status": "processing", "chunk_count": 0},
        )

        total_chunks = 0

        for page in extract_text(file_path, isbn):
            chunks = chunk_page(page.text, isbn, page.page_num)

            for chunk in chunks:
                chunk_data = {
                    "chunk_id": chunk.chunk_id,
                    "isbn": chunk.isbn,
                    "page_num": chunk.page_num,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                    "title": title,
                    "author": author,
                    "genre_tags": [],
                }

                log.info(
                    "chunk.created",
                    isbn=isbn,
                    chunk_id=chunk.chunk_id,
                    page=page.page_num,
                    tokens=chunk.token_count,
                )

                await kafka_producer.send(
                    topic=settings.KAFKA_CHUNKS_TOPIC,
                    value=chunk_data,
                    key=isbn,
                )

                total_chunks += 1

        await redis.set_json(
            status_key,
            settings.REDIS_TTL_REC,
            {"isbn": isbn, "status": "done", "chunk_count": total_chunks},
        )

        log.info("ingest.completed", isbn=isbn, total_chunks=total_chunks)

        return total_chunks

    except Exception as e:
        log.error("ingest.failed", isbn=isbn, error=str(e))
        await redis.set_json(
            f"ingest:status:{isbn}",
            settings.REDIS_TTL_REC,
            {"isbn": isbn, "status": "failed", "chunk_count": 0, "error": str(e)},
        )
        raise


@app.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def ingest_book(
    background_tasks: BackgroundTasks,
    redis: RedisClient = Depends(get_redis),
    file: UploadFile = File(..., description="Book file (PDF or ePub)"),
    isbn: str = Form(..., description="ISBN of the book"),
    title: str = Form(..., description="Title of the book"),
    author: str = Form(..., description="Author of the book"),
    api_key: str | None = Form(default=None, description="API key for authentication"),
) -> IngestResponse:
    """
    Ingest a new book into the library.

    Accepts PDF or ePub files. The file is processed asynchronously
    in a background task.

    Args:
        file: Uploaded book file
        isbn: ISBN of the book
        title: Title of the book
        author: Author of the book
        api_key: API key for authentication

    Returns:
        Job ID and status
    """
    if settings.INGEST_API_KEY and api_key != settings.INGEST_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "AI-001", "message": "Invalid API key"},
        )

    file_path = Path(f"/tmp/{isbn}_{file.filename}")

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

    except Exception as e:
        log.error("file.save.failed", isbn=isbn, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "AI-002", "message": f"Failed to save file: {e}"},
        )

    job_id = str(uuid.uuid4())

    await redis.set_json(
        f"ingest:status:{isbn}",
        settings.REDIS_TTL_REC,
        {"isbn": isbn, "status": "queued", "chunk_count": 0},
    )

    background_tasks.add_task(process_book, isbn, title, author, file_path, redis)

    log.info("ingest.queued", isbn=isbn, job_id=job_id, title=title, author=author)

    return IngestResponse(job_id=job_id, isbn=isbn, status="queued")


@app.get(
    "/ingest/{isbn}/status",
    response_model=IngestStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_ingest_status(
    isbn: str,
    redis: RedisClient = Depends(get_redis),
) -> IngestStatusResponse:
    """
    Get the status of an ingestion job.

    Args:
        isbn: ISBN of the book

    Returns:
        Current status and chunk count
    """
    status_key = f"ingest:status:{isbn}"

    status_data = await redis.get_json(status_key)

    if status_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "AI-002", "message": f"No ingestion job found for ISBN {isbn}"},
        )

    return IngestStatusResponse(
        isbn=status_data.get("isbn", isbn),
        status=status_data.get("status", "unknown"),
        chunk_count=status_data.get("chunk_count"),
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", service="ingestion")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for all unhandled exceptions."""
    log.error("unhandled.exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "AI-004",
            "message": "Internal server error",
            "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else None,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.ingestion.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )