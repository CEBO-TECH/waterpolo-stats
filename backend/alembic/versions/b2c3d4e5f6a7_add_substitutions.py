"""add_substitutions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'substitutions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('club_id', sa.String(), nullable=False),
        sa.Column('match_id', sa.String(), nullable=False),
        sa.Column('player_id', sa.String(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('quarter', sa.Integer(), server_default='1', nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ),
        sa.ForeignKeyConstraint(['match_id'], ['matches.match_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_substitutions_match', 'substitutions', ['club_id', 'match_id'])


def downgrade() -> None:
    op.drop_index('ix_substitutions_match', table_name='substitutions')
    op.drop_table('substitutions')
