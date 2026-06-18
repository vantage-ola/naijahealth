from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException

from core.config import get_config
from pipeline.runner import run as run_pipeline
from scraper.runner import run as run_scraper

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


def _require_token(x_admin_token: str | None) -> None:
    cfg = get_config()
    if not cfg.admin_token or x_admin_token != cfg.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")


async def _scrape_and_index() -> None:
    cfg = get_config()
    output_dir = Path(cfg.scraper_output_dir)
    sources = ["greenbook", "food", "herbal"]

    logger.info("admin: scrape started")
    try:
        scrape_results = await run_scraper(sources, output_dir)
        logger.info("admin: scrape done — %s", scrape_results)
    except Exception:
        logger.exception("admin: scrape failed")
        return

    logger.info("admin: pipeline started")
    try:
        pipeline_results = await run_pipeline(sources, output_dir)
        logger.info("admin: pipeline done — %s", pipeline_results)
    except Exception:
        logger.exception("admin: pipeline failed")


async def _index_only() -> None:
    cfg = get_config()
    output_dir = Path(cfg.scraper_output_dir)
    sources = ["greenbook", "food", "herbal"]

    logger.info("admin: pipeline started (index only)")
    try:
        results = await run_pipeline(sources, output_dir)
        logger.info("admin: pipeline done — %s", results)
    except Exception:
        logger.exception("admin: pipeline failed")


@router.post("/pipeline/run")
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    x_admin_token: str | None = Header(default=None),
):
    """Scrape NAFDAC + embed + index into Qdrant."""
    _require_token(x_admin_token)
    background_tasks.add_task(_scrape_and_index)
    return {"status": "started", "message": "Scrape + index running in background. Watch logs."}


@router.post("/pipeline/index-only")
async def trigger_index_only(
    background_tasks: BackgroundTasks,
    x_admin_token: str | None = Header(default=None),
):
    """Re-index existing JSONL files without scraping (faster if data already scraped)."""
    _require_token(x_admin_token)
    background_tasks.add_task(_index_only)
    return {"status": "started", "message": "Index-only pipeline running in background. Watch logs."}
