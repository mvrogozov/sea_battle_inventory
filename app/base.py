from sqlalchemy.future import select
from app.database import get_session


class BaseDAO:
    model = None

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        async with get_session() as session:
            query = select(cls.model).filter_by(id=data_id)
            result = await session.exec(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with get_session() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.exec(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_all(cls, **filter_by):
        async with get_session() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.exec(query)
            return result.scalars().all()

    @classmethod
    async def add(cls, values):
        async with get_session() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                return new_instance
