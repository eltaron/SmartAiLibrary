"""
services/rec_service/main.py
FastAPI service for book recommendations.
"""
import hashlib
import json
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
import structlog

from services.rec_service.models.ncf import NeuralCF, load_model
from services.rec_service.models.cbf import get_cbf
from services.rec_service.fusion import fuse_scores, get_user_tier
from services.rec_service.schemas import (
    RecRequest,
    RecResponse,
    ColdStartRequest,
    ColdStartResponse,
    HealthResponse,
    ErrorResponse,
)
from shared.redis_client import RedisClient
from shared.config import settings
from shared.db import db_manager

log = structlog.get_logger(__name__)

app = FastAPI(
    title="Recommendation Service",
    description="Personalised book recommendations using NCF + CBF hybrid",
    version="1.0.0",
)

redis_client = RedisClient()

NCF_MODEL: Optional[NeuralCF] = None

try:
    import torch

    NCF_MODEL = NeuralCF(n_users=100_000, n_items=50_000)
    model_path = "/models/ncf_weights.pt"
    try:
        NCF_MODEL.load_state_dict(torch.load(model_path, map_location="cpu"))
        log.info("ncf_model.loaded", path=model_path)
    except FileNotFoundError:
        log.warning("ncf_model.not_found", path=model_path)
except Exception as e:
    log.warning("ncf_model.init_failed", error=str(e))


async def get_redis() -> RedisClient:
    """Dependency for Redis client."""
    await redis_client.connect()
    return redis_client


async def get_db_session():
    """Dependency for database session."""
    async with db_manager.session() as session:
        yield session


def check_rate_limit(user_id: int, redis: RedisClient) -> bool:
    """
    Check if user has exceeded rate limit (60 requests per minute).

    Uses Redis sliding window counter.
    """
    import time

    key = f"rate:rec:{user_id}"
    now = int(time.time())
    window = 60

    redis.client.zadd(key, {str(now): now})
    redis.client.zremrangebyscore(key, 0, now - window)
    redis.client.expire(key, window + 1)

    count = redis.client.zcard(key)

    return count <= settings.REC_RATE_LIMIT_PER_MINUTE


@app.post(
    "/recommendations",
    response_model=RecResponse,
    responses={
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
)
async def get_recommendations(
    req: RecRequest,
    redis: RedisClient = Depends(get_redis),
) -> RecResponse:
    """
    Get personalized book recommendations for a user.

    Uses hybrid NCF + CBF fusion based on user tier.
    """
    if not check_rate_limit(req.user_id, redis):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "AI-004", "message": "Rate limit exceeded"},
            headers={"Retry-After": "60"},
        )

    cache_key = f"rec:{req.user_id}:{req.top_k}"
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        log.info("rec.cache_hit", user_id=req.user_id)
        return RecResponse(**cached_data)

    from sqlalchemy import text

    async with db_manager.session() as session:
        result = await session.execute(
            text("""
                SELECT isbn FROM reading_events
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 100
            """),
            {"user_id": req.user_id},
        )
        interactions = [row[0] for row in result.fetchall()]

    if not interactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "AI-003", "message": "User has no interactions"},
        )

    interaction_count = len(interactions)

    cf_scores: dict[str, float] = {}
    if NCF_MODEL is not None:
        import torch

        user_tensor = torch.tensor([req.user_id] * 50000)
        item_tensor = torch.tensor(list(range(50000)))

        with torch.no_grad():
            cf_raw = NCF_MODEL(user_tensor, item_tensor).numpy()

        cf_scores = {str(i): float(s) for i, s in enumerate(cf_raw)}

    cbf = get_cbf()
    last_isbn = interactions[0]
    cbf_results = cbf.similar_books(last_isbn, top_k=50)
    cbf_scores = {r["isbn"]: r["score"] for r in cbf_results}

    results = fuse_scores(cf_scores, cbf_scores, interaction_count, req.top_k)

    tier = get_user_tier(interaction_count)

    response = RecResponse(
        user_id=req.user_id,
        recommendations=results,
        source_tier=tier,
    )

    await redis.setex(cache_key, settings.REDIS_TTL_REC, json.dumps(response.model_dump()))

    return response


@app.get(
    "/recommendations/cold-start",
    response_model=ColdStartResponse,
)
async def cold_start_recommendations(
    genre: Optional[str] = Query(None, description="Genre filter"),
    limit: int = Query(10, ge=1, le=50),
    redis: RedisClient = Depends(get_redis),
) -> ColdStartResponse:
    """
    Get cold-start recommendations for new users with no reading history.

    Uses CBF only via similar_to_query() using genre centroid.
    """
    cache_key = f"rec:cold:{genre or 'all'}:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return ColdStartResponse(**cached_data)

    cbf = get_cbf()

    if genre:
        query_vector = cbf.get_genre_centroid(genre)
    else:
        import numpy as np

        query_vector = np.zeros(768)

    results = cbf.similar_to_query(query_vector, top_k=limit)

    response = ColdStartResponse(
        recommendations=results,
        source="cold-start-cbf",
    )

    await redis.setex(cache_key, settings.REDIS_TTL_REC, json.dumps(response.model_dump()))

    return response


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", service="rec-service")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error("unhandled.exception", path=request.url.path, error=str(exc))
    return Response(
        content=json.dumps({"error": "AI-004", "message": "Internal server error"}),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.rec_service.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )