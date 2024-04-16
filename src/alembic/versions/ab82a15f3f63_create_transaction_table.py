"""create transaction  table

Revision ID: ab82a15f3f63
Revises: c60d03ad5926
Create Date: 2024-04-03 08:38:52.452173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'ab82a15f3f63'
down_revision: Union[str, None] = 'c60d03ad5926'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'transaction',
        sa.Column('txhash', sa.String(length=256), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('txhash')
    )


def downgrade() -> None:
    op.drop_table('transaction')
    # ### end Alembic commands ###
