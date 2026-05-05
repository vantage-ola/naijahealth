"""Orchestrate JSONL -> Postgres -> chunk -> embed -> Qdrant."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.config import get_config
from db.postgres.models import Chunk as ChunkRow, Product
from db.postgres.session import get_sessionmaker
from pipeline.chunker import Chunk, chunk_record
from pipeline.embedder import Embedder
from pipeline.indexer import point_id_for, upsert_chunks

logger = logging.getLogger(__name__)

SOURCE_FILES = {
    "greenbook": "greenbook.jsonl",
    "food": "food.jsonl",
    "herbal": "herbal.jsonl",
}


def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _product_row(chunk: Chunk) -> dict:
    raw = chunk.payload
    return {
        "id": chunk.product_id,
        "source": chunk.source,
        "nafdac_number": chunk.nafdac_number,
        "product_name": chunk.product_name,
        "applicant_name": raw.get("applicant_name"),
        "manufacturer": raw.get("manufacturer") or raw.get("manufacturer_name"),
        "category": raw.get("product_category") or raw.get("category"),
        "issue_date": raw.get("approval_date") or raw.get("issue_date") or raw.get("certificate_issued_date"),
        "expiry_date": raw.get("expiry_date"),
        "raw": raw,
        "content_hash": chunk.content_hash,
    }


async def _upsert_products(chunks: list[Chunk]) -> set[str]:
    """Upsert product rows. Return product IDs whose content_hash changed (need re-embed)."""
    if not chunks:
        return set()

    sessionmaker = get_sessionmaker()
    changed: set[str] = set()

    async with sessionmaker() as session:
        ids = [c.product_id for c in chunks]
        existing = (
            await session.execute(
                select(Product.id, Product.content_hash).where(Product.id.in_(ids))
            )
        ).all()
        existing_map = {row.id: row.content_hash for row in existing}

        for chunk in chunks:
            prev = existing_map.get(chunk.product_id)
            if prev != chunk.content_hash:
                changed.add(chunk.product_id)

        rows = [_product_row(c) for c in chunks]
        stmt = pg_insert(Product).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Product.id],
            set_={
                "source": stmt.excluded.source,
                "nafdac_number": stmt.excluded.nafdac_number,
                "product_name": stmt.excluded.product_name,
                "applicant_name": stmt.excluded.applicant_name,
                "manufacturer": stmt.excluded.manufacturer,
                "category": stmt.excluded.category,
                "issue_date": stmt.excluded.issue_date,
                "expiry_date": stmt.excluded.expiry_date,
                "raw": stmt.excluded.raw,
                "content_hash": stmt.excluded.content_hash,
            },
        )
        await session.execute(stmt)
        await session.commit()

    return changed


async def _record_chunks(chunks: list[Chunk]) -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        rows = [
            {
                "id": c.product_id,
                "product_id": c.product_id,
                "text": c.text,
                "content_hash": c.content_hash,
                "embedded_at": datetime.now(timezone.utc),
                "qdrant_point_id": point_id_for(c.product_id),
            }
            for c in chunks
        ]
        stmt = pg_insert(ChunkRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[ChunkRow.id],
            set_={
                "text": stmt.excluded.text,
                "content_hash": stmt.excluded.content_hash,
                "embedded_at": stmt.excluded.embedded_at,
                "qdrant_point_id": stmt.excluded.qdrant_point_id,
            },
        )
        await session.execute(stmt)
        await session.commit()


async def process_source(source: str, jsonl_path: Path, embedder: Embedder, batch: int = 256) -> dict:
    if not jsonl_path.exists():
        logger.warning("missing jsonl for %s: %s", source, jsonl_path)
        return {"records": 0, "changed": 0, "embedded": 0}

    total = 0
    changed_count = 0
    embedded_count = 0
    pending: list[Chunk] = []

    async def flush(buf: list[Chunk]) -> None:
        nonlocal changed_count, embedded_count
        if not buf:
            return
        changed_ids = await _upsert_products(buf)
        changed_count += len(changed_ids)
        to_embed = [c for c in buf if c.product_id in changed_ids]
        if to_embed:
            vectors = await embedder.embed_documents([c.text for c in to_embed])
            await upsert_chunks(to_embed, vectors)
            await _record_chunks(to_embed)
            embedded_count += len(to_embed)

    for raw in _iter_jsonl(jsonl_path):
        try:
            chunk = chunk_record(source, raw)
        except KeyError as exc:
            logger.warning("skipping %s record (missing %s)", source, exc)
            continue
        pending.append(chunk)
        total += 1
        if len(pending) >= batch:
            await flush(pending)
            pending = []

    await flush(pending)
    logger.info(
        "%s: %d records, %d changed, %d embedded", source, total, changed_count, embedded_count
    )
    return {"records": total, "changed": changed_count, "embedded": embedded_count}


async def run(sources: list[str] | None = None, data_dir: Path | None = None) -> dict[str, dict]:
    cfg = get_config()
    data_dir = data_dir or Path(cfg.scraper_output_dir)
    sources = sources or list(SOURCE_FILES.keys())

    embedder = Embedder()
    try:
        results: dict[str, dict] = {}
        for source in sources:
            if source not in SOURCE_FILES:
                logger.error("unknown source: %s", source)
                continue
            path = data_dir / SOURCE_FILES[source]
            results[source] = await process_source(source, path, embedder)
        return results
    finally:
        await embedder.aclose()


def main() -> None:
    args = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    args = [a for a in args if a not in ("--verbose", "-v")]
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    sources = None if not args or args == ["all"] else args
    results = asyncio.run(run(sources))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
