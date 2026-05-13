# AI Tool Review Aggregator — Backend

Scrapes, analyzes, and compares reviews of 17 AI coding tools across Reddit, Trustpilot, and G2. Built for the "AI for Non-Technical Pros" YouTube channel.

## Architecture

```
                    ┌────────────────────┐
                    │   FastAPI Server    │  ← Web service (Railway)
                    │   GET /api/tools    │
                    │   GET /api/tools/:id│
                    │   GET /api/compare  │
                    │   GET /api/stats    │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │   PostgreSQL        │  ← Railway managed Postgres
                    │   + SQLAlchemy ORM  │
                    └────────▲───────────┘
                             │
      ┌──────────────────────┼──────────────────────┐
      │                      │                      │
┌─────▼──────┐   ┌──────────▼──────┐   ┌───────────▼──────┐
│ Reddit     │   │ Trustpilot      │   │ G2 Scraper        │
│ Scraper    │   │ Scraper         │   │ (RapidAPI)        │
│ (PRAW)     │   │ (Lobstr.io)     │   │                   │
│ Weekly     │   │ Quarterly       │   │ Monthly           │
└────────────┘   └─────────────────┘   └──────────────────┘
       All three run as Railway cron jobs, write to same DB
```

## Quick Start

### 1. Clone and install dependencies

```bash
cd ai-tool-review-aggregator
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys:
#   REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET  — from reddit.com/prefs/apps
#   LOBSTR_API_KEY                          — from lobstr.io (Trustpilot)
#   RAPIDAPI_KEY                            — from rapidapi.com (G2)
#   OPENAI_API_KEY                          — optional (LLM sentiment)
```

### 3. Seed the database

```bash
python scripts/seed.py
# Creates 17 tools from TOOLS_CATALOG.md
```

### 4. Scrape reviews

```bash
# All sources, all tools
python scrapers/main.py

# Single source
python scrapers/main.py --source reddit

# Single tool, dry run
python scrapers/reddit_scraper.py --tool-slug cursor --dry-run
```

### 5. Start the API

```bash
uvicorn app.main:app --reload --port 8000
# Interactive docs at http://localhost:8000/docs
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tools` | List all tools with sentiment summaries |
| GET | `/api/tools?category=cli_agents` | Filter by category |
| GET | `/api/tools/{id}` | Tool detail + reviews + sentiment |
| GET | `/api/compare?tools=id1,id2,id3` | Side-by-side comparison |
| GET | `/api/stats` | Aggregate stats (counts, categories, top rated) |
| GET | `/health` | Health check |

## Database Schema

### `tools`
| Column | Type | Notes |
|--------|------|-------|
| id | varchar(12) | Primary key |
| name | varchar(100) | Unique |
| slug | varchar(100) | URL-safe, unique |
| category | varchar(50) | app_builders, code_editors, cli_agents, autonomous_agents, traditional_nocode |
| pricing | text | JSON string |
| description | text | Auto-generated from catalog |
| website | varchar(255) | Tool homepage |
| created_at | timestamp | Auto-set |

### `reviews`
| Column | Type | Notes |
|--------|------|-------|
| id | varchar(12) | Primary key |
| tool_id | varchar(12) | FK → tools |
| source | varchar(20) | reddit / trustpilot / g2 |
| source_id | varchar(255) | Platform-specific ID (unique per source) |
| rating | integer | 1-5 star rating (if available) |
| sentiment_score | float | VADER compound (-1.0 to +1.0) |
| sentiment_label | varchar(20) | positive / negative / neutral / mixed |
| title | text | Review headline |
| body | text | Full text |
| url | text | Permalink |
| author | varchar(255) | Username |
| author_verified | boolean | G2/Trustpilot verification |
| posted_at | timestamp | Original post date |
| scraped_at | timestamp | When we collected it |

### `sentiment_summaries`
| Column | Type | Notes |
|--------|------|-------|
| id | varchar(12) | Primary key |
| tool_id | varchar(12) | FK → tools |
| source | varchar(20) | Aggregated per-source |
| avg_rating | float | Mean star rating |
| avg_sentiment | float | Mean VADER compound |
| positive_pct | float | % positive reviews |
| neutral_pct | float | % neutral reviews |
| negative_pct | float | % negative reviews |
| review_count | integer | Total reviews for this (tool, source) |
| updated_at | timestamp | Last recalc |

### `collection_runs`
Tracks every scraper execution with source, timestamps, items collected/new, status, and errors.

## Scraper Refresh Cadence

| Source | Frequency | Method | Cost |
|--------|-----------|--------|------|
| Reddit | Weekly | PRAW API | Free (non-commercial) |
| Trustpilot | Quarterly | Lobstr.io managed service | $2/1K reviews |
| G2 | Monthly | RapidAPI Advanced G2 Scraper | Free tier |

