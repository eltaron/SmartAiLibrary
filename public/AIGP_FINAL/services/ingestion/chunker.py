"""
services/ingestion/chunker.py
Sliding-window chunker for breaking text into token-bounded chunks.
"""
from dataclasses import dataclass
from typing import Optional

import structlog
from transformers import AutoTokenizer

from shared.config import settings

log = structlog.get_logger(__name__)

CHUNK_SIZE = settings.CHUNK_SIZE
CHUNK_OVERLAP = settings.CHUNK_OVERLAP

_TOKENIZER: Optional[AutoTokenizer] = None


def _get_tokenizer() -> AutoTokenizer:
    """Lazy-load the embedding tokenizer."""
    global _TOKENIZER
    if _TOKENIZER is None:
        _TOKENIZER = AutoTokenizer.from_pretrained(settings.EMBEDDING_MODEL)
    return _TOKENIZER


@dataclass(frozen=True)
class Chunk:
    """Represents a text chunk from a book."""

    chunk_id: str
    isbn: str
    page_num: int
    text: str
    token_count: int


def _token_count(text: str) -> int:
    """Get token count for text."""
    return len(
        _get_tokenizer().encode(text, add_special_tokens=False)
    )


def _split_long_sentence(sentence: str) -> list[str]:
    """Split a sentence that exceeds CHUNK_SIZE into token-bounded windows."""
    tokenizer = _get_tokenizer()
    tokens = tokenizer.encode(sentence, add_special_tokens=False)

    if len(tokens) <= CHUNK_SIZE:
        return [sentence]

    parts: list[str] = []
    step = max(CHUNK_SIZE - CHUNK_OVERLAP, 1)

    for start in range(0, len(tokens), step):
        window = tokens[start : start + CHUNK_SIZE]
        if not window:
            break
        parts.append(tokenizer.decode(window))
        if start + CHUNK_SIZE >= len(tokens):
            break

    return parts


def chunk_sentences(
    sentences: list[str],
    isbn: str,
    page_num: int,
) -> list[Chunk]:
    """
    Create chunks from sentences using sliding-window approach.

    Greedily fills each chunk up to CHUNK_SIZE tokens, carrying over
    CHUNK_OVERLAP tokens into the next chunk. The last chunk is always
    emitted even if below half of CHUNK_SIZE.

    Args:
        sentences: List of sentences from the page
        isbn: ISBN of the book
        page_num: Page number

    Returns:
        List of Chunk objects

    Raises:
        AssertionError: If invariants are violated
    """
    chunks: list[Chunk] = []
    buffer: list[str] = []
    buffer_tokens = 0
    chunk_idx = 0

    generated_ids: set[str] = set()

    expanded_sentences: list[str] = []
    for sent in sentences:
        expanded_sentences.extend(_split_long_sentence(sent))

    for sent in expanded_sentences:
        sent_tokens = _token_count(sent)

        if buffer_tokens + sent_tokens > CHUNK_SIZE and buffer:
            chunk_text = " ".join(buffer)

            chunk_id = f"{isbn}_p{page_num}_c{chunk_idx}"
            assert chunk_id not in generated_ids, f"Duplicate chunk_id: {chunk_id}"
            generated_ids.add(chunk_id)

            actual_tokens = _token_count(chunk_text)
            assert actual_tokens <= CHUNK_SIZE + 10, (
                f"Token count {actual_tokens} exceeds CHUNK_SIZE + 10 ({CHUNK_SIZE + 10})"
            )

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    isbn=isbn,
                    page_num=page_num,
                    text=chunk_text,
                    token_count=actual_tokens,
                )
            )

            chunk_idx += 1

            overlap_tokens = CHUNK_OVERLAP
            overlap_text = " ".join(buffer)
            overlap_enc = _get_tokenizer().encode(overlap_text, add_special_tokens=False)
            if len(overlap_enc) > overlap_tokens:
                overlap_decoded = _get_tokenizer().decode(overlap_enc[-overlap_tokens:])
                buffer = [overlap_decoded]
                buffer_tokens = _token_count(overlap_decoded)
            else:
                buffer = []
                buffer_tokens = 0

        buffer.append(sent)
        buffer_tokens += sent_tokens

    if buffer:
        chunk_text = " ".join(buffer)

        chunk_id = f"{isbn}_p{page_num}_c{chunk_idx}"
        assert chunk_id not in generated_ids, f"Duplicate chunk_id: {chunk_id}"
        generated_ids.add(chunk_id)

        actual_tokens = _token_count(chunk_text)
        assert actual_tokens <= CHUNK_SIZE + 10, (
            f"Token count {actual_tokens} exceeds CHUNK_SIZE + 10 ({CHUNK_SIZE + 10})"
        )

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                isbn=isbn,
                page_num=page_num,
                text=chunk_text,
                token_count=actual_tokens,
            )
        )

    log.debug(
        "chunks.created",
        isbn=isbn,
        page=page_num,
        chunks=len(chunks),
    )

    return chunks


def chunk_page(
    raw_text: str,
    isbn: str,
    page_num: int,
    skip_language_filter: bool = False,
) -> list[Chunk]:
    """
    Complete chunking pipeline for a single page.

    Args:
        raw_text: Raw text from extraction
        isbn: ISBN of the book
        page_num: Page number
        skip_language_filter: Skip language filtering

    Returns:
        List of chunks for the page
    """
    from services.ingestion.cleaner import clean_and_tokenize

    sentences = clean_and_tokenize(raw_text, skip_language_filter=skip_language_filter)

    return chunk_sentences(sentences, isbn, page_num)


def get_overlap_text(buffer: list[str], overlap_tokens: int) -> str:
    """Get the overlap text from buffer."""
    overlap_text = " ".join(buffer)
    overlap_enc = _get_tokenizer().encode(overlap_text, add_special_tokens=False)
    if len(overlap_enc) > overlap_tokens:
        return _get_tokenizer().decode(overlap_enc[-overlap_tokens:])
    return ""
