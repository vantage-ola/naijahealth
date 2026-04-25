"""Greenbook spider — scrapes the NAFDAC drug registration database.

Source: https://greenbook.nafdac.gov.ng
Tech: Laravel + jQuery DataTables with server-side processing.
API: GET / with DataTables query params and X-Requested-With: XMLHttpRequest header.
"""

import asyncio
import logging
from collections.abc import AsyncIterator

from pydantic import ValidationError

from scraper.parsers.drugs import parse_greenbook_record
from scraper.spiders.base import fetch_json, new_client
from scraper.validators.drugs import GreenBookProduct

log = logging.getLogger(__name__)

BASE_URL = "https://greenbook.nafdac.gov.ng/"
PAGE_SIZE = 200
XHR_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


async def crawl() -> AsyncIterator[GreenBookProduct]:
    async with new_client() as client:
        start = 0
        draw = 1
        total = None
        valid = 0
        errors = 0

        while total is None or start < total:
            params = {
                "draw": str(draw),
                "start": str(start),
                "length": str(PAGE_SIZE),
                "order[0][column]": "0",
                "order[0][dir]": "asc",
                "search[value]": "",
                "columns[0][data]": "product_name",
                "columns[0][name]": "product_name",
                "columns[0][searchable]": "true",
                "columns[0][orderable]": "true",
            }

            url = BASE_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
            data = await fetch_json(client, url, headers=XHR_HEADERS)

            if total is None:
                total = data.get("recordsTotal", 0)
                log.info("greenbook: %d total records", total)

            records = data.get("data", [])
            if not records:
                break

            for raw in records:
                try:
                    parsed = parse_greenbook_record(raw)
                    product = GreenBookProduct(**parsed)
                    valid += 1
                    yield product
                except (ValidationError, KeyError) as exc:
                    errors += 1
                    log.debug("greenbook validation error: %s — %s", exc, raw.get("product_name", "?"))

            start += PAGE_SIZE
            draw += 1
            await asyncio.sleep(0.3)

        log.info("greenbook: done — %d valid, %d errors", valid, errors)
