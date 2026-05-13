"""Shared utilities for scraper scripts.

DB connection, dedup helpers, sentiment-summary recalc.
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Allow running from any directory — resolve project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sqlalchemy.orm import Session
from sqlalchemy import func

from database import SessionLocal
from models import Review, SentimentSummary, CollectionRun
from sentiment import analyze_sentiment, summarize_sentiments


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_collection_run(db: Session, source: str, tool_name: str | None = None) -> CollectionRun:
    """Start a new collection run record."""
    run = CollectionRun(source=source, tool_name=tool_name, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_collection_run(
    db: Session, run: CollectionRun,
    items_collected: int, items_new: int,
    error: str | None = None,
):
    """Mark a collection run as finished (or failed)."""
    run.ended_at = _utcnow()
    run.items_collected = items_collected
    run.items_new = items_new
    run.status = "failed" if error else "completed"
    run.error_message = error
    db.commit()


def review_exists(db: Session, source: str, source_id: str) -> bool:
    """Check whether a review has already been stored (dedup)."""
    return (
        db.query(Review)
        .filter(Review.source == source, Review.source_id == source_id)
        .first()
        is not None
    )


def store_review(
    db: Session,
    *,
    tool_id: str,
    source: str,
    source_id: str,
    title: str | None = None,
    body: str,
    url: str | None = None,
    author: str | None = None,
    author_verified: bool = False,
    rating: int | None = None,
    posted_at: datetime | None = None,
) -> Review:
    """Parse sentiment, create Review row, commit.  Returns the new Review."""
    sent = analyze_sentiment(body)
    review = Review(
        tool_id=tool_id,
        source=source,
        source_id=source_id,
        title=title,
        body=body,
        url=url,
        author=author,
        author_verified=author_verified,
        rating=rating,
        sentiment_score=sent["score"],
        sentiment_label=sent["label"],
        posted_at=posted_at,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def recalc_sentiment_summary(db: Session, tool_id: str, source: str):
    """Recompute the SentimentSummary row for (tool, source) after new reviews."""
    reviews = (
        db.query(Review)
        .filter(Review.tool_id == tool_id, Review.source == source)
        .all()
    )
    sent_results = [
        {"score": r.sentiment_score or 0, "label": r.sentiment_label or "neutral"}
        for r in reviews
    ]
    ratings = [r.rating for r in reviews if r.rating is not None]
    agg = summarize_sentiments(sent_results, ratings)

    summary = (
        db.query(SentimentSummary)
        .filter(
            SentimentSummary.tool_id == tool_id,
            SentimentSummary.source == source,
        )
        .first()
    )
    if summary is None:
        summary = SentimentSummary(tool_id=tool_id, source=source)
        db.add(summary)

    summary.avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    summary.avg_sentiment = agg["avg_sentiment"]
    summary.positive_pct = agg["positive_pct"]
    summary.neutral_pct = agg["neutral_pct"]
    summary.negative_pct = agg["negative_pct"]
    summary.review_count = agg["review_count"]
    summary.updated_at = _utcnow()

    db.commit()
