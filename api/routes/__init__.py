from fastapi import APIRouter

from api.routes import health

router = APIRouter()
router.include_router(health.router)
