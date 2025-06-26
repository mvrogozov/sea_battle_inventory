from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.item_repo import ItemRepository
from app.inventory.models import Inventory, InventoryCreate, InventoryResponse

router = APIRouter(prefix='/inventory')


@router.post('/', response_model=Inventory)
async def create_inventory(inventory: InventoryCreate):
    repo = InventoryRepository()
    return await repo.add(inventory.model_dump())


@router.get('/', response_model=list[Inventory])
async def get_inventories():
    repo = InventoryRepository()
    return await repo.find_all()


@router.post('/{item_id}', response_model=Inventory | None)
async def add_item_to_inventory(
    item_id: int,
    amount: int,
):
    repo = InventoryRepository()
    return await repo.add_item(777, item_id, amount)


@router.get('/user_inventory', response_model=InventoryResponse)
async def get_user_inventory():
    repo = InventoryRepository()
    return await repo.get_user_inventory(777)


@router.get('/{inventory_id}', response_model=InventoryResponse | None)
async def get_inventory_by_id(inventory_id: int,):
    repo = InventoryRepository()
    return await repo.get_inventory_by_id(inventory_id)
