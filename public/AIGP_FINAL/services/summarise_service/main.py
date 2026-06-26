"""
services/summarise_service/main.py
FastAPI service for book summarisation.
"""
import asyncio
from typing import Optional

from pydantic import BaseModel

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
import structlog

from services.summarise_service.summariser import Summariser, SummaryType
from services.summarise_service.map_reduce import map_reduce_summarise
from services.summarise_service.mindmap_builder import get_mindmap_builder
from shared.redis_client import RedisClient
from shared.config import settings

log = structlog.get_logger(__name__)

app = FastAPI(
    title="Summarisation Service",
    description="Book summarisation with FLAN-T5 and mind-map generation",
    version="1.0.0",
)

redis_client = RedisClient()


async def get_redis() -> RedisClient:
    await redis_client.connect()
    return redis_client


async def check_gpu_queue(redis: RedisClient) -> bool:
    """Check if GPU queue has capacity."""
    key = "summarise:active"

    try:
        count = await redis.client.get(key)
        if count is None:
            return True

        return int(count) < settings.SUMMARISE_MAX_CONCURRENT

    except Exception:
        return True


async def increment_gpu_queue(redis: RedisClient) -> None:
    """Increment active job counter."""
    key = "summarise:active"
    await redis.client.incr(key)


async def decrement_gpu_queue(redis: RedisClient) -> None:
    """Decrement active job counter."""
    key = "summarise:active"
    await redis.client.decr(key)


class SummariseRequest(BaseModel):
    isbn: str
    summary_type: SummaryType = SummaryType.SHORT
    include_mindmap: bool = False


class SummariseResponse(BaseModel):
    isbn: str
    summary_type: str
    summary: str
    mindmap: Optional[dict] = None


class ProgressResponse(BaseModel):
    isbn: str
    done: int
    total: int
    percent: float


@app.post("/summarise", response_model=SummariseResponse)
async def summarise(
    req: SummariseRequest,
    background: BackgroundTasks,
    redis: RedisClient = Depends(get_redis),
) -> SummariseResponse:
    """Generate book summary with optional mind-map."""
    if not await check_gpu_queue(redis):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "AI-004",
                "message": "GPU queue full, retry in 30 seconds",
            },
        )

    cache_key = f"summary:{req.isbn}:{req.summary_type.value}"

    cached = await redis.get(cache_key)
    if cached:
        import orjson

        data = orjson.loads(cached)
        return SummariseResponse(**data, summary_type=req.summary_type.value)

    await increment_gpu_queue(redis)

    try:
        summary = await map_reduce_summarise(req.isbn, req.summary_type)

        response_data = {
            "isbn": req.isbn,
            "summary_type": req.summary_type.value,
            "summary": summary,
        }

        if req.include_mindmap:
            mindmap_builder = get_mindmap_builder()
            mindmap = await asyncio.to_thread(mindmap_builder.build, summary, req.isbn)
            response_data["mindmap"] = mindmap

        import orjson

        await redis.setex(cache_key, settings.REDIS_TTL_SUMMARY, orjson.dumps(response_data).decode("utf-8"))

        return SummariseResponse(**response_data)

    except Exception as e:
        log.error("summarise.failed", isbn=req.isbn, error=str(e))
        raise HTTPException(status_code=500, detail={"error": "AI-004", "message": str(e)})

    finally:
        await decrement_gpu_queue(redis)


@app.get("/summarise/{isbn}/progress", response_model=ProgressResponse)
async def get_progress(
    isbn: str,
    redis: RedisClient = Depends(get_redis),
) -> ProgressResponse:
    """Get summarisation job progress."""
    key = f"summary:progress:{isbn}"

    data = await redis.get_json(key)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "AI-002", "message": f"No job in progress for ISBN {isbn}"},
        )

    done = data.get("done", 0)
    total = data.get("total", 1)
    percent = (done / total * 100) if total > 0 else 0.0

    return ProgressResponse(isbn=isbn, done=done, total=total, percent=round(percent, 1))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "summarise-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.summarise_service.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )