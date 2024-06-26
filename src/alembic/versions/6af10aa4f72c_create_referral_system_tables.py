"""create referral system tables

Revision ID: 6af10aa4f72c
Revises: 7fb80eb63831
Create Date: 2024-06-12 22:25:45.499700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '6af10aa4f72c'
down_revision: Union[str, None] = '7fb80eb63831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('wallet_address', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_wallet_address'), 'users', ['wallet_address'], unique=True)
    op.create_table('referral_codes',
    sa.Column('referral_code_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('usage_limit', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('referral_code_id')
    )
    op.create_index(op.f('ix_referral_codes_code'), 'referral_codes', ['code'], unique=True)
    op.create_table('referrals',
    sa.Column('referral_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('referrer_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('referee_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('referral_code_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['referee_id'], ['users.user_id'], ),
    sa.ForeignKeyConstraint(['referral_code_id'], ['referral_codes.referral_code_id'], ),
    sa.ForeignKeyConstraint(['referrer_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('referral_id')
    )
    op.create_table('rewards',
    sa.Column('reward_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('user_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('referral_code_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('reward_percentage', sa.Float(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.ForeignKeyConstraint(['referral_code_id'], ['referral_codes.referral_code_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('reward_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('rewards')
    op.drop_table('referrals')
    op.drop_index(op.f('ix_referral_codes_code'), table_name='referral_codes')
    op.drop_table('referral_codes')
    op.drop_index(op.f('ix_users_wallet_address'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
