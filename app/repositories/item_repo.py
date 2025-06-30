from sqlalchemy import exists, select
from sqlalchemy.exc import SQLAlchemyError

from app.base import BaseDAO, logger
from app.database import get_session
from app.exceptions import DatabaseError, RepositoryError
from app.inventory.models import Item


class ItemRepository(BaseDAO):
    model = Item

    @classmethod
    async def check_name_exists(cls, name: str) -> bool:
        try:
            async with get_session() as session:
                query = select(exists().where(cls.model.name == name))
                result = await session.exec(query)
                return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Database error for item {name}: {e}")
            raise DatabaseError(
                f"Failed to fetch inventory fot item - {name}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error in repository: {e}")
            raise RepositoryError("Repository operation failed") from e
