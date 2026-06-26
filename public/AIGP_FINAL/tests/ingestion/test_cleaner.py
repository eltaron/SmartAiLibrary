"""
tests/ingestion/test_cleaner.py
Tests for text cleaning module.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestCleanText:
    """Test suite for clean_text function."""

    def test_removes_multiple_newlines(self):
        """Test that multiple newlines are collapsed."""
        from services.ingestion.cleaner import clean_text

        text = "Line 1\n\n\n\nLine 2"
        result = clean_text(text)
        assert "\n\n\n" not in result

    def test_removes_extra_whitespace(self):
        """Test that extra spaces and tabs are removed."""
        from services.ingestion.cleaner import clean_text

        text = "Word1   Word2\t\tWord3"
        result = clean_text(text)
        assert "   " not in result
        assert "\t\t" not in result

    def test_removes_page_numbers(self):
        """Test that page numbers (single/double line) are removed."""
        from services.ingestion.cleaner import clean_text

        text = "Some text\n\n123\n\nMore text"
        result = clean_text(text)
        assert "123" not in result

    def test_removes_horizontal_rules(self):
        """Test that horizontal rules are removed."""
        from services.ingestion.cleaner import clean_text

        text = "Text\n──────\nMore text"
        result = clean_text(text)
        assert "──────" not in result

    def test_removes_ocr_artifacts(self):
        """Test that OCR artifacts (3+ consecutive non-alphanumeric) are removed."""
        from services.ingestion.cleaner import clean_text

        text = "Text ##### Noise #### More"
        result = clean_text(text)
        assert "#####" not in result
        assert "Noise" in result

    def test_normalizes_unicode(self):
        """Test that Unicode is normalized to NFKC."""
        from services.ingestion.cleaner import clean_text

        text = "café"  # é can have different encodings
        result = clean_text(text)
        assert "caf" in result.lower()

    def test_strips_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        from services.ingestion.cleaner import clean_text

        text = "   Some text   "
        result = clean_text(text)
        assert result == "Some text"

    def test_preserves_sentence_structure(self):
        """Test that sentence-ending punctuation is preserved."""
        from services.ingestion.cleaner import clean_text

        text = "This is sentence one. This is sentence two!"
        result = clean_text(text)
        assert "sentence one." in result
        assert "sentence two!" in result


class TestSentenceTokenize:
    """Test suite for sentence_tokenize function."""

    def test_tokenizes_simple_sentences(self):
        """Test basic sentence tokenization."""
        from services.ingestion.cleaner import sentence_tokenize

        text = "First sentence. Second sentence. Third sentence!"
        result = sentence_tokenize(text)

        assert len(result) >= 2
        assert any("First" in s for s in result)

    def test_filters_short_sentences(self):
        """Test that sentences shorter than 10 chars are filtered."""
        from services.ingestion.cleaner import sentence_tokenize

        text = "Hi. This is a longer sentence. OK."
        result = sentence_tokenize(text)

        assert all(len(s) >= 10 for s in result)

    def test_handles_empty_text(self):
        """Test handling of empty text."""
        from services.ingestion.cleaner import sentence_tokenize

        result = sentence_tokenize("")
        assert result == []


class TestIsEnglish:
    """Test suite for is_english function."""

    @patch("services.ingestion.cleaner.detect")
    def test_detects_english(self, mock_detect):
        """Test English detection."""
        from services.ingestion.cleaner import is_english

        mock_detect.return_value = "en"
        result = is_english("This is an English sentence.")
        assert result is True

    @patch("services.ingestion.cleaner.detect")
    def test_detects_non_english(self, mock_detect):
        """Test non-English detection."""
        from services.ingestion.cleaner import is_english

        mock_detect.return_value = "fr"
        result = is_english("Ceci est français.")
        assert result is False

    @patch("services.ingestion.cleaner.detect")
    def test_handles_detection_failure(self, mock_detect):
        """Test handling when detection fails."""
        from services.ingestion.cleaner import is_english
        from langdetect import LangDetectException

        mock_detect.side_effect = LangDetectException()
        result = is_english("Some text")
        assert result is True


class TestFilterNonEnglish:
    """Test suite for filter_non_english function."""

    @patch("services.ingestion.cleaner.detect")
    def test_filters_non_english_sentences(self, mock_detect):
        """Test that non-English sentences are removed."""
        from services.ingestion.cleaner import filter_non_english

        sentences = ["This is English.", "Ceci est français.", "More English here."]
        text = " ".join(sentences)

        mock_detect.side_effect = ["en", "fr", "en"]
        result = filter_non_english(text)

        assert "français" not in result
        assert "English" in result


class TestCleanAndTokenize:
    """Test suite for clean_and_tokenize function."""

    def test_full_pipeline(self):
        """Test complete cleaning and tokenization."""
        from services.ingestion.cleaner import clean_and_tokenize

        raw = "  Line1\n\n\nLine2.  Line3!  "
        result = clean_and_tokenize(raw, skip_language_filter=True)

        assert len(result) >= 2
        assert all(isinstance(s, str) for s in result)

    def test_skips_language_filter_when_flagged(self):
        """Test that language filter is skipped when flag is set."""
        from services.ingestion.cleaner import clean_and_tokenize

        raw = "English text. French text."
        result = clean_and_tokenize(raw, skip_language_filter=True)

        assert len(result) >= 1


class TestCleanerIntegration:
    """Integration tests for cleaner with various inputs."""

    def test_handles_real_book_excerpt(self):
        """Test with realistic book excerpt."""
        from services.ingestion.cleaner import clean_and_tokenize

        excerpt = """
        Chapter One

        It was the best of times, it was the worst of times, it was the age of wisdom,
        it was the age of foolishness, it was the epoch of belief, it was the epoch of
        incredulity, it was the season of Light, it was the season of Darkness.

        123

        We were all going direct to Heaven.
        """
        result = clean_and_tokenize(excerpt, skip_language_filter=True)

        assert len(result) >= 2
        assert all(len(s) >= 10 for s in result)

    def test_preserves_quotes_and_dialogue(self):
        """Test that quotes and dialogue are preserved."""
        from services.ingestion.cleaner import clean_text

        text = 'He said, "Hello, world!" Then she replied, "Goodbye."'
        result = clean_text(text)

        assert '"Hello' in result
        assert 'Goodbye."' in result

    def test_handles_hyphenated_words(self):
        """Test that hyphenated words are preserved."""
        from services.ingestion.cleaner import clean_text

        text = "well-known pre-existing state-of-the-art"
        result = clean_text(text)

        assert "well-known" in result
        assert "state-of-the-art" in result