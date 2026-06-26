"""Initial migration - create all tables

Revision ID: 001
Revises: 
Create Date: 2026-04-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'books',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('isbn', sa.String(length=13), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('author', sa.String(length=300), nullable=False),
        sa.Column('genre_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('synopsis', sa.Text(), nullable=True),
        sa.Column('cover_url', sa.String(length=1000), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('isbn')
    )
    op.create_index('idx_books_title', 'books', ['title'])
    op.create_index('idx_books_author', 'books', ['author'])
    op.create_index('idx_books_genre_tags', 'books', ['genre_tags'], postgresql_using='gin')

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index('idx_users_created', 'users', ['created_at'])

    op.create_table(
        'reading_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('isbn', sa.String(length=13), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('dwell_seconds', sa.Integer(), nullable=True),
        sa.Column('page_num', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['isbn'], ['books.isbn'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reading_events_user_isbn', 'reading_events', ['user_id', 'isbn'])
    op.create_index('idx_reading_events_created', 'reading_events', ['created_at'])
    op.create_index('idx_reading_events_user_id', 'reading_events', ['user_id'])

    op.create_table(
        'ratings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('isbn', sa.String(length=13), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('review', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['isbn'], ['books.isbn'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'isbn', name='uq_ratings_user_isbn')
    )
    op.create_index('idx_ratings_user_id', 'ratings', ['user_id'])
    op.create_index('idx_ratings_isbn', 'ratings', ['isbn'])
    op.create_index('idx_ratings_score', 'ratings', ['score'])

    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('isbn', sa.String(length=13), nullable=False),
        sa.Column('page_num', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('highlighted_text', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['isbn'], ['books.isbn'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bookmarks_user_isbn', 'bookmarks', ['user_id', 'isbn'])
    op.create_index('idx_bookmarks_user_id', 'bookmarks', ['user_id'])


def downgrade() -> None:
    op.drop_table('bookmarks')
    op.drop_table('ratings')
    op.drop_table('reading_events')
    op.drop_table('users')
    op.drop_table('books')