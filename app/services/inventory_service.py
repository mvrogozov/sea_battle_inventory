import logging
import os
import json
from logging.handlers import RotatingFileHandler

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from fastapi_cache.backends.redis import RedisCacheBackend
from aiokafka import AIOKafkaConsumer


from app.config import settings
from app.exceptions import (DatabaseError, InventoryAlreadyExistsError,
                            NotAdminError, NotFoundError, ServiceError)
from app.inventory.models import Inventory
from app.inventory.common import get_cache
from app.inventory.schemas import (ItemToInventory, SuccessResponse, UseItem,
                                   UserInfo, InventoryResponse)
from app.repositories.inventory_repo import InventoryRepository
from app.services.item_service import ItemService, get_item_service

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


class InventoryService:
    """
    Сервис для работы с инвентарями пользователей.
    Содержит бизнес-логику для создания, получения и изменения инвентарей.
    """

    def __init__(
        self,
        item_service: ItemService,
        cache: RedisCacheBackend
    ):
        self.inventory_repository = InventoryRepository()
        self.cache = cache
        self.item_service = item_service

    async def create_inventory(self, user: UserInfo) -> Inventory:
        """
        Создать инвентарь для пользователя
        Если инвентарь уже существует — выбрасывает InventoryAlreadyExistsError
        :param user: информация о пользователе
        :return: созданный инвентарь
        """
        is_inventory_exist = await (
            self.inventory_repository.check_exists(user.user_id)
        )
        if not is_inventory_exist:
            try:
                new_inventory = await (
                    self.inventory_repository.add_for_current_user(
                        user
                    )
                )
                return new_inventory
            except InventoryAlreadyExistsError:
                # Инвентарь уже существует — пробрасываем исключение
                raise
            except DatabaseError as e:
                logger.error(f"Database error in service: {e}")
                raise ServiceError("Service temporarily unavailable") from e
            except Exception as e:
                logger.error(f"Unexpected error in service: {e}")
                raise ServiceError("Internal service error") from e
        raise InventoryAlreadyExistsError(
            "Inventory for this user already exists"
        )

    async def add_to_inventory(
        self,
        item_to_inventory: ItemToInventory,
        user: UserInfo
    ):
        """
        Добавить предмет в инвентарь пользователя
        :param item_to_inventory: данные о добавляемом предмете
        :param user: информация о пользователе
        :return: обновлённый инвентарь
        """
        await self.cache.delete(f'inventory_{user.user_id}')
        try:
            await self.item_service.get_item(item_to_inventory.item_id)
            is_inventory_exist = await self.inventory_repository.check_exists(
                user.user_id
            )

            if is_inventory_exist:
                fields = item_to_inventory.model_dump()
                fields.update({'user_id': user.user_id})
                return await self.inventory_repository.add_item(**fields)
        except NotFoundError:
            raise

    async def get_user_inventory(self, user: UserInfo):
        """
        Получить инвентарь пользователя по user_id
        :param user: пользователь
        :return: инвентарь пользователя
        """
        cache_key = f'inventory_{user.user_id}'
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            try:
                return InventoryResponse(**json.loads(cached_data))
            except json.JSONDecodeError:
                logger.error('Failed to decode cached data')
        await self.check_inventory_exists(user.user_id)
        inventory = await self.inventory_repository.get_user_inventory(
            user.user_id
        )
        try:
            await self.cache.set(
                cache_key,
                json.dumps(jsonable_encoder(inventory)),
                expire=settings.CACHE_EXPIRE,
            )
        except Exception as e:
            logger.error(f'Cache set failed: {e}')
        return inventory

    async def use_item_from_inventory(
        self,
        use_item: UseItem,
        user: UserInfo
    ):
        """
        Использование и списание предмета из инвентаря пользователя
        Проверяет наличие инвентаря и предмета, уменьшает количество
        или удаляет предмет
        :param use_item: данные о списываемом предмете
        :param user: пользователь
        :return: SuccessResponse при успехе
        """
        await self.check_inventory_exists(user.user_id)
        await self.item_service.check_item_exists(use_item.item_id)
        user_inventory = await self.get_user_inventory(user)

        if any(
            item.item_id == use_item.item_id
            for item in user_inventory.linked_items
        ):
            await self.inventory_repository.use_item_from_inventory(
                use_item,
                user
            )
            await self.cache.delete(f'inventory_{user.user_id}')
            return SuccessResponse(
                detail=f"Item {use_item.item_id} used success"
            )

        # Если предмета нет — выбрасываем NotFoundError
        raise NotFoundError(
            f"User with ID {user.user_id} not have item {use_item.item_id}"
        )

    async def check_inventory_exists(self, user_id: int) -> bool:
        """
        Проверить, что инвентарь пользователя существует
        :param user_id: идентификатор пользователя
        :return: True, если инвентарь есть, иначе выбрасывает NotFoundError
        """
        is_inventory_exist = await self.inventory_repository.check_exists(
            user_id
        )
        if is_inventory_exist:
            return is_inventory_exist
        raise NotFoundError(f"Inventory for user with ID {user_id} not found")

    @staticmethod
    async def check_user_is_admin(user: UserInfo) -> None:
        """
        Проверка, что пользователь — администратор
        :param user: информация о пользователе
        :raises NotAdminError: если пользователь не админ
        """
        if user.role != 'admin':
            raise NotAdminError("Only admin allowed")

    async def get_all_with_item(
        self,
        item_id: int,
    ) -> list[InventoryResponse]:
        """
        Получить список всех инвентарей с предметом
        :return: список инвентарей
        """
        return await self.inventory_repository.get_inventories_with_item(
            item_id,
        )


async def get_inventory_service(
    cache: RedisCacheBackend = Depends(get_cache),
    item_service: ItemService = Depends(get_item_service),
) -> InventoryService:
    return InventoryService(cache=cache, item_service=item_service)


class KafkaConsumer:
    def __init__(self):
        self.topic_name = 'prod.auth.fact.new-user.1'
        self.bootstrap_servers = settings.KAFKA_SERVER
        self.group_id = 'inventory'

    async def consume_message(self):
        """Получение сообщения из kafka"""

        consumer = AIOKafkaConsumer(
            self.topic_name,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset='earliest'
        )
        await consumer.start()
        logger.info('Starting concuming kafka...')

        try:
            async for msg in consumer:
                await self.process_message(msg)
        except Exception as e:
            logger.error(f'Consumer error: {e}')
        finally:
            await consumer.stop()

    async def process_message(self, msg):
        try:
            message = json.loads(msg.value.decode('utf-8'))
            logger.info(f'Recieved message from kafka: {message}')
            user_id = message.get('user_id')
            role = message.get('role')
            if user_id:
                inv_service = await get_inventory_service()
                await inv_service.create_inventory(
                    UserInfo(user_id=user_id, role=role)
                )
        except json.JSONDecodeError as e:
            logger.error(f'Consumer msg decode error: {e}')
