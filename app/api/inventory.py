from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.item_repo import ItemRepository
from app.inventory.models import Inventory, InventoryCreate, InventoryResponse

router = APIRouter(prefix='/inventory')


@router.post('/', response_model=Inventory)
async def create_inventory(
    inventory: InventoryCreate,
    session: AsyncSession = Depends(get_session)
):
    repo = InventoryRepository()
    return await repo.add(session, values=inventory.model_dump())


@router.get('/', response_model=list[Inventory])
async def get_inventories(
    session: AsyncSession = Depends(get_session)
):
    repo = InventoryRepository()
    return await repo.find_all(session)


@router.post('/{item_id}', response_model=Inventory | None)
async def add_item_to_inventory(
    item_id: int,
    amount: int,
    session: AsyncSession = Depends(get_session)
):
    repo = InventoryRepository()
    return await repo.add_item(session, 333, item_id, amount)


@router.get('/full-info', response_model=InventoryResponse)
async def get_inventories_full(
    session: AsyncSession = Depends(get_session)
):
    repo = InventoryRepository()
    return await repo.get_inventory_with_items(session, 333)


@router.get('/{inventory_id}', response_model=Inventory | None)
async def get_inventory_by_id(
    inventory_id: int,
    session: AsyncSession = Depends(get_session)
):
    repo = InventoryRepository()
    return await repo.find_one_or_none_by_id(session, inventory_id)
