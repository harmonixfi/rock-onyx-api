"""Add colunm risk_factor, all_time_high_per_share, total_shares, sortino_ratio, downside_risk, earned_fee, fee_structure

Revision ID: 5f35910be538
Revises: d19c99745364
Create Date: 2024-04-17 23:06:26.043910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f35910be538'
down_revision: Union[str, None] = 'd19c99745364'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vault_performance', sa.Column('risk_factor', sa.Float(), nullable=True))
    op.add_column('vault_performance', sa.Column('all_time_high_per_share', sa.Float(), nullable=True))
    op.add_column('vault_performance', sa.Column('total_shares', sa.Float(), nullable=True))
    op.add_column('vault_performance', sa.Column('sortino_ratio', sa.Float(), nullable=True))
    op.add_column('vault_performance', sa.Column('downside_risk', sa.Float(), nullable=True))
    op.add_column('vault_performance', sa.Column('earned_fee', sa.Float(), nullable=True))
    op.add_column('vault_performance', sa.Column('fee_structure', sa.String(), nullable=True))
                  


def downgrade() -> None:
    op.drop_column('vault_performance', 'risk_factor')
    op.drop_column('vault_performance', 'all_time_high_per_share')
    op.drop_column('vault_performance', 'total_shares')
    op.drop_column('vault_performance', 'sortino_ratio')
    op.drop_column('vault_performance', 'downside_risk')
    op.drop_column('vault_performance', 'earned_fee')
    op.drop_column('vault_performance', 'fee_structure')
