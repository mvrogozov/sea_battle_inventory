from app.inventory.models import Item, Inventory
from app.base import BaseDAO


class ItemRepository(BaseDAO):
    model = Item
