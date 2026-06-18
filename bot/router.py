from fastapi import APIRouter

from bot.telegram.webhook import router as telegram_router
from bot.whatsapp.webhook import router as whatsapp_router

router = APIRouter()
router.include_router(whatsapp_router)
router.include_router(telegram_router)
