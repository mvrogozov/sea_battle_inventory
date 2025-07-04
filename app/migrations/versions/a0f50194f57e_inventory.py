"""inventory

Revision ID: a0f50194f57e
Revises: 
Create Date: 2025-06-29 15:38:12.336434

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a0f50194f57e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('inventory',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_id'), 'inventory', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_user_id'), 'inventory', ['user_id'], unique=True)
    op.create_table('item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('script', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('kind', sa.Enum('CONSUMABLE', 'CURRENCY', name='itemkind'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_item_id'), 'item', ['id'], unique=False)
    op.create_index(op.f('ix_item_name'), 'item', ['name'], unique=True)
    op.create_table('inventoryitem',
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('inventory_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('item_id', 'inventory_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('inventoryitem')
    op.drop_index(op.f('ix_item_name'), table_name='item')
    op.drop_index(op.f('ix_item_id'), table_name='item')
    op.drop_table('item')
    op.drop_index(op.f('ix_inventory_user_id'), table_name='inventory')
    op.drop_index(op.f('ix_inventory_id'), table_name='inventory')
    op.drop_table('inventory')
    # ### end Alembic commands ###
