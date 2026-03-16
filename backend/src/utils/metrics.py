"""指标收集模块

提供：
1. API 性能指标（延迟、QPS、错误率）
2. 业务指标（活跃 Agent、Job 状态分布）
3. 指标存储和查询接口
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock


@dataclass
class MetricPoint:
    """单个指标数据点"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器 - 内存存储，支持查询和聚合"""

    def __init__(self):
        self._lock = Lock()

        # API 指标
        self._request_latencies: List[MetricPoint] = []  # 请求延迟
        self._request_counts: Dict[str, int] = defaultdict(int)  # 请求计数（按路径）
        self._error_counts: Dict[str, int] = defaultdict(int)  # 错误计数（按路径）

        # 业务指标缓存
        self._active_agents: Optional[int] = None
        self._job_stats: Dict[str, int] = {}
        self._bid_stats: Dict[str, int] = {}

        # 指标过期时间（秒）
        self._retention_seconds = 3600  # 1 小时

    def record_latency(self, path: str, method: str, latency_ms: float, status_code: int) -> None:
        """记录请求延迟

        Args:
            path: API 路径
            method: HTTP 方法
            latency_ms: 延迟（毫秒）
            status_code: HTTP 状态码
        """
        with self._lock:
            point = MetricPoint(
                timestamp=datetime.now(),
                value=latency_ms,
                labels={"path": path, "method": method, "status": str(status_code)},
            )
            self._request_latencies.append(point)
            self._request_counts[path] += 1

            if status_code >= 400:
                self._error_counts[path] += 1

    def get_latency_stats(self, window_seconds: int = 300) -> Dict:
        """获取延迟统计

        Args:
            window_seconds: 时间窗口（秒）

        Returns:
            延迟统计：avg, p50, p95, p99, count
        """
        cutoff = datetime.now() - timedelta(seconds=window_seconds)

        with self._lock:
            values = [
                p.value for p in self._request_latencies
                if p.timestamp >= cutoff
            ]

        if not values:
            return {"avg": 0, "p50": 0, "p95": 0, "p99": 0, "count": 0}

        values.sort()
        n = len(values)

        return {
            "avg": sum(values) / n,
            "p50": values[int(n * 0.50)],
            "p95": values[int(n * 0.95)] if n > 1 else values[-1],
            "p99": values[int(n * 0.99)] if n > 1 else values[-1],
            "count": n,
        }

    def get_qps(self, window_seconds: int = 60) -> Dict[str, float]:
        """获取每秒请求数

        Args:
            window_seconds: 时间窗口（秒）

        Returns:
            各路径的 QPS
        """
        cutoff = datetime.now() - timedelta(seconds=window_seconds)

        with self._lock:
            recent_requests = defaultdict(int)
            for p in self._request_latencies:
                if p.timestamp >= cutoff:
                    recent_requests[p.labels["path"]] += 1

        return {path: count / window_seconds for path, count in recent_requests.items()}

    def get_error_rate(self, window_seconds: int = 300) -> Dict[str, float]:
        """获取错误率

        Args:
            window_seconds: 时间窗口（秒）

        Returns:
            各路径的错误率
        """
        with self._lock:
            error_rates = {}
            for path in set(list(self._request_counts.keys()) + list(self._error_counts.keys())):
                total = self._request_counts.get(path, 0)
                errors = self._error_counts.get(path, 0)
                error_rates[path] = errors / total if total > 0 else 0.0
            return error_rates

    def cleanup_old_metrics(self) -> None:
        """清理过期指标"""
        cutoff = datetime.now() - timedelta(seconds=self._retention_seconds)

        with self._lock:
            self._request_latencies = [
                p for p in self._request_latencies
                if p.timestamp >= cutoff
            ]

    # 业务指标设置/获取
    def set_active_agents(self, count: int) -> None:
        """设置活跃 Agent 数量"""
        with self._lock:
            self._active_agents = count

    def get_active_agents(self) -> Optional[int]:
        """获取活跃 Agent 数量"""
        return self._active_agents

    def set_job_stats(self, stats: Dict[str, int]) -> None:
        """设置 Job 统计"""
        with self._lock:
            self._job_stats = stats

    def get_job_stats(self) -> Dict[str, int]:
        """获取 Job 统计"""
        return self._job_stats.copy()

    def set_bid_stats(self, stats: Dict[str, int]) -> None:
        """设置 Bid 统计"""
        with self._lock:
            self._bid_stats = stats

    def get_bid_stats(self) -> Dict[str, int]:
        """获取 Bid 统计"""
        return self._bid_stats.copy()

    def get_all_metrics(self) -> Dict:
        """获取所有指标"""
        return {
            "api_metrics": {
                "latency": self.get_latency_stats(),
                "qps": self.get_qps(),
                "error_rate": self.get_error_rate(),
            },
            "business_metrics": {
                "active_agents": self._active_agents,
                "job_stats": self._job_stats.copy(),
                "bid_stats": self._bid_stats.copy(),
            },
        }


# 全局指标收集器实例
metrics_collector = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """获取全局指标收集器"""
    return metrics_collector
