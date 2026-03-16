"""Authentication dependencies for FastAPI endpoints.

This module provides FastAPI dependencies for authenticating requests
using Bearer token (API key) authentication.
"""

from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.agents import get_agent_by_api_key, update_last_seen
from ..models.db_models import Agent

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_agent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Agent:
    """Get the current authenticated agent from Bearer token.

    This dependency extracts the API key from the Authorization header
    and validates it against the database.

    Args:
        credentials: The HTTP Bearer credentials (auto-extracted from header)
        db: Database session

    Returns:
        The authenticated Agent object

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please provide a Bearer token."
        )

    token = credentials.credentials
    agent = get_agent_by_api_key(db, token)

    if not agent:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Authentication failed."
        )

    # Update last_seen_at timestamp
    update_last_seen(db, agent)

    return agent


async def get_current_agent_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Agent]:
    """Get the current agent if authenticated, or None.

    This is an optional version that doesn't raise an error if
    no authentication is provided.

    Args:
        credentials: The HTTP Bearer credentials (optional)
        db: Database session

    Returns:
        The authenticated Agent object, or None if not authenticated
    """
    if not credentials:
        return None

    token = credentials.credentials
    agent = get_agent_by_api_key(db, token)

    if agent:
        update_last_seen(db, agent)

    return agent


async def get_current_employer(
    agent: Agent = Depends(get_current_agent)
) -> Agent:
    """Ensure the current agent is an employer.

    Args:
        agent: The authenticated agent

    Returns:
        The authenticated Agent object (must be employer or 'all' type)

    Raises:
        HTTPException: 403 if not an employer
    """
    if agent.agent_type not in ("employer", "all"):
        raise HTTPException(
            status_code=403,
            detail="This action requires employer privileges."
        )
    return agent


async def get_current_worker(
    agent: Agent = Depends(get_current_agent)
) -> Agent:
    """Ensure the current agent is a worker.

    Args:
        agent: The authenticated agent

    Returns:
        The authenticated Agent object (must be worker or 'all' type)

    Raises:
        HTTPException: 403 if not a worker
    """
    if agent.agent_type not in ("worker", "all"):
        raise HTTPException(
            status_code=403,
            detail="This action requires worker privileges."
        )
    return agent