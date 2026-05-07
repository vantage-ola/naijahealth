from __future__ import annotations

import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from core.config import get_config

logger = logging.getLogger(__name__)

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        cfg = get_config()
        _client = AsyncQdrantClient(url=cfg.qdrant_url, api_key=cfg.qdrant_api_key)
    return _client


async def ensure_collection() -> None:
    cfg = get_config()
    client = get_client()
    collections = await client.get_collections()
    names = {c.name for c in collections.collections}
    if cfg.qdrant_collection_name in names:
        return
    await client.create_collection(
        collection_name=cfg.qdrant_collection_name,
        vectors_config=qm.VectorParams(size=cfg.qdrant_vector_size, distance=qm.Distance.COSINE),
    )
    logger.info("created qdrant collection %s", cfg.qdrant_collection_name)
    await client.create_payload_index(
        collection_name=cfg.qdrant_collection_name,
        field_name="source",
        field_schema=qm.PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=cfg.qdrant_collection_name,
        field_name="nafdac_number",
        field_schema=qm.PayloadSchemaType.KEYWORD,
    )
