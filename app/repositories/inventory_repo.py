from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import (
    update as sqlalchemy_update, delete as sqlalchemy_delete, func
)

from app.inventory.models import (
    Inventory, Item, InventoryItem, InventoryItemResponse, InventoryResponse
)
from app.base import BaseDAO


class InventoryRepository(BaseDAO):
    model = Inventory

    @classmethod
    async def add_item(
        cls,
        session: AsyncSession,
        user_id: int,
        item_id: int,
        amount: int
    ):
        async with session as session:
            async with session.begin():
                query = select(cls.model).filter_by(user_id=user_id)
                result = await session.exec(query)
                inv_obj: Inventory = result.scalar_one_or_none()
                if not inv_obj:
                    inv_obj: Inventory = Inventory(user_id=user_id)
                    session.add(inv_obj)
                    session.commit()
                    session.refresh(inv_obj)
                    # raise HTTPException(
                    #     status_code=status.HTTP_404_NOT_FOUND,
                    #     detail=(
                    #         f'Не существует инвентаря для '
                    #         f'пользователя {user_id}'
                    #     )
                    # )

                item_obj = await session.get(Item, item_id)
                if not item_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f'Не существует предмета {item_id}'
                        )
                    )

                query = select(InventoryItem).where(
                    InventoryItem.inventory_id == inv_obj.id,
                    InventoryItem.item_id == item_id
                )
                existing_link = (
                    await session.exec(query)
                ).scalar_one_or_none()

                if existing_link:
                    if existing_link.amount + amount < 0:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Недостаточно средств'
                        )
                    existing_link.amount += amount
                else:
                    new_link = InventoryItem(
                        inventory_id=inv_obj.id,
                        item_id=item_id,
                        amount=amount
                    )
                    session.add(new_link)
                return inv_obj

    @classmethod
    async def get_user_inventory(
        cls,
        session,
        user_id: int
    ):
        async with session.begin():
            query = select(cls.model).filter_by(user_id=user_id)
            result = await session.execute(query)
            inv_obj: Inventory = result.scalar_one_or_none()
            if not inv_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f'Не существует инвентаря для пользователя {user_id}'
                    )
                )
            query = (
                select(
                    InventoryItem.item_id,
                    Item.name,
                    InventoryItem.amount
                )
                .join(Item, InventoryItem.item_id == Item.id)
                .where(InventoryItem.inventory_id == inv_obj.id)
            )
            result = await session.execute(query)
            items_data = result.all()
            items = [
                InventoryItemResponse(
                    item_id=item_id,
                    name=name,
                    amount=amount
                )
                for item_id, name, amount in items_data
            ]
            return InventoryResponse(
                user_id=user_id,
                items=items
            )
