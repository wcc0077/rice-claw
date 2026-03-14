"""Agent authentication module for API key generation and verification.

This module provides secure API key management for agent authentication.
API keys are used to authenticate MCP tool calls from OpenClaw agents.
"""

import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple


# API key prefix for identification
API_KEY_PREFIX = "sm_live_"
API_KEY_TEST_PREFIX = "sm_test_"


def generate_api_key(test: bool = False) -> str:
    """Generate a secure API key.

    Format: sm_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (live key)
            sm_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (test key)

    Args:
        test: If True, generate a test key instead of a live key

    Returns:
        A securely generated API key
    """
    prefix = API_KEY_TEST_PREFIX if test else API_KEY_PREFIX
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage.

    Uses SHA-256 for hashing. The hash is what should be stored in the database.

    Args:
        api_key: The plain text API key

    Returns:
        The SHA-256 hash of the API key as a hex string
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify an API key against a stored hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        api_key: The plain text API key to verify
        stored_hash: The stored hash from the database

    Returns:
        True if the API key matches the hash, False otherwise
    """
    if not api_key or not stored_hash:
        return False

    computed_hash = hash_api_key(api_key)
    return secrets.compare_digest(computed_hash, stored_hash)


def validate_api_key_format(api_key: str) -> Tuple[bool, Optional[str]]:
    """Validate the format of an API key.

    Args:
        api_key: The API key to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, "error message") if invalid
    """
    if not api_key:
        return False, "API key is required"

    if not (api_key.startswith(API_KEY_PREFIX) or api_key.startswith(API_KEY_TEST_PREFIX)):
        return False, f"Invalid API key format. Must start with {API_KEY_PREFIX} or {API_KEY_TEST_PREFIX}"

    # Check minimum length (prefix + at least 32 chars)
    min_length = len(API_KEY_PREFIX) + 32
    if len(api_key) < min_length:
        return False, f"API key is too short. Minimum length is {min_length} characters"

    return True, None


class AgentAuthContext:
    """Authentication context for an authenticated agent.

    This class holds the authenticated agent's information after
    successful API key verification.
    """

    def __init__(self, agent_id: str, agent_type: str, is_verified: bool = False):
        """Initialize the authentication context.

        Args:
            agent_id: The authenticated agent's ID
            agent_type: The agent's type (employer/worker)
            is_verified: Whether the agent has been verified
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.is_verified = is_verified
        self.authenticated_at = datetime.now(timezone.utc)

    def is_employer(self) -> bool:
        """Check if the agent is an employer."""
        return self.agent_type == "employer"

    def is_worker(self) -> bool:
        """Check if the agent is a worker."""
        return self.agent_type == "worker"

    def __repr__(self) -> str:
        return f"AgentAuthContext(agent_id={self.agent_id}, type={self.agent_type})"