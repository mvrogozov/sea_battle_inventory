from enum import Enum

from pydantic import BaseModel
from sqlmodel import SQLModel


class ConsumeRequest(BaseModel):
    item_id: int
    quantity: int
    battle_id: str
    user_id: int


class ItemKind(str, Enum):
    CONSUMABLE = 'расходник'
    CURRENCY = 'валюта'


class ItemCreate(SQLModel):
    name: str
    description: str | None = None
    script: str | None = None
    kind: ItemKind = ItemKind.CONSUMABLE

class ItemToInventory(BaseModel):
    user_id: int
    item_id: int
    amount: int

class InventoryItemResponse(SQLModel):
    item_id: int
    name: str
    amount: int


class InventoryResponse(SQLModel):
    user_id: int
    items: list[InventoryItemResponse] = []
