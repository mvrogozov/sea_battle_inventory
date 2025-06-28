import logging
import os

from logging.handlers import RotatingFileHandler
from fastapi import HTTPException, status

from app.config import settings
from app.inventory.models import Item
from app.inventory.schemas import ItemCreate, UserInfo
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

    async def add_item(self, item: ItemCreate, user: UserInfo) -> Item:
        """
        Создать новый предмет
        :param item: данные нового предмета (ItemCreate)
        :return: созданный предмет (Item)
        """
        if user.role != 'admin':
            raise HTTPException(
                detail='Недостаточно прав',
                status_code=status.HTTP_403_FORBIDDEN
            )
        return await self.item_repository.add_item(item.model_dump())

    async def get_all_items(self) -> list[Item]:
        """
        Получить список всех предметов
        :return: список предметов (list[Item])
        """
        return await self.item_repository.find_all()

    async def get_item(self, item_id: int) -> Item:
        """
        Получить предмет по его ID
        :param item_id: идентификатор предмета
        :return: предмет (Item) или None, если не найден
        """
        return await self.item_repository.get_item_by_id(item_id)
