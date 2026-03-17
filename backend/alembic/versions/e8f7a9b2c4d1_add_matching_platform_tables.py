"""add matching platform tables

Revision ID: e8f7a9b2c4d1
Revises: d044622a3747
Create Date: 2026-03-17 19:45:00.000000

This migration consolidates the changes from src/migrations/add_matching_platform.py
into proper Alembic format, enabling unified migration management.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f7a9b2c4d1'
down_revision: Union[str, Sequence[str], None] = 'd044622a3747'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add matching platform tables and extend jobs table."""

    # =====================================================================
    # Part 1: Extend jobs table with transaction fields
    # =====================================================================
    # Check if columns exist before adding (SQLite safe approach)
    conn = op.get_bind()

    # Get existing columns - PRAGMA returns: cid, name, type, notnull, dflt_value, pk
    existing_columns = {col[1] for col in conn.execute(sa.text("PRAGMA table_info(jobs)")).fetchall()}

    jobs_columns = [
        ('reward_amount', sa.Integer(), None),
        ('deposit_amount', sa.Integer(), None),
        ('deposit_paid', sa.Boolean(), sa.text('0')),
        ('platform_fee', sa.Integer(), None),
        ('locked_at', sa.DateTime(), None),
        ('lock_deadline', sa.DateTime(), None),
        ('winner_id', sa.String(64), None),
        ('final_payment_status', sa.String(32), sa.text("'PENDING'")),
        ('final_payment_amount', sa.Integer(), None),
    ]

    for col_name, col_type, default in jobs_columns:
        if col_name not in existing_columns:
            op.add_column('jobs', sa.Column(col_name, col_type, nullable=True, server_default=default))

    # Add foreign key for winner_id (SQLite doesn't support adding FK to existing table)
    # The constraint is enforced at application level

    # =====================================================================
    # Part 2: Create job_workers table
    # =====================================================================
    if not conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='job_workers'")).fetchone():
        op.create_table(
            'job_workers',
            sa.Column('id', sa.String(64), nullable=False),
            sa.Column('job_id', sa.String(64), nullable=False),
            sa.Column('bid_id', sa.String(64), nullable=False),
            sa.Column('worker_id', sa.String(64), nullable=False),
            sa.Column('status', sa.String(32), server_default='PENDING'),
            sa.Column('is_confirmed', sa.Boolean(), server_default=sa.text('0')),
            sa.Column('confirmed_at', sa.DateTime(), nullable=True),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('is_winner', sa.Boolean(), server_default=sa.text('0')),
            sa.Column('subsidy_amount', sa.Integer(), nullable=True),
            sa.Column('credit_penalty', sa.Integer(), server_default='0'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['bid_id'], ['bids.bid_id']),
            sa.ForeignKeyConstraint(['worker_id'], ['agents.agent_id']),
        )
        op.create_index('idx_job_workers_job', 'job_workers', ['job_id'])
        op.create_index('idx_job_workers_worker', 'job_workers', ['worker_id'])

    # =====================================================================
    # Part 3: Create artifact_versions table
    # =====================================================================
    if not conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='artifact_versions'")).fetchone():
        op.create_table(
            'artifact_versions',
            sa.Column('version_id', sa.String(64), nullable=False),
            sa.Column('artifact_id', sa.String(64), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('file_url', sa.String(512), nullable=False),
            sa.Column('preview_url', sa.String(512), nullable=True),
            sa.Column('is_watermarked', sa.Boolean(), server_default=sa.text('0')),
            sa.Column('worker_id', sa.String(64), nullable=False),
            sa.Column('is_final', sa.Boolean(), server_default=sa.text('0')),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('version_id'),
            sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.artifact_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['worker_id'], ['agents.agent_id']),
        )
        op.create_index('idx_artifact_versions_artifact', 'artifact_versions', ['artifact_id'])
        op.create_index('idx_artifact_versions_worker', 'artifact_versions', ['worker_id'])

    # =====================================================================
    # Part 4: Create payments table
    # =====================================================================
    if not conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")).fetchone():
        op.create_table(
            'payments',
            sa.Column('payment_id', sa.String(64), nullable=False),
            sa.Column('job_id', sa.String(64), nullable=False),
            sa.Column('payer_id', sa.String(64), nullable=False),
            sa.Column('payee_id', sa.String(64), nullable=False),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('type', sa.String(32), nullable=False),
            sa.Column('status', sa.String(32), server_default='PENDING'),
            sa.Column('transaction_id', sa.String(128), nullable=True),
            sa.Column('description', sa.String(256), nullable=True),
            sa.Column('job_worker_id', sa.String(64), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('settled_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('payment_id'),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['payer_id'], ['agents.agent_id']),
            sa.ForeignKeyConstraint(['payee_id'], ['agents.agent_id']),
            sa.ForeignKeyConstraint(['job_worker_id'], ['job_workers.id']),
        )
        op.create_index('idx_payments_job', 'payments', ['job_id'])
        op.create_index('idx_payments_payer', 'payments', ['payer_id'])
        op.create_index('idx_payments_payee', 'payments', ['payee_id'])

    # =====================================================================
    # Part 5: Create ws_connections table
    # =====================================================================
    if not conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='ws_connections'")).fetchone():
        op.create_table(
            'ws_connections',
            sa.Column('connection_id', sa.String(64), nullable=False),
            sa.Column('agent_id', sa.String(64), nullable=False),
            sa.Column('server_node', sa.String(64), nullable=False),
            sa.Column('connected_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('disconnected_at', sa.DateTime(), nullable=True),
            sa.Column('disconnect_reason', sa.String(32), nullable=True),
            sa.PrimaryKeyConstraint('connection_id'),
            sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
        )
        op.create_index('idx_ws_connections_agent', 'ws_connections', ['agent_id'])

    # =====================================================================
    # Part 6: Create message_delivery table
    # =====================================================================
    if not conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='message_delivery'")).fetchone():
        op.create_table(
            'message_delivery',
            sa.Column('message_id', sa.String(64), nullable=False),
            sa.Column('recipient_id', sa.String(64), nullable=False),
            sa.Column('delivered', sa.Boolean(), server_default=sa.text('0')),
            sa.Column('read', sa.Boolean(), server_default=sa.text('0')),
            sa.Column('delivered_at', sa.DateTime(), nullable=True),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('message_id', 'recipient_id'),
            sa.ForeignKeyConstraint(['recipient_id'], ['agents.agent_id']),
        )
        op.create_index('idx_message_delivery_recipient', 'message_delivery', ['recipient_id'])
        op.create_index('idx_message_delivery_delivered', 'message_delivery', ['recipient_id', 'delivered'])

    # =====================================================================
    # Part 7: Add missing columns to other tables
    # =====================================================================
    # Check for employer_rating in bids - PRAGMA returns: cid, name, type, notnull, dflt_value, pk
    bids_columns = {col[1] for col in conn.execute(sa.text("PRAGMA table_info(bids)")).fetchall()}
    if 'employer_rating' not in bids_columns:
        op.add_column('bids', sa.Column('employer_rating', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema - remove matching platform tables."""
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index('idx_message_delivery_delivered', 'message_delivery')
    op.drop_index('idx_message_delivery_recipient', 'message_delivery')
    op.drop_table('message_delivery')

    op.drop_index('idx_ws_connections_agent', 'ws_connections')
    op.drop_table('ws_connections')

    op.drop_index('idx_payments_payee', 'payments')
    op.drop_index('idx_payments_payer', 'payments')
    op.drop_index('idx_payments_job', 'payments')
    op.drop_table('payments')

    op.drop_index('idx_artifact_versions_worker', 'artifact_versions')
    op.drop_index('idx_artifact_versions_artifact', 'artifact_versions')
    op.drop_table('artifact_versions')

    op.drop_index('idx_job_workers_worker', 'job_workers')
    op.drop_index('idx_job_workers_job', 'job_workers')
    op.drop_table('job_workers')

    # Drop employer_rating from bids
    op.drop_column('bids', 'employer_rating')

    # Note: SQLite doesn't support DROP COLUMN for jobs table fields
    # To fully rollback, you would need to recreate the jobs table