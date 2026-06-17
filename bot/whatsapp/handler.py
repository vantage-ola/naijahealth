from __future__ import annotations

import logging

import httpx

from bot.whatsapp.formatter import format_answer
from core.config import get_config
from rag.engine import answer

logger = logging.getLogger(__name__)

_GRAPH_URL = "https://graph.facebook.com/v19.0"


async def _send_message(to: str, text: str) -> None:
    cfg = get_config()
    if not cfg.whatsapp_access_token or not cfg.whatsapp_phone_number_id:
        logger.warning("WhatsApp credentials not configured — reply skipped")
        return

    url = f"{_GRAPH_URL}/{cfg.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    headers = {
        "Authorization": f"Bearer {cfg.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        logger.debug("sent message to %s: %s", to, resp.json())


async def handle_message(from_number: str, user_text: str) -> None:
    logger.info("incoming message from=%s text=%r", from_number, user_text[:80])
    try:
        result = await answer(user_text)
        reply = format_answer(result.answer, result.sources)
    except Exception:
        logger.exception("rag failed for query=%r", user_text[:80])
        reply = (
            "Sorry, I couldn't process your request right now. "
            "Please try again or visit nafdac.gov.ng for official information."
        )
    await _send_message(from_number, reply)
