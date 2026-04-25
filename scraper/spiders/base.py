import asyncio
import re
from html import unescape

import httpx


TIMEOUT = httpx.Timeout(30.0, connect=10.0)
LIMITS = httpx.Limits(max_connections=5, max_keepalive_connections=3)
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NaijaHealth/1.0)"}


def new_client(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=TIMEOUT,
        limits=LIMITS,
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        **kwargs,
    )


async def fetch_json(client: httpx.AsyncClient, url: str, *, headers: dict | None = None, retries: int = 3) -> dict | list:
    last_exc = None
    for attempt in range(retries):
        try:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            return r.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_exc  # type: ignore[misc]


async def fetch_text(client: httpx.AsyncClient, url: str, *, retries: int = 3) -> str:
    last_exc = None
    for attempt in range(retries):
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_exc  # type: ignore[misc]


def clean_str(val: str | None) -> str | None:
    if val is None:
        return None
    val = unescape(val).strip()
    val = re.sub(r"\s+", " ", val)
    return val or None


def extract_nonce(html: str) -> str | None:
    m = re.search(r'"ninja_table_public_nonce"\s*:\s*"([a-f0-9]+)"', html)
    return m.group(1) if m else None
