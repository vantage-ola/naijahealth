from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response

from bot.whatsapp.handler import handle_message
from core.config import get_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


def _verify_signature(body: bytes, signature: str) -> bool:
    cfg = get_config()
    if not cfg.whatsapp_webhook_secret:
        return True  # skip if secret not configured
    if not signature:
        return False
    expected = hmac.new(
        cfg.whatsapp_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    received = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@router.get("")
async def verify(request: Request):
    params = dict(request.query_params)
    cfg = get_config()
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == cfg.whatsapp_verify_token
    ):
        return Response(content=params.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not _verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue
                value = change["value"]
                for msg in value.get("messages", []):
                    if msg.get("type") != "text":
                        continue
                    from_number = msg["from"]
                    message_id = msg["id"]
                    user_text = msg["text"]["body"]
                    background_tasks.add_task(handle_message, from_number, message_id, user_text)
                    logger.info("queued message id=%s from=%s", message_id, from_number)
    except Exception:
        logger.exception("error parsing whatsapp payload")

    return {"status": "ok"}
