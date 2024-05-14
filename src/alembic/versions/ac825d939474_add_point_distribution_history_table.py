"""add point_distribution_history table

Revision ID: ac825d939474
Revises: a24a82767f1e
Create Date: 2024-05-14 03:51:31.245445

"""
from typing import Sequence, Union
from uuid import UUID

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'ac825d939474'
down_revision: Union[str, None] = 'a24a82767f1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'point_distribution_history',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('partner_name', sa.String(length=255), nullable=False),
        sa.Column('point', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=text("(now() at time zone 'utc')")),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_point_distribution_history_partner_name', 'partner_name'),
        sa.Index('ix_point_distribution_history_created_at', 'created_at'),
    )


def downgrade() -> None:
    op.drop_table('point_distribution_history')
