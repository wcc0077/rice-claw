"""Authentication dependencies for FastAPI endpoints.

This module provides FastAPI dependencies for authenticating requests
using Bearer token (JWT or API key) authentication.
"""

from typing import Optional, Union

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db.database import get_db
from ..db.agents import get_agent_by_api_key, update_last_seen
from ..models.db_models import Agent, AdminUser
from ..auth.jwt_config import JWT_SECRET_KEY, JWT_ALGORITHM

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


async def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Get the current authenticated admin user from JWT Bearer token.

    This dependency extracts the JWT token from the Authorization header,
    validates it, and retrieves the corresponding AdminUser.

    Args:
        credentials: The HTTP Bearer credentials (auto-extracted from header)
        db: Database session

    Returns:
        The authenticated AdminUser object

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please provide a Bearer token."
        )

    token = credentials.credentials

    # Verify JWT token
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Query AdminUser by user_id
    stmt = select(AdminUser).where(AdminUser.user_id == user_id)
    result = db.execute(stmt)
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        raise HTTPException(status_code=401, detail="User not found")

    if not admin_user.status:
        raise HTTPException(status_code=403, detail="Account is disabled")

    return admin_user


async def get_current_admin_user_with_role(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Get the current authenticated admin user with admin role check.

    This is similar to get_current_admin_user but also verifies the user
    has admin or super_admin role.

    Args:
        credentials: The HTTP Bearer credentials
        db: Database session

    Returns:
        The authenticated AdminUser with admin privileges

    Raises:
        HTTPException: 401 if auth fails, 403 if not admin role
    """
    admin_user = await get_current_admin_user(credentials, db)

    if admin_user.role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=403,
            detail="This action requires admin privileges."
        )

    return admin_user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Get the current authenticated user (admin or regular user).

    This allows both admin and regular users to access endpoints.
    Use this for user-scoped operations (their own agents, jobs, etc.).

    Args:
        credentials: The HTTP Bearer credentials
        db: Database session

    Returns:
        The authenticated AdminUser (any role)

    Raises:
        HTTPException: 401 if auth fails
    """
    return await get_current_admin_user(credentials, db)


from dataclasses import dataclass


@dataclass
class AuthResult:
    """Authentication result with user type and object."""
    user_type: str  # "admin" or "agent"
    user_id: str
    user: Union[AdminUser, Agent]


async def get_current_user_or_agent(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> AuthResult:
    """Authenticate using either JWT (AdminUser) or API Key (Agent).

    This dependency tries both authentication methods:
    1. First, try JWT token for AdminUser
    2. If JWT fails, try API Key for Agent

    Args:
        credentials: The HTTP Bearer credentials (auto-extracted from header)
        db: Database session

    Returns:
        AuthResult with user_type, user_id, and user object

    Raises:
        HTTPException: 401 if both authentication methods fail
    """
    import logging
    logger = logging.getLogger(__name__)

    if not credentials:
        logger.warning("No credentials provided")
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please provide a Bearer token."
        )

    token = credentials.credentials
    logger.info(f"Authenticating with token: {token[:30]}...")

    # Try JWT first (AdminUser)
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        logger.info(f"JWT payload: sub={user_id}")
        if user_id is not None:
            stmt = select(AdminUser).where(AdminUser.user_id == user_id)
            result = db.execute(stmt)
            admin_user = result.scalar_one_or_none()
            logger.info(f"AdminUser query for {user_id}: {admin_user}")
            if admin_user and admin_user.status:
                logger.info(f"Returning admin user_type for {user_id}")
                return AuthResult(
                    user_type="admin",
                    user_id=user_id,
                    user=admin_user
                )
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
    except Exception as e:
        logger.warning(f"JWT verification error: {e}")

    # Try API Key (Agent)
    logger.info("Trying API Key authentication")
    agent = get_agent_by_api_key(db, token)
    if agent:
        update_last_seen(db, agent)
        return AuthResult(
            user_type="agent",
            user_id=agent.agent_id,
            user=agent
        )

    # Both methods failed
    raise HTTPException(
        status_code=401,
        detail="Invalid authentication. Please provide a valid JWT token or API key."
    )


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