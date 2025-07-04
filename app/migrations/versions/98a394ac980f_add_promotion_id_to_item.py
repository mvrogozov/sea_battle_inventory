"""add promotion id to item

Revision ID: 98a394ac980f
Revises: a0f50194f57e
Create Date: 2025-07-04 13:18:20.017739

"""
from typing import Sequence, Union
import sqlmodel 
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98a394ac980f'
down_revision: Union[str, Sequence[str], None] = 'a0f50194f57e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('item', sa.Column('promotion_id', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('item', 'promotion_id')
    # ### end Alembic commands ###