## Sentiment Analysis

**Two-tier strategy (from RESEARCH.md):**

**Tier 1 — VADER (implemented):** Fast, free, runs on every review. Uses `vaderSentiment` library optimized for social-media text. Classifies into positive/negative/neutral/mixed.

**Tier 2 — LLM (optional):** Gate on `OPENAI_API_KEY` being set. GPT-4o-mini for deep pull-quotes on high-signal reviews (~$0.02/500 reviews).

## Project Structure

```
ai-tool-review-aggregator/
├── app/
│   └── main.py              # FastAPI application (all routes)
├── models/
│   └── __init__.py           # SQLAlchemy ORM models
├── scrapers/
│   ├── main.py               # Orchestrator (cron entry point)
│   ├── reddit_scraper.py     # PRAW-based Reddit scraper
│   ├── trustpilot_scraper.py # Lobstr.io Trustpilot scraper
│   ├── g2_scraper.py         # RapidAPI G2 scraper
│   ├── db_helpers.py         # Shared DB + sentiment utilities
│   ├── Dockerfile            # Railway cron container
│   └── requirements.txt      # Scraper-only deps
├── scripts/
│   └── seed.py               # DB seed from TOOLS_CATALOG.md
├── config.py                 # Pydantic settings (env vars)
├── database.py               # SQLAlchemy engine + session
├── schemas.py                # Pydantic response schemas
├── sentiment.py              # VADER sentiment analysis
├── requirements.txt          # Full project deps
├── .env.example              # Environment template
└── README.md
```

## Railway Deployment

Three services on Railway Hobby plan (~$3-6/mo):

| Service | Type | Source |
|---------|------|--------|
| `web` | Web service | Root (Railpack auto-detects Python/FastAPI) |
| `scraper` | Cron job | `scrapers/` directory (uses Dockerfile) |
| `postgres` | Database | Railway managed |

**Required env vars on Railway:**
- `DATABASE_URL` — reference `${{Postgres.DATABASE_URL}}`
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
- `LOBSTR_API_KEY`, `RAPIDAPI_KEY`
- `OPENAI_API_KEY` (optional)

**Cron schedule:** Set in Railway service settings. Recommended: weekly for Reddit, monthly for G2, quarterly for Trustpilot.

## Legal / Fair Use

- **Reddit:** Non-commercial research use via API. Content research for YouTube is arguably commercial — ensure OAuth approval.
- **Trustpilot:** Public data via managed service. Quote excerpts with attribution, don't republish full reviews.
- **G2:** RapidAPI free tier for structured review data. Excerpts for commentary/criticism = fair use.

**General principle:** We aggregate for **content creation** (video research), not republishing a competing review site. Quote short excerpts with attribution.

## Signal Quality Filters (Reddit)

Applied at collection time per RESEARCH.md:

1. Upvote threshold ≥ 5 (≥ 20 for "high-signal" tag)
2. Date range: last 7 days (configurable)
3. Account age ≥ 30 days
4. Comment count ≥ 2
5. Sponsored detection heuristics (5 rules)

## Decisions & Deviations from TECH_STACK.md

The parent research task (t_870e22d8) recommended Next.js App Router + Prisma + GPT-4o-mini sentiment.
This implementation chose:

| Decision | TECH_STACK.md | Implementation | Rationale |
|----------|--------------|----------------|-----------|
| **Framework** | Next.js App Router | **FastAPI** | Python end-to-end (scrapers + API + sentiment in one language), cleaner separation of data pipeline from frontend, auto-generated OpenAPI docs at `/docs` |
| **ORM** | Prisma | **SQLAlchemy 2.0** | Native Python, no Node.js dependency, well-established migration story via Alembic |
| **Sentiment** | GPT-4o-mini ($0.02/500 reviews) | **VADER** (free) | Zero cost, instant results, good-enough accuracy for social-media text. LLM gate exists via `OPENAI_API_KEY` env var check for deep pull-quotes |
| **Local dev DB** | PostgreSQL | **SQLite** (dev) / Postgres (prod) | Zero-config local development; switch to Postgres via `DATABASE_URL` env var |
| **Scrapers** | Python cron jobs | **Python scripts** (same) | Aligned with TECH_STACK.md — self-contained CLI scripts runnable standalone or via orchestrator |

These decisions were reviewed and approved (task unblocked 2026-05-13).

- **FastAPI** — Web framework
- **SQLAlchemy** — ORM
- **PRAW** — Reddit scraper
- **httpx** — HTTP client (Trustpilot/G2 APIs)
- **vaderSentiment** — Sentiment analysis
- **loguru** — Logging
- **pydantic** / **pydantic-settings** — Config + serialization
