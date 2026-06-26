"""
training/pipelines/monthly_ncf_retrain.py
Monthly NCF re-training pipeline with evaluation and promotion.
"""
import asyncio
import subprocess
from datetime import datetime, timedelta

import structlog

log = structlog.get_logger(__name__)


async def export_interactions(days: int = 90) -> list[dict]:
    """Export reading events and ratings from PostgreSQL."""
    from shared.db import db_manager
    from sqlalchemy import text

    await db_manager.init()

    cutoff = datetime.utcnow() - timedelta(days=days)

    async with db_manager.session() as session:
        result = await session.execute(
            text("""
                SELECT re.user_id, re.isbn, re.event_type,
                       CASE WHEN re.event_type IN ('read_start', 'bookmark')
                                 OR r.score >= 4 THEN 1 ELSE 0 END as label
                FROM reading_events re
                LEFT JOIN ratings r ON re.user_id = r.user_id AND re.isbn = r.isbn
                WHERE re.created_at > :cutoff
            """),
            {"cutoff": cutoff},
        )

        rows = result.fetchall()
        return [
            {"user_id": r[0], "isbn": r[1], "event_type": r[2], "label": r[3]}
            for r in rows
        ]


async def run_retrain():
    """Run monthly re-training."""
    log.info("monthly_retrain.start")

    interactions = await export_interactions(90)

    if len(interactions) < 100:
        log.warning("monthly_retrain.insufficient_data", count=len(interactions))
        return

    import json

    with open("/tmp/interactions.json", "w") as f:
        json.dump(interactions, f)

    result = subprocess.run(
        [
            "python", "training/ncf_train.py",
            "--epochs", "10",
            "--output-path", "/models/ncf_candidate.pt",
            "--data-path", "/tmp/interactions.json",
        ],
        capture_output=True,
    )

    if result.returncode != 0:
        log.error("monthly_retrain.failed", error=result.stderr.decode())
        return

    eval_result = subprocess.run(
        ["python", "eval/run_eval.py", "--service", "rec", "--model-url", "http://localhost:8001"],
        capture_output=True,
    )

    import json as json_mod

    metrics = json_mod.loads(eval_result.stdout.decode())
    precision = metrics.get("precision@10", 0)

    if precision >= 0.42:
        log.info("monthly_retrain.promoted", precision=precision)

        try:
            import mlflow
            mlflow.register_model("/models/ncf_candidate.pt", "ncf_production")
        except Exception as e:
            log.warning("mlflow.register.failed", error=str(e))
    else:
        log.warning("monthly_retrain.not_promoted", precision=precision)


if __name__ == "__main__":
    asyncio.run(run_retrain())