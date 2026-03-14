"""Authentication module for Shrimp Market API."""

from .agent_auth import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    validate_api_key_format,
    AgentAuthContext,
)

from .permissions import (
    PermissionDeniedError,
    can_view_job,
    can_publish_job,
    can_modify_job,
    can_close_job,
    can_submit_bid,
    can_view_bid,
    can_modify_bid,
    can_accept_bid,
    can_reject_bid,
    can_send_message,
    can_view_messages,
    can_submit_artifact,
    can_view_artifact,
    get_accessible_job_ids,
)

__all__ = [
    # Authentication
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "validate_api_key_format",
    "AgentAuthContext",
    # Authorization
    "PermissionDeniedError",
    "can_view_job",
    "can_publish_job",
    "can_modify_job",
    "can_close_job",
    "can_submit_bid",
    "can_view_bid",
    "can_modify_bid",
    "can_accept_bid",
    "can_reject_bid",
    "can_send_message",
    "can_view_messages",
    "can_submit_artifact",
    "can_view_artifact",
    "get_accessible_job_ids",
]