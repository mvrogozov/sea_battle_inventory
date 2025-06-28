import logging
from logging.handlers import RotatingFileHandler
import os

from app.config import settings
from app.exceptions import DatabaseError, ServiceError, InventoryAlreadyExistsError, NotFoundError, NotAdminError
from app.inventory.models import Inventory
from app.inventory.schemas import ItemToInventory, UserInfo, UseItem, SuccessResponse
from app.repositories.inventory_repo import InventoryRepository
from app.services.item_service import ItemService

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

class InventoryService:
    """
    Сервис для работы с инвентарями пользователей.
    Содержит бизнес-логику для создания, получения и изменения инвентарей.
    """

    inventory_repository = InventoryRepository()
    item_service = ItemService()

    async def create_inventory(self, user: UserInfo) -> Inventory:
        """
        Создать инвентарь для пользователя
        Если инвентарь уже существует — выбрасывает InventoryAlreadyExistsError
        :param user: информация о пользователе
        :return: созданный инвентарь
        """
        if not await self.check_inventory_exists(user.user_id):
            try:
                new_inventory = await self.inventory_repository.add_for_current_user(user.user_id)
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
        raise InventoryAlreadyExistsError("Inventory for this user already exists")

    async def add_to_inventory(
        self,
        item_to_inventory: ItemToInventory,
        user: UserInfo
    ):
        """
        Добавить предмет в инвентарь пользователя (только для администратора)
        :param item_to_inventory: данные о добавляемом предмете
        :param user: информация о пользователе (должен быть админ)
        :return: обновлённый инвентарь
        """
        await self.check_user_is_admin(user)
        try:
            await self.item_service.get_item(item_to_inventory.item_id)
            if await self.check_inventory_exists(item_to_inventory.user_id):
                fields = item_to_inventory.model_dump()
                return await self.inventory_repository.add_item(**fields)
        except NotFoundError:
            raise

    async def get_user_inventory(self, user_id: int):
        """
        Получить инвентарь пользователя по user_id
        :param user_id: идентификатор пользователя
        :return: инвентарь пользователя
        """
        await self.check_inventory_exists(user_id)
        return await self.inventory_repository.get_user_inventory(user_id)

    async def use_item_from_inventory(self, use_item: UseItem):
        """
        Использование и списание предмета из инвентаря пользователя
        Проверяет наличие инвентаря и предмета, уменьшает количество или удаляет предмет
        :param use_item: данные о списываемом предмете
        :return: SuccessResponse при успехе
        """
        await self.check_inventory_exists(use_item.user_id)
        await self.item_service.check_item_exists(use_item.item_id)
        user_inventory = await self.get_user_inventory(use_item.user_id)

        # Проверяем, есть ли нужный предмет в инвентаре пользователя
        if any(item.item_id == use_item.item_id for item in user_inventory.items):
            await self.inventory_repository.use_item_from_inventory(use_item)
            return SuccessResponse(detail=f"Item {use_item.item_id} used success")

        # Если предмета нет — выбрасываем NotFoundError
        raise NotFoundError(f"User with ID {use_item.user_id} not have item {use_item.item_id}")

    async def check_inventory_exists(self, user_id: int) -> bool:
        """
        Проверить, что инвентарь пользователя существует
        :param user_id: идентификатор пользователя
        :return: True, если инвентарь есть, иначе выбрасывает NotFoundError
        """
        is_inventory_exist = await self.inventory_repository.check_exists(user_id)
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
