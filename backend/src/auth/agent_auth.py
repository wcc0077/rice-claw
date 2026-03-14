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
# Key ID length (used for O(1) lookup)
KEY_ID_LENGTH = 8
# Characters for key_id (no underscores to avoid parsing issues)
KEY_ID_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"


def generate_api_key(test: bool = False) -> Tuple[str, str]:
    """Generate a secure API key with an embedded key ID.

    Format: sm_live_{key_id}_{random} (live key)
            sm_test_{key_id}_{random} (test key)

    The key_id is a short identifier used for O(1) database lookup.
    The random part is the secret that gets hashed.

    Args:
        test: If True, generate a test key instead of a live key

    Returns:
        Tuple of (api_key, key_id) where:
        - api_key: The full API key (store securely, show once)
        - key_id: The short identifier for database indexing
    """
    prefix = API_KEY_TEST_PREFIX if test else API_KEY_PREFIX
    # Use URL-safe chars without underscore for key_id (avoids parsing issues)
    key_id = ''.join(secrets.choice(KEY_ID_CHARS) for _ in range(KEY_ID_LENGTH))
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{key_id}_{random_part}", key_id


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

    # Check minimum length (prefix + key_id + underscore + at least 32 chars)
    min_length = len(API_KEY_PREFIX) + KEY_ID_LENGTH + 1 + 32
    if len(api_key) < min_length:
        return False, f"API key is too short. Minimum length is {min_length} characters"

    return True, None


def extract_key_id(api_key: str) -> Optional[str]:
    """Extract the key ID from an API key.

    The key ID is embedded in the API key for O(1) database lookup.

    Args:
        api_key: The full API key

    Returns:
        The key ID if valid, None otherwise
    """
    if not api_key:
        return None

    # Determine prefix length
    if api_key.startswith(API_KEY_PREFIX):
        prefix_len = len(API_KEY_PREFIX)
    elif api_key.startswith(API_KEY_TEST_PREFIX):
        prefix_len = len(API_KEY_TEST_PREFIX)
    else:
        return None

    # Extract key_id (format: prefix{key_id}_{random})
    try:
        after_prefix = api_key[prefix_len:]
        key_id = after_prefix.split("_")[0]
        if len(key_id) == KEY_ID_LENGTH:
            return key_id
    except (IndexError, ValueError):
        pass

    return None


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