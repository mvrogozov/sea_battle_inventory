from enum import Enum

from pydantic import BaseModel, Field
from sqlmodel import SQLModel


class SuccessResponse(BaseModel):
    success: bool = True
    detail: str


class ItemKind(str, Enum):
    CONSUMABLE = 'расходник'
    CURRENCY = 'валюта'


class BaseItem(BaseModel):
    name: str
    kind: ItemKind
    description: str
    script: str = None


class ItemResponse(BaseItem):
    id: int


class ItemCreate(SQLModel):
    name: str
    description: str | None = None
    script: str | None = None
    kind: ItemKind = ItemKind.CONSUMABLE


class ItemToInventory(BaseModel):
    """Модель добавления предмета в инвентарь игрока"""
    user_id: int = Field(
        description="ID игрока, в чей инвентарь добавляется предмет"
    )
    item_id: int = Field(description="ID предмета для добавления в инвентарь")
    amount: int = Field(gt=0, description="Количество добавляемых предметов")


class InventoryItemResponse(SQLModel):
    item_id: int
    name: str
    amount: int


class InventoryResponse(SQLModel):
    user_id: int
    items: list[InventoryItemResponse] = []


class UserInfo(SQLModel):
    user_id: int
    role: str


class UseItem(BaseModel):
    """Модель использования предмета (списания предмета из инвентаря)"""
    item_id: int = Field(gt=0, description="ID использованного предмета")
    user_id: int = Field(
        gt=0, description="ID пользователя, использовавшего предмет"
    )
    amount: int = Field(
        gt=0, default=1, description="Количество элементов на использование"
    )
