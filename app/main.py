from fastapi import FastAPI
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from app.api import items, inventory
from app.database import engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(items.router)
app.include_router(inventory.router)
# app.include_router(inventories.router)
