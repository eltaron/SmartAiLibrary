"""
training/pipelines/biweekly_hard_negatives.py
Bi-weekly hard negative mining for search fine-tuning.
"""
import asyncio
from datetime import timedelta
from collections import defaultdict

import structlog

from shared.db import db_manager
from shared.config import settings

log = structlog.get_logger(__name__)


async def find_zero_click_searches() -> list[dict]:
    """Find searches with zero clicks in past 2 weeks."""
    from sqlalchemy import text

    cutoff = datetime.utcnow() - timedelta(days=14)

    async with db_manager.session() as session:
        result = await session.execute(
            text("""
                SELECT s.query, s.isbn, s.created_at
                FROM search_queries s
                LEFT JOIN reading_events re ON s.user_id = re.user_id
                    AND re.isbn = s.isbn
                    AND re.created_at > s.created_at
                    AND re.created_at < s.created_at + interval '60 seconds'
                WHERE s.created_at > :cutoff
                AND re.id IS NULL
            """),
            {"cutoff": cutoff},
        )

        rows = result.fetchall()
        return [{"query": r[0], "isbn": r[1]} for r in rows]


async def get_top_results(isbn: str, top_k: int = 10) -> list[str]:
    """Get top-K search results for an ISBN."""
    from services.search_service.main import app
    from services.search_service.encoder import get_encoder
    from services.search_service.reranker import get_reranker

    encoder = get_encoder()
    reranker = get_reranker()

    query = f"find book {isbn}"
    vec = encoder.encode(query).tolist()

    from shared.pinecone_client import pinecone_client

    matches = await pinecone_client.query_global(vec, top_k=top_k)
    return [m["metadata"]["isbn"] for m in matches if "isbn" in m["metadata"]]


async def run_hard_negative_mining():
    """Run bi-weekly hard negative mining."""
    log.info("hard_negatives.start")

    searches = await find_zero_click_searches()

    if len(searches) < 100:
        log.warning("hard_negatives.insufficient", count=len(searches))
        return

    negatives = []
    seen = set()

    for search in searches[:500]:
        if len(negatives) >= 500:
            break

        try:
            top_results = await get_top_results(search["isbn"], top_k=10)
            if top_results:
                key = (search["query"], top_results[0])
                if key not in seen:
                    seen.add(key)
                    negatives.append({
                        "query": search["query"],
                        "positive": search["isbn"],
                        "negative": top_results[0],
                    })
        except Exception as e:
            log.warning("hard_negatives.skip", error=str(e))

    if len(negatives) >= 500:
        log.info("hard_negatives.trigger_finetune", count=len(negatives))

        import json

        with open("training/datasets/search_pairs.json", "r") as f:
            existing = json.load(f)

        existing.extend(negatives)

        with open("training/datasets/search_pairs.json", "w") as f:
            json.dump(existing, f)

        import subprocess

        subprocess.run([
            "python", "training/biencoder_finetune.py",
            "--epochs", "1",
        ])


if __name__ == "__main__":
    from datetime import datetime

    asyncio.run(run_hard_negative_mining())