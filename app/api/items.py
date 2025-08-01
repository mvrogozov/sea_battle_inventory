from typing import Annotated

from fastapi import APIRouter, Path, Request
from fastapi.params import Depends

from app.api.responses import (NOT_FOUND_RESPONSE, SERVICE_ERROR,
                               UNEXPECTED_ERROR, DELETED_RESPONSE)
from app.inventory.common import get_current_user
from app.inventory.schemas import ItemCreate, ItemResponse, UserInfo
from app.services.item_service import ItemService, get_item_service


router = APIRouter(
    prefix='/items',
    tags=['items'],
    responses={**SERVICE_ERROR, **UNEXPECTED_ERROR}
)


@router.get(
    '/',
    response_model=list[ItemResponse],
    summary="Получить список всех предметов",
    description="Возвращает список всех предметов в игре",
)
async def get_items(
    item_service: Annotated[ItemService, Depends(get_item_service)]
):
    items = await item_service.get_all_items()
    return items


@router.delete(
    '/{item_id}',
    summary="Удалить предмет по его ID",
    responses=DELETED_RESPONSE,
    description=(
        'Удаляет предмет по его уникальному идентификатору. '
        'Доступно только администраторам'
    ),
    tags=['admin']
)
async def delete_item(
    item_service: Annotated[ItemService, Depends(get_item_service)],
    user: Annotated[UserInfo, Depends(get_current_user)],
    item_id: int = Path(
        ..., gt=0, description="ID предмета (должен быть больше 0)"
    )
):
    return await item_service.delete_item(item_id, user)


@router.post(
    '/create',
    response_model=ItemResponse,
    summary="Создать новый предмет. Доступно только администратору",
    description="Возвращает созданный предмет",
    tags=['admin']
)
async def create_item(
        request: Request,
        item: ItemCreate,
        item_service: Annotated[ItemService, Depends(get_item_service)],
        user: Annotated[UserInfo, Depends(get_current_user)]
):
    return await item_service.create_item(item, user, request)


@router.get(
    '/{item_id}',
    response_model=ItemResponse,
    responses=NOT_FOUND_RESPONSE,
    summary="Получить предмет по его ID",
    description="Возвращает предмет по его уникальному идентификатору",
)
async def get_item_by_id(
        item_service: Annotated[ItemService, Depends(get_item_service)],
        item_id: int = Path(
            ..., gt=0, description="ID предмета (должен быть больше 0)"
        ),
):
    item = await item_service.get_item(item_id)
    return item
