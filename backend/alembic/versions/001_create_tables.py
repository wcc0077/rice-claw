"""create all tables

Revision ID: 001_create_tables
Revises:
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_create_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== admin_users =====
    op.create_table(
        'admin_users',
        sa.Column('user_id', sa.String(64), primary_key=True),
        sa.Column('username', sa.String(64), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=True),
        sa.Column('phone', sa.String(20), unique=True, nullable=True),
        sa.Column('phone_verified', sa.Boolean, default=False),
        sa.Column('role', sa.String(16), default='admin'),
        sa.Column('status', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== agents =====
    op.create_table(
        'agents',
        sa.Column('agent_id', sa.String(64), primary_key=True),
        sa.Column('agent_type', sa.String(16), nullable=False, default='all'),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('capabilities', sa.Text, default=''),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.String(16), default='idle'),
        sa.Column('rating', sa.Float, default=0.0),
        sa.Column('completed_jobs', sa.Integer, default=0),
        sa.Column('reputation_score', sa.Integer, default=1500),
        sa.Column('reputation_updated_at', sa.DateTime, nullable=True),
        sa.Column('api_key_id', sa.String(16), nullable=True, index=True),
        sa.Column('api_key_hash', sa.String(256), nullable=True),
        sa.Column('api_key_created_at', sa.DateTime, nullable=True),
        sa.Column('last_seen_at', sa.DateTime, nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('owner_id', sa.String(64), sa.ForeignKey('admin_users.user_id'), nullable=True, index=True),
        sa.Column('deleted', sa.Boolean, default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== jobs =====
    op.create_table(
        'jobs',
        sa.Column('job_id', sa.String(64), primary_key=True),
        sa.Column('employer_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('required_tags', sa.Text, default=''),
        sa.Column('budget_min', sa.Integer, nullable=True),
        sa.Column('budget_max', sa.Integer, nullable=True),
        sa.Column('currency', sa.String(8), default='CNY'),
        sa.Column('deadline', sa.DateTime, nullable=True),
        sa.Column('bid_limit', sa.Integer, default=5),
        sa.Column('priority', sa.String(16), default='normal'),
        sa.Column('status', sa.String(32), default='OPEN', nullable=False),
        sa.Column('selected_worker_ids', sa.Text, default=''),
        sa.Column('reward_amount', sa.Integer, nullable=True),
        sa.Column('deposit_amount', sa.Integer, nullable=True),
        sa.Column('deposit_paid', sa.Boolean, default=False, nullable=False),
        sa.Column('platform_fee', sa.Integer, nullable=True),
        sa.Column('locked_at', sa.DateTime, nullable=True),
        sa.Column('lock_deadline', sa.DateTime, nullable=True),
        sa.Column('winner_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=True),
        sa.Column('final_payment_status', sa.String(32), default='PENDING', nullable=False),
        sa.Column('final_payment_amount', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column('closed_at', sa.DateTime, nullable=True),
    )

    # ===== bids =====
    op.create_table(
        'bids',
        sa.Column('bid_id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('jobs.job_id'), nullable=False),
        sa.Column('worker_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('proposal', sa.Text, nullable=True),
        sa.Column('quote_amount', sa.Integer, nullable=True),
        sa.Column('quote_currency', sa.String(8), default='CNY'),
        sa.Column('delivery_days', sa.Integer, nullable=True),
        sa.Column('portfolio_links', sa.Text, default=''),
        sa.Column('is_hired', sa.Boolean, default=False),
        sa.Column('status', sa.String(16), default='BIDDING'),
        sa.Column('employer_rating', sa.Integer, nullable=True),
        sa.Column('submitted_at', sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('deleted', sa.Boolean, default=False, nullable=False),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )

    # ===== messages =====
    op.create_table(
        'messages',
        sa.Column('message_id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('jobs.job_id'), nullable=False),
        sa.Column('from_agent_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('to_agent_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('message_type', sa.String(16), default='text'),
        sa.Column('attachments', sa.Text, default=''),
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== artifacts =====
    op.create_table(
        'artifacts',
        sa.Column('artifact_id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('jobs.job_id'), nullable=False),
        sa.Column('worker_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('artifact_type', sa.String(16), nullable=False),
        sa.Column('title', sa.String(256), nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('attachments', sa.Text, default=''),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== audit_logs =====
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.String(64), primary_key=True),
        sa.Column('agent_id', sa.String(64), nullable=True, index=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(32), nullable=True),
        sa.Column('resource_id', sa.String(64), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(256), nullable=True),
        sa.Column('request_data', sa.Text, nullable=True),
        sa.Column('response_status', sa.Integer, default=200),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== reputation_logs =====
    op.create_table(
        'reputation_logs',
        sa.Column('log_id', sa.String(64), primary_key=True),
        sa.Column('agent_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False, index=True),
        sa.Column('change_type', sa.String(32), nullable=False),
        sa.Column('resource_id', sa.String(64), nullable=True),
        sa.Column('resource_type', sa.String(32), nullable=True),
        sa.Column('score_before', sa.Integer, nullable=False),
        sa.Column('score_after', sa.Integer, nullable=False),
        sa.Column('score_change', sa.Integer, nullable=False),
        sa.Column('fulfillment_change', sa.Integer, default=0),
        sa.Column('quality_change', sa.Integer, default=0),
        sa.Column('activity_change', sa.Integer, default=0),
        sa.Column('description', sa.String(256), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== sms_verification_codes =====
    op.create_table(
        'sms_verification_codes',
        sa.Column('code_id', sa.String(64), primary_key=True),
        sa.Column('phone', sa.String(20), nullable=False, index=True),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('purpose', sa.String(16), nullable=False, default='login'),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('used', sa.Boolean, default=False),
        sa.Column('attempt_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== sms_rate_limits =====
    op.create_table(
        'sms_rate_limits',
        sa.Column('phone', sa.String(20), primary_key=True),
        sa.Column('send_count', sa.Integer, default=1),
        sa.Column('window_start', sa.DateTime, server_default=sa.func.current_timestamp()),
        sa.Column('last_sent_at', sa.DateTime, server_default=sa.func.current_timestamp()),
    )

    # ===== job_workers =====
    op.create_table(
        'job_workers',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('jobs.job_id'), nullable=False, index=True),
        sa.Column('bid_id', sa.String(64), sa.ForeignKey('bids.bid_id'), nullable=False),
        sa.Column('worker_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False, index=True),
        sa.Column('status', sa.String(32), default='PENDING', nullable=False),
        sa.Column('is_confirmed', sa.Boolean, default=False, nullable=False),
        sa.Column('confirmed_at', sa.DateTime, nullable=True),
        sa.Column('delivered_at', sa.DateTime, nullable=True),
        sa.Column('is_winner', sa.Boolean, default=False, nullable=False),
        sa.Column('subsidy_amount', sa.Integer, nullable=True),
        sa.Column('credit_penalty', sa.Integer, default=0, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.current_timestamp(), nullable=False),
    )

    # ===== artifact_versions =====
    op.create_table(
        'artifact_versions',
        sa.Column('version_id', sa.String(64), primary_key=True),
        sa.Column('artifact_id', sa.String(64), sa.ForeignKey('artifacts.artifact_id'), nullable=False, index=True),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('file_url', sa.String(512), nullable=False),
        sa.Column('preview_url', sa.String(512), nullable=True),
        sa.Column('is_watermarked', sa.Boolean, default=False, nullable=False),
        sa.Column('worker_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False, index=True),
        sa.Column('is_final', sa.Boolean, default=False, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp(), nullable=False),
    )

    # ===== payments =====
    op.create_table(
        'payments',
        sa.Column('payment_id', sa.String(64), primary_key=True),
        sa.Column('job_id', sa.String(64), sa.ForeignKey('jobs.job_id'), nullable=False, index=True),
        sa.Column('payer_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False, index=True),
        sa.Column('payee_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('status', sa.String(32), default='PENDING', nullable=False),
        sa.Column('transaction_id', sa.String(128), nullable=True),
        sa.Column('description', sa.String(256), nullable=True),
        sa.Column('job_worker_id', sa.String(64), sa.ForeignKey('job_workers.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('settled_at', sa.DateTime, nullable=True),
    )

    # ===== ws_connections =====
    op.create_table(
        'ws_connections',
        sa.Column('connection_id', sa.String(64), primary_key=True),
        sa.Column('agent_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False, index=True),
        sa.Column('server_node', sa.String(64), nullable=False),
        sa.Column('connected_at', sa.DateTime, server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('disconnected_at', sa.DateTime, nullable=True),
        sa.Column('disconnect_reason', sa.String(32), nullable=True),
    )

    # ===== message_delivery =====
    op.create_table(
        'message_delivery',
        sa.Column('message_id', sa.String(64), primary_key=True),
        sa.Column('recipient_id', sa.String(64), sa.ForeignKey('agents.agent_id'), nullable=False, index=True),
        sa.Column('delivered', sa.Boolean, default=False, nullable=False),
        sa.Column('read', sa.Boolean, default=False, nullable=False),
        sa.Column('delivered_at', sa.DateTime, nullable=True),
        sa.Column('read_at', sa.DateTime, nullable=True),
    )

    # Create indexes
    op.create_index('ix_artifact_versions_artifact_id', 'artifact_versions', ['artifact_id'])
    op.create_index('ix_artifact_versions_worker_id', 'artifact_versions', ['worker_id'])
    op.create_index('ix_job_workers_job_id', 'job_workers', ['job_id'])
    op.create_index('ix_job_workers_worker_id', 'job_workers', ['worker_id'])
    op.create_index('ix_message_delivery_recipient_id', 'message_delivery', ['recipient_id'])
    op.create_index('ix_payments_job_id', 'payments', ['job_id'])
    op.create_index('ix_payments_payer_id', 'payments', ['payer_id'])
    op.create_index('ix_ws_connections_agent_id', 'ws_connections', ['agent_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('message_delivery')
    op.drop_table('ws_connections')
    op.drop_table('payments')
    op.drop_table('artifact_versions')
    op.drop_table('job_workers')
    op.drop_table('sms_rate_limits')
    op.drop_table('sms_verification_codes')
    op.drop_table('reputation_logs')
    op.drop_table('audit_logs')
    op.drop_table('artifacts')
    op.drop_table('messages')
    op.drop_table('bids')
    op.drop_table('jobs')
    op.drop_table('agents')
    op.drop_table('admin_users')