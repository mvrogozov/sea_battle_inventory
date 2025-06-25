from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.repositories.item_repo import ItemRepository
from app.inventory.models import Item

router = APIRouter(prefix="/items")


@router.post("/", response_model=Item)
async def create_item(
    item: Item,
    session: AsyncSession = Depends(get_session)
):
    repo = ItemRepository(session)
    return await repo.create(item.model_dump())


@router.get("/", response_model=Item)
async def get_item(
    session: AsyncSession = Depends(get_session)
):
    repo = ItemRepository(session)
    return await repo.get_by_id(1)