from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.repositories.item_repo import ItemRepository
from app.inventory.models import Item, ItemCreate

router = APIRouter(prefix="/items")


@router.post("/", response_model=Item)
async def create_item(item: ItemCreate):
    repo = ItemRepository()
    return await repo.add(item.model_dump())


@router.get("/", response_model=list[Item])
async def get_items():
    repo = ItemRepository()
    return await repo.find_all()


@router.get("/{item_id}", response_model=Item | None)
async def get_item_by_id(item_id: int):
    repo = ItemRepository()
    return await repo.find_one_or_none_by_id(item_id)
