"""
tests/shared/test_models.py
Tests for SQLAlchemy ORM models.
"""
import uuid
import pytest
from datetime import datetime


class TestBookModel:
    """Test suite for Book ORM model."""

    def test_book_creation(self):
        """Test creating a Book instance."""
        from shared.models import Book

        book = Book(
            isbn="978-0-123456-78-9",
            title="Test Book",
            author="Test Author",
            genre_tags=["fiction", "drama"],
            synopsis="A test book synopsis",
            page_count=200,
            language="en",
        )

        assert book.isbn == "978-0-123456-78-9"
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.genre_tags == ["fiction", "drama"]
        assert book.synopsis == "A test book synopsis"
        assert book.page_count == 200
        assert book.language == "en"
        assert book.id is not None
        assert book.created_at is not None

    def test_book_default_values(self):
        """Test default values for Book model."""
        from shared.models import Book

        book = Book(
            isbn="978-0-123456-78-9",
            title="Test Book",
            author="Test Author",
        )

        assert book.genre_tags == []
        assert book.language == "en"
        assert book.indexed_at is None


class TestUserModel:
    """Test suite for User ORM model."""

    def test_user_creation(self):
        """Test creating a User instance."""
        from shared.models import User

        user = User(
            external_id="user-123",
            is_active=True,
        )

        assert user.external_id == "user-123"
        assert user.is_active is True
        assert user.id is not None
        assert user.created_at is not None


class TestReadingEventModel:
    """Test suite for ReadingEvent ORM model."""

    def test_reading_event_creation(self):
        """Test creating a ReadingEvent instance."""
        from shared.models import ReadingEvent, Book, User

        user = User(external_id="user-123")
        book = Book(
            isbn="978-0-123456-78-9",
            title="Test Book",
            author="Test Author",
        )

        event = ReadingEvent(
            user_id=user.id,
            isbn=book.isbn,
            event_type="read_start",
            dwell_seconds=120,
            page_num=1,
            session_id="session-123",
        )

        assert event.user_id == user.id
        assert event.isbn == book.isbn
        assert event.event_type == "read_start"
        assert event.dwell_seconds == 120
        assert event.page_num == 1
        assert event.session_id == "session-123"


class TestRatingModel:
    """Test suite for Rating ORM model."""

    def test_rating_creation(self):
        """Test creating a Rating instance."""
        from shared.models import Rating, Book, User

        user = User(external_id="user-123")
        book = Book(
            isbn="978-0-123456-78-9",
            title="Test Book",
            author="Test Author",
        )

        rating = Rating(
            user_id=user.id,
            isbn=book.isbn,
            score=5,
            review="Great book!",
        )

        assert rating.user_id == user.id
        assert rating.isbn == book.isbn
        assert rating.score == 5
        assert rating.review == "Great book!"

    def test_rating_score_validation(self):
        """Test rating score bounds."""
        from shared.models import Rating

        rating = Rating(
            user_id=uuid.uuid4(),
            isbn="978-0-123456-78-9",
            score=1,
        )
        assert rating.score == 1

        rating.score = 5
        assert rating.score == 5


class TestBookmarkModel:
    """Test suite for Bookmark ORM model."""

    def test_bookmark_creation(self):
        """Test creating a Bookmark instance."""
        from shared.models import Bookmark, Book, User

        user = User(external_id="user-123")
        book = Book(
            isbn="978-0-123456-78-9",
            title="Test Book",
            author="Test Author",
        )

        bookmark = Bookmark(
            user_id=user.id,
            isbn=book.isbn,
            page_num=42,
            note="Important passage",
            highlighted_text="Some highlighted text",
        )

        assert bookmark.user_id == user.id
        assert bookmark.isbn == book.isbn
        assert bookmark.page_num == 42
        assert bookmark.note == "Important passage"
        assert bookmark.highlighted_text == "Some highlighted text"


class TestModelRelationships:
    """Test suite for model relationships."""

    def test_book_relationships(self):
        """Test Book has relationships to other models."""
        from shared.models import Book, ReadingEvent, Rating, Bookmark

        book = Book(
            isbn="978-0-123456-78-9",
            title="Test Book",
            author="Test Author",
        )

        assert hasattr(book, "reading_events")
        assert hasattr(book, "ratings")
        assert hasattr(book, "bookmarks")

    def test_user_relationships(self):
        """Test User has relationships to other models."""
        from shared.models import User, ReadingEvent, Rating, Bookmark

        user = User(external_id="user-123")

        assert hasattr(user, "reading_events")
        assert hasattr(user, "ratings")
        assert hasattr(user, "bookmarks")