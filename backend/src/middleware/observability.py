"""观测性中间件

整合：
1. 请求链路追踪（Request ID 生成和传递）
2. API 性能指标收集
3. 慢查询日志
4. 结构化日志记录
"""

import uuid
import time
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.logger import get_logger, ContextLogger, log_slow_query
from ..utils.metrics import get_metrics

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """观测性中间件

    功能：
    1. 为每个请求生成唯一的 Request ID
    2. 记录请求开始和结束时间
    3. 收集 API 延迟指标
    4. 记录慢请求（>1000ms）
    """

    # 慢请求阈值（毫秒）
    SLOW_REQUEST_THRESHOLD = 1000.0

    # 排除的路径
    EXCLUDED_PATHS = {
        "/health",
        "/",
        "/favicon.ico",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并收集指标"""

        # 跳过排除的路径
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # 生成 Request ID
        request_id = str(uuid.uuid4())

        # 绑定到上下文（用于日志追踪）
        ContextLogger.bind(request_id=request_id, path=request.url.path, method=request.method)

        # 存储到 request state（供 handlers 使用）
        request.state.request_id = request_id

        # 记录开始时间
        start_time = time.perf_counter()

        response_status = 500
        try:
            response = await call_next(request)
            response_status = response.status_code
            return response
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
        finally:
            # 计算耗时
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 记录指标
            metrics = get_metrics()
            metrics.record_latency(
                path=request.url.path,
                method=request.method,
                latency_ms=duration_ms,
                status_code=response_status,
            )

            # 记录日志
            log_level = "WARNING" if duration_ms > self.SLOW_REQUEST_THRESHOLD else "INFO"
            logger.log(
                log_level,
                f"{request.method} {request.url.path} - {response_status} ({duration_ms:.2f}ms)",
                duration_ms=duration_ms,
                status_code=response_status,
            )

            # 慢请求告警
            if duration_ms > self.SLOW_REQUEST_THRESHOLD:
                log_slow_query(
                    query_desc=f"{request.method} {request.url.path}",
                    duration_ms=duration_ms,
                    threshold_ms=self.SLOW_REQUEST_THRESHOLD,
                )

            # 清理上下文
            ContextLogger.clear()


class BusinessMetricsMiddleware(BaseHTTPMiddleware):
    """业务指标更新中间件

    定期更新业务指标缓存（活跃 Agent 数、Job 状态分布等）
    """

    # 指标更新间隔（秒）
    UPDATE_INTERVAL = 60

    def __init__(self, app):
        super().__init__(app)
        self._last_update = 0.0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并可能更新业务指标"""

        current_time = time.time()

        # 定期更新业务指标
        if current_time - self._last_update > self.UPDATE_INTERVAL:
            self._last_update = current_time
            # 触发指标更新（在后台进行，不阻塞请求）
            import asyncio
            asyncio.create_task(self._update_business_metrics())

        return await call_next(request)

    async def _update_business_metrics(self):
        """更新业务指标"""
        try:
            from ..db.database import SessionLocal
            from ..models.db_models import Agent, Job, Bid
            from datetime import datetime, timedelta

            db = SessionLocal()

            # 活跃 Agent 数（最近 5 分钟有操作的）
            five_minutes_ago = datetime.now() - timedelta(minutes=5)
            active_agents = db.query(Agent).filter(
                Agent.updated_at >= five_minutes_ago
            ).count()

            # Job 状态分布
            job_stats = {
                "open": db.query(Job).filter(Job.status == "OPEN").count(),
                "active": db.query(Job).filter(Job.status == "ACTIVE").count(),
                "review": db.query(Job).filter(Job.status == "REVIEW").count(),
                "closed": db.query(Job).filter(Job.status == "CLOSED").count(),
            }

            # Bid 状态分布
            bid_stats = {
                "bidding": db.query(Bid).filter(Bid.status == "BIDDING").count(),
                "selected": db.query(Bid).filter(Bid.status == "SELECTED").count(),
                "in_progress": db.query(Bid).filter(Bid.status == "IN_PROGRESS").count(),
                "completed": db.query(Bid).filter(Bid.status == "COMPLETED").count(),
            }

            # 更新指标
            metrics = get_metrics()
            metrics.set_active_agents(active_agents)
            metrics.set_job_stats(job_stats)
            metrics.set_bid_stats(bid_stats)

            db.close()

            logger.info(
                f"Business metrics updated: {active_agents} active agents, "
                f"{sum(job_stats.values())} jobs, {sum(bid_stats.values())} bids"
            )

        except Exception as e:
            logger.error(f"Failed to update business metrics: {e}")
