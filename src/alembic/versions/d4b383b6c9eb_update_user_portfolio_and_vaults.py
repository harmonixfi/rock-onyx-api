"""update user_portfolio and vaults

Revision ID: d4b383b6c9eb
Revises: 4d9e109ab04b
Create Date: 2024-03-27 08:44:30.677287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4b383b6c9eb'
down_revision: Union[str, None] = '4d9e109ab04b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_portfolio', sa.Column('exit_price', sa.Float(), nullable=True))
    op.add_column('user_portfolio', sa.Column('trade_end_date', sa.DateTime(), nullable=True))
    op.add_column('vaults', sa.Column('slug', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('user_portfolio', 'exit_price')
    op.drop_column('user_portfolio', 'trade_end_date')
    op.drop_column('vaults', 'slug')
