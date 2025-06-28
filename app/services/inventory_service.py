import jwt

from fastapi import HTTPException, status
from app.inventory.models import InventoryCreate, Inventory
from app.inventory.schemas import (
    ItemToInventory, UserInfo, ItemToInventoryByUserId
)
from app.repositories.inventory_repo import InventoryRepository


class InventoryService:
    """
    Сервис для работы с инвентарями пользователей.
    Содержит бизнес-логику для создания, получения и изменения инвентарей.
    """

    inventory_repository = InventoryRepository()

    async def create_inventory(
        self,
        user: UserInfo
    ) -> Inventory:
        """
        Создать новый инвентарь для пользователя
        :param inventory: данные для создания инвентаря
        :return: созданный инвентарь
        """
        return await self.inventory_repository.add_for_current_user(
            user.model_dump()
        )

    async def get_all(self) -> list[Inventory]:
        """
        Получить список всех инвентарей
        :return: список инвентарей
        """
        return await self.inventory_repository.find_all()

    async def add_to_inventory(
        self,
        item_to_inventory: ItemToInventory,
        user: UserInfo
    ):
        """
        Добавить предмет в инвентарь пользователя
        :param item_to_inventory: данные о добавляемом предмете и инвентаре
        :return: обновлённый инвентарь или None
        """
        fields = item_to_inventory.model_dump()
        fields.update(user_id=user.user_id)
        return await self.inventory_repository.add_item(**fields)

    async def add_to_inventory_by_user_id(
        self,
        item_to_inventory: ItemToInventoryByUserId,
        user: UserInfo,
    ):
        """
        Добавить предмет в инвентарь пользователя по его user_id
        :param item_to_inventory: данные о добавляемом предмете и инвентаре
        :return: обновлённый инвентарь или None
        """
        if user.role != 'admin':
            raise HTTPException(
                detail='Недостаточно прав',
                status_code=status.HTTP_403_FORBIDDEN
            )
        fields = item_to_inventory.model_dump()
        return await self.inventory_repository.add_item(**fields)

    async def get_current_user_inventory(self, user: UserInfo):
        """
        Получить инвентарь текущего пользователя
        :return: инвентарь пользователя
        """
        return await self.inventory_repository.get_user_inventory(user.user_id)

    async def get_user_inventory_by_id(self, user: UserInfo, user_id: int):
        """
        Получить инвентарь пользователя по id
        :return: инвентарь пользователя
        """
        if user.role != 'admin':
            raise HTTPException(
                detail='Недостаточно прав',
                status_code=status.HTTP_403_FORBIDDEN
            )
        return await self.inventory_repository.get_user_inventory(user_id)

    async def get_by_id(self, inventory_id: int, user: UserInfo):
        """
        Получить инвентарь по его ID
        :param inventory_id: идентификатор инвентаря
        :return: инвентарь или None
        """
        if user.role != 'admin':
            raise HTTPException(
                detail='Недостаточно прав',
                status_code=status.HTTP_403_FORBIDDEN
            )
        return await self.inventory_repository.get_inventory_by_id(
            inventory_id
        )
