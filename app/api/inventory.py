from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.responses import (ALREADY_EXISTS, NOT_FOUND_RESPONSE,
                               SERVICE_ERROR, UNEXPECTED_ERROR)
from app.inventory.common import get_current_user
from app.inventory.schemas import (InventoryResponse, ItemToInventory,
                                   SuccessResponse, UseItem, UserInfo)
from app.services.inventory_service import InventoryService

router = APIRouter(
    prefix='/inventory',
    tags=["inventory"],
    responses={**SERVICE_ERROR, **UNEXPECTED_ERROR},
)


@router.post(
    '/',
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ALREADY_EXISTS,
    summary="Создать инвентарь пользователя",
    description=(
        "Возвращает сообщение с полем {'detail': 'Inventory created'}"
        " при успешном создании инвентаря"
    ),
)
async def create_inventory(
        inventory_service: Annotated[InventoryService, Depends()],
        user: Annotated[UserInfo, Depends(get_current_user)]
):
    await inventory_service.create_inventory(user)
    return SuccessResponse(detail="Inventory created")


@router.post(
    '/add_item',
    response_model=SuccessResponse,
    responses=NOT_FOUND_RESPONSE,
    summary=(
        "Добавить предмет в инвентарь пользователя. "
        "Доступно только администраторам"
    ),
    description="Поля для добавления",
    tags=["admin"]
)
async def add_to_inventory(
        item_to_inventory: ItemToInventory,
        inventory_service: Annotated[InventoryService, Depends()],
        user: Annotated[UserInfo, Depends(get_current_user)],
):
    await inventory_service.add_to_inventory(item_to_inventory, user)
    return SuccessResponse(detail="Item added")


@router.patch(
    '/use_item',
    response_model=SuccessResponse,
    summary="Использовать предмет из инвентаря игрока",
    description="Использует предмет и уменьшает его количество в инвентаре",
              )
async def remove_from_inventory(
    item: UseItem,
    inventory_service: Annotated[InventoryService, Depends()],
    # user: Annotated[UserInfo, Depends(get_current_user)],
):
    return await inventory_service.use_item_from_inventory(item)


@router.get('/user_inventory', response_model=InventoryResponse)
async def get_user_inventory(
        inventory_service: Annotated[InventoryService, Depends()],
        user: Annotated[UserInfo, Depends(get_current_user)]
):
    """
    Получить инвентарь текущего пользователя.

    - **returns**: Инвентарь пользователя
    """
    return await inventory_service.get_user_inventory(user)
