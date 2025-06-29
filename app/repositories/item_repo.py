from sqlalchemy import select, exists
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_session
from app.exceptions import DatabaseError, RepositoryError
from app.inventory.models import Item, Inventory
from app.base import BaseDAO, logger


class ItemRepository(BaseDAO):
    model = Item

    # async def check_exists(self, item_id: int) -> bool:
    #     try:
    #         async with get_session() as session:
    #             query = select(exists().where(self.model.id == item_id))
    #             result = await session.exec(query)
    #             return result.scalar()
    #     except SQLAlchemyError as e:
    #             logger.error(f"Database error for item_id {item_id}: {e}")
    #             raise DatabaseError(f"Failed to fetch item {item_id}") from e
    #     except Exception as e:
    #         logger.error(f"Unexpected error in repository: {e}")
    #         raise RepositoryError("Repository operation failed") from e
