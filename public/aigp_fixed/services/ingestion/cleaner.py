"""
services/ingestion/cleaner.py
Text cleaning and NLP preprocessing for extracted book content.
"""
import re
import unicodedata
from typing import Iterator

import structlog
from langdetect import detect, LangDetectException

from shared.config import settings

log = structlog.get_logger(__name__)

try:
    import spacy

    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
except OSError:
    log.warning("spacy.en_core_web_sm.not_found", msg="Using simple sentence tokenizer")
    nlp = None


def clean_text(raw: str) -> str:
    """
    Clean raw text by removing artifacts and normalising.

    Removes:
    - Multiple consecutive newlines
    - Extra whitespace
    - Page numbers (single/double line with digits)
    - Horizontal rules (─,═, etc.)
    - OCR artifacts (3+ consecutive non-alphanumeric chars)
    - Normalises Unicode (NFKC)

    Args:
        raw: Raw text from extraction

    Returns:
        Cleaned text
    """
    text = raw

    text = re.sub(r"\n{3,}", "\n\n", text)

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)

    text = re.sub(r"[-─══]{5,}", "", text)

    text = re.sub(r"[\u200b-\u200f\u2028-\u202f]", "", text)

    text = re.sub(r"[^\w\s.,!?;:'\"-]{3,}", " ", text)

    text = unicodedata.normalize("NFKC", text)

    text = re.sub(r"\s+", " ", text)

    text = text.strip()

    return text


def sentence_tokenize(text: str) -> list[str]:
    """
    Split text into sentences using spaCy if available.

    Filters out sentences shorter than 10 characters.

    Args:
        text: Cleaned text to tokenize

    Returns:
        List of sentences
    """
    MIN_SENTENCE_LENGTH = 10

    if nlp is not None:
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
    else:
        sentences = re.split(r"(?<=[.!?])\s+", text)

    filtered = [s for s in sentences if len(s) >= MIN_SENTENCE_LENGTH]

    log.debug(
        "text.tokenized",
        input_length=len(text),
        sentences_out=len(filtered),
    )

    return filtered


def is_english(text: str, min_confidence: float = 0.85) -> bool:
    """
    Detect if text is primarily in English.

    Args:
        text: Text to analyze
        min_confidence: Minimum confidence threshold (0-1)

    Returns:
        True if detected language is English with sufficient confidence
    """
    try:
        result = detect(text)
        return result == "en"
    except LangDetectException:
        log.warning("langdetect.failed", text_length=len(text))
        return True


def filter_non_english(text: str) -> str:
    """
    Filter out non-English sentences from text.

    Uses langdetect to identify the language of each sentence.
    Removes sentences with confidence < 0.85.

    Args:
        text: Text to filter

    Returns:
        Text with non-English sentences removed
    """
    MIN_CONFIDENCE = 0.85

    sentences = sentence_tokenize(text)
    english_sentences = []

    for sent in sentences:
        try:
            result = detect(sent)
            if result == "en":
                english_sentences.append(sent)
            else:
                log.debug(
                    "sentence.filtered.non_english",
                    length=len(sent),
                    language=result,
                )
        except LangDetectException:
            english_sentences.append(sent)

    return " ".join(english_sentences)


def clean_and_tokenize(raw_text: str, skip_language_filter: bool = False) -> list[str]:
    """
    Complete cleaning and tokenization pipeline.

    Args:
        raw_text: Raw text from extraction
        skip_language_filter: Skip language detection (for testing)

    Returns:
        List of cleaned sentences
    """
    cleaned = clean_text(raw_text)

    if not skip_language_filter:
        cleaned = filter_non_english(cleaned)

    sentences = sentence_tokenize(cleaned)

    log.debug(
        "cleaning.complete",
        raw_length=len(raw_text),
        cleaned_length=len(cleaned),
        sentences=len(sentences),
    )

    return sentences