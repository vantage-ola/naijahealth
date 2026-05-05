# Index embedded chunks into Qdrant.

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from qdrant_client.http import models as qm

from core.config import get_config
from db.qdrant.collections import ensure_collection, get_client
from pipeline.chunker import Chunk

logger = logging.getLogger(__name__)


def point_id_for(product_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, product_id))


async def upsert_chunks(chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> list[str]:
    if not chunks:
        return []
    if len(chunks) != len(vectors):
        raise ValueError("chunk/vector length mismatch")

    await ensure_collection()
    client = get_client()
    cfg = get_config()

    points: list[qm.PointStruct] = []
    point_ids: list[str] = []
    for chunk, vector in zip(chunks, vectors):
        pid = point_id_for(chunk.product_id)
        point_ids.append(pid)
        points.append(
            qm.PointStruct(
                id=pid,
                vector=list(vector),
                payload={
                    "product_id": chunk.product_id,
                    "source": chunk.source,
                    "nafdac_number": chunk.nafdac_number,
                    "product_name": chunk.product_name,
                    "text": chunk.text,
                },
            )
        )

    await client.upsert(collection_name=cfg.qdrant_collection_name, points=points, wait=True)
    logger.info("upserted %d points to qdrant", len(points))
    return point_ids
