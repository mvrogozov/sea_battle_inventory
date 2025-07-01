from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.sql import exists

from app.base import BaseDAO
from app.database import get_session
from app.exceptions import (
    DatabaseError, RepositoryError, InventoryAlreadyExistsError
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
                    user_id=user_id,
                    items=items
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
            logger.error(f"Database error for user_id {user_id}: {e}")
            raise DatabaseError(
                f"Failed to fetch inventory fot user - {user_id}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error in repository: {e}")
            raise RepositoryError("Repository operation failed") from e

    @classmethod
    async def use_item_from_inventory(cls, use_item: UseItem):
        try:
            async with get_session() as session:
                query = (
                    select(InventoryItem)
                    .join(Inventory, InventoryItem.inventory_id == Inventory.id)
                    .where(Inventory.user_id == use_item.user_id)
                )
                result = await session.exec(query)
                db_item = result.scalar_one_or_none()
                db_item.amount -= use_item.amount
                if db_item.amount == 0:
                    await session.delete(db_item)
                await session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error for create new inventory: {e}")
            raise DatabaseError(f"Failed to create new  inventory") from e
        except InventoryAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in repository: {e}")
            raise RepositoryError("Repository operation failed") from e
