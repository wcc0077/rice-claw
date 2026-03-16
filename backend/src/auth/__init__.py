"""Authentication module for Shrimp Market API."""

from .jwt_config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_EXPIRE_HOURS,
)

from .agent_auth import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
    validate_api_key_format,
    extract_key_id,
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

from .dependencies import (
    get_current_agent,
    get_current_agent_optional,
    get_current_employer,
    get_current_worker,
)

__all__ = [
    # JWT Configuration
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "JWT_EXPIRE_HOURS",
    # Authentication
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "validate_api_key_format",
    "extract_key_id",
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
    # FastAPI Dependencies
    "get_current_agent",
    "get_current_agent_optional",
    "get_current_employer",
    "get_current_worker",
]