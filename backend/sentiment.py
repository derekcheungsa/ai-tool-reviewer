"""Sentiment analysis using VADER (Valence Aware Dictionary and sEntiment Reasoner).

VADER is optimized for social-media / short text — ideal for reviews.
Returns compound score (-1 to +1) and categorical label.

Two-tier strategy (per RESEARCH.md):
  Tier 1 — VADER for fast, free, bulk scoring (this module).
  Tier 2 — LLM-based for deep pull-quotes (optional, gate on OPENAI_API_KEY).

Usage:
    from sentiment import analyze_sentiment
    result = analyze_sentiment("Great UI but the export is completely broken.")
    # => {"score": -0.34, "label": "mixed", "pos": 0.2, "neg": 0.4, "neu": 0.4}
"""

from __future__ import annotations

from typing import TypedDict

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


class SentimentResult(TypedDict):
    score: float        # compound: -1.0 (neg) .. +1.0 (pos)
    label: str          # positive | negative | neutral | mixed
    pos: float          # proportion positive
    neg: float          # proportion negative
    neu: float          # proportion neutral


def analyze_sentiment(text: str) -> SentimentResult:
    """Run VADER sentiment on a single text string."""
    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    # Classify: use mixed when both pos + neg signals are present
    if abs(compound) < 0.05:
        label = "neutral"
    elif compound >= 0.05 and scores["neg"] >= 0.1:
        label = "mixed"
    elif compound <= -0.05 and scores["pos"] >= 0.1:
        label = "mixed"
    elif compound >= 0.05:
        label = "positive"
    else:
        label = "negative"

    return SentimentResult(
        score=round(compound, 4),
        label=label,
        pos=round(scores["pos"], 4),
        neg=round(scores["neg"], 4),
        neu=round(scores["neu"], 4),
    )


def summarize_sentiments(
    results: list[SentimentResult],
    ratings: list[int] | None = None,
) -> dict:
    """Aggregate a list of sentiment results into a summary.

    Returns keys matching SentimentSummary model fields.
    """
    n = len(results)
    if n == 0:
        return {
            "avg_sentiment": None,
            "positive_pct": None,
            "neutral_pct": None,
            "negative_pct": None,
            "review_count": 0,
        }

    labels = [r["label"] for r in results]
    scores = [r["score"] for r in results]

    return {
        "avg_sentiment": round(sum(scores) / n, 4),
        "positive_pct": round(100.0 * labels.count("positive") / n, 1),
        "neutral_pct": round(100.0 * labels.count("neutral") / n, 1),
        "negative_pct": round(100.0 * labels.count("negative") / n, 1),
        # mixed is folded into the distribution — pos+neg+neu won't always sum to 100
        "review_count": n,
    }
