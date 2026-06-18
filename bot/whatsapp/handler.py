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
    try:
        await client.post(
            _messages_url(),
            headers=_headers(),
            json={"messaging_product": "whatsapp", "status": "read", "message_id": message_id},
        )
    except Exception:
        logger.warning("mark-as-read failed for %s", message_id)


async def _show_typing(client: httpx.AsyncClient, to: str) -> None:
    try:
        await client.post(
            _messages_url(),
            headers=_headers(),
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "typing_indicator": {"type": "text"},
            },
        )
    except Exception:
        logger.warning("typing indicator failed for %s", to)


async def _send_text(client: httpx.AsyncClient, to: str, text: str) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    resp = await client.post(_messages_url(), json=payload, headers=_headers())
    if resp.status_code != 200:
        logger.error("send failed %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
    logger.info("reply sent to %s", to)


async def handle_message(from_number: str, message_id: str, user_text: str) -> None:
    cfg = get_config()
    if not cfg.whatsapp_access_token or not cfg.whatsapp_phone_number_id:
        logger.warning("WhatsApp credentials not configured — reply skipped")
        return

    logger.info("incoming from=%s id=%s text=%r", from_number, message_id, user_text[:80])

    async with httpx.AsyncClient(timeout=30) as client:
        await _mark_read(client, message_id)
        await _show_typing(client, from_number)

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
