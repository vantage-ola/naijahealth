from fastapi import APIRouter

from bot.whatsapp.webhook import router as whatsapp_router

router = APIRouter()
router.include_router(whatsapp_router)
