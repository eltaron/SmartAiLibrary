"""
training/datasets/generate_synthetic_pairs.py
Generate synthetic query-book pairs using GPT-4o-mini.
"""
import argparse
import asyncio
import json
import os
from typing import Optional

import aiohttp
import structlog

from shared.config import settings

log = structlog.get_logger(__name__)

SYSTEM_PROMPT = "You are a helpful assistant that generates search queries for books."

USER_PROMPT_TEMPLATE = """Generate 4 diverse natural language search queries that a reader would type to find a book with this synopsis. Return a JSON array of strings only.

Synopsis: {synopsis}

Return ONLY a JSON array, no other text."""


async def generate_queries_for_book(
    session: aiohttp.ClientSession,
    synopsis: str,
    title: str,
) -> list[dict]:
    """Generate search queries for a single book using OpenAI."""
    if not settings.OPENAI_API_KEY:
        log.warning("openai_api_key.not_set")
        return []

    prompt = USER_PROMPT_TEMPLATE.format(synopsis=synopsis)

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }

    try:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            if response.status != 200:
                log.warning("openai.request_failed", status=response.status)
                return []

            data = await response.json()
            content = data["choices"][0]["message"]["content"]

            queries = json.loads(content)

            return [
                {"query": q, "positive": synopsis, "title": title}
                for q in queries
            ]

    except json.JSONDecodeError:
        log.warning("openai.invalid_json", title=title)
        return []
    except Exception as e:
        log.error("openai.error", error=str(e), title=title)
        return []


async def generate_pairs(
    books: list[dict],
    target_pairs: int = 10000,
) -> list[dict]:
    """Generate query-book pairs for all books."""
    pairs = []
    seen_queries = set()

    async with aiohttp.ClientSession() as session:
        for book in books:
            if len(pairs) >= target_pairs:
                break

            synopsis = book.get("synopsis", "")
            title = book.get("title", "")
            genres = book.get("genres", [])

            if not synopsis:
                continue

            new_pairs = await generate_queries_for_book(session, synopsis, title)

            for pair in new_pairs:
                query = pair["query"]
                if query not in seen_queries:
                    seen_queries.add(query)
                    pairs.append({
                        "query": query,
                        "positive": pair["positive"],
                        "title": title,
                        "genres": genres,
                    })

            log.info("generate.progress", current=len(pairs), target=target_pairs)

    log.info("generate.complete", total_pairs=len(pairs))
    return pairs


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic search pairs")
    parser.add_argument(
        "--input",
        type=str,
        default="training/datasets/books_metadata.json",
        help="Input books metadata JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="training/datasets/search_pairs.json",
        help="Output search pairs JSON",
    )
    parser.add_argument(
        "--target-pairs",
        type=int,
        default=10000,
        help="Target number of pairs",
    )

    args = parser.parse_args()

    with open(args.input) as f:
        books = json.load(f)

    log.info("generate.start", books=len(books), target=args.target_pairs)

    pairs = asyncio.run(generate_pairs(books, args.target_pairs))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(pairs, f, indent=2)

    log.info("generate.saved", path=args.output, pairs=len(pairs))


if __name__ == "__main__":
    from pathlib import Path

    main()