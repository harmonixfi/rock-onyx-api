"""add strategy name to vault

Revision ID: 0b905117c7ff
Revises: b3593cef3d00
Create Date: 2024-05-21 13:54:05.876301

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '0b905117c7ff'
down_revision: Union[str, None] = 'b3593cef3d00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vaults', sa.Column('strategy_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('vaults', 'strategy_name')
    # ### end Alembic commands ###