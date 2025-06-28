import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from app.database import get_session
from app.exceptions import DatabaseError, RepositoryError

logger = logging.getLogger(__name__)


class BaseDAO:
    model = None

    @classmethod
    async def find_one_or_none_by_id(cls, data_id: int):
        try:
            async with get_session() as session:
                query = select(cls.model).filter_by(id=data_id)
                result = await session.exec(query)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
                logger.error(f"Database error for item_id {data_id}: {e}")
                raise DatabaseError(f"Failed to fetch item {data_id}") from e
        except Exception as e:
            logger.error(f"Unexpected error in repository: {e}")
            raise RepositoryError("Repository operation failed") from e

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        try:
            async with get_session() as session:
                query = select(cls.model).filter_by(**filter_by)
                result = await session.exec(query)
                return result.scalar_one_or_none()
        except SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise DatabaseError(f"Failed to fetch find item") from e
        except Exception as e:
            logger.error(f"Unexpected error in repository: {e}")
            raise RepositoryError("Repository operation failed") from e


    @classmethod
    async def find_all(cls, **filter_by):
        try:
            async with get_session() as session:
                query = select(cls.model).filter_by(**filter_by)
                result = await session.exec(query)
                return result.scalars().all()
        except SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise DatabaseError(f"Failed to fetch find all items") from e
        except Exception as e:
            logger.error(f"Unexpected error in repository: {e}")
            raise RepositoryError("Repository operation failed") from e


    @classmethod
    async def add(cls, values):
        try:
            async with get_session() as session:
                async with session.begin():
                    new_instance = cls.model(**values)
                    session.add(new_instance)
                    return new_instance
        except SQLAlchemyError as e:
                logger.error(f"Database error: {e}")
                raise DatabaseError(f"Failed to add new item") from e
        except Exception as e:
            logger.error(f"Unexpected error in repository: {e}")
            raise RepositoryError("Repository operation failed") from e