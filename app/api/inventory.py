from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.responses import (ALREADY_EXISTS, NOT_FOUND_RESPONSE,
                               SERVICE_ERROR, UNEXPECTED_ERROR)
from app.inventory.common import get_current_user
from app.inventory.schemas import (InventoryResponse, ItemToInventory,
                                   SuccessResponse, UseItem, UserInfo)
from app.services.inventory_service import (
    InventoryService, get_inventory_service
)

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
        inventory_service: Annotated[
            InventoryService, Depends(get_inventory_service)
        ],
        user: Annotated[UserInfo, Depends(get_current_user)]
):
    await inventory_service.create_inventory(user)
    return SuccessResponse(detail="Inventory created")


@router.patch(
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
        inventory_service: Annotated[
            InventoryService, Depends(get_inventory_service)
        ],
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
    inventory_service: Annotated[
        InventoryService, Depends(get_inventory_service)
    ],
    user: Annotated[UserInfo, Depends(get_current_user)],
):
    return await inventory_service.use_item_from_inventory(item, user)


@router.get(
    '/user_inventory',
    response_model=InventoryResponse,
    summary="Получить инвентарь игрока",
    description="Возвращает инвентарь пользователя",
)
async def get_user_inventory(
        inventory_service: Annotated[
            InventoryService, Depends(get_inventory_service)
        ],
        user: Annotated[UserInfo, Depends(get_current_user)]
):
    """
    Получить инвентарь текущего пользователя.

    - **returns**: Инвентарь пользователя
    """
    return await inventory_service.get_user_inventory(user)


@router.get(
    '/all_inventory_with_item',
    response_model=list[InventoryResponse],
    summary="Получить все инвентари игроков, содержащие предмет с ID",
    description="Возвращает инвентари пользователей",
)
async def get_all_inventory_with_item(
        inventory_service: Annotated[
            InventoryService,
            Depends(get_inventory_service)
        ],
        item_id: int,
        user: Annotated[UserInfo, Depends(get_current_user)]
):
    """
    Получить все инвентари игроков, содержащие предмет с ID.

    - **returns**: Инвентари пользователя
    """
    return await inventory_service.get_all_with_item(item_id)
