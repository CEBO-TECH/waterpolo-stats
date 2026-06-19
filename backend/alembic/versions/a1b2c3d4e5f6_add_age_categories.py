"""add_age_categories

Revision ID: a1b2c3d4e5f6
Revises: f6171ece1321
Create Date: 2026-06-18 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f6171ece1321'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_AGE_CATEGORIES = ["Seniorzy", "U19", "U17", "U15"]


def upgrade() -> None:
    op.create_table(
        'age_categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('club_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('club_id', 'name'),
    )

    # Backfill default categories for clubs that already exist.
    conn = op.get_bind()
    clubs = conn.execute(sa.text("SELECT id FROM clubs")).fetchall()
    for (club_id,) in clubs:
        for i, name in enumerate(DEFAULT_AGE_CATEGORIES):
            conn.execute(
                sa.text(
                    "INSERT INTO age_categories (id, club_id, name, sort_order) "
                    "VALUES (:id, :club_id, :name, :so)"
                ),
                {"id": str(uuid.uuid4()), "club_id": club_id, "name": name, "so": i},
            )


def downgrade() -> None:
    op.drop_table('age_categories')
