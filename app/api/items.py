from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends

from app.inventory.schemas import ItemCreate
from app.inventory.models import Item
from app.services.item_service import ItemService


router = APIRouter(prefix="/items", tags=["items"])


@router.post("/", response_model=Item)
async def create_item(
        item: ItemCreate,
        item_service: Annotated[ItemService, Depends()],
):
    """
    Создать новый предмет.

    - **item**: Данные нового предмета (название, описание, тип, скрипт и т.д.)
    - **returns**: Объект созданного предмета.
    """
    return await item_service.add_item(item)


@router.get("/", response_model=list[Item])
async def get_items(
        item_service: Annotated[ItemService, Depends()],
):
    """
    Получить список всех предметов.

    - **returns**: Список всех предметов в системе.
    """
    return await item_service.get_all_items()


@router.get("/{item_id}", response_model=Item | None)
async def get_item_by_id(
        item_id: int,
        item_service: Annotated[ItemService, Depends(),],
):
    """
    Получить предмет по его ID.

    - **item_id**: Идентификатор предмета
    - **returns**: Объект предмета или None, если не найден
    """
    return await item_service.get_item(item_id)
