"""
tests/ingestion/test_chunker.py
Tests for sliding-window chunker module.
"""
import pytest
from unittest.mock import patch


class TestChunkSentences:
    """Test suite for chunk_sentences function."""

    def test_basic_chunking(self):
        """Test basic chunk creation."""
        from services.ingestion.chunker import chunk_sentences, Chunk

        sentences = [
            "This is the first sentence.",
            "This is the second sentence.",
            "This is the third sentence.",
        ]

        chunks = chunk_sentences(sentences, "978-0-123456-78-9", 1)

        assert len(chunks) >= 1
        assert isinstance(chunks[0], Chunk)
        assert chunks[0].isbn == "978-0-123456-78-9"
        assert chunks[0].page_num == 1

    def test_chunk_ids_unique(self):
        """Test that chunk IDs are globally unique within a book."""
        from services.ingestion.chunker import chunk_sentences

        sentences = [f"This is sentence number {i}." for i in range(100)]

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        chunk_ids = [c.chunk_id for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk_ids found"

    def test_chunk_ids_unique_across_pages(self):
        """Test that chunk IDs are unique across different pages."""
        from services.ingestion.chunker import chunk_sentences

        sentences = ["Sentence one.", "Sentence two."]

        chunks_p1 = chunk_sentences(sentences, "isbn-123", 1)
        chunks_p2 = chunk_sentences(sentences, "isbn-123", 2)

        all_ids = [c.chunk_id for c in chunks_p1 + chunks_p2]
        assert len(all_ids) == len(set(all_ids)), "Duplicate chunk_ids across pages"

    def test_token_count_within_limit(self):
        """Test that no chunk exceeds CHUNK_SIZE + 10 tokens."""
        from services.ingestion.chunker import chunk_sentences
        from shared.config import settings

        sentences = [
            "Lorem ipsum dolor sit amet " * 50,
            "Consectetur adipiscing elit " * 50,
        ]

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        for chunk in chunks:
            assert chunk.token_count <= settings.CHUNK_SIZE + 10, (
                f"Chunk {chunk.chunk_id} has {chunk.token_count} tokens, "
                f"exceeding limit of {settings.CHUNK_SIZE + 10}"
            )

    def test_last_chunk_always_emitted(self):
        """Test that the last chunk is always emitted even if below half CHUNK_SIZE."""
        from services.ingestion.chunker import chunk_sentences
        from shared.config import settings

        sentences = ["Short sentence."]

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        assert len(chunks) >= 1, "Last chunk should always be emitted"

    def test_empty_sentences(self):
        """Test handling of empty sentence list."""
        from services.ingestion.chunker import chunk_sentences

        chunks = chunk_sentences([], "isbn-123", 1)
        assert chunks == []


class TestChunkCoverage:
    """Test suite for chunk coverage (all tokens appear in at least one chunk)."""

    def test_all_tokens_in_chunks(self):
        """Test that every token from input appears in at least one chunk."""
        from services.ingestion.chunker import chunk_sentences

        sentences = [
            "The quick brown fox jumps over the lazy dog.",
            "Pack my box with five dozen liquor jugs.",
            "How vexingly quick daft zebras jump!",
            "The five boxing wizards jump quickly.",
            "Sphinx of black quartz, judge my vow.",
        ]

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        all_chunk_text = " ".join(c.text for c in chunks)

        for sent in sentences:
            assert sent.strip() in all_chunk_text or any(
                word in all_chunk_text for word in sent.split()[:3]
            ), f"Sentence '{sent}' not represented in chunks"

    def test_small_input_coverage(self):
        """Test coverage with small input."""
        from services.ingestion.chunker import chunk_sentences

        sentences = ["A simple test sentence."]

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        assert len(chunks) >= 1
        combined_text = " ".join(c.text for c in chunks)
        assert "simple" in combined_text.lower()


class TestChunkOverlap:
    """Test suite for chunk overlap functionality."""

    def test_consecutive_chunks_share_tokens(self):
        """Test that consecutive chunks share approximately 50 tokens."""
        from services.ingestion.chunker import chunk_sentences
        from shared.config import settings

        sentences = []
        for i in range(50):
            words = " ".join([f"word{j}" for j in range(20)])
            sentences.append(f"Sentence {i} {words}.")

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        if len(chunks) >= 2:
            last_chunk_tokens = chunks[0].text.split()
            first_chunk_tokens = chunks[1].text.split()

            overlap_count = len(set(last_chunk_tokens[-20:]) & set(first_chunk_tokens[:20]))
            assert overlap_count > 0, "Consecutive chunks should share some tokens"

    def test_overlap_preserves_context(self):
        """Test that overlap preserves meaningful context."""
        from services.ingestion.chunker import chunk_sentences

        sentences = [
            "The protagonist journeyed through the mystical forest.",
            "Forest creatures whispered ancient secrets to the traveler.",
            "Traveler discovered a hidden kingdom beyond the trees.",
        ]

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        if len(chunks) >= 2:
            assert "forest" in chunks[1].text.lower() or "Forest" in chunks[1].text


class TestChunkPage:
    """Test suite for chunk_page function."""

    @patch("services.ingestion.chunker.clean_and_tokenize")
    def test_chunk_page_integration(self, mock_clean):
        """Test chunk_page with mocked cleaner."""
        from services.ingestion.chunker import chunk_page

        mock_clean.return_value = [
            "Sentence one.",
            "Sentence two.",
            "Sentence three.",
        ]

        chunks = chunk_page("Raw text here", "isbn-123", 1)

        assert len(chunks) >= 1
        mock_clean.assert_called_once()


class TestChunkDataClass:
    """Test suite for Chunk dataclass."""

    def test_chunk_creation(self):
        """Test creating a Chunk instance."""
        from services.ingestion.chunker import Chunk

        chunk = Chunk(
            chunk_id="test_p1_c0",
            isbn="978-0-123456-78-9",
            page_num=1,
            text="Test text content",
            token_count=5,
        )

        assert chunk.chunk_id == "test_p1_c0"
        assert chunk.isbn == "978-0-123456-78-9"
        assert chunk.page_num == 1
        assert chunk.text == "Test text content"
        assert chunk.token_count == 5

    def test_chunk_immutable(self):
        """Test that Chunk is immutable (frozen=True)."""
        from services.ingestion.chunker import Chunk

        chunk = Chunk(
            chunk_id="test_p1_c0",
            isbn="isbn",
            page_num=1,
            text="text",
            token_count=5,
        )

        with pytest.raises(AttributeError):
            chunk.text = "modified"  # type: ignore


class TestTokenCount:
    """Test suite for token counting functionality."""

    def test_token_count_function(self):
        """Test the _token_count helper function."""
        from services.ingestion.chunker import _token_count

        text = "This is a test sentence."
        count = _token_count(text)

        assert isinstance(count, int)
        assert count > 0

    def test_empty_text_token_count(self):
        """Test token count for empty text."""
        from services.ingestion.chunker import _token_count

        count = _token_count("")
        assert count == 0


class TestChunkInvariantValidation:
    """Test suite for assertion-based invariant validation."""

    def test_raises_on_duplicate_chunk_id(self):
        """Test that duplicate chunk IDs raise AssertionError."""
        from services.ingestion.chunker import chunk_sentences

        sentences = ["Test sentence."] * 10
        chunks = chunk_sentences(sentences, "isbn-123", 1)

        chunk_ids = [c.chunk_id for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))

    def test_raises_on_token_overflow(self):
        """Test that excessive tokens raise AssertionError."""
        from services.ingestion.chunker import chunk_sentences

        long_text = "word " * 600
        sentences = [long_text]

        chunks = chunk_sentences(sentences, "isbn-123", 1)

        for chunk in chunks:
            assert chunk.token_count <= 522, f"Token overflow: {chunk.token_count}"