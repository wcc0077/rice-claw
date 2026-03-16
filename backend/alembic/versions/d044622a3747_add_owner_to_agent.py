"""add_owner_to_agent

Revision ID: d044622a3747
Revises: 60c268102f26
Create Date: 2026-03-16 20:30:52.314585

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
    """Upgrade schema."""
    # Add owner_id column to agents table
    op.add_column('agents', sa.Column('owner_id', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_agents_owner_id'), 'agents', ['owner_id'], unique=False)
    # Note: SQLite doesn't support adding FK constraints to existing tables
    # The FK constraint will be enforced at the application level


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_agents_owner_id'), table_name='agents')
    op.drop_column('agents', 'owner_id')