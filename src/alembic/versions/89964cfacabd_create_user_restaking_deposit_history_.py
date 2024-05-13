"""create user_restaking_deposit_history and user_restaking_deposit_history_audit

Revision ID: 89964cfacabd
Revises: e4a64c5c1243
Create Date: 2024-05-12 08:30:45.074658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '89964cfacabd'
down_revision: Union[str, None] = 'e4a64c5c1243'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # UserRestakingDepositHistory table
    op.create_table(
        'user_restaking_deposit_history',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('position_id', sa.Integer, sa.ForeignKey('user_portfolio.id')),
        sa.Column('deposit_amount', sa.Float),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # UserRestakingDepositHistoryAudit table
    op.create_table(
        'user_restaking_deposit_history_audit',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('deposit_history_id', sqlmodel.sql.sqltypes.GUID(), sa.ForeignKey('user_restaking_deposit_history.id')),
        sa.Column('field_name', sa.String(255), nullable=False),
        sa.Column('old_value', sa.String(255), nullable=False),
        sa.Column('new_value', sa.String(255), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('user_restaking_deposit_history_audit')
    op.drop_table('user_restaking_deposit_history')
