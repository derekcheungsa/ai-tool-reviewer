"""SQLAlchemy ORM models for the AI tool review aggregator.

Matches the schema from RESEARCH.md plus the task specification:
  - tools:  id, name, category, pricing, description, created_at
  - reviews:  id, tool_id, source, rating, sentiment_score, title, body, url, author, posted_at, scraped_at
  - sentiment_summary:  id, tool_id, source, avg_rating, avg_sentiment, positive_pct, neutral_pct,
                         negative_pct, review_count, updated_at
  - collection_runs: tracking table for scraper runs
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index, Boolean,
)
from sqlalchemy.orm import relationship

from database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


# ── Tools ────────────────────────────────────────────────────────────

class Tool(Base):
    __tablename__ = "tools"

    id          = Column(String(12), primary_key=True, default=_new_id)
    name        = Column(String(100), nullable=False, unique=True)
    slug        = Column(String(100), nullable=False, unique=True)
    category    = Column(String(50), nullable=False)
    pricing     = Column(Text, nullable=True)       # JSON string
    description = Column(Text, nullable=True)
    website     = Column(String(255), nullable=True)
    created_at  = Column(DateTime, nullable=False, default=_utcnow)

    reviews = relationship("Review", back_populates="tool", cascade="all, delete-orphan")
    sentiment_summaries = relationship("SentimentSummary", back_populates="tool", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tool {self.name}>"


# ── Reviews ──────────────────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id              = Column(String(12), primary_key=True, default=_new_id)
    tool_id         = Column(String(12), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    source          = Column(String(20), nullable=False)   # reddit | trustpilot | g2
    source_id       = Column(String(255), nullable=False)   # platform-specific unique id
    rating          = Column(Integer, nullable=True)        # 1-5 star rating if available
    sentiment_score = Column(Float, nullable=True)          # -1.0 to 1.0
    sentiment_label = Column(String(20), nullable=True)     # positive | negative | neutral | mixed
    title           = Column(Text, nullable=True)
    body            = Column(Text, nullable=False)
    url             = Column(Text, nullable=True)
    author          = Column(String(255), nullable=True)
    author_verified = Column(Boolean, default=False)
    posted_at       = Column(DateTime, nullable=True)
    scraped_at      = Column(DateTime, nullable=False, default=_utcnow)

    tool = relationship("Tool", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_review_source_id"),
        CheckConstraint(
            "source IN ('reddit', 'trustpilot', 'g2')",
            name="ck_review_source",
        ),
        Index("ix_reviews_tool_id", "tool_id"),
        Index("ix_reviews_source", "source"),
        Index("ix_reviews_tool_source", "tool_id", "source"),
        Index("ix_reviews_posted_at", "posted_at"),
    )

    def __repr__(self) -> str:
        return f"<Review {self.source}:{self.source_id}>"


# ── Sentiment Summaries ──────────────────────────────────────────────

class SentimentSummary(Base):
    __tablename__ = "sentiment_summaries"

    id             = Column(String(12), primary_key=True, default=_new_id)
    tool_id        = Column(String(12), ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    source         = Column(String(20), nullable=False)
    avg_rating     = Column(Float, nullable=True)
    avg_sentiment  = Column(Float, nullable=True)          # average compound score
    positive_pct   = Column(Float, nullable=True)          # 0-100
    neutral_pct    = Column(Float, nullable=True)
    negative_pct   = Column(Float, nullable=True)
    review_count   = Column(Integer, nullable=False, default=0)
    updated_at     = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    tool = relationship("Tool", back_populates="sentiment_summaries")

    __table_args__ = (
        UniqueConstraint("tool_id", "source", name="uq_sentiment_tool_source"),
        Index("ix_sentiment_tool_id", "tool_id"),
    )

    def __repr__(self) -> str:
        return f"<SentimentSummary {self.tool_id}:{self.source}>"


# ── Collection Runs (tracking) ───────────────────────────────────────

class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id              = Column(String(12), primary_key=True, default=_new_id)
    source          = Column(String(20), nullable=False)
    tool_name       = Column(String(100), nullable=True)   # None = all tools
    started_at      = Column(DateTime, nullable=False, default=_utcnow)
    ended_at        = Column(DateTime, nullable=True)
    items_collected = Column(Integer, default=0)
    items_new       = Column(Integer, default=0)
    status          = Column(String(20), default="running")
    error_message   = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_collection_runs_source", "source"),
        Index("ix_collection_runs_status", "status"),
    )
