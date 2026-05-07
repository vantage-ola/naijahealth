from __future__ import annotations

import asyncio
import logging
from typing import Iterable, Sequence

import cohere

from core.config import get_config

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self) -> None:
        cfg = get_config()
        if not cfg.cohere_api_key:
            raise RuntimeError("COHERE_API_KEY is not set")
        self._client = cohere.AsyncClientV2(api_key=cfg.cohere_api_key)
        self._model = cfg.cohere_embed_model
        self._batch_size = cfg.embed_batch_size

    async def aclose(self) -> None:
        # AsyncClientV2 manages its own httpx client; nothing to close explicitly.
        pass

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return await self._embed(texts, input_type="search_document")

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self._embed([text], input_type="search_query")
        return vectors[0]

    async def _embed(self, texts: Sequence[str], *, input_type: str) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        for batch in _batched(texts, self._batch_size):
            vectors = await self._embed_batch(batch, input_type=input_type)
            out.extend(vectors)
        return out

    async def _embed_batch(
        self, batch: Sequence[str], *, input_type: str, attempt: int = 0
    ) -> list[list[float]]:
        try:
            resp = await self._client.embed(
                texts=list(batch),
                model=self._model,
                input_type=input_type,
                embedding_types=["float"],
            )
            return resp.embeddings.float_
        except Exception as exc:
            if attempt >= 3:
                raise
            wait = 2 ** attempt
            logger.warning("cohere embed failed (%s); retrying in %ss", exc, wait)
            await asyncio.sleep(wait)
            return await self._embed_batch(batch, input_type=input_type, attempt=attempt + 1)


def _batched(seq: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]
