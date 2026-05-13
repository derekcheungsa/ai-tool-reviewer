"""Pydantic schemas for API request/response serialization."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Tool ─────────────────────────────────────────────────────────────

class ToolOut(BaseModel):
    id: str
    name: str
    slug: str
    category: str
    pricing: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ToolDetailOut(ToolOut):
    """Tool + its reviews + sentiment summaries."""
    reviews: list[ReviewOut] = []
    sentiment_summaries: list[SentimentSummaryOut] = []


# ── Review ───────────────────────────────────────────────────────────

class ReviewOut(BaseModel):
    id: str
    tool_id: str
    source: str
    source_id: str
    rating: Optional[int] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    title: Optional[str] = None
    body: str
    url: Optional[str] = None
    author: Optional[str] = None
    author_verified: bool = False
    posted_at: Optional[datetime] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}


# ── Sentiment Summary ────────────────────────────────────────────────

class SentimentSummaryOut(BaseModel):
    id: str
    tool_id: str
    source: str
    avg_rating: Optional[float] = None
    avg_sentiment: Optional[float] = None
    positive_pct: Optional[float] = None
    neutral_pct: Optional[float] = None
    negative_pct: Optional[float] = None
    review_count: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class ToolWithSummary(ToolOut):
    """Tool card with aggregated sentiment (for list views)."""
    sentiment_summaries: list[SentimentSummaryOut] = []


# ── Compare ──────────────────────────────────────────────────────────

class CompareTool(BaseModel):
    """One tool's data in a comparison response."""
    tool: ToolOut
    reviews: list[ReviewOut] = []
    sentiment_summaries: list[SentimentSummaryOut] = []


class CompareResponse(BaseModel):
    tools: list[CompareTool]


# ── Stats ────────────────────────────────────────────────────────────

class StatsOut(BaseModel):
    total_tools: int
    total_reviews: int
    sources: dict[str, int]           # {"reddit": N, "trustpilot": N, "g2": N}
    top_rated: list[ToolOut]          # top 5 by avg sentiment
    most_reviewed: list[ToolOut]      # top 5 by review count
    categories: dict[str, int]        # tool count per category
