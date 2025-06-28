from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.sql import exists

from app.inventory.models import Item, Inventory
from app.base import BaseDAO
from app.database import get_session


class ItemRepository(BaseDAO):
    model = Item

    @classmethod
    async def add_item(cls, values):
        async with get_session() as session:
            async with session.begin():
                query = select(exists().where(
                    cls.model.name == values.get('name'))
                )
                obj = await session.exec(query)
                obj = obj.one()
                if obj[0]:
                    raise HTTPException(
                        detail='Already exists',
                        status_code=status.HTTP_409_CONFLICT
                    )
                new_instance = cls.model(**values)
                session.add(new_instance)
                return new_instance

    @classmethod
    async def get_item_by_id(
            cls,
            item_id: int
    ):
        async with get_session() as session:
            async with session.begin():
                inv_obj = await session.get(Item, item_id)
                if not inv_obj:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=(
                            f'Не существует предмета {item_id}'
                        )
                    )
                return inv_obj
