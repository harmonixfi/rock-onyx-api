"""Added session and points multiplier table

Revision ID: 3e5552b0f75e
Revises: 6af10aa4f72c
Create Date: 2024-06-16 11:06:56.190670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3e5552b0f75e'
down_revision: Union[str, None] = '6af10aa4f72c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reward_sessions',
    sa.Column('session_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('session_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('partner_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index(op.f('ix_reward_sessions_session_name'), 'reward_sessions', ['session_name'], unique=False)
    op.create_table('points_multiplier_config',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('vault_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('multiplier', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['vault_id'], ['vaults.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('points_multiplier_config')
    op.drop_index(op.f('ix_reward_sessions_session_name'), table_name='reward_sessions')
    op.drop_table('reward_sessions')
    # ### end Alembic commands ###
