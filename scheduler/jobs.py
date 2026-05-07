"""Daily scraper job scheduled via APScheduler.

Runs inside the FastAPI process — started/stopped via the app lifespan.
"""

import logging
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.config import get_config
from pipeline.runner import run as run_pipeline
from scraper.runner import run

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S")

_scheduler: AsyncIOScheduler | None = None


async def scrape_all() -> None:
    config = get_config()
    output_dir = Path(config.scraper_output_dir)
    names = ["greenbook", "food", "herbal"]

    log.info("scheduled scrape starting — spiders: %s", ", ".join(names))
    try:
        results = await run(names, output_dir)
        total = sum(results.values())
        log.info("scheduled scrape done — %d total records (%s)", total, results)
    except Exception:
        log.exception("scheduled scrape failed")
        return

    if not config.run_pipeline_after_scrape:
        return

    log.info("pipeline starting — embedding new/changed records")
    try:
        pipeline_results = await run_pipeline(names, output_dir)
        log.info("pipeline done — %s", pipeline_results)
    except Exception:
        log.exception("pipeline failed")


def start_scheduler() -> None:
    global _scheduler
    config = get_config()

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        scrape_all,
        trigger=CronTrigger(hour=config.scrape_hour, minute=config.scrape_minute),
        id="daily_scrape",
        name="Daily NAFDAC scrape",
        replace_existing=True,
    )
    _scheduler.start()

    job = _scheduler.get_job("daily_scrape")
    log.info("scheduler started — next run at %s", job.next_run_time)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        log.info("scheduler stopped")
        _scheduler = None
