from __future__ import annotations

import logging
import uuid
from typing import Sequence

from db.qdrant.collections import ensure_collection, upsert_points
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

    points = []
    point_ids = []
    for chunk, vector in zip(chunks, vectors):
        pid = point_id_for(chunk.product_id)
        point_ids.append(pid)
        points.append({
            "id": pid,
            "vector": list(vector),
            "payload": {
                "product_id": chunk.product_id,
                "source": chunk.source,
                "nafdac_number": chunk.nafdac_number,
                "product_name": chunk.product_name,
                "text": chunk.text,
            },
        })

    await upsert_points(points)
    return point_ids
