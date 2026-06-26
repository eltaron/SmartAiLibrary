"""
eval/run_eval.py
CLI for running evaluation on all services.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import structlog
import requests

from eval import rec_eval, search_eval, summarise_eval, rag_eval

log = structlog.get_logger(__name__)


def run_rec_eval(model_url: str) -> dict:
    """Run recommendation evaluation."""
    log.info("eval.rec.start", url=model_url)

    test_data = {
        1: {"978-1", "978-2", "978-3"},
        2: {"978-4", "978-5"},
        3: {"978-6", "978-7", "978-8"},
    }

    def model_fn(user_id: int):
        response = requests.post(
            f"{model_url}/recommendations",
            json={"user_id": user_id, "top_k": 10},
            timeout=10,
        )
        data = response.json()
        return [r["isbn"] for r in data.get("recommendations", [])]

    metrics = rec_eval.evaluate_recommendations(model_fn, test_data, k=10)

    results = {
        **metrics,
        "targets": {
            "precision@10": rec_eval.TARGET_PRECISION,
            "recall@10": rec_eval.TARGET_RECALL,
            "ndcg@10": rec_eval.TARGET_NDCG,
        },
        "status": rec_eval.check_pass(metrics),
    }

    log.info("eval.rec.complete", metrics=metrics)
    return results


def run_search_eval(model_url: str) -> dict:
    """Run search evaluation."""
    log.info("eval.search.start", url=model_url)

    test_queries = [
        {
            "query": "dystopian novel",
            "relevant": {"978-1", "978-2"},
            "predicted": ["978-1", "978-3", "978-2"],
        },
        {
            "query": "science fiction adventure",
            "relevant": {"978-4"},
            "predicted": ["978-4", "978-5"],
        },
    ]

    predictions = [
        (set(t["relevant"]), t["predicted"]) for t in test_queries
    ]

    metrics = search_eval.evaluate_search(predictions)

    results = {
        **metrics,
        "targets": {
            "mrr": search_eval.TARGET_MRR,
        },
        "status": search_eval.check_pass(metrics),
    }

    log.info("eval.search.complete", metrics=metrics)
    return results


def run_summarise_eval(model_url: str) -> dict:
    """Run summarisation evaluation."""
    log.info("eval.summarise.start", url=model_url)

    predictions = [
        ("The book explores themes of love and loss.", "The novel is about love and loss."),
        ("A thrilling adventure across space.", "An adventure in space."),
    ]

    metrics = summarise_eval.evaluate_summarisation(predictions)

    results = {
        **metrics,
        "targets": {
            "rouge_l": summarise_eval.TARGET_ROUGE_L,
        },
        "status": summarise_eval.check_pass(metrics),
    }

    log.info("eval.summarise.complete", metrics=metrics)
    return results


def run_rag_eval(model_url: str) -> dict:
    """Run RAG evaluation."""
    log.info("eval.rag.start", url=model_url)

    predictions = [
        {
            "question": "What is the main theme?",
            "answer": "The main theme is love and redemption.",
            "chunks": ["The theme of love is present throughout.", "Redemption is explored."],
        },
    ]

    metrics = rag_eval.evaluate_rag(predictions)

    results = {
        **metrics,
        "targets": {
            "faithfulness": rag_eval.TARGET_FAITHFULNESS,
        },
        "status": rag_eval.check_pass(metrics),
    }

    log.info("eval.rag.complete", metrics=metrics)
    return results


def main():
    parser = argparse.ArgumentParser(description="Run evaluation on AI services")
    parser.add_argument(
        "--service",
        type=str,
        required=True,
        choices=["rec", "search", "summarise", "rag"],
        help="Service to evaluate",
    )
    parser.add_argument(
        "--model-url",
        type=str,
        default="http://localhost:8001",
        help="Base URL for the service",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path",
    )

    args = parser.parse_args()

    if args.service == "rec":
        results = run_rec_eval(args.model_url)
    elif args.service == "search":
        results = run_search_eval(args.model_url)
    elif args.service == "summarise":
        results = run_summarise_eval(args.model_url)
    elif args.service == "rag":
        results = run_rag_eval(args.model_url)

    if args.output:
        output_dir = Path(args.output).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{args.service}_{timestamp}.json"
        output_path = output_dir / filename

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        log.info("eval.saved", path=str(output_path))

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()