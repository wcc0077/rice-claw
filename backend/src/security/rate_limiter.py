"""Rate Limiter Middleware - 速率限制中间件

Redis-based rate limiting middleware for API endpoints and WebSocket connections.

Security Layer: Resource Protection
"""

import time
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis import asyncio as aioredis
from loguru import logger


class RateLimitConfig:
    """速率限制配置"""

    # 默认限制 (时间窗口秒数，最大请求数)
    DEFAULT_LIMITS = {
        "global": (1, 100),           # 全局：每秒 100 次
        "api_per_second": (1, 20),    # API：每秒 20 次
        "api_per_minute": (60, 100),  # API：每分钟 100 次
        "job_create_hour": (3600, 10),    # 任务创建：每小时 10 个
        "bid_submit_hour": (3600, 20),    # 竞标提交：每小时 20 个
        "message_send_minute": (60, 30),  # 消息发送：每分钟 30 条
        "login_attempt": (300, 5),        # 登录尝试：5 分钟 5 次
        "sms_send": (3600, 5),            # 短信发送：每小时 5 次
        "ws_connect": (3600, 10),         # WebSocket 连接：每小时 10 次
    }

    # 不同角色的限制倍数
    TIER_MULTIPLIERS = {
        "free": 1.0,
        "verified": 2.0,
        "premium": 5.0,
        "enterprise": 10.0,
    }


class RateLimiter:
    """
    Redis 驱动的速率限制器

    使用滑动窗口算法，精确控制请求频率
    """

    def __init__(self, redis: aioredis.Redis, prefix: str = "shrimp:ratelimit:"):
        self.redis = redis
        self.prefix = prefix
        self.config = RateLimitConfig()

    async def check_limit(
        self,
        key: str,
        limit_name: str = "api_per_second",
        tier: str = "free"
    ) -> Tuple[bool, int, int]:
        """
        检查是否超过限制

        Args:
            key: 限制 key (通常是 agent_id 或 IP)
            limit_name: 限制类型名称
            tier: 用户等级

        Returns:
            (是否允许，当前计数，最大限制)
        """
        if limit_name not in self.config.DEFAULT_LIMITS:
            logger.warning(f"Unknown limit name: {limit_name}")
            return True, 0, 0

        window, max_count = self.config.DEFAULT_LIMITS[limit_name]
        max_count = int(max_count * self.config.TIER_MULTIPLIERS.get(tier, 1.0))

        redis_key = f"{self.prefix}{limit_name}:{key}"
        now = time.time()

        # 使用 Redis pipeline 保证原子性
        pipe = self.redis.pipeline()

        # 移除窗口外的请求
        pipe.zremrangebyscore(redis_key, 0, now - window)

        # 添加当前请求
        pipe.zadd(redis_key, {f"{now}:{time.time_ns()}": now})

        # 设置过期时间
        pipe.expire(redis_key, window)

        # 获取当前计数
        pipe.zcard(redis_key)

        results = await pipe.execute()
        current_count = results[-1]

        return current_count <= max_count, current_count, max_count

    async def get_remaining(self, key: str, limit_name: str) -> int:
        """获取剩余可用次数"""
        allowed, current, max_count = await self.check_limit(key, limit_name)
        return max(0, max_count - current)

    async def reset_limit(self, key: str, limit_name: str):
        """重置限制（用于管理员操作）"""
        redis_key = f"{self.prefix}{limit_name}:{key}"
        await self.redis.delete(redis_key)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件

    自动对 API 请求进行速率限制
    """

    # 不需要限制的路径
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    # 路径到限制类型的映射
    PATH_LIMIT_MAP = {
        "/api/v1/jobs": "job_create_hour",
        "/api/v1/bids": "bid_submit_hour",
        "/api/v1/messages": "message_send_minute",
        "/api/v1/auth/sms/send": "sms_send",
        "/api/v1/auth/password/login": "login_attempt",
    }

    def __init__(self, app, redis: aioredis.Redis):
        super().__init__(app)
        self.limiter = RateLimiter(redis)

    async def dispatch(self, request: Request, call_next):
        # 跳过排除的路径
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # 获取客户端标识 (优先使用 agent_id，否则使用 IP)
        client_id = self._get_client_identifier(request)
        if not client_id:
            return await call_next(request)

        # 获取用户等级
        tier = self._get_client_tier(request)

        # 检查多个限制
        limits_to_check = [
            "api_per_second",
            "api_per_minute",
        ]

        # 根据路径添加特定限制
        for path_prefix, limit_name in self.PATH_LIMIT_MAP.items():
            if request.url.path.startswith(path_prefix):
                limits_to_check.append(limit_name)
                break

        # 逐个检查限制
        for limit_name in limits_to_check:
            allowed, current, max_count = await self.limiter.check_limit(
                client_id, limit_name, tier
            )

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded: {client_id} on {limit_name} "
                    f"(current: {current}, max: {max_count})"
                )

                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "请求过于频繁，请稍后再试",
                        "limit": limit_name,
                        "retry_after": self._calculate_retry_after(limit_name),
                    },
                    headers={
                        "X-RateLimit-Limit": str(max_count),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(self._calculate_retry_after(limit_name)),
                    }
                )

        response = await call_next(request)

        # 添加速率限制头信息
        remaining = await self.limiter.get_remaining(client_id, "api_per_minute")
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _get_client_identifier(self, request: Request) -> Optional[str]:
        """获取客户端标识"""
        # 尝试从认证头获取 agent_id
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 这里简化处理，实际应该解析 JWT
            token = auth_header[7:]
            return f"token:{token[:16]}"

        # 退回到 IP 地址
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            return f"ip:{ip}"

        if request.client:
            return f"ip:{request.client.host}"

        return None

    def _get_client_tier(self, request: Request) -> str:
        """获取客户端等级"""
        # 简化实现，实际应该从用户数据中获取
        return "free"

    def _calculate_retry_after(self, limit_name: str) -> int:
        """计算重试等待时间（秒）"""
        if limit_name in self.limiter.config.DEFAULT_LIMITS:
            return self.limiter.config.DEFAULT_LIMITS[limit_name][0]
        return 60


# 便捷函数
async def check_rate_limit(
    redis: aioredis.Redis,
    key: str,
    limit_name: str = "api_per_second",
    tier: str = "free"
) -> Tuple[bool, int, int]:
    """
    便捷函数：检查速率限制

    Args:
        redis: Redis 实例
        key: 限制 key
        limit_name: 限制类型
        tier: 用户等级

    Returns:
        (是否允许，当前计数，最大限制)
    """
    limiter = RateLimiter(redis)
    return await limiter.check_limit(key, limit_name, tier)


async def raise_if_rate_limited(
    redis: aioredis.Redis,
    key: str,
    limit_name: str = "api_per_second",
    tier: str = "free"
):
    """
    便捷函数：如果超过限制则抛出异常

    Raises:
        HTTPException: 当超过限制时
    """
    allowed, current, max_count = await check_rate_limit(redis, key, limit_name, tier)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求过于频繁 ({current}/{max_count})，请稍后再试",
            headers={"Retry-After": "60"}
        )
