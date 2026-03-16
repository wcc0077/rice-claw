# Service 层重构指南

## 架构目标

将业务逻辑从 HTTP API、MCP Server、WebSocket Handler 中抽取到统一的 Service 层，实现：

1. **代码复用** - 避免相同的业务逻辑写多遍
2. **单一数据源** - 业务规则只在一个地方定义
3. **易于测试** - Service 层可独立测试
4. **协议无关** - HTTP、WebSocket、MCP 都只是协议适配层

---

## 重构后的架构

```
┌─────────────────────────────────────────────────────────────┐
│                     协议适配层                               │
├─────────────────┬─────────────────┬─────────────────────────┤
│ HTTP API        │ MCP Server      │ WebSocket Handler       │
│ (api/*.py)      │ (mcp_server.py) │ (websocket/routes.py)   │
│ - 参数验证       │ - JWT 认证       │ - 消息解析               │
│ - 响应格式化     │ - Tool 注册      │ - WebSocket 推送         │
│ - 错误转 HTTP    │ - 错误转 MCP    │ - 错误转 WS 消息          │
└────────────────┴────────┬────────┴──────────┬──────────────┘
         │                 │                    │
         └─────────────────┼────────────────────┘
                           │
                  ┌────────▼────────┐
                  │   Service 层     │
                  │  (services/)    │
                  │                 │
                  │ - JobService    │
                  │ - BidService    │
                  │ - MessageService│
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │    DAL 层        │
                  │   (db/)         │
                  │ - jobs.py       │
                  │ - bids.py       │
                  └─────────────────┘
```

---

## 使用示例

### 1. HTTP API 中使用 Service

**重构前** (`api/bids.py`):
```python
@router.post("/{job_id}", response_model=BidResponse)
async def create_bid_endpoint(
    job_id: str,
    request: BidCreate,
    db: Session = Depends(get_db)
):
    # 验证 job 存在
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 验证 job 状态
    if job.status != "OPEN":
        raise HTTPException(status_code=400, detail="Job not accepting bids")

    # 检查 bid limit
    bids = bid_dal.get_bids_for_job(db, job_id)
    if len(bids) >= job.bid_limit:
        raise HTTPException(status_code=400, detail="Bid limit reached")

    # 创建 bid
    bid_data = {...}
    bid = bid_dal.create_bid(db, bid_data)
    return BidResponse(**bid.to_dict_with_quote())
```

**重构后**:
```python
from src.services import BidService, BidValidationError

@router.post("/{job_id}", response_model=BidResponse)
async def create_bid_endpoint(
    job_id: str,
    request: BidCreate,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent)  # 认证
):
    try:
        # 使用 Service 层，业务逻辑被封装
        bid_service = BidService(db)
        bid = bid_service.create_bid(
            job_id=job_id,
            worker_id=current_agent.agent_id,
            proposal=request.proposal,
            quote=request.quote.model_dump(),
            portfolio_links=request.portfolio_links
        )
        return BidResponse(**bid)
    except BidValidationError as e:
        # Service 层异常转换为 HTTP 400
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        # 权限异常转换为 HTTP 403
        raise HTTPException(status_code=403, detail=str(e))
```

---

### 2. MCP Server 中使用 Service

**重构前** (`mcp_server.py`):
```python
@mcp.tool()
def submit_bid(job_id: str, proposal: str, quote_amount: int, ...):
    agent = get_current_agent()
    db = get_db_session()
    try:
        # 权限检查
        if agent["agent_type"] not in ("worker", "all"):
            raise PermissionDeniedError(...)

        # 业务逻辑重复
        bid_data = {...}
        bid = create_bid(db, bid_data)  # 调用 DAL
        return {"bid_id": bid.bid_id}
    finally:
        db.close()
```

**重构后**:
```python
from src.services import BidService, BidValidationError

@mcp.tool()
def submit_bid(job_id: str, proposal: str, quote_amount: int, ...):
    """Submit a bid for a job."""
    agent = get_current_agent()
    db = get_db_session()
    try:
        # 直接使用 Service 层
        bid_service = BidService(db)
        bid = bid_service.create_bid(
            job_id=job_id,
            worker_id=agent["agent_id"],
            proposal=proposal,
            quote={"amount": quote_amount, "currency": "CNY", "delivery_days": 7}
        )
        return {
            "bid_id": bid["bid_id"],
            "status": bid["status"],
            "message": "Bid submitted successfully"
        }
    except BidValidationError as e:
        raise ValueError(str(e))  # MCP 层转换为 Tool Error
    except PermissionDeniedError as e:
        raise PermissionDeniedError(...)
    finally:
        db.close()
```

---

### 3. WebSocket Handler 中使用 Service

