"""Update reward_session table

Revision ID: 33e9f6b924d5
Revises: 3e5552b0f75e
Create Date: 2024-06-17 10:25:20.672920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '33e9f6b924d5'
down_revision: Union[str, None] = '3e5552b0f75e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_points', sa.Column('session_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
    op.create_foreign_key(None, 'user_points', 'reward_sessions', ['session_id'], ['session_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user_points', type_='foreignkey')
    op.drop_column('user_points', 'session_id')
    # ### end Alembic commands ###
