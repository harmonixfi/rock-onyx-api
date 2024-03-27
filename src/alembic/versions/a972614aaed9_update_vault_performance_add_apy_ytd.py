"""update vault performance add apy_ytd

Revision ID: a972614aaed9
Revises: d4b383b6c9eb
Create Date: 2024-03-27 09:06:47.663079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a972614aaed9'
down_revision: Union[str, None] = 'd4b383b6c9eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vault_performance', sa.Column('apy_ytd', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('vault_performance', 'apy_ytd')
