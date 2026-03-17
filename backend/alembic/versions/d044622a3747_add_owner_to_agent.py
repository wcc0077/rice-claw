"""add_owner_to_agent

Revision ID: d044622a3747
Revises: 60c268102f26
Create Date: 2026-03-16 20:30:52.314585

Note: owner_id is now included in the initial migration (60c268102f26).
This migration is kept for backward compatibility with existing databases.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd044622a3747'
down_revision: Union[str, Sequence[str], None] = '60c268102f26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add owner_id to agents table if not exists."""
    # Check if column already exists (it might be in initial migration now)
    conn = op.get_bind()
    columns = {col['name'] for col in conn.execute(sa.text("PRAGMA table_info(agents)")).fetchall()}

    if 'owner_id' not in columns:
        op.add_column('agents', sa.Column('owner_id', sa.String(64), nullable=True))

    # Check if index exists
    indexes = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='agents'")).fetchall()
    index_names = {idx[0] for idx in indexes}

    if 'ix_agents_owner_id' not in index_names:
        op.create_index('ix_agents_owner_id', 'agents', ['owner_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite doesn't support DROP COLUMN in older versions
    # This is a no-op for safety
    pass