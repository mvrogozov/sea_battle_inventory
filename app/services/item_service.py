import logging
import os
import json
from logging.handlers import RotatingFileHandler
from fastapi.responses import Response
from fastapi.encoders import jsonable_encoder
from fastapi import status, Depends
from fastapi_cache.backends.redis import CACHE_KEY, RedisCacheBackend


from app.config import settings
from app.exceptions import (DatabaseError, ItemAlreadyExistsError,
                            NotAdminError, NotFoundError, ServiceError,
                            ValidationError)
from app.inventory.common import producer, redis_cache, get_cache
from app.inventory.models import Item
from app.inventory.schemas import ItemCreate, ItemResponse, UserInfo
from app.repositories.item_repo import ItemRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    os.path.join(settings.LOG_PATH, 'app.log'),
    maxBytes=50000,
    backupCount=1
)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


class ItemService:
    """
    Сервис для работы с предметами (Item)
    Содержит бизнес-логику для создания, получения и поиска предметов
    """

    def __init__(self, cache: RedisCacheBackend):
        self.item_repository = ItemRepository()
        self.cache = cache

    async def create_item(self, item: ItemCreate, user: UserInfo) -> Item:
        """
        Создать новый предмет. Доступен только администратору

        :param item: данные нового предмета (ItemCreate)
        :return: созданный предмет (Item)
        """
        await self.check_user_is_admin(user)
        is_item_exist = await (
            self.item_repository.check_name_exists(item.name)
        )
        if is_item_exist:
            raise ItemAlreadyExistsError('Item already exists')
        try:
            await self.cache.delete('items_list')
            new_instance: Item = await (
                self.item_repository.add(item.model_dump())
            )
            producer.produce(
                topic='shop.inventory.updates',
                key=str(new_instance.id).encode('utf-8'),
                value=new_instance.model_dump_json()
            )
            return new_instance
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
        cache_key = 'items_list'
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                try:
                    logger.info('+++')
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    logger.error('Failed to decode cached data')
            items = await self.item_repository.find_all()
            try:
                logger.info('---')
                await self.cache.set(
                    cache_key,
                    json.dumps(jsonable_encoder(items)),
                    expire=settings.CACHE_EXPIRE
                )
            except Exception as e:
                logger.error(f'Cache set failed: {e}')
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
        cache_key = f'item_{item_id}'
        try:
            if item_id <= 0:
                raise ValidationError("Item ID must be positive")
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                try:
                    logger.info('+++')
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    logger.error('Failed to decode cached data')
            await self.check_item_exists(item_id)
            item = await self.item_repository.find_one_or_none_by_id(item_id)
            try:
                logger.info('---')
                await self.cache.set(
                    cache_key,
                    json.dumps(jsonable_encoder(item)),
                    expire=settings.CACHE_EXPIRE
                )
            except Exception as e:
                logger.error(f'Cache set failed: {e}')
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
        """
            Проверить, что предмет существует по id.
            Возбуждает NotFoundError если не существует
        """
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

    async def delete_item(self, item_id: int, user: UserInfo) -> Response:
        """
        Удалить предмет по его ID

        :param item_id: идентификатор предмета
        :return: предмет (Item) или None, если не найден
        """
        cache_key = f'item_{item_id}'
        try:
            if item_id <= 0:
                raise ValidationError("Item ID must be positive")
            await self.check_user_is_admin(user)
            await self.check_item_exists(item_id)
            await self.cache.delete(cache_key)
            await self.cache.delete('items_list')
            await self.item_repository.delete_one_by_id(item_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except (NotFoundError, NotAdminError):
            raise
        except ValidationError:
            raise
        except DatabaseError as e:
            logger.error(f"Database error in service: {e}")
            raise ServiceError("Service temporarily unavailable") from e
        except Exception as e:
            logger.error(f"Unexpected error in service: {e}")
            raise ServiceError("Internal service error") from e


async def get_item_service(
    cache: RedisCacheBackend = Depends(get_cache)
) -> ItemService:
    return ItemService(cache)