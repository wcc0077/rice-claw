"""Initial tables

Revision ID: 60c268102f26
Revises:
Create Date: 2026-03-13 22:12:22.120356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60c268102f26'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create all initial tables."""
    # Create admin_users table
    op.create_table(
        'admin_users',
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('username', sa.String(64), nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('phone_verified', sa.Boolean(), server_default='0'),
        sa.Column('role', sa.String(16), server_default='admin'),
        sa.Column('status', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('phone'),
    )

    # Create agents table
    op.create_table(
        'agents',
        sa.Column('agent_id', sa.String(64), nullable=False),
        sa.Column('agent_type', sa.String(16), server_default='all'),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('capabilities', sa.Text(), server_default=''),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(16), server_default='idle'),
        sa.Column('rating', sa.Float(), server_default='0.0'),
        sa.Column('completed_jobs', sa.Integer(), server_default='0'),
        sa.Column('reputation_score', sa.Integer(), server_default='1500'),
        sa.Column('reputation_updated_at', sa.DateTime(), nullable=True),
        sa.Column('api_key_id', sa.String(16), nullable=True),
        sa.Column('api_key_hash', sa.String(256), nullable=True),
        sa.Column('api_key_created_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default='0'),
        sa.Column('owner_id', sa.String(64), nullable=True),
        sa.Column('deleted', sa.Boolean(), server_default='0'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('agent_id'),
        sa.ForeignKeyConstraint(['owner_id'], ['admin_users.user_id']),
    )
    op.create_index('ix_agents_owner_id', 'agents', ['owner_id'])
    op.create_index('ix_agents_api_key_id', 'agents', ['api_key_id'])

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('job_id', sa.String(64), nullable=False),
        sa.Column('employer_id', sa.String(64), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('required_tags', sa.Text(), server_default=''),
        sa.Column('budget_min', sa.Integer(), nullable=True),
        sa.Column('budget_max', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(8), server_default='CNY'),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('bid_limit', sa.Integer(), server_default='5'),
        sa.Column('priority', sa.String(16), server_default='normal'),
        sa.Column('status', sa.String(32), server_default='OPEN'),
        sa.Column('selected_worker_ids', sa.Text(), server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('job_id'),
        sa.ForeignKeyConstraint(['employer_id'], ['agents.agent_id']),
    )

    # Create bids table
    op.create_table(
        'bids',
        sa.Column('bid_id', sa.String(64), nullable=False),
        sa.Column('job_id', sa.String(64), nullable=False),
        sa.Column('worker_id', sa.String(64), nullable=False),
        sa.Column('proposal', sa.Text(), nullable=True),
        sa.Column('quote_amount', sa.Integer(), nullable=True),
        sa.Column('quote_currency', sa.String(8), server_default='CNY'),
        sa.Column('delivery_days', sa.Integer(), nullable=True),
        sa.Column('portfolio_links', sa.Text(), server_default=''),
        sa.Column('is_hired', sa.Boolean(), server_default='0'),
        sa.Column('status', sa.String(16), server_default='BIDDING'),
        sa.Column('employer_rating', sa.Integer(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('bid_id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id']),
        sa.ForeignKeyConstraint(['worker_id'], ['agents.agent_id']),
    )

    # Create artifacts table
    op.create_table(
        'artifacts',
        sa.Column('artifact_id', sa.String(64), nullable=False),
        sa.Column('job_id', sa.String(64), nullable=False),
        sa.Column('worker_id', sa.String(64), nullable=False),
        sa.Column('artifact_type', sa.String(16), nullable=False),
        sa.Column('title', sa.String(256), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('attachments', sa.Text(), server_default=''),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('artifact_id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id']),
        sa.ForeignKeyConstraint(['worker_id'], ['agents.agent_id']),
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('message_id', sa.String(64), nullable=False),
        sa.Column('job_id', sa.String(64), nullable=False),
        sa.Column('from_agent_id', sa.String(64), nullable=False),
        sa.Column('to_agent_id', sa.String(64), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(16), server_default='text'),
        sa.Column('attachments', sa.Text(), server_default=''),
        sa.Column('is_read', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('message_id'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.job_id']),
        sa.ForeignKeyConstraint(['from_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['to_agent_id'], ['agents.agent_id']),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.String(64), nullable=False),
        sa.Column('agent_id', sa.String(64), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(32), nullable=True),
        sa.Column('resource_id', sa.String(64), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(256), nullable=True),
        sa.Column('request_data', sa.Text(), nullable=True),
        sa.Column('response_status', sa.Integer(), server_default='200'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('log_id'),
    )
    op.create_index('ix_audit_logs_agent_id', 'audit_logs', ['agent_id'])

    # Create reputation_logs table
    op.create_table(
        'reputation_logs',
        sa.Column('log_id', sa.String(64), nullable=False),
        sa.Column('agent_id', sa.String(64), nullable=False),
        sa.Column('change_type', sa.String(32), nullable=False),
        sa.Column('resource_id', sa.String(64), nullable=True),
        sa.Column('resource_type', sa.String(32), nullable=True),
        sa.Column('score_before', sa.Integer(), nullable=False),
        sa.Column('score_after', sa.Integer(), nullable=False),
        sa.Column('score_change', sa.Integer(), nullable=False),
        sa.Column('fulfillment_change', sa.Integer(), server_default='0'),
        sa.Column('quality_change', sa.Integer(), server_default='0'),
        sa.Column('activity_change', sa.Integer(), server_default='0'),
        sa.Column('description', sa.String(256), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('log_id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
    )
    op.create_index('ix_reputation_logs_agent_id', 'reputation_logs', ['agent_id'])

    # Create sms_verification_codes table
    op.create_table(
        'sms_verification_codes',
        sa.Column('code_id', sa.String(64), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('purpose', sa.String(16), server_default='login'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), server_default='0'),
        sa.Column('attempt_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('code_id'),
    )
    op.create_index('ix_sms_verification_codes_phone', 'sms_verification_codes', ['phone'])

    # Create sms_rate_limits table
    op.create_table(
        'sms_rate_limits',
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('send_count', sa.Integer(), server_default='1'),
        sa.Column('window_start', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_sent_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('phone'),
    )


def downgrade() -> None:
    """Downgrade schema - Drop all tables."""
    op.drop_table('sms_rate_limits')
    op.drop_table('sms_verification_codes')
    op.drop_table('reputation_logs')
    op.drop_table('audit_logs')
    op.drop_table('messages')
    op.drop_table('artifacts')
    op.drop_table('bids')
    op.drop_table('jobs')
    op.drop_table('agents')
    op.drop_table('admin_users')