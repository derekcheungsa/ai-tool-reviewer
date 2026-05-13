"""Firecrawl-based unified scraper for Trustpilot and G2 reviews.

Replaces the separate Lobstr.io (Trustpilot) and RapidAPI (G2) scrapers
with a single integration.  Uses Firecrawl's /v2/scrape endpoint to get
clean markdown from review pages, then parses reviews from the content.

Usage:
  python firecrawl_scraper.py [--source trustpilot|g2] [--tool-slug bolt-new]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

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

FIRECRAWL_BASE = "https://api.firecrawl.dev/v2"

# ── URL mappings ──────────────────────────────────────────────────────

TRUSTPILOT_URLS: dict[str, str] = {
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

G2_URLS: dict[str, str] = {
    "bolt-new": "https://www.g2.com/products/bolt-new/reviews",
    "replit-agent": "https://www.g2.com/products/replit/reviews",
    "cursor": "https://www.g2.com/products/cursor/reviews",
    "github-copilot": "https://www.g2.com/products/github-copilot/reviews",
    "windsurf": "https://www.g2.com/products/exafunction-windsurf/reviews",
    "claude-code": "https://www.g2.com/products/anthropic-claude-code/reviews",
    "codex-cli": "https://www.g2.com/products/openai-codex/reviews",
    "aider": "https://www.g2.com/products/aider-chat",
    "v0": "https://www.g2.com/products/vercel/reviews",
    "bubble": "https://www.g2.com/products/bubble/reviews",
    "glide": "https://www.g2.com/products/glide/reviews",
    "devin": "https://www.g2.com/sellers/cognition",
}

URL_MAPS = {
    "trustpilot": TRUSTPILOT_URLS,
    "g2": G2_URLS,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Firecrawl API ─────────────────────────────────────────────────────

def firecrawl_scrape(url: str, api_key: str) -> str:
    """Scrape a URL with Firecrawl and return markdown content."""
    resp = httpx.post(
        f"{FIRECRAWL_BASE}/scrape",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "maxAge": 3600000,  # 1 hour cache
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Firecrawl error: {data.get('error', 'unknown')}")
    return data["data"].get("markdown", "")


# ── Review parsing ────────────────────────────────────────────────────

# Trustpilot review card pattern: star rating + title + body + author + date
TP_REVIEW_RE = re.compile(
    r"(?:(?:★|☆){1,5})\s*\n\n"          # star rating
    r"(.+?)\n\n"                          # title
    r"(.+?)\n\n"                          # body
    r"(.+?),\s*(.+?)(?:\n|$)",           # author, date
    re.DOTALL,
)

# G2 review pattern: rating + title + pros/cons + author
G2_REVIEW_RE = re.compile(
    r"(\d(?:\.\d)?)\s*(?:out of|/)\s*5.*?\n"  # rating
    r"(.+?)\n"                                  # title
    r".*?Pros.*?\n(.+?)\n"                     # pros
    r".*?Cons.*?\n(.+?)",                      # cons
    re.DOTALL,
)


def _parse_trustpilot_markdown(md: str) -> list[dict]:
    """Extract reviews from Trustpilot markdown."""
    reviews = []
    # Trustpilot pages have review cards with star ratings, titles, bodies
    # Look for patterns like "★ ★ ★ ★ ★" or "★★★★★"
    star_blocks = re.split(r"(?:★|☆){3,5}|(?:★★★★★|★★★★☆|★★★☆☆|★★☆☆☆|★☆☆☆☆)", md)

    # More robust approach: split by review separators
    # Trustpilot markdown typically separates reviews with dividers or headings
    sections = re.split(r"\n---\n|\n## \d+\.\s", md)

    for section in sections:
        section = section.strip()
        if len(section) < 50:
            continue

        # Try to extract: rating, title, body, author, date
        # Stars are usually first
        stars = len(re.findall(r"★", section))
        if stars == 0:
            stars = len(re.findall(r"⭐", section))

        # Find title (first non-empty line after stars)
        lines = [l.strip() for l in section.split("\n") if l.strip()]
        title = lines[0] if lines else ""
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        # Extract author/date (usually at the end)
        author = ""
        date_str = ""
        author_match = re.search(r"([\w\s\.]+),\s*(.+\d{4})", body[-100:])
        if author_match:
            author = author_match.group(1).strip()
            date_str = author_match.group(2).strip()

        reviews.append({
            "title": title[:200] if title else None,
            "body": body[:2000],
            "author": author,
            "rating": stars if stars > 0 else None,
        })

    return reviews


def _parse_g2_markdown(md: str) -> list[dict]:
    """Extract reviews from G2 markdown."""
    reviews = []
    # G2 pages separate reviews with headings like "### Review by {name}"
    sections = re.split(r"\n###\s", md)

    for section in sections:
        section = section.strip()
        if len(section) < 50:
            continue

        lines = [l.strip() for l in section.split("\n") if l.strip()]
        title = lines[0] if lines else ""

        # Find star rating
        rating_match = re.search(r"(\d(?:\.\d)?)\s*(?:out of|/)\s*5", section)
        rating = float(rating_match.group(1)) if rating_match else None

        body = "\n".join(lines[1:])

        # Author usually in the heading
        author = ""
        author_match = re.match(r"Review by (.+)", title)
        if author_match:
            author = author_match.group(1).strip()

        reviews.append({
            "title": title[:200] if title else None,
            "body": body[:2000],
            "author": author,
            "rating": int(rating) if rating else None,
        })

    return reviews


def parse_reviews(markdown: str, source: str) -> list[dict]:
    """Dispatch to the correct parser based on source."""
    if source == "trustpilot":
        return _parse_trustpilot_markdown(markdown)
    elif source == "g2":
        return _parse_g2_markdown(markdown)
    return []


# ── Main scraper ──────────────────────────────────────────────────────

def scrape_firecrawl(
    db: Session,
    source: str = "trustpilot",
    tool_slug: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Scrape reviews using Firecrawl for one source and one or all tools."""
    api_key = settings.firecrawl_api_key
    if not api_key:
        logger.warning("FIRECRAWL_API_KEY not set — Firecrawl scraper disabled")
        return {}

    url_map = URL_MAPS.get(source, {})
    if not url_map:
        logger.error(f"Unknown source: {source}")
        return {}

    if tool_slug:
        tools = db.query(Tool).filter(Tool.slug == tool_slug).all()
    else:
        tools = db.query(Tool).all()

    results: dict[str, int] = {}

    for tool in tools:
        page_url = url_map.get(tool.slug)
        if not page_url:
            logger.debug(f"No {source} URL for {tool.slug}, skipping")
            continue

        run = get_or_create_collection_run(db, source, tool.slug)
        new_count = 0

        try:
            logger.info(f"Firecrawl scraping {source}: {tool.name} → {page_url}")
            markdown = firecrawl_scrape(page_url, api_key)
        except Exception as exc:
            logger.error(f"Firecrawl error for {tool.slug}: {exc}")
            finish_collection_run(db, run, items_collected=0, items_new=0, error=str(exc))
            continue

        if not markdown:
            logger.warning(f"No content returned for {tool.slug}")
            finish_collection_run(db, run, items_collected=0, items_new=0)
            continue

        reviews = parse_reviews(markdown, source)
        logger.info(f"{source} [{tool.slug}]: parsed {len(reviews)} reviews from markdown")

        for i, review in enumerate(reviews):
            source_id = f"{tool.slug}-{source}-{i}"

            if review_exists(db, source, source_id):
                continue

            if not review.get("body"):
                continue

            if dry_run:
                logger.info(f"[DRY RUN] {source}: {review.get('title', '')[:80]}")
                new_count += 1
                continue

            store_review(
                db,
                tool_id=tool.id,
                source=source,
                source_id=source_id,
                title=review.get("title"),
                body=review["body"],
                url=page_url,
                author=review.get("author"),
                rating=review.get("rating"),
            )
            new_count += 1

        if new_count > 0 and not dry_run:
            recalc_sentiment_summary(db, tool.id, source)

        finish_collection_run(db, run, items_collected=len(reviews), items_new=new_count)
        results[tool.slug] = new_count
        logger.info(f"Firecrawl {source} [{tool.slug}]: {len(reviews)} parsed, {new_count} new")

    return results


# ── CLI ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Firecrawl review scraper")
    parser.add_argument("--source", choices=["trustpilot", "g2"], default="trustpilot")
    parser.add_argument("--tool-slug", help="Scrape a single tool by slug")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        scrape_firecrawl(db, source=args.source, tool_slug=args.tool_slug, dry_run=args.dry_run)
    finally:
        db.close()
