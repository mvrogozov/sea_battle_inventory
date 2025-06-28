from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.inventory.schemas import (
    InventoryResponse, ItemToInventory, UserInfo, ItemToInventoryByUserId
)
from app.inventory.models import Inventory, InventoryCreate
from app.inventory.common import get_current_user, logger
from app.services.inventory_service import InventoryService

router = APIRouter(prefix='/inventory', tags=["inventory"])


@router.post('/', response_model=Inventory)
async def create_inventory(
    inventory_service: Annotated[InventoryService, Depends()],
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """
    Создать новый инвентарь для пользователя.

    - **returns**: Объект созданного инвентаря.
    """
    return await inventory_service.create_inventory(user)


@router.get(
    '/',
    response_model=list[Inventory],
    dependencies=[Depends(get_current_user)]
)
async def get_inventories(
    inventory_service: Annotated[InventoryService, Depends()],
    _user: UserInfo = Depends(get_current_user)
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
        user: Annotated[UserInfo, Depends(get_current_user)],
):
    """
    Добавить предмет в инвентарь текущего пользователя.

    - **item_to_inventory**: Данные о добавляемом предмете и инвентаре
    - **returns**: Обновлённый инвентарь или None, если не найден
    """
    return await inventory_service.add_to_inventory(item_to_inventory, user)


@router.post('/add_item_by_user_id', response_model=Inventory | None)
async def add_to_inventory_by_id(
        item_to_inventory: ItemToInventoryByUserId,
        inventory_service: Annotated[InventoryService, Depends()],
        user: Annotated[UserInfo, Depends(get_current_user)],
):
    """
    Добавить предмет в инвентарь пользователя по user_id.

    - **item_to_inventory**: Данные о добавляемом предмете и инвентаре
    - **returns**: Обновлённый инвентарь или None, если не найден
    """
    return await inventory_service.add_to_inventory_by_user_id(
        item_to_inventory, user
    )


@router.get('/user_inventory', response_model=InventoryResponse)
async def get_current_user_inventory(
    inventory_service: Annotated[InventoryService, Depends()],
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """
    Получить инвентарь текущего пользователя.

    - **returns**: Инвентарь пользователя
    """
    return await inventory_service.get_current_user_inventory(user)


@router.get('/inventory_by_user_id', response_model=InventoryResponse)
async def get_inventory_by_user_id(
    inventory_service: Annotated[InventoryService, Depends()],
    user: Annotated[UserInfo, Depends(get_current_user)],
    user_id: int
):
    """
    Получить инвентарь пользователя по user_id.

    - **returns**: Инвентарь пользователя
    """
    return await inventory_service.get_user_inventory_by_id(user, user_id)


@router.get('/{inventory_id}', response_model=InventoryResponse | None)
async def get_inventory_by_id(
    inventory_id: int,
    inventory_service: Annotated[InventoryService, Depends()],
    user: Annotated[UserInfo, Depends(get_current_user)]
):
    """
    Получить инвентарь по его ID.

    - **inventory_id**: Идентификатор инвентаря
    - **returns**: Инвентарь или None, если не найден
    """
    return await inventory_service.get_by_id(inventory_id, user)
