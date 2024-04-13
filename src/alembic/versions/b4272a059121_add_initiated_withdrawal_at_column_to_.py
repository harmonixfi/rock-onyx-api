"""add initiated_withdrawal_at column to user_portfolio

Revision ID: b4272a059121
Revises: c60d03ad5926
Create Date: 2024-04-13 07:48:22.850851

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4272a059121"
down_revision: Union[str, None] = "c60d03ad5926"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_portfolio",
        sa.Column("initiated_withdrawal_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_portfolio", "initiated_withdrawal_at")
