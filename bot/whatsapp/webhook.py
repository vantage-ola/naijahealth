from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request

from bot.whatsapp.handler import handle_message
from core.config import get_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


@router.get("")
async def verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
):
    cfg = get_config()
    if hub_mode == "subscribe" and hub_verify_token == cfg.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages")
        if not messages:
            return {"status": "no_messages"}

        msg = messages[0]
        if msg.get("type") != "text":
            return {"status": "unsupported_type"}

        from_number = msg["from"]
        user_text = msg["text"]["body"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("malformed whatsapp payload: %s", exc)
        return {"status": "ignored"}

    background_tasks.add_task(handle_message, from_number, user_text)
    return {"status": "queued"}
