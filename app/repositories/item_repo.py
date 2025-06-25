from sqlmodel.ext.asyncio.session import AsyncSession
from app.inventory.models import Item


class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, item_data: dict) -> Item:
        item = Item(**item_data)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: int) -> Item | None:
        return await self.session.get(Item, item_id)
