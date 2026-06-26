"""
services/ingestion/extractor.py
Text extraction from PDF and ePub files.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

import fitz  # PyMuPDF
import structlog

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class PageContent:
    """Represents extracted content from a single page."""

    page_num: int
    text: str
    isbn: str

    def __post_init__(self) -> None:
        if self.page_num < 1:
            raise ValueError("page_num must be >= 1")
        if not self.isbn:
            raise ValueError("isbn cannot be empty")


def extract_pdf(file_path: Path, isbn: str) -> Iterator[PageContent]:
    """
    Extract plain text from each page of a PDF file.

    Filters out pages with fewer than 50 characters (covers, blanks, etc.).

    Args:
        file_path: Path to the PDF file
        isbn: ISBN of the book being processed

    Yields:
        PageContent for each valid page
    """
    MIN_PAGE_LENGTH = 50

    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        log.error("pdf.open.failed", path=str(file_path), error=str(e))
        raise RuntimeError(f"AI-004: Failed to open PDF: {e}") from e

    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if len(text) >= MIN_PAGE_LENGTH:
                yield PageContent(
                    page_num=page_num + 1,
                    text=text,
                    isbn=isbn,
                )
            else:
                log.debug(
                    "pdf.page.skipped",
                    isbn=isbn,
                    page=page_num + 1,
                    length=len(text),
                    reason="below_min_length",
                )
    finally:
        doc.close()

    log.info("pdf.extracted", isbn=isbn, file_path=str(file_path))


def extract_epub(file_path: Path, isbn: str) -> Iterator[PageContent]:
    """
    Extract text from an ePub file.

    Extracts chapter HTML content, strips tags, and yields plain text.
    Filters out content with fewer than 50 characters.

    Args:
        file_path: Path to the ePub file
        isbn: ISBN of the book being processed

    Yields:
        PageContent for each valid section
    """
    from ebooklib import epub

    MIN_PAGE_LENGTH = 50

    try:
        book = epub.read_epub(str(file_path))
    except Exception as e:
        log.error("epub.open.failed", path=str(file_path), error=str(e))
        raise RuntimeError(f"AI-004: Failed to open ePub: {e}") from e

    page_num = 0

    for item in book.get_items():
        if item.get_type() == 9:
            try:
                content = item.get_content()
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")

                import re

                text = re.sub(r"<[^>]+>", "", content)
                text = text.strip()

                if len(text) >= MIN_PAGE_LENGTH:
                    page_num += 1
                    yield PageContent(
                        page_num=page_num,
                        text=text,
                        isbn=isbn,
                    )
                else:
                    log.debug(
                        "epub.page.skipped",
                        isbn=isbn,
                        page=page_num + 1,
                        length=len(text),
                        reason="below_min_length",
                    )
            except Exception as e:
                log.warning(
                    "epub.item.parse.failed",
                    isbn=isbn,
                    item_id=item.get_id(),
                    error=str(e),
                )
                continue

    log.info("epub.extracted", isbn=isbn, file_path=str(file_path))


def detect_format(file_path: Path) -> Literal["pdf", "epub", "unsupported"]:
    """
    Detect the format of a file based on extension.

    Args:
        file_path: Path to the file

    Returns:
        "pdf", "epub", or "unsupported"
    """
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return "pdf"
    elif extension in (".epub",):
        return "epub"
    else:
        return "unsupported"


def extract_text(file_path: Path, isbn: str) -> Iterator[PageContent]:
    """
    Extract text from a file, automatically detecting format.

    Args:
        file_path: Path to the file
        isbn: ISBN of the book being processed

    Yields:
        PageContent for each page/section

    Raises:
        ValueError: If file format is not supported (AI-002)
    """
    file_format = detect_format(file_path)

    if file_format == "pdf":
        yield from extract_pdf(file_path, isbn)
    elif file_format == "epub":
        yield from extract_epub(file_path, isbn)
    else:
        log.error("unsupported.format", path=str(file_path))
        raise ValueError("AI-002: unsupported format")