"""
services/rec_service/main.py
FastAPI service for book recommendations.
"""
import asyncio
import json
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
import structlog

from services.rec_service.models.ncf import NeuralCF
from services.rec_service.models.cbf import get_cbf
from services.rec_service.fusion import fuse_scores, get_user_tier
from services.rec_service.schemas import (
    RecRequest,
    RecResponse,
    ColdStartResponse,
    HealthResponse,
    ErrorResponse,
)
from shared.redis_client import RedisClient
from shared.config import settings
from shared.db import db_manager
from services.rec_service.mappings import (
    REVERSE_ITEM_MAP,
    ITEM_ID_MAP,
    load_ncf_mappings,
    resolve_user_index,
)

log = structlog.get_logger(__name__)

app = FastAPI(
    title="Recommendation Service",
    description="Personalised book recommendations using NCF + CBF hybrid",
    version="1.0.0",
)

redis_client = RedisClient()

from services.rec_service.mappings import N_ITEMS, N_USERS

NCF_MODEL: Optional[NeuralCF] = None


def _load_ncf_model() -> None:
    """Load NCF weights and ID mappings from configured paths."""
    global NCF_MODEL

    load_ncf_mappings()
    model_path = Path(settings.NCF_MODEL_PATH)
    n_users = N_USERS or 100_000
    n_items = N_ITEMS or 50_000

    try:
        import torch

        NCF_MODEL = NeuralCF(n_users=n_users, n_items=n_items)
        if model_path.exists():
            NCF_MODEL.load_state_dict(torch.load(str(model_path), map_location="cpu"))
            log.info("ncf_model.loaded", path=str(model_path), n_users=n_users, n_items=n_items)
        else:
            log.warning("ncf_model.not_found", path=str(model_path))
            NCF_MODEL = None
    except Exception as e:
        log.warning("ncf_model.init_failed", error=str(e))
        NCF_MODEL = None


_load_ncf_model()


async def get_redis() -> RedisClient:
    """Dependency for Redis client."""
    await redis_client.connect()
    return redis_client


async def resolve_user_uuid(user_id: str) -> UUID:
    """Resolve external_id or UUID string to internal user UUID."""
    from sqlalchemy import text

    try:
        parsed = UUID(user_id)
        user_filter = "u.id = :user_id"
        params = {"user_id": parsed}
    except ValueError:
        user_filter = "u.external_id = :user_id"
        params = {"user_id": user_id}

    async with db_manager.session() as session:
        result = await session.execute(
            text(f"SELECT u.id FROM users u WHERE {user_filter} LIMIT 1"),
            params,
        )
        row = result.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "AI-003", "message": f"User not found: {user_id}"},
        )

    return row[0]


async def check_rate_limit(user_id: str, redis: RedisClient) -> bool:
    """
    Check if user has exceeded rate limit (60 requests per minute).

    Uses Redis sliding window counter with unique members per request.
    """
    import time
    from uuid import uuid4

    key = f"rate:rec:{user_id}"
    now = int(time.time())
    window = 60

    await redis.client.zadd(key, {f"{now}:{uuid4()}": now})
    await redis.client.zremrangebyscore(key, 0, now - window)
    await redis.client.expire(key, window + 1)

    count = await redis.client.zcard(key)

    return count <= settings.REC_RATE_LIMIT_PER_MINUTE


def _score_cf(user_key: str) -> dict[str, float]:
    """Score all known items for a user using NCF, returning ISBN -> score."""
    if NCF_MODEL is None or not ITEM_ID_MAP:
        return {}

    user_idx = resolve_user_index(user_key)
    if user_idx is None:
        return {}

    import torch

    item_indices = sorted(REVERSE_ITEM_MAP.keys())
    if not item_indices:
        return {}

    user_tensor = torch.tensor([user_idx] * len(item_indices))
    item_tensor = torch.tensor(item_indices)

    with torch.no_grad():
        cf_raw = NCF_MODEL(user_tensor, item_tensor).numpy()

    return {
        REVERSE_ITEM_MAP[item_idx]: float(score)
        for item_idx, score in zip(item_indices, cf_raw)
        if item_idx in REVERSE_ITEM_MAP
    }


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
    if not await check_rate_limit(req.user_id, redis):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "AI-004", "message": "Rate limit exceeded"},
            headers={"Retry-After": "60"},
        )

    user_uuid = await resolve_user_uuid(req.user_id)
    user_key = str(user_uuid)

    cache_key = f"rec:{user_key}:{req.top_k}"
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
            {"user_id": user_uuid},
        )
        interactions = [row[0] for row in result.fetchall()]

    if not interactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "AI-003", "message": "User has no interactions"},
        )

    interaction_count = len(interactions)

    cf_scores = await asyncio.to_thread(_score_cf, user_key)

    cbf = get_cbf()
    last_isbn = interactions[0]
    cbf_results = await cbf.similar_books(last_isbn, top_k=50)
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
        query_vector = await cbf.get_genre_centroid(genre)
    else:
        import numpy as np

        query_vector = np.full(768, 1e-6, dtype=np.float32)

    results = await cbf.similar_to_query(query_vector, top_k=limit)

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
