from __future__ import annotations

import logging

import httpx

from core.config import get_config

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return get_config().qdrant_url.rstrip("/")


def _headers() -> dict:
    cfg = get_config()
    h = {"Content-Type": "application/json"}
    if cfg.qdrant_api_key:
        h["api-key"] = cfg.qdrant_api_key
    return h


async def ensure_collection() -> None:
    cfg = get_config()
    base = _base_url()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{base}/collections", headers=_headers())
        resp.raise_for_status()
        names = {c["name"] for c in resp.json()["result"]["collections"]}

        if cfg.qdrant_collection_name in names:
            return

        r = await client.put(
            f"{base}/collections/{cfg.qdrant_collection_name}",
            headers=_headers(),
            json={"vectors": {"size": cfg.qdrant_vector_size, "distance": "Cosine"}},
        )
        r.raise_for_status()
        logger.info("created qdrant collection %s", cfg.qdrant_collection_name)

        for field, schema in [("source", "keyword"), ("nafdac_number", "keyword")]:
            await client.put(
                f"{base}/collections/{cfg.qdrant_collection_name}/index",
                headers=_headers(),
                json={"field_name": field, "field_schema": schema},
            )


async def upsert_points(points: list[dict]) -> None:
    if not points:
        return
    cfg = get_config()
    base = _base_url()

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.put(
            f"{base}/collections/{cfg.qdrant_collection_name}/points",
            headers=_headers(),
            json={"points": points},
        )
        resp.raise_for_status()
        logger.info("upserted %d points to qdrant", len(points))


async def search_points(vector: list[float], limit: int, score_threshold: float = 0.0) -> list[dict]:
    cfg = get_config()
    base = _base_url()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{base}/collections/{cfg.qdrant_collection_name}/points/search",
            headers=_headers(),
            json={
                "vector": vector,
                "limit": limit,
                "score_threshold": score_threshold,
                "with_payload": True,
            },
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
