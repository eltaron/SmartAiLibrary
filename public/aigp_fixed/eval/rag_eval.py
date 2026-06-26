"""
eval/rag_eval.py
RAG evaluation metrics.
"""
import json
from typing import Optional

import structlog

log = structlog.get_logger(__name__)


def faithfulness_from_context(answer: str, chunks: list[str]) -> float:
    """
    Compute faithfulness based on retrieved chunks.

    Args:
        answer: Generated answer
        chunks: Retrieved context chunks

    Returns:
        Faithfulness score 0-1
    """
    answer_words = set(answer.lower().split())
    chunk_words = set(" ".join(chunks).lower().split())

    if not answer_words:
        return 0.0

    overlap = len(answer_words & chunk_words)
    return overlap / len(answer_words)


def answer_relevance(question: str, answer: str) -> float:
    """
    Estimate answer relevance to question.

    Uses simple keyword overlap for now.

    Args:
        question: Original question
        answer: Generated answer

    Returns:
        Relevance score 0-1
    """
    q_words = set(question.lower().split())
    a_words = set(answer.lower().split())

    if not a_words:
        return 0.0

    overlap = len(q_words & a_words)
    return overlap / len(a_words)


TARGET_FAITHFULNESS = 0.80


def evaluate_rag(
    predictions: list[dict],
) -> dict:
    """
    Evaluate RAG predictions.

    Args:
        predictions: List of dicts with question, answer, chunks

    Returns:
        Dict with metrics
    """
    faithfulness_scores = []
    relevance_scores = []

    for pred in predictions:
        answer = pred.get("answer", "")
        chunks = pred.get("chunks", [])
        question = pred.get("question", "")

        faithful = faithfulness_from_context(answer, chunks)
        relevance = answer_relevance(question, answer)

        faithfulness_scores.append(faithful)
        relevance_scores.append(relevance)

    return {
        "faithfulness": round(sum(faithfulness_scores) / len(faithfulness_scores), 4) if faithfulness_scores else 0.0,
        "relevance": round(sum(relevance_scores) / len(relevance_scores), 4) if relevance_scores else 0.0,
    }


def check_pass(metrics: dict) -> dict:
    """Check if metrics meet targets."""
    return {
        "faithfulness": "PASS" if metrics.get("faithfulness", 0) >= TARGET_FAITHFULNESS else "FAIL",
    }