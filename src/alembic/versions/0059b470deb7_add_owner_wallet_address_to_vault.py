"""add owner wallet address to vault

Revision ID: 0059b470deb7
Revises: ab75c2ab7dec
Create Date: 2024-05-31 14:29:32.840046

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "0059b470deb7"
down_revision: Union[str, None] = "ab75c2ab7dec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "vaults",
        sa.Column(
            "owner_wallet_address", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("vaults", "owner_wallet_address")
    # ### end Alembic commands ###