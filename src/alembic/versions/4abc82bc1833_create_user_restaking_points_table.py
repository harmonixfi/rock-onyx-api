"""create user restaking points table

Revision ID: 4abc82bc1833
Revises: a24a82767f1e
Create Date: 2024-05-11 07:50:38.163092

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4abc82bc1833"
down_revision: Union[str, None] = "a24a82767f1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "user_restaking_points",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("position_id", sa.Integer(), nullable=False),
        sa.Column("vault_id", sa.UUID(), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("points", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("session_name", sa.String(length=255), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["position_id"], ["user_portfolio.id"]),
        sa.ForeignKeyConstraint(["vault_id"], ["vaults.id"]),
    )


def downgrade():
    op.drop_table("user_restaking_points")
