"""add_player_account_fields

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('players', sa.Column('birth_year', sa.Integer(), nullable=True))
    op.add_column('players', sa.Column('email', sa.String(), nullable=True))
    op.add_column('players', sa.Column('user_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('players', 'user_id')
    op.drop_column('players', 'email')
    op.drop_column('players', 'birth_year')
