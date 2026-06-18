from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import cohere

from core.config import get_config
from rag.prompt import SYSTEM_PROMPT, build_prompt
from rag.retriever import retrieve

logger = logging.getLogger(__name__)

_client: cohere.AsyncClientV2 | None = None


def _get_client() -> cohere.AsyncClientV2:
    global _client
    if _client is None:
        cfg = get_config()
        if not cfg.cohere_api_key:
            raise RuntimeError("COHERE_API_KEY is not set")
        _client = cohere.AsyncClientV2(api_key=cfg.cohere_api_key)
    return _client


@dataclass
class RAGResult:
    answer: str
    sources: list[dict[str, Any]]


async def answer(query: str) -> RAGResult:
    cfg = get_config()
    hits = await retrieve(query, top_k=cfg.rag_top_k)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + build_prompt(query, hits)
    client = _get_client()

    response = await client.chat(
        model=cfg.cohere_generate_model,
        messages=messages,
    )

    text = response.message.content[0].text if response.message.content else ""
    logger.info("rag answer generated for query=%r (%d chars)", query[:60], len(text))

    sources = [
        {
            "product_name": h["product_name"],
            "source": h["source"],
            "nafdac_number": h["nafdac_number"],
            "score": round(h["score"], 4),
        }
        for h in hits
    ]
    return RAGResult(answer=text, sources=sources)
