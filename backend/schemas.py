"""Pydantic schemas for API request/response serialization.

Uses camelCase aliases so the JSON matches the TypeScript frontend types.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field
from pydantic.alias_generators import to_camel


def _camel_config():
    return {
        "from_attributes": True,
        "alias_generator": to_camel,
        "populate_by_name": True,
    }


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

    model_config = _camel_config()


class ToolDetailOut(ToolOut):
    """Tool + its reviews + sentiment summaries.

    The frontend expects:
      - sentimentSummaries: array (per-source breakdowns)
      - sentimentSummary:  single merged object (for summary cards)
      - sentimentBySource: alias for sentimentSummaries (tool detail page)
    """
    reviews: list[ReviewOut] = []
    sentiment_summaries: list[SentimentSummaryOut] = []

    model_config = _camel_config()

    @computed_field
    @property
    def sentiment_by_source(self) -> list[SentimentSummaryOut]:
        """Per-source breakdowns — aliased for frontend tool detail page."""
        return self.sentiment_summaries

    @computed_field
    @property
    def sentiment_summary(self) -> SentimentSummaryOut | None:
        """Merge per-source summaries into one aggregated object."""
        if not self.sentiment_summaries:
            return None

        total_reviews = sum(s.review_count for s in self.sentiment_summaries)
        if total_reviews == 0:
            return None

        weighted_rating = sum(
            (s.avg_rating or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_sentiment = sum(
            (s.avg_sentiment or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_pos = sum(
            (s.positive_pct or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_neu = sum(
            (s.neutral_pct or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_neg = sum(
            (s.negative_pct or 0) * s.review_count
            for s in self.sentiment_summaries
        )

        merged_rating = round(weighted_rating / total_reviews, 2)
        merged_rating = max(0.0, min(5.0, merged_rating))

        return SentimentSummaryOut(
            id="merged",
            tool_id=self.id,
            source="all",
            avg_rating=merged_rating,
            avg_sentiment=round(weighted_sentiment / total_reviews, 4),
            positive_pct=round(weighted_pos / total_reviews, 1),
            neutral_pct=round(weighted_neu / total_reviews, 1),
            negative_pct=round(weighted_neg / total_reviews, 1),
            review_count=total_reviews,
            updated_at=max(s.updated_at for s in self.sentiment_summaries),
        )


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
    url: Optional[str] = Field(None, serialization_alias="sourceUrl")
    author: Optional[str] = Field(None, serialization_alias="authorName")
    author_role: Optional[str] = Field(None, serialization_alias="authorRole")
    author_verified: bool = False
    posted_at: Optional[datetime] = Field(None, serialization_alias="publishedAt")
    scraped_at: datetime

    model_config = _camel_config()


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

    model_config = _camel_config()


class ToolWithSummary(ToolOut):
    """Tool card with aggregated sentiment (for list views).

    The frontend expects:
      - sentimentSummaries: array (per-source breakdowns)
      - sentimentSummary:  single merged object (for card display)
    """
    sentiment_summaries: list[SentimentSummaryOut] = []

    model_config = _camel_config()

    @computed_field
    @property
    def sentiment_summary(self) -> SentimentSummaryOut | None:
        """Merge per-source summaries into one aggregated object."""
        if not self.sentiment_summaries:
            return None

        total_reviews = sum(s.review_count for s in self.sentiment_summaries)
        if total_reviews == 0:
            return None

        # Weighted averages
        weighted_rating = sum(
            (s.avg_rating or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_sentiment = sum(
            (s.avg_sentiment or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_pos = sum(
            (s.positive_pct or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_neu = sum(
            (s.neutral_pct or 0) * s.review_count
            for s in self.sentiment_summaries
        )
        weighted_neg = sum(
            (s.negative_pct or 0) * s.review_count
            for s in self.sentiment_summaries
        )

        merged_rating = round(weighted_rating / total_reviews, 2)
        # Clamp to valid 0-5 range
        merged_rating = max(0.0, min(5.0, merged_rating))

        return SentimentSummaryOut(
            id="merged",
            tool_id=self.id,
            source="all",
            avg_rating=merged_rating,
            avg_sentiment=round(weighted_sentiment / total_reviews, 4),
            positive_pct=round(weighted_pos / total_reviews, 1),
            neutral_pct=round(weighted_neu / total_reviews, 1),
            negative_pct=round(weighted_neg / total_reviews, 1),
            review_count=total_reviews,
            updated_at=max(s.updated_at for s in self.sentiment_summaries),
        )


# ── Compare ──────────────────────────────────────────────────────────

class CompareTool(BaseModel):
    """One tool's data in a comparison response."""
    tool: ToolOut
    reviews: list[ReviewOut] = []
    sentiment_summaries: list[SentimentSummaryOut] = []

    model_config = _camel_config()


class CompareResponse(BaseModel):
    tools: list[CompareTool]

    model_config = _camel_config()


# ── Stats ────────────────────────────────────────────────────────────

class StatsOut(BaseModel):
    total_tools: int
    total_reviews: int
    sources: dict[str, int]           # {"reddit": N, "trustpilot": N, "g2": N}
    top_rated: list[ToolOut]          # top 5 by avg sentiment
    most_reviewed: list[ToolOut]      # top 5 by review count
    categories: dict[str, int]        # tool count per category

    model_config = _camel_config()
