import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.inventory import router as inventory_router
from app.api.items import router as item_router
from app.config import settings
from app.database import init_db
from app.exceptions import (BusinessError, InventoryAlreadyExistsError,
                            ItemAlreadyExistsError, NotAdminError,
                            NotFoundError, ServiceError, ValidationError)

import aioredis
from app.services.item_service import ItemService

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

redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """"""
    global redis_client

    try:
        logger.info("Initializing database...")
        await init_db()

        logger.info("Initializing Redis...")
        redis_client = await aioredis.from_url(
            "redis://redis:6379", encoding="utf-8", decode_responses=True
        )
        ItemService.set_redis(redis_client)

    except SQLAlchemyError as e:
        logger.critical(f"Failed to initialize database: {e}")
        raise
    except Exception as e:
        logger.critical(f"Failed to initialize Redis: {e}")
        raise

    yield
    logger.info("Application shutdown started")
    logger.info("Application shutdown completed")


app = FastAPI(lifespan=lifespan)

@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)}
    )


@app.exception_handler(BusinessError)
async def business_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(ServiceError)
async def service_handler(request: Request, exc: ServiceError):
    logger.error(f"Service error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Service unavailable"}
    )


@app.exception_handler(InventoryAlreadyExistsError)
async def inventory_already_exists_handler(
    request: Request,
    exc: InventoryAlreadyExistsError
):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )


@app.exception_handler(ItemAlreadyExistsError)
async def item_already_exists_handler(
    request: Request,
    exc: InventoryAlreadyExistsError
):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


@app.exception_handler(NotAdminError)
async def user_not_admin_handler(request: Request, exc: NotAdminError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal error"}
    )


app.include_router(item_router)
app.include_router(inventory_router)
