"""Herbal products spider — scrapes NAFDAC registered herbal products.

Source: https://nafdac.gov.ng/herbal-products-database/
Tech: WordPress + Ninja Tables (default/CSV provider, server-rendered).
The AJAX endpoint may return empty for this table. Falls back to parsing the
server-rendered HTML table with BeautifulSoup.
"""

import asyncio
import logging
from collections.abc import AsyncIterator

from pydantic import ValidationError

from scraper.parsers.herbal import parse_herbal_record
from scraper.spiders.base import clean_str, extract_nonce, fetch_json, fetch_text, new_client
from scraper.validators.herbal import HerbalProduct

log = logging.getLogger(__name__)

PAGE_URL = "https://nafdac.gov.ng/herbal-products-database/"
AJAX_URL = "https://nafdac.gov.ng/wp-admin/admin-ajax.php"
TABLE_ID = "20312"
XHR_HEADERS = {"X-Requested-With": "XMLHttpRequest"}

COLUMN_KEYS = [
    "sn", "productname", "nafdacnumber", "othername", "packsize",
    "presentation", "dosageform", "applicantname", "address",
    "manufacturername", "contactaddress", "state",
    "certificateissueddate", "expirydate",
]


async def _try_ajax(client, nonce: str) -> list[dict] | None:
    """Try the Ninja Tables AJAX endpoint. Returns rows or None if empty."""
    chunk = 1
    all_rows: list[dict] = []

    while True:
        params = {
            "action": "wp_ajax_ninja_tables_public_action",
            "table_id": TABLE_ID,
            "target_action": "get-all-data",
            "default_sorting": "old_first",
            "skip_rows": "0",
            "limit_rows": "0",
            "chunk_number": str(chunk),
            "ninja_table_public_nonce": nonce,
        }
        url = AJAX_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
        data = await fetch_json(client, url, headers=XHR_HEADERS)

        rows = data if isinstance(data, list) else data.get("data", [])
        if not rows:
            break

        all_rows.extend(rows)
        log.info("herbal ajax: chunk %d — %d records", chunk, len(rows))
        chunk += 1
        await asyncio.sleep(1.0)

    return all_rows or None


def _parse_html_table(html: str) -> list[dict]:
    """Fallback: parse server-rendered Ninja Table HTML with BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="ninja_footable")
    if not table:
        return []

    rows = []
    for tr in table.select("tbody tr"):
        cells = [clean_str(td.get_text()) for td in tr.find_all("td")]
        if len(cells) >= len(COLUMN_KEYS):
            row = {"value": dict(zip(COLUMN_KEYS, cells))}
            rows.append(row)

    return rows


async def crawl() -> AsyncIterator[HerbalProduct]:
    async with new_client() as client:
        html = await fetch_text(client, PAGE_URL)
        nonce = extract_nonce(html)
        if not nonce:
            raise RuntimeError("could not extract nonce from herbal page")
        log.info("herbal: nonce=%s", nonce)

        raw_rows = await _try_ajax(client, nonce)
        if raw_rows:
            log.info("herbal: got %d records via AJAX", len(raw_rows))
        else:
            log.info("herbal: AJAX empty, falling back to HTML parsing")
            raw_rows = _parse_html_table(html)
            log.info("herbal: parsed %d records from HTML", len(raw_rows))

        valid = 0
        errors = 0
        for raw in raw_rows:
            try:
                parsed = parse_herbal_record(raw)
                product = HerbalProduct(**parsed)
                valid += 1
                yield product
            except (ValidationError, KeyError) as exc:
                errors += 1
                log.debug("herbal validation error: %s", exc)

        log.info("herbal: done — %d valid, %d errors", valid, errors)
