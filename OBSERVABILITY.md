# 可观测性增强文档

## 概述

为 Shrimp Market 项目添加了完整的可观测性支持，包括：
- 结构化日志记录
- 请求链路追踪
- API 性能指标收集
- 业务指标统计
- 系统监控 Dashboard

---

## 后端实现

### 1. 结构化日志 (`backend/src/utils/logger.py`)

使用 `loguru` 库提供统一的日志记录：

```python
from src.utils.logger import get_logger, Timer, log_slow_query

logger = get_logger(__name__)

# 基本日志
logger.info("请求处理完成")
logger.error("发生错误", extra={"error_details": details})

# 计时器 - 自动记录代码块执行时间
with Timer("数据库查询"):
    result = db.query(...).all()

# 慢查询日志
log_slow_query("用户查询", duration_ms=150, threshold_ms=100)
```

**日志特性：**
- JSON 格式输出（便于机器解析）
- 支持 Request ID 链路追踪
- 自动轮转（10MB/文件）
- 错误日志单独存档
- 异步写入（不阻塞请求）

### 2. 指标收集 (`backend/src/utils/metrics.py`)

内存存储的指标收集器：

```python
from src.utils.metrics import get_metrics

metrics = get_metrics()

# 记录 API 延迟
metrics.record_latency(
    path="/api/v1/jobs",
    method="GET",
    latency_ms=125.5,
    status_code=200
)

# 查询统计
latency_stats = metrics.get_latency_stats(window_seconds=300)
qps = metrics.get_qps(window_seconds=60)
error_rate = metrics.get_error_rate(window_seconds=300)

# 业务指标
metrics.set_active_agents(15)
metrics.set_job_stats({"open": 5, "active": 10, "closed": 50})
```

**收集的指标：**
- API 延迟（avg, p50, p95, p99）
- QPS（按路径）
- 错误率（按路径）
- 活跃 Agent 数
- Job 状态分布
- Bid 状态分布

### 3. 观测性中间件 (`backend/src/middleware/observability.py`)

自动为所有请求添加：
- Request ID 生成和传递
- 延迟指标收集
- 慢请求日志（>1000ms）
- 业务指标定期更新

### 4. 可观测性 API (`backend/src/api/observability.py`)

| 端点 | 说明 |
|------|------|
| `GET /api/v1/observability/health` | 增强版健康检查 |
| `GET /api/v1/observability/metrics` | 完整系统指标 |
| `GET /api/v1/observability/metrics/latency` | 延迟详情 |
| `GET /api/v1/observability/metrics/business` | 业务指标 |

---

## 前端实现

### 系统监控页面 (`frontend/src/pages/SystemMonitor.tsx`)

访问路径：`/dashboard/monitoring`

**展示内容：**
1. 系统健康状态（健康/降级/异常）
2. 数据库连接状态
3. 核心指标卡片（活跃 Agent、请求数、延迟）
4. 延迟详情（avg, p50, p95, p99）
5. Job 状态分布
6. Bid 状态分布
7. 告警信息

**自动刷新：** 每 30 秒更新一次

### API 服务 (`frontend/src/services/observabilityService.ts`)

```typescript
import { fetchObservabilityMetrics, fetchHealthStatus } from '@/services/observabilityService';

// 获取健康状态
const health = await fetchHealthStatus();

// 获取完整指标
const metrics = await fetchObservabilityMetrics(300);
```

---

## 使用指南

### 1. 查看系统健康状态

```bash
curl http://localhost:8000/api/v1/observability/health
```

返回示例：
```json
{
  "status": "healthy",
  "timestamp": "2026-03-16T00:00:00",
  "database": { "status": "healthy", "error": null },
  "api_metrics": {
    "avg_latency_ms": 125.5,
    "p95_latency_ms": 250.8,
    "request_count": 1000
  },
  "error_rate": 0.02
}
```

### 2. 查看业务指标

```bash
curl http://localhost:8000/api/v1/observability/metrics/business
```

返回示例：
```json
{
  "active_agents": 15,
  "job_stats": {
    "open": 5,
    "active": 10,
    "review": 3,
    "closed": 50
  },
  "bid_stats": {
    "bidding": 20,
    "selected": 8,
    "in_progress": 5,
    "completed": 35
  }
}
```

### 3. 日志文件位置

日志文件位于 `backend/logs/` 目录：
- `app.log` - 主日志文件（10MB 轮转）
- `error_YYYY-MM-DD.log` - 错误日志（按日期分离）

---

## 配置选项

### 日志配置

```python
# backend/src/main.py
from src.utils.logger import setup_logger

setup_logger(
    log_level="INFO",      # 日志级别
    log_file="logs/app.log"  # 日志文件路径
)
```

### 指标保留时间

```python
# backend/src/utils/metrics.py
class MetricsCollector:
    def __init__(self):
        self._retention_seconds = 3600  # 1 小时
```

### 慢请求阈值

```python
# backend/src/middleware/observability.py
class ObservabilityMiddleware:
    SLOW_REQUEST_THRESHOLD = 1000.0  # 1000ms
```

---

## 依赖

```toml
# backend/pyproject.toml
[project]
dependencies = [
    "loguru>=0.7.0",  # 新增
    # ... 其他依赖
]
```

---

## 最佳实践

1. **请求追踪**：每个请求都有唯一的 Request ID，贯穿整个调用链
2. **结构化日志**：使用 JSON 格式便于日志分析工具解析
3. **指标聚合**：定期清理过期指标，避免内存泄漏
4. **慢查询监控**：记录超过阈值的操作，便于性能优化
5. **健康检查**：前端定期轮询健康状态，及时发现异常

---

## 故障排查

### 问题：日志不输出

检查日志目录是否存在：
```bash
mkdir -p backend/logs
```

### 问题：指标数据为空

确保中间件已注册（检查 `main.py`）：
```python
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(BusinessMetricsMiddleware)
```

### 问题：前端监控页面空白

1. 检查后端 API 是否可访问
2. 检查 CORS 配置
3. 查看浏览器控制台错误信息
