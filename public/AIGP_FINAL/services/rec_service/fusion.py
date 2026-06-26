"""
services/rec_service/fusion.py
Hybrid fusion logic combining CF and CBF scores.
"""
from typing import Literal, Optional

import structlog

from shared.config import settings

log = structlog.get_logger(__name__)

UserTier = Literal["new", "returning", "power"]

ALPHA_BY_TIER: dict[UserTier, float] = {
    "new": 0.10,
    "returning": 0.55,
    "power": 0.80,
}


def get_user_tier(interaction_count: int) -> UserTier:
    """
    Determine user tier based on interaction count.

    Args:
        interaction_count: Number of user interactions

    Returns:
        User tier: "new", "returning", or "power"
    """
    if interaction_count < 5:
        return "new"
    elif interaction_count < 50:
        return "returning"
    return "power"


def fuse_scores(
    cf_scores: dict[str, float],
    cbf_scores: dict[str, float],
    interaction_count: int,
    top_k: int = 10,
) -> list[dict]:
    """
    Fuse collaborative filtering and content-based filtering scores.

    Weighted linear blend: final = alpha * CF + (1 - alpha) * CBF
    Alpha is determined by user tier based on interaction count.

    Args:
        cf_scores: Dict of ISBN -> CF score (0-1)
        cbf_scores: Dict of ISBN -> CBF score (0-1)
        interaction_count: Number of user interactions
        top_k: Number of top results to return

    Returns:
        List of dicts with isbn and score, sorted by score descending

    Raises:
        ValueError: If both cf_scores and cbf_scores are empty
    """
    if not cf_scores and not cbf_scores:
        raise ValueError("AI-003: insufficient signal for fusion")

    tier = get_user_tier(interaction_count)
    alpha = ALPHA_BY_TIER[tier]
    beta = 1.0 - alpha

    log.info("fusion.tier", tier=tier, alpha=alpha, beta=beta)

    all_isbns = set(cf_scores.keys()) | set(cbf_scores.keys())

    fused_scores: dict[str, float] = {}
    for isbn in all_isbns:
        cf = cf_scores.get(isbn, 0.0)
        cbf = cbf_scores.get(isbn, 0.0)
        fused_scores[isbn] = alpha * cf + beta * cbf

    ranked = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

    return [
        {"isbn": isbn, "score": round(score, 4)}
        for isbn, score in ranked[:top_k]
    ]


def normalise_scores(scores: dict[str, float]) -> dict[str, float]:
    """
    Normalize scores to [0, 1] range using min-max scaling.

    Args:
        scores: Dict of ISBN -> score

    Returns:
        Normalized scores
    """
    if not scores:
        return {}

    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)

    if max_val - min_val == 0:
        return {k: 0.5 for k in scores}

    return {
        k: (v - min_val) / (max_val - min_val)
        for k, v in scores.items()
    }


def fuse_with_tier_override(
    cf_scores: dict[str, float],
    cbf_scores: dict[str, float],
    interaction_count: int,
    top_k: int = 10,
    override_tier: Optional[UserTier] = None,
) -> list[dict]:
    """
    Fuse scores with optional tier override (for testing).

    Args:
        cf_scores: CF scores
        cbf_scores: CBF scores
        interaction_count: User interaction count
        top_k: Number of results
        override_tier: Override the computed tier

    Returns:
        List of fused results
    """
    if not cf_scores and not cbf_scores:
        raise ValueError("AI-003: insufficient signal for fusion")

    tier = override_tier or get_user_tier(interaction_count)
    alpha = ALPHA_BY_TIER[tier]
    beta = 1.0 - alpha

    all_isbns = set(cf_scores.keys()) | set(cbf_scores.keys())
    fused = {
        isbn: alpha * cf_scores.get(isbn, 0.0) + beta * cbf_scores.get(isbn, 0.0)
        for isbn in all_isbns
    }

    ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)
    return [{"isbn": isbn, "score": round(score, 4)} for isbn, score in ranked[:top_k]]