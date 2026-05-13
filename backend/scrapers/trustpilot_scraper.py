"""Trustpilot scraper using Lobstr.io managed service.

Per RESEARCH.md: Trustpilot has strong Cloudflare anti-bot protection and no
public API.  Lobstr.io ($2/1K reviews, 100 free/month) handles the scraping
and returns structured JSON.  This module wraps that API.

Extractable fields (Lobstr.io):
  review_id, author, date_published, headline, body, language, star_rating,
  verification_level, reviewer_country, experience_date, likes, owner_reply

Usage:
  python trustpilot_scraper.py [--tool-slug bolt-new] [--limit 100]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

# Allow running from any directory — resolve project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Tool
from scrapers.db_helpers import (
    get_or_create_collection_run,
    finish_collection_run,
    review_exists,
    store_review,
    recalc_sentiment_summary,
)
from config import settings

LOBSTR_BASE = "https://api.lobstr.io/v1"

# Trustpilot URLs from TOOLS_CATALOG.md
TOOL_TRUSTPILOT_URLS: dict[str, str] = {
    "lovable": "https://www.trustpilot.com/review/lovable.dev",
    "bolt-new": "https://www.trustpilot.com/review/bolt.new",
    "replit-agent": "https://www.trustpilot.com/review/replit.com",
    "v0": "https://www.trustpilot.com/review/v0.dev",
    "cursor": "https://www.trustpilot.com/review/cursor.com",
    "windsurf": "https://www.trustpilot.com/review/codeium.com",
    "claude-code": "https://www.trustpilot.com/review/anthropic.com",
    "taskade-genesis": "https://www.trustpilot.com/review/taskade.com",
    "bubble": "https://www.trustpilot.com/review/bubble.io",
    "glide": "https://www.trustpilot.com/review/www.glideapps.com",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def fetch_trustpilot_reviews(
    url: str,
    api_key: str,
    limit: int = 100,
) -> list[dict]:
    """Call Lobstr.io to fetch reviews for a Trustpilot page.

    Returns a list of review dicts.  Consult Lobstr.io docs for the exact
    response shape; this implementation uses a generic pattern.
    """
    # Lobstr.io example endpoint (check their docs for exact path)
    endpoint = f"{LOBSTR_BASE}/trustpilot/reviews"

    # NOTE: Lobstr.io API may require a POST with the target URL + options.
    # The exact payload depends on their current API.  This is the documented pattern.
    resp = httpx.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "url": url,
            "limit": limit,
            "sort": "newest",
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("reviews", data.get("results", []))


def _parse_lobstr_review(item: dict) -> dict:
    """Normalize a Lobstr.io review item to our internal fields."""
    posted_raw = item.get("date_published") or item.get("datePublished")
    posted_at = None
    if posted_raw:
        try:
            posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    return {
        "source_id": str(item.get("review_id") or item.get("reviewId")),
        "title": item.get("headline") or item.get("title"),
        "body": item.get("body") or item.get("text") or "",
        "url": item.get("url"),
        "author": item.get("author") or item.get("author_name"),
        "author_verified": bool(item.get("verified") or item.get("verification_level") == "verified"),
        "rating": int(item["star_rating"]) if item.get("star_rating") else None,
        "posted_at": posted_at,
    }


def scrape_trustpilot(
    db: Session,
    tool_slug: str | None = None,
    limit: int = 100,
    dry_run: bool = False,
) -> dict:
    """Scrape Trustpilot reviews via Lobstr.io for one or all tools."""
    api_key = settings.lobstr_api_key
    if not api_key:
        logger.warning("LOBSTR_API_KEY not set — Trustpilot scraper disabled")
        return {}

    if tool_slug:
        tools = db.query(Tool).filter(Tool.slug == tool_slug).all()
    else:
        tools = db.query(Tool).all()

    results: dict[str, int] = {}

    for tool in tools:
        tp_url = TOOL_TRUSTPILOT_URLS.get(tool.slug)
        if not tp_url:
            logger.debug(f"No Trustpilot URL for {tool.slug}, skipping")
            continue

        run = get_or_create_collection_run(db, "trustpilot", tool.slug)
        new_count = 0
        collected = 0

        try:
            reviews = fetch_trustpilot_reviews(tp_url, api_key, limit=limit)
            collected = len(reviews)
        except httpx.HTTPError as exc:
            logger.error(f"Lobstr.io API error for {tool.slug}: {exc}")
            finish_collection_run(db, run, items_collected=0, items_new=0, error=str(exc))
            continue

        for item in reviews:
            parsed = _parse_lobstr_review(item)
            if not parsed["body"]:
                continue
            if review_exists(db, "trustpilot", parsed["source_id"]):
                continue

            if dry_run:
                logger.info(f"[DRY RUN] Trustpilot: {parsed['title'][:80]}")
                new_count += 1
                continue

            store_review(
                db,
                tool_id=tool.id,
                source="trustpilot",
                source_id=parsed["source_id"],
                title=parsed["title"],
                body=parsed["body"],
                url=parsed["url"],
                author=parsed["author"],
                author_verified=parsed["author_verified"],
                rating=parsed["rating"],
                posted_at=parsed["posted_at"],
            )
            new_count += 1

        if new_count > 0 and not dry_run:
            recalc_sentiment_summary(db, tool.id, "trustpilot")

        finish_collection_run(db, run, items_collected=collected, items_new=new_count)
        results[tool.slug] = new_count
        logger.info(f"Trustpilot [{tool.slug}]: collected {collected}, new {new_count}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trustpilot scraper (Lobstr.io)")
    parser.add_argument("--tool-slug", help="Scrape a single tool")
    parser.add_argument("--limit", type=int, default=100, help="Max reviews to fetch")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        scrape_trustpilot(db, tool_slug=args.tool_slug, limit=args.limit, dry_run=args.dry_run)
    finally:
        db.close()
