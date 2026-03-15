"""FastMCP Authentication Provider for Shrimp Market.

This module provides a custom AuthProvider that validates API keys
from the Authorization header (Bearer token).
"""

from typing import Optional
from fastmcp.server.auth import AuthProvider, AccessToken
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..db.agents import get_agent_by_api_key
from ..auth.agent_auth import validate_api_key_format


class ShrimpMarketAuthProvider(AuthProvider):
    """Custom AuthProvider that validates Shrimp Market API keys.

    API keys are passed via the Authorization header as Bearer tokens.
    Format: Authorization: Bearer sm_live_xxxxxxxx_xxxxx
    """

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """Verify an API key and return access token info.

        Args:
            token: The API key from the Authorization header

        Returns:
            AccessToken if valid, None otherwise
        """
        if not token:
            return None

        # Validate format
        is_valid, error_msg = validate_api_key_format(token)
        if not is_valid:
            return None

        # Look up agent by API key
        db: Session = SessionLocal()
        try:
            agent = get_agent_by_api_key(db, token)
            if not agent:
                return None

            # Update last seen
            from ..db.agents import update_last_seen
            update_last_seen(db, agent)

            # Return access token with agent info in claims
            return AccessToken(
                token=token,
                client_id=agent.agent_id,
                scopes=[agent.agent_type],  # employer or worker
                claims={
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "is_verified": agent.is_verified or False,
                    "name": agent.name,
                }
            )
        finally:
            db.close()