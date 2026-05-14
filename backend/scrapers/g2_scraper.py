"""G2 scraper using RapidAPI's Advanced G2 Scraper.

Per RESEARCH.md: G2 has a free tier on RapidAPI via the Advanced G2 Scraper
(https://github.com/biegehydra/Advanced-G2-Scraper, MIT licensed).

Endpoints:
  GET /product/{slug}/reviews?page=N  → structured review JSON

Review structure returned:
  - rating (1-5 stars)
  - title (review headline)
  - likes (pros)
  - dislikes (cons)
  - author name, role, company size
  - verified status
  - timestamp

Usage:
  python g2_scraper.py [--tool-slug cursor] [--max-pages 3]
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

RAPIDAPI_HOST = "g2-products-reviews-users2.p.rapidapi.com"
RAPIDAPI_BASE = f"https://{RAPIDAPI_HOST}"

# G2 product slugs (from RESEARCH.md + TOOLS_CATALOG.md)
TOOL_G2_SLUGS: dict[str, str] = {
    "bolt-new": "bolt-new",
    "replit-agent": "replit",
    "cursor": "cursor",
    "github-copilot": "github-copilot",
    "windsurf": "exafunction-windsurf",
    "claude-code": "anthropic-claude-code",
    "codex-cli": "openai-codex",
    "aider": "aider-chat",
    "v0": "vercel",
    "bubble": "bubble",
    "glide": "glide",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def fetch_g2_reviews(g2_slug: str, api_key: str, page: int = 1) -> dict:
    """Fetch one page of G2 reviews via RapidAPI."""
    resp = httpx.get(
        f"{RAPIDAPI_BASE}/product/{g2_slug}/reviews",
        headers={
            "X-RapidAPI-Host": RAPIDAPI_HOST,
            "X-RapidAPI-Key": api_key,
        },
        params={"page": page},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


GARBAGE_MARKERS = [
    "Sponsored",
    "Leave a Review",
    "Answer a few questions",
    "Visit Website",
    "out of 5 stars",
    "Save to board",
    "Product Information",
    "freemium-gray-banner",
    "Profile Status",
    "G2 Sort",
    "Search reviews",
    "View Filters",
    "Company Size",
    "User Role",
    "Clear Results",
    "View Results",
    "G2 reviews are authentic",
    "Review Summary",
    "Generated using AI",
    "Pros & Cons",
    "Generated from real user reviews",
]


def _is_garbage(body: str) -> bool:
    """Detect page chrome / non-review content from G2 scraping."""
    if not body or len(body.strip()) < 20:
        return True
    return any(marker.lower() in body.lower() for marker in GARBAGE_MARKERS)


def _parse_g2_review(item: dict) -> dict | None:
    """Normalize a G2 review item to our internal fields.

    Returns None if the item is page chrome / not a real review.
    """
    posted_raw = item.get("timestamp") or item.get("createdAt")
    posted_at = None
    if posted_raw:
        try:
            posted_at = datetime.fromisoformat(posted_raw.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    # G2 has structured pros/cons — combine for full-text sentiment
    likes = item.get("likes") or item.get("pros") or ""
    dislikes = item.get("dislikes") or item.get("cons") or ""
    body = f"Pros: {likes}\nCons: {dislikes}" if likes or dislikes else (item.get("body") or "")

    body = body.strip()

    # Reject garbage (page chrome, not real reviews)
    if _is_garbage(body):
        return None

    return {
        "source_id": str(item.get("id") or item.get("reviewId")),
        "title": item.get("title") or item.get("headline"),
        "body": body,
        "url": item.get("url"),
        "author": item.get("author") or item.get("authorName"),
        "author_verified": bool(item.get("verified") or item.get("verifiedCurrentUser")),
        "rating": int(item["rating"]) if item.get("rating") else None,
        "posted_at": posted_at,
    }


def scrape_g2(
    db: Session,
    tool_slug: str | None = None,
    max_pages: int = 3,
    dry_run: bool = False,
) -> dict:
    """Scrape G2 reviews via RapidAPI for one or all tools."""
    api_key = settings.rapidapi_key
    if not api_key:
        logger.warning("RAPIDAPI_KEY not set — G2 scraper disabled")
        return {}

    if tool_slug:
        tools = db.query(Tool).filter(Tool.slug == tool_slug).all()
    else:
        tools = db.query(Tool).all()

    results: dict[str, int] = {}

    for tool in tools:
        g2_slug = TOOL_G2_SLUGS.get(tool.slug)
        if not g2_slug:
            logger.debug(f"No G2 slug for {tool.slug}, skipping")
            continue

        run = get_or_create_collection_run(db, "g2", tool.slug)
        new_count = 0
        collected = 0

        for page in range(1, max_pages + 1):
            try:
                data = fetch_g2_reviews(g2_slug, api_key, page=page)
            except httpx.HTTPError as exc:
                logger.error(f"G2 API error for {tool.slug} page {page}: {exc}")
                continue

            reviews = data.get("reviews", data.get("results", []))
            if not reviews:
                break  # no more pages

            collected += len(reviews)

            for item in reviews:
                parsed = _parse_g2_review(item)
                if parsed is None:
                    continue
                if not parsed["body"]:
                    continue
                if review_exists(db, "g2", parsed["source_id"]):
                    continue

                if dry_run:
                    logger.info(f"[DRY RUN] G2: {parsed['title'] or parsed['body'][:80]}")
                    new_count += 1
                    continue

                store_review(
                    db,
                    tool_id=tool.id,
                    source="g2",
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
            recalc_sentiment_summary(db, tool.id, "g2")

        finish_collection_run(db, run, items_collected=collected, items_new=new_count)
        results[tool.slug] = new_count
        logger.info(f"G2 [{tool.slug}]: collected {collected}, new {new_count}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="G2 scraper (RapidAPI)")
    parser.add_argument("--tool-slug", help="Scrape a single tool")
    parser.add_argument("--max-pages", type=int, default=3, help="Max pages to paginate")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        scrape_g2(db, tool_slug=args.tool_slug, max_pages=args.max_pages, dry_run=args.dry_run)
    finally:
        db.close()
