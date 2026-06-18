from __future__ import annotations

import logging

import httpx

from bot.whatsapp.formatter import format_answer
from core.config import get_config
from rag.engine import answer

logger = logging.getLogger(__name__)

_API_URL = "https://api.telegram.org/bot{token}/{method}"


def _url(method: str) -> str:
    return _API_URL.format(token=get_config().telegram_bot_token, method=method)


async def _send_chat_action(client: httpx.AsyncClient, chat_id: int) -> None:
    try:
        await client.post(_url("sendChatAction"), json={"chat_id": chat_id, "action": "typing"})
    except Exception:
        logger.warning("sendChatAction failed for chat_id=%s", chat_id)


async def _send_message(client: httpx.AsyncClient, chat_id: int, text: str) -> None:
    resp = await client.post(
        _url("sendMessage"),
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
    )
    if resp.status_code != 200:
        logger.error("sendMessage failed %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
    logger.info("reply sent to chat_id=%s", chat_id)


async def handle_message(chat_id: int, user_text: str) -> None:
    logger.info("incoming chat_id=%s text=%r", chat_id, user_text[:80])

    async with httpx.AsyncClient(timeout=30) as client:
        await _send_chat_action(client, chat_id)

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
            await _send_message(client, chat_id, reply)
        except Exception:
            logger.exception("failed to send reply to chat_id=%s", chat_id)
