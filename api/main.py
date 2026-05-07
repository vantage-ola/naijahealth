from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from core.config import get_config
from scheduler.jobs import start_scheduler, stop_scheduler


config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=config.app_name, version=config.app_version, lifespan=lifespan)
app.include_router(router)
