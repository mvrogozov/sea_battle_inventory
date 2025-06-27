import logging
import os

from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.api.items import router as item_router
from app.database import init_db
from app.api.inventory import router as inventory_router

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    os.path.join(settings.LOG_PATH, 'main.log'),
    maxBytes=50000,
    backupCount=1
)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """"""
    try:
        logger.info("Initializing database...")
        await init_db()
    except SQLAlchemyError as e:
        logger.critical(f"Failed to initialize database: {e}")
        raise

    yield
    logger.info("Application shutdown started")
    logger.info("Application shutdown completed")


app = FastAPI(lifespan=lifespan)
app.include_router(item_router)
app.include_router(inventory_router)
