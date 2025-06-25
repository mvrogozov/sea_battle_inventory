from app.inventory.models import (
    Inventory, Item, InventoryItem, InventoryItemResponse, InventoryResponse
)
from app.base import BaseDAO
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import (
    update as sqlalchemy_update, delete as sqlalchemy_delete, func
)


class InventoryRepository(BaseDAO):
    model = Inventory

    @classmethod
    async def add_item(
        cls,
        session,
        user_id: int,
        item_id: int,
        amount: int
    ):
        async with session as session:
            async with session.begin():
                query = select(cls.model).filter_by(user_id=user_id)
                result = await session.execute(query)
                inv_obj: Inventory = result.scalar_one_or_none()
                if not inv_obj:
                    raise ValueError(f"Inventory for user {user_id} not found")

                item_obj = await session.get(Item, item_id)
                if not item_obj:
                    raise ValueError(f"Item with id {item_id} not found")

                query = select(InventoryItem).where(
                    InventoryItem.inventory_id == inv_obj.id,
                    InventoryItem.item_id == item_id
                )
                existing_link = (await session.execute(query)).scalar_one_or_none()

                if existing_link:
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
    async def get_inventory_with_items(
        cls,
        session,
        user_id: int
    ):
        async with session.begin():
            query = select(cls.model).filter_by(user_id=user_id)
            result = await session.execute(query)
            inv_obj: Inventory = result.scalar_one_or_none()
            if not inv_obj:
                raise ValueError(f"Inventory for user {user_id} not found")
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
