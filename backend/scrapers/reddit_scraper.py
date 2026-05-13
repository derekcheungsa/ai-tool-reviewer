"""Reddit scraper using PRAW (Python Reddit API Wrapper).

Features:
  - Searches configured subreddits for AI-tool keywords
  - Applies signal-filtering rules from RESEARCH.md
  - Deduplicates via Reddit post ID
  - Runs VADER sentiment analysis on every review
  - Updates sentiment_summaries after each batch

Usage:
  python reddit_scraper.py [--tool-slug lovable] [--days 7]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from any directory — always resolve project root as parent of scrapers/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import time
from datetime import datetime, timedelta, timezone

import praw
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

# ── Configuration ────────────────────────────────────────────────────

SUBREDDITS = [
    "vibecoding",
    "ChatGPTCoding",
    "SaaS",
    "nocode",
]

KEYWORDS = [
    "bolt.new", "lovable", "replit agent", "cursor", "v0 by vercel",
    "github copilot", "windsurf", "codeium", "claude code", "codex cli",
    "aider", "opencode", "devin", "base44", "taskade genesis",
    "vibe coding", "AI coding", "AI app builder", "AI code editor",
    "bubble.io no-code", "glide apps",
]

# Signal filters (from RESEARCH.md)
MIN_UPVOTES = 5
MIN_COMMENTS = 2
MAX_AGE_DAYS_DEFAULT = 7


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Helpers ──────────────────────────────────────────────────────────

def _map_tool_name(text: str) -> str | None:
    """Heuristic: try to match a mention to a known tool slug in the DB."""
    text_lower = text.lower()
    # Simple keyword → slug mapping; extend as needed
    mapping = {
        "bolt.new": "bolt-new",
        "bolt new": "bolt-new",
        "lovable": "lovable",
        "replit agent": "replit-agent",
        "replit": "replit-agent",
        "cursor": "cursor",
        "v0 by vercel": "v0",
        "v0": "v0",
        "github copilot": "github-copilot",
        "copilot": "github-copilot",
        "windsurf": "windsurf",
        "codeium": "windsurf",
        "claude code": "claude-code",
        "codex cli": "codex-cli",
        "codex": "codex-cli",
        "aider": "aider",
        "opencode": "opencode",
        "devin": "devin",
        "base44": "base44",
        "taskade genesis": "taskade-genesis",
        "taskade": "taskade-genesis",
        "bubble": "bubble",
        "glide": "glide",
        "google antigravity": "google-antigravity",
    }
    for keyword, slug in mapping.items():
        if keyword in text_lower:
            return slug
    return None


def _sponsored_check(author, submission) -> bool:
    """Heuristic sponsored/affiliate detection (rules from RESEARCH.md).

    Returns True if the post looks like sponsored content and should be skipped.
    """
    red_flags = 0
    try:
        # Rule 1: new account + only posts about one tool
        age_days = (_utcnow() - datetime.fromtimestamp(author.created_utc, tz=timezone.utc)).days
        if age_days < 30:
            red_flags += 1

        # Rule 3: marketing-speak patterns (simple keyword check)
        marketing_terms = ["game-changer", "revolutionary", "life-changing", "unbelievable"]
        lower_text = (submission.title + " " + submission.selftext).lower()
        if any(term in lower_text for term in marketing_terms) and "but" not in lower_text:
            red_flags += 1  # unqualified hype

        # Rule 4: cross-reference (simplified — check if account is very one-dimensional)
        if author.link_karma < 10 and author.comment_karma < 10:
            red_flags += 1
    except Exception:
        pass  # author info unavailable

    return red_flags >= 2


# ── Main scraper ─────────────────────────────────────────────────────

def scrape_reddit(
    db: Session,
    tool_slug: str | None = None,
    days_back: int = MAX_AGE_DAYS_DEFAULT,
    dry_run: bool = False,
) -> dict:
    """Run Reddit scraper for one or all tools.

    Returns: {tool_slug: new_review_count}
    """
    reddit = praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )

    # Determine which tools to scrape
    if tool_slug:
        tools = db.query(Tool).filter(Tool.slug == tool_slug).all()
    else:
        tools = db.query(Tool).all()

    if not tools:
        logger.warning("No tools found in DB. Run seed first.")
        return {}

    results: dict[str, int] = {}
    since = _utcnow() - timedelta(days=days_back)

    for tool in tools:
        run = get_or_create_collection_run(db, "reddit", tool.slug)
        new_count = 0
        collected = 0

        # Build a targeted query: tool name + "review" or "experience"
        query = f'"{tool.name}" review OR "{tool.name}" experience'

        for sub_name in SUBREDDITS:
            try:
                subreddit = reddit.subreddit(sub_name)
                for submission in subreddit.search(query, sort="new", time_filter="week", limit=50):
                    collected += 1
                    posted_dt = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)

                    # Apply filters
                    if submission.score < MIN_UPVOTES:
                        continue
                    if submission.num_comments < MIN_COMMENTS:
                        continue
                    if posted_dt < since:
                        continue

                    source_id = submission.id
                    if review_exists(db, "reddit", source_id):
                        continue

                    # Sponsored check
                    try:
                        author = submission.author
                        if author and _sponsored_check(author, submission):
                            logger.info(f"Skipping likely sponsored post: {submission.id}")
                            continue
                    except Exception:
                        pass

                    if dry_run:
                        logger.info(f"[DRY RUN] Would store: {submission.title[:80]}")
                        new_count += 1
                        continue

                    body = submission.selftext or submission.title
                    store_review(
                        db,
                        tool_id=tool.id,
                        source="reddit",
                        source_id=source_id,
                        title=submission.title,
                        body=body,
                        url=f"https://reddit.com{submission.permalink}",
                        author=str(submission.author) if submission.author else None,
                        posted_at=posted_dt,
                    )
                    new_count += 1
                    logger.debug(f"Stored Reddit review: {submission.id[:8]} — {submission.title[:60]}")

                    # Rate-limit courtesy (PRAW: 60 req/min → 1 req/sec)
                    time.sleep(1.0)

            except Exception as exc:
                logger.error(f"Error searching r/{sub_name} for {tool.name}: {exc}")
                continue

        # Recalculate sentiment summary for this tool+source
        if new_count > 0 and not dry_run:
            recalc_sentiment_summary(db, tool.id, "reddit")

        finish_collection_run(db, run, items_collected=collected, items_new=new_count)
        results[tool.slug] = new_count
        logger.info(f"Tool [{tool.slug}]: collected {collected}, new {new_count}")

    return results


# ── CLI ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reddit review scraper")
    parser.add_argument("--tool-slug", help="Scrape a single tool by slug")
    parser.add_argument("--days", type=int, default=MAX_AGE_DAYS_DEFAULT, help="Days back to search")
    parser.add_argument("--dry-run", action="store_true", help="Log without storing")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        scrape_reddit(db, tool_slug=args.tool_slug, days_back=args.days, dry_run=args.dry_run)
    finally:
        db.close()
