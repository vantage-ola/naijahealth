"""Food products spider — scrapes NAFDAC registered food products.

Source: https://nafdac.gov.ng/food-products-database/
Tech: WordPress + Ninja Tables Pro (FooTable), AJAX-loaded in 3,000-record chunks.
API: GET admin-ajax.php?action=wp_ajax_ninja_tables_public_action&table_id=19494&chunk_number=N
"""

import asyncio
import logging
from collections.abc import AsyncIterator

from pydantic import ValidationError

from scraper.parsers.food import parse_food_record
from scraper.spiders.base import extract_nonce, fetch_json, fetch_text, new_client
from scraper.validators.food import FoodProduct

log = logging.getLogger(__name__)

PAGE_URL = "https://nafdac.gov.ng/food-products-database/"
AJAX_URL = "https://nafdac.gov.ng/wp-admin/admin-ajax.php"
TABLE_ID = "19494"
XHR_HEADERS = {"X-Requested-With": "XMLHttpRequest"}


async def _get_nonce(client) -> str:
    html = await fetch_text(client, PAGE_URL)
    nonce = extract_nonce(html)
    if not nonce:
        raise RuntimeError("could not extract ninja_table_public_nonce from food page")
    return nonce


async def crawl() -> AsyncIterator[FoodProduct]:
    async with new_client() as client:
        nonce = await _get_nonce(client)
        log.info("food: nonce=%s", nonce)

        chunk = 1
        valid = 0
        errors = 0

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

            # Ninja Tables returns either a list of rows or {"success": true, "data": []}
            rows = data if isinstance(data, list) else data.get("data", [])
            if not rows:
                break

            log.info("food: chunk %d — %d records", chunk, len(rows))

            for raw in rows:
                try:
                    parsed = parse_food_record(raw)
                    product = FoodProduct(**parsed)
                    valid += 1
                    yield product
                except (ValidationError, KeyError) as exc:
                    errors += 1
                    log.debug("food validation error: %s", exc)

            chunk += 1
            await asyncio.sleep(1.0)

        log.info("food: done — %d valid, %d errors", valid, errors)