**重构前** (`websocket/routes.py`):
```python
async def handle_grab_order(data, agent_id, manager, db, websocket):
    job_id = data.get("data", {}).get("job_id")

    try:
        # 业务逻辑重复
        bid_data = {
            "job_id": job_id,
            "worker_id": agent_id,
            "proposal": data.get("data", {}).get("proposal", ""),
            "quote": data.get("data", {}).get("quote", {}),
        }
        bid = bid_dal.create_bid(db, bid_data)

        # 创建 job_worker 关联
        job_worker_data = {...}
        job_worker_dal.create_job_worker(db, job_worker_data)

        # 订阅 bid
        await manager.subscribe_bid(agent_id, bid.bid_id)

        # 返回结果
        await websocket.send_json({
            "type": "grab_result",
            "data": {"success": True, "bid_id": bid.bid_id}
        })

        # 通知雇主
        job = job_dal.get_job(db, job_id)
        await manager.send_to_agent(job.employer_id, {...})

    except ValueError as e:
        await websocket.send_json({...})
```

**重构后**:
```python
from src.services import BidService, BidValidationError

async def handle_grab_order(data, agent_id, manager, db, websocket):
    job_id = data.get("data", {}).get("job_id")

    try:
        # 使用 Service 层处理抢单
        bid_service = BidService(db)
        bid = bid_service.create_bid(
            job_id=job_id,
            worker_id=agent_id,
            proposal=data.get("data", {}).get("proposal", ""),
            quote=data.get("data", {}).get("quote", {})
        )

        # 创建 job_worker 关联（Service 提供便捷方法）
        bid_service.create_job_worker_association(
            job_id=job_id,
            bid_id=bid["bid_id"],
            worker_id=agent_id
        )

        # 订阅 bid
        await manager.subscribe_bid(agent_id, bid["bid_id"])

        # 返回结果
        await websocket.send_json({
            "type": "grab_result",
            "data": {
                "success": True,
                "bid_id": bid["bid_id"],
                "message": "抢单成功，等待派单"
            }
        })

        # 通知雇主
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        await manager.send_to_agent(job["employer_id"], {
            "type": "new_bid",
            "data": {"job_id": job_id, "bid_id": bid["bid_id"]}
        })

    except BidValidationError as e:
        # 业务验证错误返回给客户端
        await websocket.send_json({
            "type": "grab_result",
            "data": {"success": False, "message": str(e)}
        })
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"code": "INTERNAL_ERROR", "message": str(e)}
        })
```

---

## 异常处理规范

Service 层定义统一的异常类型，各协议层负责转换为各自的响应格式：

```python
# services/bid_service.py
class BidValidationError(Exception):
    """Bid 业务验证异常"""
    pass

# services/job_service.py
class JobValidationError(Exception):
    """Job 业务验证异常"""
    pass
```

### 各协议层的异常转换

| 协议层 | 异常类型 | 转换方式 |
|--------|---------|---------|
| HTTP API | `BidValidationError` | → `HTTPException(status_code=400)` |
| HTTP API | `PermissionDeniedError` | → `HTTPException(status_code=403)` |
| MCP Server | `BidValidationError` | → `ValueError(str(e))` |
| MCP Server | `PermissionDeniedError` | → 直接抛出（MCP 框架处理） |
| WebSocket | `BidValidationError` | → `{"type": "error", "data": {"message": str(e)}}` |

---

## 迁移清单

### 第一阶段：创建 Service 层 ✅

- [x] `services/bid_service.py` - BidService
- [x] `services/job_service.py` - JobService (同步版本)

### 第二阶段：重构 HTTP API ✅

- [x] `api/bids.py` - 使用 `BidService`
- [x] `api/jobs.py` - 使用 `JobService`
- [x] `api/jobs.py` - 新增端点使用 `BidService` (submit_bid_for_job_endpoint)
- [x] `api/auth.py` - 保持不变（认证层）

### 第三阶段：重构 MCP Server ✅

- [x] `mcp_server.py` - `submit_bid` 使用 `BidService`
- [x] `mcp_server.py` - `publish_job` 使用 `JobService`
- [x] `mcp_server.py` - `get_job_details` 使用 `JobService`
- [x] `mcp_server.py` - `cancel_job` 使用 `JobService`
- [x] `mcp_server.py` - `finalize_hiring` 使用 `BidService`
- [x] `mcp_server.py` - `verify_and_close` 使用 `JobService`
- [x] `mcp_server.py` - `get_all_bids` 使用 `BidService`

### 第四阶段：重构 WebSocket Handler ✅

- [x] `websocket/routes.py` - `handle_grab_order` 使用 `BidService`

---

## 注意事项

1. **Service 层不直接处理 HTTP/WebSocket 响应**
   - 只返回数据字典或领域模型
   - 不导入 FastAPI、WebSocket 等协议相关类

2. **Service 层可以抛出业务异常**
   - 使用自定义异常类型（如 `BidValidationError`）
   - 由协议层转换为具体的响应格式

3. **DAL 层保持不变**
   - `db/*.py` 继续负责 SQL 操作
   - Service 层在 DAL 之上封装业务规则

4. **权限检查的位置**
   - Service 层可以进行资源所有权验证
   - 但认证（Authentication）应在协议层完成

---

## 后续扩展

当需要创建新的业务功能时：

1. 先在 `services/` 创建 Service 类
2. 在 Service 中实现核心业务逻辑
3. HTTP API、MCP Server、WebSocket Handler 调用 Service

示例：
```
services/
├── bid_service.py      ✅
├── job_service.py      ✅
├── message_service.py  (已有，可考虑重构)
├── artifact_service.py  (待创建)
└── payment_service.py  (已有)
```
