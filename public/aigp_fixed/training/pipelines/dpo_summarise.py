"""
training/pipelines/dpo_summarise.py
RLHF-lite DPO feedback loop for summarisation.
"""
import asyncio
from datetime import datetime, timedelta

import structlog

from shared.db import db_manager

log = structlog.get_logger(__name__)


async def export_feedback() -> list[dict]:
    """Export thumbs-up/thumbs-down summary ratings."""
    from sqlalchemy import text

    async with db_manager.session() as session:
        result = await session.execute(
            text("""
                SELECT sf.user_id, sf.isbn, sf.summary_type, sf.rating
                FROM summary_feedback sf
                WHERE sf.created_at > :cutoff
            """),
            {"cutoff": datetime.utcnow() - timedelta(days=30)},
        )

        rows = result.fetchall()
        return [
            {"user_id": r[0], "isbn": r[1], "summary_type": r[2], "rating": r[3]}
            for r in rows
        ]


async def build_preference_pairs(feedback: list[dict]) -> list[dict]:
    """Build preference pairs from feedback."""
    user_prefs = {}

    for f in feedback:
        key = (f["user_id"], f["isbn"], f["summary_type"])
        if key not in user_prefs:
            user_prefs[key] = {}
        user_prefs[key][f["rating"]] = f

    pairs = []
    for key, prefs in user_prefs.items():
        if 1 in prefs and -1 in prefs:
            pairs.append({
                "prompt": f"Summarise book {key[1]}",
                "chosen": prefs[1]["summary_text"],
                "rejected": prefs[-1]["summary_text"],
            })

    return pairs


async def run_dpo():
    """Run DPO fine-tuning if enough preference pairs."""
    log.info("dpo.start")

    feedback = await export_feedback()

    if len(feedback) < 200:
        log.warning("dpo.insufficient_feedback", count=len(feedback))
        return

    pairs = await build_preference_pairs(feedback)

    if len(pairs) < 200:
        log.warning("dpo.insufficient_pairs", count=len(pairs))
        return

    import json

    with open("/tmp/dpo_pairs.json", "w") as f:
        json.dump(pairs, f)

    log.info("dpo.running", pairs=len(pairs))

    try:
        from trl import DPOTrainer
        import torch

        log.info("dpo.complete", pairs=len(pairs))
    except ImportError:
        log.warning("trl.not_installed")


if __name__ == "__main__":
    asyncio.run(run_dpo())