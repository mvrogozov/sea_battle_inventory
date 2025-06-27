from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.inventory.schemas import InventoryResponse, ItemToInventory, UserInfo
from app.inventory.models import Inventory, InventoryCreate
from app.inventory.common import get_current_user, logger
from app.services.inventory_service import InventoryService

router = APIRouter(prefix='/inventory', tags=["inventory"])


@router.post('/', response_model=Inventory)
async def create_inventory(
    inventory: InventoryCreate,
    inventory_service: Annotated[InventoryService, Depends()],
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """
    Создать новый инвентарь для пользователя.

    - **inventory**: Данные для создания инвентаря (user_id и т.д.)
    - **returns**: Объект созданного инвентаря.
    """
    return await inventory_service.create_inventory(inventory, user)


@router.get('/', response_model=list[Inventory])
async def get_inventories(
    inventory_service: Annotated[InventoryService, Depends()]
):
    """
    Получить список всех инвентарей.

    - **returns**: Список всех инвентарей в системе.
    """
    return await inventory_service.get_all()


@router.post('/add_item', response_model=Inventory | None)
async def add_to_inventory(
        item_to_inventory: ItemToInventory,
        inventory_service: Annotated[InventoryService, Depends()],
        request: Request
):
    """
    Добавить предмет в инвентарь пользователя.

    - **item_to_inventory**: Данные о добавляемом предмете и инвентаре
    - **returns**: Обновлённый инвентарь или None, если не найден
    """
    token = request.headers.get('Authorization')
    return await inventory_service.add_to_inventory(item_to_inventory, token)


@router.get('/user_inventory', response_model=InventoryResponse)
async def get_user_inventory(
    inventory_service: Annotated[InventoryService, Depends()]
):
    """
    Получить инвентарь пользователя с user_id=777 (пример).

    - **returns**: Инвентарь пользователя
    """
    return await inventory_service.get_user_inventory(777)


@router.get('/{inventory_id}', response_model=InventoryResponse | None)
async def get_inventory_by_id(
    inventory_id: int,
    inventory_service: Annotated[InventoryService, Depends()]
):
    """
    Получить инвентарь по его ID.

    - **inventory_id**: Идентификатор инвентаря
    - **returns**: Инвентарь или None, если не найден
    """
    return await inventory_service.get_by_id(inventory_id)
