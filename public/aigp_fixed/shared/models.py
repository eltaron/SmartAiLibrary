"""
shared/models.py
SQLAlchemy ORM models for Smart AI Library.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class Book(Base):
    __tablename__ = "books"

    isbn: Mapped[str] = mapped_column(String(13), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str] = mapped_column(String(300), nullable=False)
    genre_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), default_factory=list)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reading_events: Mapped[list["ReadingEvent"]] = relationship(
        back_populates="book", cascade="all, delete-orphan",
    )
    ratings: Mapped[list["Rating"]] = relationship(
        back_populates="book", cascade="all, delete-orphan",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="book", cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_books_title", "title"),
        Index("idx_books_author", "author"),
        Index("idx_books_genre_tags", "genre_tags", postgresql_using="gin"),
    )


class User(Base):
    __tablename__ = "users"

    external_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    preferences: Mapped[dict | None] = mapped_column(default=None)

    reading_events: Mapped[list["ReadingEvent"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    ratings: Mapped[list["Rating"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )

    __table_args__ = (Index("idx_users_created", "created_at"),)


class ReadingEvent(Base):
    __tablename__ = "reading_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    isbn: Mapped[str] = mapped_column(
        String(13), ForeignKey("books.isbn", ondelete="CASCADE"), nullable=False, index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    dwell_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_num: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    user: Mapped["User"] = relationship(back_populates="reading_events")
    book: Mapped["Book"] = relationship(back_populates="reading_events")

    __table_args__ = (
        Index("idx_reading_events_user_isbn", "user_id", "isbn"),
        Index("idx_reading_events_created", "created_at"),
    )


class Rating(Base):
    __tablename__ = "ratings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    isbn: Mapped[str] = mapped_column(
        String(13), ForeignKey("books.isbn", ondelete="CASCADE"), nullable=False, index=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="ratings")
    book: Mapped["Book"] = relationship(back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("user_id", "isbn", name="uq_ratings_user_isbn"),
        Index("idx_ratings_score", "score"),
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    isbn: Mapped[str] = mapped_column(
        String(13), ForeignKey("books.isbn", ondelete="CASCADE"), nullable=False, index=True,
    )
    page_num: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    highlighted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="bookmarks")
    book: Mapped["Book"] = relationship(back_populates="bookmarks")

    __table_args__ = (Index("idx_bookmarks_user_isbn", "user_id", "isbn"),)
