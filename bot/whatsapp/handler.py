from __future__ import annotations

import logging

import httpx

from bot.whatsapp.formatter import format_answer
from core.config import get_config
from rag.engine import answer

logger = logging.getLogger(__name__)

_GRAPH_URL = "https://graph.facebook.com/v25.0"


def _headers() -> dict:
    cfg = get_config()
    return {
        "Authorization": f"Bearer {cfg.whatsapp_access_token}",
        "Content-Type": "application/json",
    }


def _messages_url() -> str:
    cfg = get_config()
    return f"{_GRAPH_URL}/{cfg.whatsapp_phone_number_id}/messages"


async def _mark_read(client: httpx.AsyncClient, message_id: str) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {"type": "text"},
    }
    try:
        await client.post(_messages_url(), json=payload, headers=_headers())
    except Exception:
        logger.warning("failed to mark message %s as read", message_id)


async def _send_text(client: httpx.AsyncClient, to: str, text: str) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    resp = await client.post(_messages_url(), json=payload, headers=_headers())
    resp.raise_for_status()
    logger.debug("sent reply to %s: %s", to, resp.json())


async def handle_message(from_number: str, message_id: str, user_text: str) -> None:
    cfg = get_config()
    if not cfg.whatsapp_access_token or not cfg.whatsapp_phone_number_id:
        logger.warning("WhatsApp credentials not configured — reply skipped")
        return

    logger.info("incoming from=%s id=%s text=%r", from_number, message_id, user_text[:80])

    async with httpx.AsyncClient(timeout=30) as client:
        await _mark_read(client, message_id)

        try:
            result = await answer(user_text)
            reply = format_answer(result.answer, result.sources)
        except Exception:
            logger.exception("rag failed for query=%r", user_text[:80])
            reply = (
                "Sorry, I couldn't process your request right now. "
                "Please try again or visit nafdac.gov.ng for official information."
            )

        try:
            await _send_text(client, from_number, reply)
        except Exception:
            logger.exception("failed to send reply to %s", from_number)
