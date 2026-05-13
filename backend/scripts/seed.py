"""Database seed script — populates the tools table from TOOLS_CATALOG.md.

Reads the structured JSON from TOOLS_CATALOG.md (at a well-known path) and
inserts every tool into the database.  Idempotent — skips tools that already
exist (matched by slug).

Usage:
  python -m scripts.seed          # from project root
  python scripts/seed.py          # from scripts/ dir
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import Tool


# ── Tool catalog (extracted from TOOLS_CATALOG.md JSON block) ────────

TOOLS_JSON = r"""
{
  "compiled": "2026-05-13",
  "total_tools": 17,
  "categories": {
    "app_builders": {
      "label": "App Builders (for non-coders)",
      "tools": [
        {
          "name": "Lovable",
          "website": "https://lovable.dev",
          "pricing": {"free": "5 daily credits", "pro": "$25/mo (100 credits/mo)", "business": "$100/mo", "enterprise": "Custom"},
          "target_user": "non-coders",
          "launch_date": "2023-10",
          "maturity": "unicorn ($100M+ ARR)",
          "reddit_search": "site:reddit.com Lovable AI app builder",
          "trustpilot": "https://www.trustpilot.com/review/lovable.dev",
          "g2": null
        },
        {
          "name": "Bolt.new",
          "website": "https://bolt.new",
          "pricing": {"free": "1M tokens/mo", "pro": "$25/mo (10M tokens/mo)", "teams": "$30/user/mo"},
          "target_user": "non-coders",
          "launch_date": "2024-10-03",
          "maturity": "$40M ARR, 5M+ users",
          "reddit_search": "site:reddit.com Bolt.new AI",
          "trustpilot": "https://www.trustpilot.com/review/bolt.new",
          "g2": "https://www.g2.com/products/bolt-new/reviews"
        },
        {
          "name": "Replit Agent",
          "website": "https://replit.com",
          "pricing": {"free": "Starter", "core": "$20/mo (includes $25 credits)", "enterprise": "Custom"},
          "target_user": "both",
          "launch_date": "2024",
          "maturity": "established platform (since 2016)",
          "reddit_search": "site:reddit.com Replit Agent",
          "trustpilot": "https://www.trustpilot.com/review/replit.com",
          "g2": "https://www.g2.com/products/replit/reviews"
        },
        {
          "name": "v0 by Vercel",
          "website": "https://v0.app",
          "pricing": {"free": "$5 credits/mo", "premium": "$20/mo", "team": "$30/user/mo", "business": "$100/user/mo"},
          "target_user": "developers",
          "launch_date": "2023-10",
          "maturity": "6M+ developers, est. $42M ARR",
          "reddit_search": "site:reddit.com \"v0 by Vercel\"",
          "trustpilot": "https://www.trustpilot.com/review/v0.dev",
          "g2": "https://www.g2.com/products/vercel/reviews"
        },
        {
          "name": "Base44",
          "website": "https://base44.com",
          "pricing": {"builder": "$50/mo (250 credits)", "pro": "$80/mo", "elite": "$160/mo"},
          "target_user": "non-coders",
          "launch_date": "2025-02",
          "maturity": "acquired by Wix ($80M)",
          "reddit_search": "site:reddit.com Base44 AI",
          "trustpilot": null,
          "g2": null
        },
        {
          "name": "Taskade Genesis",
          "website": "https://www.taskade.com",
          "pricing": {"free": "3,000 credits one-time", "starter": "$8/mo (10K credits/mo)", "pro": "$30/mo (50K credits/mo)", "business": "$60/mo (150K credits/mo)"},
          "target_user": "non-coders",
          "launch_date": "2025-10",
          "maturity": "established platform + new Genesis layer",
          "reddit_search": "site:reddit.com Taskade Genesis",
          "trustpilot": "https://www.trustpilot.com/review/taskade.com",
          "g2": null
        }
      ]
    },
    "code_editors": {
      "label": "AI Code Editors (for developers)",
      "tools": [
        {
          "name": "Cursor",
          "website": "https://cursor.com",
          "pricing": {"hobby": "Free (2K completions/mo)", "pro": "$20/mo", "pro_plus": "$60/mo", "ultra": "$200/mo", "business": "$40/user/mo"},
          "target_user": "developers",
          "launch_date": "2023-03",
          "maturity": "unicorn ($29.3B valuation)",
          "reddit_search": "site:reddit.com Cursor AI editor",
          "trustpilot": "https://www.trustpilot.com/review/cursor.com",
          "g2": "https://www.g2.com/products/cursor/reviews"
        },
        {
          "name": "Windsurf",
          "website": "https://windsurf.com",
          "pricing": {"free": "Forever free (individuals)", "pro": "$15/mo (2,000 steps)", "enterprise": "Custom"},
          "target_user": "developers",
          "launch_date": "2024-11",
          "maturity": "rapidly growing, rebranded from Codeium",
          "reddit_search": "site:reddit.com Windsurf editor Codeium",
          "trustpilot": "https://www.trustpilot.com/review/codeium.com",
          "g2": "https://www.g2.com/products/exafunction-windsurf/reviews"
        },
        {
          "name": "GitHub Copilot",
          "website": "https://github.com/features/copilot",
          "pricing": {"free": "2K completions/mo + 50 premium", "business": "$19/user/mo", "enterprise": "$39/user/mo"},
          "target_user": "developers",
          "launch_date": "2021-06",
          "maturity": "most established, millions of users",
          "reddit_search": "site:reddit.com GitHub Copilot",
          "trustpilot": null,
          "g2": "https://www.g2.com/products/github-copilot/reviews"
        },
        {
          "name": "Google Antigravity",
          "website": "https://antigravity.google",
          "pricing": {"free": "Public preview (generous limits)", "premium": "$20/mo (Google One AI)"},
          "target_user": "developers",
          "launch_date": "2025-11-18",
          "maturity": "early stage (public preview)",
          "reddit_search": "site:reddit.com Google Antigravity",
          "trustpilot": null,
          "g2": null
        }
      ]
    },
    "cli_agents": {
      "label": "Terminal/CLI Agents",
      "tools": [
        {
          "name": "Claude Code",
          "website": "https://claude.ai",
          "pricing": {"pro": "$20/mo", "max": "$100/mo", "max_20x": "$200/mo", "api": "pay-per-token", "managed_agents": "$0.08/hr"},
          "target_user": "developers",
          "launch_date": "2025-02",
          "maturity": "viral adoption, widely used",
          "reddit_search": "site:reddit.com Claude Code Anthropic",
          "trustpilot": "https://www.trustpilot.com/review/anthropic.com",
          "g2": "https://www.g2.com/products/anthropic-claude-code/reviews"
        },
        {
          "name": "Codex CLI",
          "website": "https://github.com/openai/codex",
          "pricing": {"free": "Open source (BYO keys)", "plus": "$20/mo (included)", "pro": "$200/mo (included)", "api": "pay-per-token"},
          "target_user": "developers",
          "launch_date": "2025-04-16",
          "maturity": "rapidly iterating, open source",
          "reddit_search": "site:reddit.com OpenAI Codex CLI",
          "trustpilot": null,
          "g2": "https://www.g2.com/products/openai-codex/reviews"
        },
        {
          "name": "Aider",
          "website": "https://aider.chat",
          "pricing": {"free": "100% free / open source", "costs": "API usage only (BYO keys)"},
          "target_user": "developers",
          "launch_date": "2023",
          "maturity": "mature OSS, self-writing codebase",
          "reddit_search": "site:reddit.com Aider AI coding",
          "trustpilot": null,
          "g2": "https://www.g2.com/products/aider-chat"
        },
        {
          "name": "OpenCode",
          "website": "https://opencode.ai",
          "pricing": {"free": "Open source (BYO keys)", "go": "$10/mo ($5 first month)", "enterprise": "Custom"},
          "target_user": "developers",
          "launch_date": "2025",
          "maturity": "growing OSS community",
          "reddit_search": "site:reddit.com OpenCode CLI",
          "trustpilot": null,
          "g2": null
        }
      ]
    },
    "autonomous_agents": {
      "label": "Autonomous Agents",
      "tools": [
        {
          "name": "Devin 2.0",
          "website": "https://devin.ai",
          "pricing": {"free": "Limited usage", "pro": "$20/mo", "max": "$200/mo", "teams": "Usage-based (min $500/mo)"},
          "target_user": "developers",
          "launch_date": "2025-04-03",
          "maturity": "pioneering category, price cut from $500/mo",
          "reddit_search": "site:reddit.com Devin AI Cognition",
          "trustpilot": null,
          "g2": "https://www.g2.com/sellers/cognition"
        }
      ]
    },
    "traditional_nocode": {
      "label": "Traditional No-Code (baseline)",
      "tools": [
        {
          "name": "Bubble",
          "website": "https://bubble.io",
          "pricing": {"free": "Development only", "starter": "$69/mo", "growth": "$249/mo", "team": "$499/mo"},
          "target_user": "non-coders",
          "launch_date": "2012",
          "maturity": "most mature no-code, 3M+ users",
          "reddit_search": "site:reddit.com Bubble.io no-code",
          "trustpilot": "https://www.trustpilot.com/review/bubble.io",
          "g2": "https://www.g2.com/products/bubble/reviews"
        },
        {
          "name": "Glide",
          "website": "https://www.glideapps.com",
          "pricing": {"free": "Limited", "maker": "$25-49/mo", "team": "$99/mo", "business": "$149-249/mo", "enterprise": "$750/mo+"},
          "target_user": "non-coders",
          "launch_date": "2018",
          "maturity": "mature, strong in business tools",
          "reddit_search": "site:reddit.com Glide apps no-code",
          "trustpilot": "https://www.trustpilot.com/review/www.glideapps.com",
          "g2": "https://www.g2.com/products/glide/reviews"
        }
      ]
    }
  }
}
"""


# Tool names where the automatic slugify produces an awkward result.
# These override the auto-generated slug to keep scraper lookups clean.
SLUG_OVERRIDES: dict[str, str] = {
    "v0 by Vercel": "v0",
    "Devin 2.0": "devin",
}


def _slugify(name: str) -> str:
    """Convert tool name → URL-safe slug, with overrides for known weird ones."""
    if name in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[name]
    return name.lower().replace(" ", "-").replace(".", "-")


def _make_description(tool: dict, cat_label: str) -> str:
    """Build a short description string from catalog metadata."""
    pricing = tool.get("pricing", {})
    paid = next((v for k, v in pricing.items() if k not in ("free", "costs")), "")
    free_tier = pricing.get("free", "")
    parts = [
        f"{tool['name']} — {cat_label}.",
        f"Target: {tool.get('target_user', 'unknown')}.",
        f"Launched: {tool.get('launch_date', 'unknown')}.",
        f"Maturity: {tool.get('maturity', 'unknown')}.",
    ]
    if free_tier:
        parts.append(f"Free tier: {free_tier}.")
    if paid:
        parts.append(f"Paid: {paid}.")
    return " ".join(parts)


def seed(db: Session):
    """Insert all tools from the catalog.  Idempotent by slug."""
    catalog = json.loads(TOOLS_JSON)
    created = 0
    skipped = 0

    for cat_key, cat_data in catalog["categories"].items():
        cat_label = cat_data["label"]
        for tool_data in cat_data["tools"]:
            slug = _slugify(tool_data["name"])

            existing = db.query(Tool).filter(Tool.slug == slug).first()
            if existing:
                logger.debug(f"Tool [{slug}] already exists, skipping")
                skipped += 1
                continue

            tool = Tool(
                name=tool_data["name"],
                slug=slug,
                category=cat_key,
                pricing=json.dumps(tool_data.get("pricing", {})),
                description=_make_description(tool_data, cat_label),
                website=tool_data.get("website"),
            )
            db.add(tool)
            created += 1
            logger.info(f"Created tool: {tool.name} [{slug}]")

    db.commit()
    logger.info(f"Seed complete: {created} created, {skipped} skipped, "
                 f"{db.query(Tool).count()} total tools")


if __name__ == "__main__":
    # Auto-create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
