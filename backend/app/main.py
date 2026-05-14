"""FastAPI application — AI Tool Review Aggregator backend.

Routes:
  GET /api/tools              — list all tools with sentiment summaries
  GET /api/tools/{id}         — tool detail + reviews
  GET /api/compare?tools=a,b  — side-by-side comparison
  GET /api/stats              — aggregate statistics
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import func, case
from sqlalchemy.orm import Session, joinedload

from database import get_db, engine, Base
from models import Tool, Review, SentimentSummary
from schemas import (
    ToolOut, ToolDetailOut, ReviewOut, SentimentSummaryOut,
    ToolWithSummary, CompareTool, CompareResponse, StatsOut,
)


# ── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-create tables, run migrations, and seed tools catalog on startup."""
    Base.metadata.create_all(bind=engine)
    # Migration: update check constraint to include producthunt
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE reviews DROP CONSTRAINT IF EXISTS ck_review_source"))
            conn.execute(text("ALTER TABLE reviews ADD CONSTRAINT ck_review_source CHECK (source IN ('reddit', 'trustpilot', 'g2', 'producthunt'))"))
            conn.commit()
    except Exception:
        pass  # constraint might already be updated or table doesn't exist
    # Seed tools catalog (idempotent — skips existing)
    try:
        from scripts.seed import seed
        from database import SessionLocal
        db = SessionLocal()
        try:
            seed(db)
        finally:
            db.close()
    except Exception:
        import traceback
        traceback.print_exc()
    yield


# ── App factory ──────────────────────────────────────────────────────

app = FastAPI(
    title="AI Tool Review Aggregator",
    description="Backend for scraping, analyzing, and comparing AI coding tool reviews.",
    version="0.1.0",
    lifespan=lifespan,
)


# ── GET /api/tools ───────────────────────────────────────────────────

@app.get("/api/tools", response_model=list[ToolWithSummary])
def list_tools(
    category: str | None = Query(None, description="Filter by category slug"),
    db: Session = Depends(get_db),
):
    """Return all tools, each with its sentiment summaries."""
    q = db.query(Tool)
    if category:
        q = q.filter(Tool.category == category)

    tools = q.options(joinedload(Tool.sentiment_summaries)).all()
    # Re-query with joinedload is cleaner, but for simplicity we rely on
    # the relationship being eagerly loaded above
    return tools


# ── GET /api/tools/{id} ──────────────────────────────────────────────

@app.get("/api/tools/{tool_id_or_slug}", response_model=ToolDetailOut)
def get_tool(tool_id_or_slug: str, db: Session = Depends(get_db)):
    """Return tool details, its reviews, and sentiment summaries.

    Accepts either a UUID (tool id) or a URL slug.
    """
    # Try UUID first, then slug lookup
    tool = (
        db.query(Tool)
        .options(
            joinedload(Tool.reviews),
            joinedload(Tool.sentiment_summaries),
        )
        .filter(Tool.id == tool_id_or_slug)
        .first()
    )
    if not tool:
        tool = (
            db.query(Tool)
            .options(
                joinedload(Tool.reviews),
                joinedload(Tool.sentiment_summaries),
            )
            .filter(Tool.slug == tool_id_or_slug)
            .first()
        )
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


# ── GET /api/compare ─────────────────────────────────────────────────

@app.get("/api/compare", response_model=CompareResponse)
def compare_tools(
    tools: str = Query(..., description="Comma-separated tool ids"),
    db: Session = Depends(get_db),
):
    """Side-by-side comparison of multiple tools."""
    tool_ids = [t.strip() for t in tools.split(",") if t.strip()]
    if len(tool_ids) < 1:
        raise HTTPException(status_code=400, detail="At least one tool id required")

    results: list[CompareTool] = []
    for tid in tool_ids:
        tool = (
            db.query(Tool)
            .options(
                joinedload(Tool.reviews),
                joinedload(Tool.sentiment_summaries),
            )
            .filter(Tool.id == tid)
            .first()
        )
        if tool:
            results.append(
                CompareTool(
                    tool=tool,
                    reviews=tool.reviews,
                    sentiment_summaries=tool.sentiment_summaries,
                )
            )

    return CompareResponse(tools=results)


# ── GET /api/stats ───────────────────────────────────────────────────

@app.get("/api/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    """Aggregate statistics across all tools and reviews."""
    total_tools = db.query(func.count(Tool.id)).scalar() or 0
    total_reviews = db.query(func.count(Review.id)).scalar() or 0

    # Reviews per source
    source_rows = (
        db.query(Review.source, func.count(Review.id))
        .group_by(Review.source)
        .all()
    )
    sources = {row[0]: row[1] for row in source_rows}

    # Top 5 tools by average sentiment
    top_sentiment = (
        db.query(Tool)
        .join(SentimentSummary)
        .group_by(Tool.id)
        .order_by(func.avg(SentimentSummary.avg_sentiment).desc())
        .limit(5)
        .all()
    )

    # Top 5 tools by review count
    most_reviewed = (
        db.query(Tool)
        .join(SentimentSummary)
        .group_by(Tool.id)
        .order_by(func.sum(SentimentSummary.review_count).desc())
        .limit(5)
        .all()
    )

    # Tools per category
    cat_rows = (
        db.query(Tool.category, func.count(Tool.id))
        .group_by(Tool.category)
        .all()
    )
    categories = {row[0]: row[1] for row in cat_rows}

    return StatsOut(
        total_tools=total_tools,
        total_reviews=total_reviews,
        sources=sources,
        top_rated=top_sentiment,
        most_reviewed=most_reviewed,
        categories=categories,
    )


# ── Scraper trigger ──────────────────────────────────────────────────

@app.post("/api/scrape/{source}")
def trigger_scrape(
    source: str,
    tool_slug: str | None = None,
    dry_run: bool = False,
    max_pages: int = 5,
):
    """Trigger a scraper run. source: reddit, trustpilot, or g2."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        if source == "reddit":
            from scrapers.reddit_scraper import scrape_reddit
            results = scrape_reddit(db, tool_slug=tool_slug, dry_run=dry_run)
        elif source in ("trustpilot", "g2", "producthunt"):
            from scrapers.firecrawl_scraper import scrape_firecrawl
            results = scrape_firecrawl(db, source=source, tool_slug=tool_slug, dry_run=dry_run, max_pages=max_pages)
        else:
            return {"error": f"Unknown source: {source}"}
        return {"status": "ok", "source": source, "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


# ── Health check ─────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
