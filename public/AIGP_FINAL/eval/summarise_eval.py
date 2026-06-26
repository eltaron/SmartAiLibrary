"""
eval/summarise_eval.py
Summarisation evaluation metrics (ROUGE-L, faithfulness).
"""
import json
from typing import Optional

import structlog

log = structlog.get_logger(__name__)


def compute_rouge_l(prediction: str, reference: str) -> float:
    """
    Compute ROUGE-L score.

    Longest Common Subsequence based metric.

    Args:
        prediction: Generated summary
        reference: Reference summary

    Returns:
        ROUGE-L score
    """
    prediction_tokens = prediction.split()
    reference_tokens = reference.split()

    m = len(prediction_tokens)
    n = len(reference_tokens)

    if m == 0 or n == 0:
        return 0.0

    lcs_matrix = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if prediction_tokens[i - 1] == reference_tokens[j - 1]:
                lcs_matrix[i][j] = lcs_matrix[i - 1][j - 1] + 1
            else:
                lcs_matrix[i][j] = max(lcs_matrix[i - 1][j], lcs_matrix[i][j - 1])

    lcs_length = lcs_matrix[m][n]

    precision = lcs_length / m if m > 0 else 0
    recall = lcs_length / n if n > 0 else 0

    if precision + recall == 0:
        return 0.0

    f1 = 2 * (precision * recall) / (precision + recall)

    return f1


def faithfulness_score(prediction: str, context: str) -> float:
    """
    Estimate faithfulness (how much prediction is supported by context).

    Uses NLI-style heuristic: counts overlapping n-grams.

    Args:
        prediction: Generated text
        context: Source context

    Returns:
        Faithfulness score 0-1
    """
    pred_words = set(prediction.lower().split())
    ctx_words = set(context.lower().split())

    if not pred_words:
        return 0.0

    overlap = len(pred_words & ctx_words)
    score = overlap / len(pred_words)

    return score


TARGET_ROUGE_L = 0.44
TARGET_FAITHFULNESS = 0.80


def evaluate_summarisation(
    predictions: list[tuple[str, str]],
) -> dict:
    """
    Evaluate summarisation predictions.

    Args:
        predictions: List of (prediction, reference) tuples

    Returns:
        Dict with metrics
    """
    rouge_scores = []
    faithfulness_scores = []

    for pred, ref in predictions:
        rouge = compute_rouge_l(pred, ref)
        rouge_scores.append(rouge)

    return {
        "rouge_l": round(sum(rouge_scores) / len(rouge_scores), 4) if rouge_scores else 0.0,
    }


def check_pass(metrics: dict) -> dict:
    """Check if metrics meet targets."""
    return {
        "rouge_l": "PASS" if metrics.get("rouge_l", 0) >= TARGET_ROUGE_L else "FAIL",
    }