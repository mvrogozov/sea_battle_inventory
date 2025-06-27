import jwt

from app.inventory.models import InventoryCreate, Inventory
from app.inventory.schemas import ItemToInventory
from app.repositories.inventory_repo import InventoryRepository


class InventoryService:
    """
    Сервис для работы с инвентарями пользователей.
    Содержит бизнес-логику для создания, получения и изменения инвентарей.
    """

    inventory_repository = InventoryRepository()

    async def create_inventory(self, inventory: InventoryCreate) -> Inventory:
        """
        Создать новый инвентарь для пользователя
        :param inventory: данные для создания инвентаря
        :return: созданный инвентарь
        """
        return await self.inventory_repository.add(inventory.model_dump())

    async def get_all(self) -> list[Inventory]:
        """
        Получить список всех инвентарей
        :return: список инвентарей
        """
        return await self.inventory_repository.find_all()

    async def add_to_inventory(
        self,
        item_to_inventory: ItemToInventory,
        token: str | None
    ):
        """
        Добавить предмет в инвентарь пользователя
        :param item_to_inventory: данные о добавляемом предмете и инвентаре
        :return: обновлённый инвентарь или None
        """
        # TODO: get user from token
        token = token.replace('Bearer ', '')
        decoded = jwt.decode(token, options={'verify_signature': False})
        user_id = decoded.get('user_id', 777)
        fields = item_to_inventory.model_dump()
        fields.update(user_id=user_id)
        return await self.inventory_repository.add_item(**fields)

    async def get_user_inventory(self, user_id: int):
        """
        Получить инвентарь пользователя по user_id
        :param user_id: идентификатор пользователя
        :return: инвентарь пользователя
        """
        return await self.inventory_repository.get_user_inventory(user_id)

    async def get_by_id(self, inventory_id: int):
        """
        Получить инвентарь по его ID
        :param inventory_id: идентификатор инвентаря
        :return: инвентарь или None
        """
        return await self.inventory_repository.get_inventory_by_id(
            inventory_id
        )
