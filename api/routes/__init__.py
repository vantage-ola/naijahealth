from fastapi import APIRouter

from api.routes import health, query
from bot.router import router as bot_router

router = APIRouter()
router.include_router(health.router)
router.include_router(query.router)
router.include_router(bot_router)
