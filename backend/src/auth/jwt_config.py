"""Shared JWT configuration."""

import secrets

# JWT settings - in production, load from environment
JWT_SECRET_KEY = secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24