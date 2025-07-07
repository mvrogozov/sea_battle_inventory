from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.inventory.schemas import ItemKind


class InventoryItem(SQLModel, table=True):
    """Связь инвентарей и предметов"""
    item_id: int = Field(
        foreign_key='item.id',
        primary_key=True,
        ondelete='CASCADE'
    )
    inventory_id: int = Field(
        foreign_key='inventory.id',
        primary_key=True,
        ondelete='CASCADE'
    )
    amount: int = Field(default=0, ge=0)
    inventory: Optional["Inventory"] = Relationship(
        back_populates="inventory_items",
    )
    item: Optional["Item"] = Relationship(
        back_populates="inventory_items",
        sa_relationship_kwargs={'cascade': 'all, delete'}
    )


class Item(SQLModel, table=True):
    """Модель предмета"""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(unique=True, index=True)
    description: str | None = Field(default=None)
    shop_item_id: int | None = Field(default=None)
    script: Optional[str] = Field(
        default=None,
        description="Мета-язык/скрипт для ядра"
    )
    use_limit: int = Field(default=1)
    cooldown: int = Field(default=0)
    kind: ItemKind = Field(default=ItemKind.CONSUMABLE)
    inventory_items: list["InventoryItem"] = Relationship(
        back_populates="item",
        sa_relationship_kwargs={'cascade': 'all, delete'}
    )

    class Config:
        use_enum_values = True


class Inventory(SQLModel, table=True):
    """Модель инвентаря пользователя"""
    id: int | None = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(unique=True, index=True)
    inventory_items: list["InventoryItem"] = Relationship(
        back_populates="inventory"
    )
