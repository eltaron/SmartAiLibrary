"""
eval/search_eval.py
Search service evaluation metrics.
"""
import numpy as np
import structlog

log = structlog.get_logger(__name__)


def mean_reciprocal_rank(relevances: list[list[bool]]) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR).

    Args:
        relevances: List of relevance lists for each query

    Returns:
        MRR score
    """
    reciprocal_ranks = []

    for relevance in relevances:
        for i, rel in enumerate(relevance, 1):
            if rel:
                reciprocal_ranks.append(1.0 / i)
                break
        else:
            reciprocal_ranks.append(0.0)

    return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0


def average_precision(relevant: set, predicted: list) -> float:
    """Calculate Average Precision for a single query."""
    if not relevant:
        return 0.0

    num_relevant = 0
    sum_precision = 0.0

    for i, pred in enumerate(predicted, 1):
        if pred in relevant:
            num_relevant += 1
            sum_precision += num_relevant / i

    return sum_precision / len(relevant)


def map_at_k(relevances: list[tuple[set, list]], k: int = 10) -> float:
    """Calculate Mean Average Precision at K."""
    aps = []
    for relevant, predicted in relevances:
        ap = average_precision(relevant, predicted[:k])
        aps.append(ap)

    return np.mean(aps) if aps else 0.0


TARGET_MRR = 0.55


def evaluate_search(
    predictions: list[tuple[set, list]],
) -> dict:
    """
    Evaluate search results.

    Args:
        predictions: List of (relevant_set, predicted_list) tuples

    Returns:
        Dict with metrics
    """
    mrr = mean_reciprocal_rank([[p[1][i] in p[0] for i in range(len(p[1]))] for p in predictions])
    map_score = map_at_k(predictions)

    return {
        "mrr": round(mrr, 4),
        "map@10": round(map_score, 4),
    }


def check_pass(metrics: dict) -> dict:
    """Check if metrics meet targets."""
    return {
        "mrr": "PASS" if metrics.get("mrr", 0) >= TARGET_MRR else "FAIL",
    }