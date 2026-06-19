"""Redis cache for the RAG path — query embeddings and full answers.

Fail-open: any Redis error logs a warning and returns a miss, so a cache
outage never breaks user queries.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from core.config import get_config

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None

_ANSWER_PREFIX = "nh:ans:"
_EMBED_PREFIX = "nh:emb:"


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(get_config().redis_url, decode_responses=False)
    return _client


def _digest(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()


def _answer_key(query: str) -> str:
    return _ANSWER_PREFIX + _digest(query)


def _embed_key(query: str) -> str:
    return _EMBED_PREFIX + _digest(query)


async def get_cached_answer(query: str) -> dict[str, Any] | None:
    if not get_config().cache_enabled:
        return None
    try:
        raw = await get_client().get(_answer_key(query))
        if raw is None:
            return None
        logger.debug("answer cache hit for query=%r", query[:60])
        return json.loads(raw)
    except Exception as exc:
        logger.warning("redis get_cached_answer failed: %s", exc)
        return None


async def set_cached_answer(query: str, payload: dict[str, Any], ttl: int) -> None:
    if not get_config().cache_enabled:
        return
    try:
        await get_client().set(_answer_key(query), json.dumps(payload), ex=ttl)
    except Exception as exc:
        logger.warning("redis set_cached_answer failed: %s", exc)


async def get_cached_embedding(query: str) -> list[float] | None:
    if not get_config().cache_enabled:
        return None
    try:
        raw = await get_client().get(_embed_key(query))
        if raw is None:
            return None
        logger.debug("embedding cache hit for query=%r", query[:60])
        return json.loads(raw)
    except Exception as exc:
        logger.warning("redis get_cached_embedding failed: %s", exc)
        return None


async def set_cached_embedding(query: str, vector: list[float], ttl: int) -> None:
    if not get_config().cache_enabled:
        return
    try:
        await get_client().set(_embed_key(query), json.dumps(vector), ex=ttl)
    except Exception as exc:
        logger.warning("redis set_cached_embedding failed: %s", exc)


async def ping() -> bool:
    try:
        return bool(await get_client().ping())
    except Exception as exc:
        logger.warning("redis ping failed: %s", exc)
        return False


async def aclose() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception as exc:
            logger.warning("redis aclose failed: %s", exc)
        _client = None
