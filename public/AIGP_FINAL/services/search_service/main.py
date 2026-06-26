"""
services/search_service/main.py
FastAPI service for semantic search.
"""
import asyncio
import hashlib
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import structlog

from services.search_service.encoder import get_encoder
from services.search_service.reranker import get_reranker
from shared.pinecone_client import pinecone_client
from shared.redis_client import RedisClient
from shared.config import settings

log = structlog.get_logger(__name__)

app = FastAPI(
    title="Search Service",
    description="Semantic search with bi-encoder + cross-encoder reranking",
    version="1.0.0",
)

encoder = get_encoder()
reranker = get_reranker()
redis_client = RedisClient()

ANN_TOP_K = settings.ANN_TOP_K
FINAL_TOP_K = settings.FINAL_TOP_K


class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(10, description="Number of results", ge=1, le=50)
    filter_genres: Optional[list[str]] = Field(None, description="Genre filter")


class SearchResult(BaseModel):
    """Single search result."""

    isbn: str
    title: str
    score: float
    page_ref: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


def _get_cache_key(query: str, top_k: int, genres: Optional[list[str]]) -> str:
    """Generate cache key from query params."""
    content = f"{query}:{top_k}:{sorted(genres) if genres else []}"
    return f"search:{hashlib.sha256(content.encode()).hexdigest()}"


@app.post("/search", response_model=list[SearchResult])
async def semantic_search(req: SearchRequest) -> list[SearchResult]:
    """Semantic search with caching."""
    cache_key = _get_cache_key(req.query, req.top_k, req.filter_genres)

    await redis_client.connect()
    cached = await redis_client.get(cache_key)

    if cached:
        import orjson
        results = orjson.loads(cached)
        log.info("search.cache_hit", query=req.query[:50])
        return [SearchResult(**r) for r in results]

    start_time = time.monotonic()

    query_vec = (await asyncio.to_thread(encoder.encode, req.query)).tolist()

    pinecone_filter = {"doc_type": {"$eq": "chunk"}}
    if req.filter_genres:
        pinecone_filter["genre"] = {"$in": req.filter_genres}

    try:
        ann_candidates = await pinecone_client.query_global(
            vector=query_vec,
            top_k=min(ANN_TOP_K, req.top_k * 5),
            filter=pinecone_filter,
            namespace=settings.PINECONE_GLOBAL_NAMESPACE,
        )
    except Exception as e:
        log.error("pinecone.query.failed", error=str(e))
        if ANN_TOP_K == 0:
            return []
        raise HTTPException(status_code=500, detail=f"AI-004: Search failed: {e}")

    if not ann_candidates:
        return []

    reranked = await asyncio.to_thread(reranker.rerank, req.query, ann_candidates)

    elapsed = (time.monotonic() - start_time) * 1000
    log.info("search.latency", query=req.query[:50], latency_ms=round(elapsed, 1))

    results = [
        SearchResult(
            isbn=r.get("metadata", {}).get("isbn", ""),
            title=r.get("metadata", {}).get("title", ""),
            score=round(r.get("rerank_score", r.get("score", 0.0)), 4),
            page_ref=r.get("metadata", {}).get("page_num"),
        )
        for r in reranked[: req.top_k]
    ]

    if results:
        import orjson

        await redis_client.setex(
            cache_key,
            settings.REDIS_TTL_SEARCH,
            orjson.dumps([r.model_dump() for r in results]),
        )

    return results


@app.post("/search/similar/{isbn}")
async def similar_books(
    isbn: str,
    top_k: int = Query(10, ge=1, le=50),
) -> list[SearchResult]:
    """Find books similar to a given ISBN."""
    cache_key = f"similar:{isbn}:{top_k}"

    await redis_client.connect()
    cached = await redis_client.get(cache_key)

    if cached:
        import orjson
        results = orjson.loads(cached)
        return [SearchResult(**r) for r in results]

    try:
        from services.rec_service.models.cbf import get_cbf

        cbf = get_cbf()
        cbf_results = await cbf.similar_books(isbn, top_k=top_k)

        results = [
            SearchResult(
                isbn=r["isbn"],
                title=r.get("title", ""),
                score=round(r["score"], 4),
                page_ref=None,
            )
            for r in cbf_results
        ]

        if results:
            import orjson

            await redis_client.setex(
                cache_key,
                settings.REDIS_TTL_SEARCH,
                orjson.dumps([r.model_dump() for r in results]),
            )

        return results

    except Exception as e:
        log.error("similar.failed", isbn=isbn, error=str(e))
        raise HTTPException(status_code=500, detail=f"AI-004: {e}")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", service="search-service")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error("unhandled.exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "AI-004", "message": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.search_service.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
    )