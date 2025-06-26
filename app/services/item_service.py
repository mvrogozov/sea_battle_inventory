from app.inventory.models import Item
from app.inventory.scemas import ItemCreate
from app.repositories.item_repo import ItemRepository


class ItemService:
    """
    Сервис для работы с предметами (Item)
    Содержит бизнес-логику для создания, получения и поиска предметов
    """
    item_repository = ItemRepository()

    async def add_item(self, item: ItemCreate) -> Item:
        """
        Создать новый предмет
        :param item: данные нового предмета (ItemCreate)
        :return: созданный предмет (Item)
        """
        return await self.item_repository.add(item.model_dump())

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
        return await self.item_repository.find_one_or_none_by_id(item_id)