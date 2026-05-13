"""Scraper orchestrator — runs all sources for all (or specified) tools.

Designed to be run as a Railway cron job: starts, scrapes, exits cleanly.

Usage:
  python main.py [--source reddit|trustpilot|g2] [--tool-slug bolt-new] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from any directory — resolve project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from loguru import logger

from database import SessionLocal
from scrapers.reddit_scraper import scrape_reddit
from scrapers.trustpilot_scraper import scrape_trustpilot
from scrapers.g2_scraper import scrape_g2


def main():
    parser = argparse.ArgumentParser(description="AI Tool Review Scraper Orchestrator")
    parser.add_argument(
        "--source", choices=["reddit", "trustpilot", "g2"],
        help="Run a single source (default: all)",
    )
    parser.add_argument("--tool-slug", help="Scrape a single tool by slug")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()

    try:
        sources_to_run = [args.source] if args.source else ["reddit", "trustpilot", "g2"]

        for source in sources_to_run:
            logger.info(f"=== Starting {source} scraper ===")
            try:
                if source == "reddit":
                    scrape_reddit(db, tool_slug=args.tool_slug, dry_run=args.dry_run)
                elif source == "trustpilot":
                    scrape_trustpilot(db, tool_slug=args.tool_slug, dry_run=args.dry_run)
                elif source == "g2":
                    scrape_g2(db, tool_slug=args.tool_slug, dry_run=args.dry_run)
            except Exception as exc:
                logger.exception(f"{source} scraper failed: {exc}")
            logger.info(f"=== Finished {source} scraper ===")

    finally:
        db.close()


if __name__ == "__main__":
    main()
