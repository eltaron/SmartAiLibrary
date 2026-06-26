"""
eval/rec_eval.py
Recommendation engine evaluation metrics.
"""
from typing import Callable

import numpy as np
import structlog

log = structlog.get_logger(__name__)


def precision_at_k(recommended: list, relevant: set, k: int) -> float:
    """
    Fraction of top-K recommendations that are relevant.

    Args:
        recommended: List of recommended ISBNs (ordered)
        relevant: Set of relevant ISBNs
        k: Cutoff position

    Returns:
        Precision@K score
    """
    if k == 0:
        return 0.0

    top_k = set(recommended[:k])
    return len(top_k & relevant) / k


def recall_at_k(recommended: list, relevant: set, k: int) -> float:
    """
    Fraction of relevant items found in top-K.

    Args:
        recommended: List of recommended ISBNs
        relevant: Set of relevant ISBNs
        k: Cutoff position

    Returns:
        Recall@K score
    """
    if not relevant:
        return 0.0

    top_k = set(recommended[:k])
    return len(top_k & relevant) / len(relevant)


def ndcg_at_k(recommended: list, relevant: set, k: int) -> float:
    """
    Normalised Discounted Cumulative Gain.

    Args:
        recommended: List of recommended ISBNs
        relevant: Set of relevant ISBNs
        k: Cutoff position

    Returns:
        NDCG@K score
    """
    dcg = 0.0
    for i, item in enumerate(recommended[:k]):
        if item in relevant:
            dcg += 1.0 / np.log2(i + 2)

    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant), k)))

    return dcg / idcg if idcg > 0 else 0.0


def evaluate_recommendations(
    model_fn: Callable[[int], list[str]],
    test_interactions: dict[int, set[str]],
    k: int = 10,
) -> dict:
    """
    Evaluate recommendation model on test interactions.

    Args:
        model_fn: Function that takes user_id and returns list of ISBNs
        test_interactions: Dict of user_id -> set of relevant ISBNs
        k: Cutoff position

    Returns:
        Dict with precision@K, recall@K, ndcg@K
    """
    p_scores = []
    r_scores = []
    ndcg_scores = []

    for user_id, relevant in test_interactions.items():
        try:
            recommendations = model_fn(user_id)
        except Exception as e:
            log.warning("eval.user_failed", user_id=user_id, error=str(e))
            continue

        p_scores.append(precision_at_k(recommendations, relevant, k))
        r_scores.append(recall_at_k(recommendations, relevant, k))
        ndcg_scores.append(ndcg_at_k(recommendations, relevant, k))

    return {
        f"precision@{k}": round(np.mean(p_scores), 4) if p_scores else 0.0,
        f"recall@{k}": round(np.mean(r_scores), 4) if r_scores else 0.0,
        f"ndcg@{k}": round(np.mean(ndcg_scores), 4) if ndcg_scores else 0.0,
    }


TARGET_PRECISION = 0.42
TARGET_RECALL = 0.35
TARGET_NDCG = 0.55


def check_pass(metrics: dict) -> dict:
    """Check if metrics meet targets."""
    return {
        "precision@10": "PASS" if metrics.get("precision@10", 0) >= TARGET_PRECISION else "FAIL",
        "recall@10": "PASS" if metrics.get("recall@10", 0) >= TARGET_RECALL else "FAIL",
        "ndcg@10": "PASS" if metrics.get("ndcg@10", 0) >= TARGET_NDCG else "FAIL",
    }