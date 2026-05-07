# Health check and status monitoring routes.

from fastapi import APIRouter
from core.config import get_config

router = APIRouter()
config = get_config()


@router.get("/health")
async def health():
    return {"message": 0}