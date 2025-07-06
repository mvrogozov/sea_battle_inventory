from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.sql import exists

from app.base import BaseDAO
from app.database import get_session
from app.exceptions import (
    DatabaseError, RepositoryError, InventoryAlreadyExistsError,
    ValidationError, NotFoundError
)
from app.inventory.common import logger
from app.inventory.models import Inventory, InventoryItem, Item
from app.inventory.schemas import (InventoryItemResponse, InventoryResponse,
                                   UserInfo, UseItem)


class InventoryRepository(BaseDAO):
    model = Inventory

    @classmethod
    async def add_for_current_user(cls, user: UserInfo):
        user_id = user.user_id
        async with get_session() as session:
            async with session.begin():
                query = select(exists().where(cls.model.user_id == user_id))
                obj = await session.exec(query)
                obj = obj.one()
                if obj[0]:
                    raise HTTPException(
                        detail='Already exists',
                        status_code=status.HTTP_409_CONFLICT
                    )
                new_instance = cls.model(user_id=user_id)
                session.add(new_instance)
                return new_instance

    @classmethod
    async def add_item(
            cls,
            user_id: int,
            item_id: int,
            amount: int
    ):
        if amount <= 0:
            raise ValidationError(
                detail='Amount should be positive'
            )
        async with get_session() as session:
            async with session.begin():
                query = select(cls.model).filter_by(user_id=user_id)
                result = await session.exec(query)
                inv_obj: Inventory = result.scalar_one_or_none()
                if not inv_obj:
                    inv_obj: Inventory = Inventory(user_id=user_id)
                    session.add(inv_obj)
                    session.commit()
                    session.refresh(inv_obj)

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
            user_id: int
    ):
        async with get_session() as session:
            async with session.begin():
                query = select(cls.model).filter_by(user_id=user_id)
                result = await session.exec(query)
                inv_obj: Inventory = result.scalar_one_or_none()
                if not inv_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f'Не существует инвентаря для '
                            f'пользователя {user_id}'
                        )
                    )
                query = (
                    select(
                        InventoryItem.item_id,
                        Item.name,
                        Item.script,
                        InventoryItem.amount
                    )
                    .join(Item, InventoryItem.item_id == Item.id)
                    .where(InventoryItem.inventory_id == inv_obj.id)
                )
                result = await session.exec(query)
                items_data = result.all()
                linked_items = [
                    InventoryItemResponse(
                        item_id=item_id,
                        name=name,
                        script=script,
                        amount=amount
                    )
                    for item_id, name, script, amount in items_data
                ]
                return InventoryResponse(
                    user_id=user_id,
                    linked_items=linked_items
                )

    @classmethod
    async def get_inventory_by_id(
            cls,
            inventory_id: int
    ):
        async with get_session() as session:
            async with session.begin():
                inv_obj = await session.get(Inventory, inventory_id)
                if not inv_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f'Не существует инвентаря {inventory_id}'
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
                result = await session.exec(query)
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
                    user_id=inv_obj.user_id,
                    items=items
                )

    @classmethod
    async def check_exists(cls, user_id: int) -> bool:
        try:
            async with get_session() as session:
                query = select(exists().where(cls.model.user_id == user_id))
                result = await session.exec(query)
                return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f'Database error for user_id {user_id}: {e}')
            raise DatabaseError(
                f'Failed to fetch inventory fot user - {user_id}'
            ) from e
        except Exception as e:
            logger.error(f'Unexpected error in repository: {e}')
            raise RepositoryError('Repository operation failed') from e

    @classmethod
    async def use_item_from_inventory(cls, use_item: UseItem, user: UserInfo):
        try:
            async with get_session() as session:
                query = (
                    select(InventoryItem)
                    .join(
                        Inventory, InventoryItem.inventory_id == Inventory.id
                    )
                    .where(
                        Inventory.user_id == user.user_id,
                        InventoryItem.item_id == use_item.item_id
                    )
                )
                result = await session.exec(query)
                db_item = result.scalar_one_or_none()
                if db_item.amount < use_item.amount:
                    raise ValidationError('Not unough items')
                db_item.amount -= use_item.amount
                if db_item.amount == 0:
                    await session.delete(db_item)
                await session.commit()
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            logger.error(f'Database error for create new inventory: {e}')
            raise DatabaseError('Failed to create new  inventory') from e
        except InventoryAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f'Unexpected error in repository: {e}')
            raise RepositoryError('Repository operation failed') from e

    @classmethod
    async def get_inventories_with_item(
        cls,
        item_id: int,
        #promotion_id: int | None
    ):
        async with get_session() as session:
            async with session.begin():
                item_query = select(Item).filter_by(id=item_id)
                item_result = await session.exec(item_query)
                item_obj: Item = item_result.scalar_one_or_none()
                if not item_obj:
                    raise NotFoundError(f"Item with ID {item_id} not found")
                query = (
                    select(
                        InventoryItem.inventory_id,
                        Inventory.user_id,
                        Item.name,
                        Item.script,
                        Item.shop_item_id,
                        InventoryItem.amount
                    )
                    .join(Item, InventoryItem.item_id == Item.id)
                    .join(
                        Inventory,
                        InventoryItem.inventory_id == Inventory.id
                    )
                    .where(InventoryItem.item_id == item_id)
                )

                result = await session.exec(query)
                items_data = result.all()
                inventories = {}
                for (
                    inventory_id,
                    user_id,
                    name,
                    script,
                    shop_item_id,
                    amount
                 ) in items_data:
                    if inventory_id not in inventories:
                        inventories[inventory_id] = {
                            'user_id': user_id,
                            'linked_items': []
                        }
                    inventories[inventory_id]['linked_items'].append({
                        'item_id': item_id,
                        'name': name,
                        'script': script,
                        'shop_item_id': shop_item_id,
                        'amount': amount
                    })
                return [
                    InventoryResponse(
                        user_id=data['user_id'],
                        linked_items=[
                            InventoryItemResponse(
                                item_id=item['item_id'],
                                name=item['name'],
                                shop_item_id=item['shop_item_id'],
                                script=item['script'],
                                amount=item['amount']
                            )
                            for item in data['linked_items']
                        ]
                    )
                    for inventory_id, data in inventories.items()
                ]
