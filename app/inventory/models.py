from enum import Enum
from typing import List

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.orm import Mapped


class ItemKind(str, Enum):
    CONSUMABLE = 'расходник'
    CURRENCY = 'валюта'


class InventoryItem(SQLModel, table=True):
    item_id: int = Field(
        foreign_key='item.id',
        primary_key=True
    )
    inventory_id: int = Field(
        foreign_key='inventory.id',
        primary_key=True
    )
    amount: int = Field(default=0, ge=0)


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    name: str = Field(unique=True, index=True)
    description: str | None = Field(default=None)
    script: str | None = Field(default=None)
    kind: ItemKind = Field(
        default=ItemKind.CONSUMABLE,
        sa_type=PG_ENUM(ItemKind, name='item_kind')
    )
    inventories: list['Inventory'] = Relationship(
        back_populates='linked_items',
        link_model=InventoryItem,
        #sa_relationship_kwargs={'cascade': 'all, delete-orphan'}
    )


class Inventory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(unique=True, index=True)
    linked_items: list['Item'] = Relationship(
        back_populates='inventories',
        link_model=InventoryItem,
    )
# class Book(SQLModel, table=True):
#     id: int | None = Field(default=None, primary_key=True, index=True)
#     title: str
#     author: str


