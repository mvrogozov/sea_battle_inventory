import logging
import os

from logging.handlers import RotatingFileHandler

from app.config import settings
from app.exceptions import (
    DatabaseError, ServiceError, ValidationError, NotFoundError,
    NotAdminError
)
from app.inventory.models import Item
from app.inventory.schemas import ItemCreate, ItemResponse, UserInfo
from app.repositories.item_repo import ItemRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    os.path.join(settings.LOG_PATH, 'app_service.log'),
    maxBytes=50000,
    backupCount=1
)
logger.addHandler(handler)


class ItemService:
    """
    Сервис для работы с предметами (Item)
    Содержит бизнес-логику для создания, получения и поиска предметов
    """
    item_repository = ItemRepository()

    async def create_item(self, item: ItemCreate, user: UserInfo) -> Item:
        """
        Создать новый предмет. Доступен только администратору

        :param item: данные нового предмета (ItemCreate)
        :return: созданный предмет (Item)
        """
        await self.check_user_is_admin(user)
        try:
            return await self.item_repository.add(item.model_dump())
        except DatabaseError as e:
            logger.error(f"Database error in service: {e}")
            raise ServiceError("Service temporarily unavailable") from e
        except Exception as e:
            logger.error(f"Unexpected error in service: {e}")
            raise ServiceError("Internal service error") from e

    async def get_all_items(self) -> list[ItemResponse]:
        """
        Получить список всех предметов

        :return: список предметов (list[ItemResponse])
        """
        try:
            items = await self.item_repository.find_all()
            return items
        except DatabaseError as e:
            logger.error(f"Database error in service: {e}")
            raise ServiceError("Service temporarily unavailable") from e
        except Exception as e:
            logger.error(f"Unexpected error in service: {e}")
            raise ServiceError("Internal service error") from e

    async def get_item(self, item_id: int) -> Item | None:
        """
        Получить предмет по его ID

        :param item_id: идентификатор предмета
        :return: предмет (Item) или None, если не найден
        """
        try:
            if item_id <= 0:
                raise ValidationError("Item ID must be positive")

            await self.check_item_exists(item_id)
            item = await self.item_repository.find_one_or_none_by_id(item_id)
            return item
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except DatabaseError as e:
            logger.error(f"Database error in service: {e}")
            raise ServiceError("Service temporarily unavailable") from e
        except Exception as e:
            logger.error(f"Unexpected error in service: {e}")
            raise ServiceError("Internal service error") from e

    async def check_item_exists(self, item_id: int) -> bool:
        """Проверить, что предмет существует"""
        item_is_exist = await self.item_repository.check_exists(item_id)
        if item_is_exist:
            return item_is_exist
        raise NotFoundError(f"Item with ID {item_id} not found")

    @staticmethod
    async def check_user_is_admin(user: UserInfo) -> None:
        """
        Проверка, что пользователь — администратор
        :param user: информация о пользователе
        :raises NotAdminError: если пользователь не админ
        """
        if user.role != 'admin':
            raise NotAdminError("Only admin allowed")