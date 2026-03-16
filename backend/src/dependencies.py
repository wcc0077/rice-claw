"""Shared Dependencies - 共享依赖

This module provides shared dependency injectors for FastAPI endpoints.
Using centralized dependencies ensures:
- Single Redis connection pool shared across all requests
- Singleton security guards (no repeated regex compilation)
- Consistent dependency injection across all endpoints
"""

from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from redis import asyncio as aioredis
from loguru import logger

from src.security import PromptGuard, OutputGuard


# =============================================================================
# Redis Dependency
# =============================================================================

_redis_instance: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """获取 Redis 连接实例 (singleton)

    Creates a single Redis connection pool shared across all requests.
    This avoids connection pool allocation overhead on every request.
    """
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = aioredis.from_url(
            "redis://localhost:6379/0",
            decode_responses=True
        )
        logger.info("Redis connection pool initialized")
    return _redis_instance


RedisSession = Annotated[aioredis.Redis, Depends(get_redis)]


# =============================================================================
# Security Guard Dependencies
# =============================================================================

# Singleton guards - created once, reused for all requests
# This avoids repeated regex compilation overhead (~40 patterns per guard)

@lru_cache(maxsize=1)
def _get_strict_prompt_guard() -> PromptGuard:
    """Get singleton PromptGuard with strict mode enabled"""
    return PromptGuard(strict_mode=True)


@lru_cache(maxsize=1)
def _get_default_prompt_guard() -> PromptGuard:
    """Get singleton PromptGuard with strict mode disabled"""
    return PromptGuard(strict_mode=False)


def get_prompt_guard_strict() -> PromptGuard:
    """获取 PromptGuard 实例 (strict mode - for user input)"""
    return _get_strict_prompt_guard()


def get_prompt_guard_default() -> PromptGuard:
    """获取 PromptGuard 实例 (default mode - for internal validation)"""
    return _get_default_prompt_guard()


PromptGuardStrict = Annotated[PromptGuard, Depends(get_prompt_guard_strict)]
PromptGuardDefault = Annotated[PromptGuard, Depends(get_prompt_guard_default)]


@lru_cache(maxsize=1)
def _get_output_guard() -> OutputGuard:
    """Get singleton OutputGuard"""
    return OutputGuard()


def get_output_guard_singleton() -> OutputGuard:
    """获取 OutputGuard 实例"""
    return _get_output_guard()


OutputGuardSession = Annotated[OutputGuard, Depends(get_output_guard_singleton)]


# =============================================================================
# Dependency Usage Examples
# =============================================================================

"""
Example endpoint using shared dependencies:

from fastapi import APIRouter, Depends
from src.dependencies import RedisSession, PromptGuardStrict

router = APIRouter()

@router.post("/jobs/publish")
async def publish_job(
    request: JobPublishRequest,
    redis: RedisSession,
    guard: PromptGuardStrict
):
    # Use redis and guard - both are singletons
    await raise_if_rate_limited(redis, request.user_id, "job_create_hour")
    result = guard.analyze(request.description)
    ...
"""
