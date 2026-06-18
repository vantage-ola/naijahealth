from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Request

from bot.telegram.handler import handle_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook/telegram", tags=["telegram"])


@router.post("")
async def receive(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()

    try:
        message = data.get("message") or data.get("edited_message")
        if not message:
            return {"status": "no_message"}

        text = message.get("text", "").strip()
        if not text:
            return {"status": "no_text"}

        chat_id = message["chat"]["id"]
        background_tasks.add_task(handle_message, chat_id, text)
        logger.info("queued message from chat_id=%s", chat_id)
    except Exception:
        logger.exception("error parsing telegram payload")

    return {"status": "ok"}
