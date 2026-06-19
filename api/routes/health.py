# Health check and status monitoring routes.

from __future__ import annotations

import asyncio
import logging

import httpx
from fastapi import APIRouter, Response
from sqlalchemy import text

from core.config import get_config
from db.postgres.session import get_sessionmaker
from db.redis import cache

logger = logging.getLogger(__name__)
router = APIRouter()
config = get_config()


@router.get("/health")
async def health():
    return {"status": "ok", "version": config.app_version}


async def _check_postgres() -> bool:
    try:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("postgres health check failed: %s", exc)
        return False


async def _check_qdrant() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{config.qdrant_url.rstrip('/')}/healthz")
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("qdrant health check failed: %s", exc)
        return False


@router.get("/health/ready")
async def ready(response: Response):
    postgres_ok, qdrant_ok, redis_ok = await asyncio.gather(
        _check_postgres(), _check_qdrant(), cache.ping()
    )

    checks = {
        "postgres": "ok" if postgres_ok else "error",
        "qdrant": "ok" if qdrant_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }

    # Redis is fail-open everywhere, so it degrades but does not gate readiness.
    critical_ok = postgres_ok and qdrant_ok
    if not critical_ok:
        response.status_code = 503
        status = "unavailable"
    elif not redis_ok:
        status = "degraded"
    else:
        status = "ready"

    return {"status": status, "checks": checks}
