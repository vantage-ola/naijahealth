from __future__ import annotations

import logging
from typing import Any

from core.config import get_config
from db.qdrant.collections import ensure_collection, search_points
from pipeline.embedder import Embedder

logger = logging.getLogger(__name__)

_embedder: Embedder | None = None


def _get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder


async def retrieve(query: str, top_k: int | None = None) -> list[dict[str, Any]]:
    cfg = get_config()
    k = top_k if top_k is not None else cfg.rag_top_k

    embedder = _get_embedder()
    vector = await embedder.embed_query(query)

    await ensure_collection()
    results = await search_points(vector, limit=k)

    hits = []
    for r in results:
        payload = r.get("payload") or {}
        hits.append({
            "score": r.get("score", 0),
            "product_id": payload.get("product_id"),
            "product_name": payload.get("product_name"),
            "source": payload.get("source"),
            "nafdac_number": payload.get("nafdac_number"),
            "text": payload.get("text", ""),
        })

    logger.debug("retrieved %d hits for query=%r", len(hits), query[:60])
    return hits
