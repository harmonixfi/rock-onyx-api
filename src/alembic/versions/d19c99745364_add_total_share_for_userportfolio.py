"""add total_share for UserPortfolio

Revision ID: d19c99745364
Revises: ab82a15f3f63
Create Date: 2024-04-09 22:33:17.442867

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd19c99745364'
down_revision: Union[str, None] = 'ab82a15f3f63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_portfolio", sa.Column("total_shares", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("user_portfolio", "total_shares")
