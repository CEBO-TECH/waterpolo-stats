"""add_voice_notes

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'voice_notes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('club_id', sa.String(), nullable=False),
        sa.Column('match_id', sa.String(), nullable=False),
        sa.Column('player_id', sa.String(), nullable=True),
        sa.Column('audio_key', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), server_default='audio/webm', nullable=False),
        sa.Column('duration_s', sa.Integer(), server_default='0', nullable=False),
        sa.Column('note', sa.String(), server_default='', nullable=False),
        sa.Column('created_by', sa.String(), server_default='', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ),
        sa.ForeignKeyConstraint(['match_id'], ['matches.match_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_voice_notes_match', 'voice_notes', ['club_id', 'match_id'])


def downgrade() -> None:
    op.drop_index('ix_voice_notes_match', table_name='voice_notes')
    op.drop_table('voice_notes')
