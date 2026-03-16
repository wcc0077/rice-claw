"""可观测性 API 端点

提供：
1. 系统健康检查（增强版）
2. API 性能指标
3. 业务指标
4. 指标历史数据
"""

from fastapi import APIRouter
from typing import Dict
from datetime import datetime

from ..utils.metrics import get_metrics
from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/health")
async def health_check():
    """增强版健康检查

    返回：
    - 整体状态
    - 数据库连接状态
    - API 延迟统计
    - 错误率
    """
    from ..db.database import SessionLocal
    from sqlalchemy import text

    metrics = get_metrics()
    latency_stats = metrics.get_latency_stats(window_seconds=300)
    error_rates = metrics.get_error_rate(window_seconds=300)

    # 数据库健康检查
    db_status = "healthy"
    db_error = None
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    # 整体健康状态
    avg_latency = latency_stats.get("avg", 0)
    overall_error_rate = sum(error_rates.values()) / len(error_rates) if error_rates else 0

    if db_status == "unhealthy":
        status = "unhealthy"
    elif avg_latency > 5000:  # 平均延迟 > 5s
        status = "degraded"
    elif overall_error_rate > 0.1:  # 错误率 > 10%
        status = "degraded"
    else:
        status = "healthy"

    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "database": {
            "status": db_status,
            "error": db_error,
        },
        "api_metrics": {
            "avg_latency_ms": round(latency_stats.get("avg", 0), 2),
            "p95_latency_ms": round(latency_stats.get("p95", 0), 2),
            "p99_latency_ms": round(latency_stats.get("p99", 0), 2),
            "request_count": latency_stats.get("count", 0),
        },
        "error_rate": round(overall_error_rate, 4),
    }


@router.get("/metrics")
async def get_system_metrics(
    window_seconds: int = 300,
) -> Dict:
    """获取系统指标

    Args:
        window_seconds: 时间窗口（秒），默认 300 秒

    Returns:
        包含 API 指标和业务指标的完整数据
    """
    metrics = get_metrics()

    return {
        "window_seconds": window_seconds,
        "api_metrics": {
            "latency": metrics.get_latency_stats(window_seconds),
            "qps": metrics.get_qps(window_seconds=60),
            "error_rate": metrics.get_error_rate(window_seconds),
        },
        "business_metrics": {
            "active_agents": metrics.get_active_agents(),
            "job_stats": metrics.get_job_stats(),
            "bid_stats": metrics.get_bid_stats(),
        },
    }


@router.get("/metrics/latency")
async def get_latency_metrics(
    window_seconds: int = 300,
) -> Dict:
    """获取延迟指标

    Returns:
        延迟统计：avg, p50, p95, p99, count
    """
    metrics = get_metrics()
    stats = metrics.get_latency_stats(window_seconds)

    return {
        "window_seconds": window_seconds,
        "latency_ms": {
            "avg": round(stats.get("avg", 0), 2),
            "p50": round(stats.get("p50", 0), 2),
            "p95": round(stats.get("p95", 0), 2),
            "p99": round(stats.get("p99", 0), 2),
        },
        "request_count": stats.get("count", 0),
    }


@router.get("/metrics/business")
async def get_business_metrics() -> Dict:
    """获取业务指标

    Returns:
        活跃 Agent 数、Job 状态分布、Bid 状态分布
    """
    metrics = get_metrics()

    return {
        "active_agents": metrics.get_active_agents(),
        "job_stats": metrics.get_job_stats(),
        "bid_stats": metrics.get_bid_stats(),
    }


@router.get("/metrics/slow-requests")
async def get_slow_requests(
    threshold_ms: float = 1000.0,
    limit: int = 20,
) -> Dict:
    """获取慢请求列表

    Args:
        threshold_ms: 慢请求阈值（毫秒）
        limit: 返回数量限制

    Returns:
        慢请求列表
    """
    # 注意：这里需要从日志中读取，暂时返回空列表
    # 实际实现需要读取日志文件或专门的慢查询存储
    return {
        "threshold_ms": threshold_ms,
        "count": 0,
        "requests": [],
    }
