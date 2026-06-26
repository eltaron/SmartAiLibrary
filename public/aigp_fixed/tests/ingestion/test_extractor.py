"""
tests/ingestion/test_extractor.py
Tests for text extraction module.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import os


class TestDetectFormat:
    """Test suite for detect_format function."""

    def test_detect_pdf(self):
        """Test that .pdf files are detected correctly."""
        from services.ingestion.extractor import detect_format

        path = Path("test.pdf")
        assert detect_format(path) == "pdf"

    def test_detect_epub(self):
        """Test that .epub files are detected correctly."""
        from services.ingestion.extractor import detect_format

        path = Path("test.epub")
        assert detect_format(path) == "epub"

    def test_detect_unsupported(self):
        """Test that unsupported formats return 'unsupported'."""
        from services.ingestion.extractor import detect_format

        assert detect_format(Path("test.txt")) == "unsupported"
        assert detect_format(Path("test.docx")) == "unsupported"
        assert detect_format(Path("test.mobi")) == "unsupported"


class TestExtractPdf:
    """Test suite for PDF extraction."""

    def test_extract_pdf_mock(self):
        """Test PDF extraction with mocked fitz."""
        from services.ingestion.extractor import extract_pdf, PageContent

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 2
        mock_doc.__getitem__ = lambda self, idx: MagicMock(
            get_text=lambda mode: f"Page {idx + 1} content. This is a test page with sufficient text to pass the minimum length filter."
        )

        with patch("fitz.open", return_value=mock_doc):
            pages = list(extract_pdf(Path("test.pdf"), "978-0-123456-78-9"))

            assert len(pages) == 2
            assert pages[0].page_num == 1
            assert pages[0].isbn == "978-0-123456-78-9"
            assert "Page 1" in pages[0].text
            assert pages[1].page_num == 2
            assert "Page 2" in pages[1].text

    def test_extract_pdf_filters_short_pages(self):
        """Test that pages with fewer than 50 characters are filtered."""
        from services.ingestion.extractor import extract_pdf

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 3
        mock_doc.__getitem__ = lambda self, idx: MagicMock(
            get_text=lambda mode: "Short" if idx < 2 else "This is a longer page with more than fifty characters of text content."
        )

        with patch("fitz.open", return_value=mock_doc):
            pages = list(extract_pdf(Path("test.pdf"), "978-0-123456-78-9"))

            assert len(pages) == 1
            assert "longer page" in pages[0].text

    def test_extract_pdf_page_numbers_sequential(self):
        """Test that page numbers are sequential starting from 1."""
        from services.ingestion.extractor import extract_pdf

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 5
        mock_doc.__getitem__ = lambda self, idx: MagicMock(
            get_text=lambda mode: f"Content of page {idx + 1} with sufficient text length for extraction."
        )

        with patch("fitz.open", return_value=mock_doc):
            pages = list(extract_pdf(Path("test.pdf"), "isbn-123"))

            for i, page in enumerate(pages):
                assert page.page_num == i + 1


class TestExtractEpub:
    """Test suite for ePub extraction."""

    def test_extract_epub_mock(self):
        """Test ePub extraction with mocked ebooklib."""
        from services.ingestion.extractor import extract_epub, PageContent

        mock_item = MagicMock()
        mock_item.get_type.return_value = 9
        mock_item.get_content.return_value = b"<p>Chapter 1 content here</p>"
        mock_item.get_id.return_value = "item-1"

        mock_book = MagicMock()
        mock_book.get_items.return_value = [mock_item]

        with patch("ebooklib.epub.read_epub", return_value=mock_book):
            pages = list(extract_epub(Path("test.epub"), "978-0-123456-78-9"))

            assert len(pages) == 1
            assert pages[0].isbn == "978-0-123456-78-9"
            assert "Chapter 1" in pages[0].text or "Chapter 1" in pages[0].text.replace(
                "<p>", ""
            ).replace("</p>", "")

    def test_extract_epub_filters_short_content(self):
        """Test that content with fewer than 50 characters is filtered."""
        from services.ingestion.extractor import extract_epub

        mock_item = MagicMock()
        mock_item.get_type.return_value = 9
        mock_item.get_content.return_value = b"Short"
        mock_item.get_id.return_value = "item-1"

        mock_book = MagicMock()
        mock_book.get_items.return_value = [mock_item]

        with patch("ebooklib.epub.read_epub", return_value=mock_book):
            pages = list(extract_epub(Path("test.epub"), "isbn-123"))

            assert len(pages) == 0


class TestExtractText:
    """Test suite for unified extract_text function."""

    def test_extract_text_routes_to_pdf(self):
        """Test that PDF files route to extract_pdf."""
        from services.ingestion.extractor import extract_text, PageContent

        mock_doc = MagicMock()
        mock_doc.__len__ = lambda self: 1
        mock_doc.__getitem__ = lambda self, idx: MagicMock(
            get_text=lambda mode: "PDF content"
        )

        with patch("fitz.open", return_value=mock_doc):
            pages = list(extract_text(Path("test.pdf"), "isbn-123"))

            assert len(pages) == 1

    def test_extract_text_routes_to_epub(self):
        """Test that ePub files route to extract_epub."""
        from services.ingestion.extractor import extract_text

        mock_item = MagicMock()
        mock_item.get_type.return_value = 9
        mock_item.get_content.return_value = b"<p>Content</p>"

        mock_book = MagicMock()
        mock_book.get_items.return_value = [mock_item]

        with patch("ebooklib.epub.read_epub", return_value=mock_book):
            pages = list(extract_text(Path("test.epub"), "isbn-123"))

            assert len(pages) == 1

    def test_extract_text_raises_for_unsupported(self):
        """Test that unsupported formats raise ValueError."""
        from services.ingestion.extractor import extract_text

        with pytest.raises(ValueError, match="AI-002"):
            list(extract_text(Path("test.txt"), "isbn-123"))


class TestPageContent:
    """Test suite for PageContent dataclass."""

    def test_page_content_creation(self):
        """Test creating a PageContent instance."""
        from services.ingestion.extractor import PageContent

        page = PageContent(page_num=1, text="Test text", isbn="978-0-123456-78-9")

        assert page.page_num == 1
        assert page.text == "Test text"
        assert page.isbn == "978-0-123456-78-9"

    def test_page_content_validates_page_num(self):
        """Test that page_num must be >= 1."""
        from services.ingestion.extractor import PageContent

        with pytest.raises(ValueError, match="page_num must be >= 1"):
            PageContent(page_num=0, text="test", isbn="isbn")

    def test_page_content_validates_isbn(self):
        """Test that isbn cannot be empty."""
        from services.ingestion.extractor import PageContent

        with pytest.raises(ValueError, match="isbn cannot be empty"):
            PageContent(page_num=1, text="test", isbn="")

    def test_page_content_is_frozen(self):
        """Test that PageContent is immutable."""
        from services.ingestion.extractor import PageContent

        page = PageContent(page_num=1, text="test", isbn="isbn")

        with pytest.raises(AttributeError):
            page.page_num = 2