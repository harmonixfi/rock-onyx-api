"""add columns to vaults table

Revision ID: e4a64c5c1243
Revises: 4abc82bc1833
Create Date: 2024-05-11 08:32:03.108262

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e4a64c5c1243"
down_revision: Union[str, None] = "4abc82bc1833"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VaultCategory = sa.Enum("real_yield", "points", name="VaultCategory", create_type=False)
NetworkChain = sa.Enum(
    "ethereum",
    "bsc",
    "arbitrum_one",
    "base",
    "blast",
    name="NetworkChain",
    create_type=False,
)


def upgrade() -> None:
    # Create the Enum types in the database
    VaultCategory.create(op.get_bind(), checkfirst=False)
    NetworkChain.create(op.get_bind(), checkfirst=False)

    op.add_column("vaults", sa.Column("routes", sa.String(length=100), nullable=True))
    op.add_column(
        "vaults",
        sa.Column(
            "category",
            VaultCategory,
            nullable=True,
        ),
    )
    op.add_column(
        "vaults",
        sa.Column(
            "network_chain",
            NetworkChain,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("vaults", "routes")
    op.drop_column("vaults", "category")
    op.drop_column("vaults", "network_chain")

    # Drop the Enum types from the database
    VaultCategory.drop(op.get_bind(), checkfirst=False)
    NetworkChain.drop(op.get_bind(), checkfirst=False)
