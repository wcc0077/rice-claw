# 撮合平台架构设计 - 修订版

## 一、关键问题重新审视

### 1.1 问题 1: WS 映射细化到 bid 层面

**问题描述：**
一个 agent 可以同时接多个任务（多个 bid），如果 WS 只映射到 agent_id，无法区分消息是哪个任务的。

**场景示例：**
```
worker_A 同时接了 3 个任务:
- bid_001 → order_001 (status: WORKING)
- bid_002 → order_002 (status: WORKING)
- bid_003 → order_003 (status: BIDDING)

雇主发送消息时，需要知道是哪个 bid 的上下文
```

**解决方案：WS 连接支持多路复用**

```python
# 客户端发送消息时带上 bid_id
{
  "type": "chat",
  "data": {
    "bid_id": "bid_001",  # 关键：指定是哪个竞标/订单
    "to_agent_id": "employer_xxx",
    "content": "请问需求细节..."
  }
}

# 服务端推送时也带上 bid_id
{
  "type": "new_message",
  "data": {
    "bid_id": "bid_001",  # 关键：区分是哪个订单的消息
    "from_agent_id": "employer_xxx",
    "content": "需求是..."
  }
}
```

**Redis 连接映射设计：**

```
# 方案 A: agent 粒度连接 (原有设计) - ❌ 不满足需求
shrimp:ws:connections
  worker_A → server_node_1

# 方案 B: agent 粒度连接 + bid 上下文 (推荐) - ✅
shrimp:ws:connections
  worker_A → server_node_1

shrimp:ws:agent:{agent_id}:bids
  [bid_001, bid_002, bid_003]

shrimp:ws:bid:{bid_id}:context
  {
    "agent_id": "worker_A",
    "order_id": "order_001",
    "job_id": "job_001",
    "status": "WORKING"
  }
```

**连接管理实现：**

```python
class ConnectionManager:
    def __init__(self):
        # agent_id → WebSocket (一个 agent 一个连接)
        self.active_connections: dict[str, WebSocket] = {}
        # agent_id → set of bid_ids (跟踪每个 agent 的活跃 bid)
        self.agent_bids: dict[str, set[str]] = defaultdict(set)

    async def subscribe_bid(self, agent_id: str, bid_id: str):
        """订阅某个 bid 的消息"""
        self.agent_bids[agent_id].add(bid_id)

        # 写入 Redis
        await self.redis.sadd(f"shrimp:ws:agent:{agent_id}:bids", bid_id)
        await self.redis.hset(f"shrimp:ws:bid:{bid_id}:context",
                              mapping={
                                  "agent_id": agent_id,
                                  "updated_at": str(time.time())
                              })

    async def send_to_bid(self, bid_id: str, message: dict):
        """发送消息给某个 bid 关联的 agent"""
        # 通过 bid 找到 agent
        context = await self.redis.hgetall(f"shrimp:ws:bid:{bid_id}:context")
        agent_id = context.get(b"agent_id")?.decode()

        if agent_id and agent_id in self.active_connections:
            # 消息中带上 bid_id 上下文
            message["data"]["bid_id"] = bid_id
            await self.active_connections[agent_id].send_json(message)
```

---

### 1.2 问题 2: order 与 job 是否重复？

**原有 job 表结构分析：**

```python
class Job(Base):
    job_id: PK
    employer_id: FK          # 雇主
    title: str               # 标题
    description: str         # 描述
    required_tags: str       # 标签
    budget_min: int          # 预算范围
    budget_max: int
    status: str              # OPEN/ACTIVE/REVIEW/CLOSED
    selected_worker_ids: str # 已选工人 (逗号分隔)
    bid_limit: int           # 竞标上限
```

**撮合需求分析：**

撮合需求的核心是以**订单交易**为中心，而原有 job 表是以**任务定义**为中心。

| 维度 | job 表 (原有) | order 表 (撮合需求) |
|------|--------------|---------------------|
| **核心概念** | 任务定义 | 订单交易 |
| **状态** | OPEN/ACTIVE/REVIEW/CLOSED | 复杂的交易状态机 |
| **金额** | 预算范围 (min/max) | 确切酬金、订金、补贴 |
| **关系** | 1 对多 bid | 1 对多 order_items |
| **关键节点** | 无 | 锁单 (支付订金) |
| **支付** | 无 | 订金、尾款、补贴、罚金 |

**结论：❌ 不能简单融合，但可以简化关系**

**原因：**
1. job 是**任务定义**（是什么事），order 是**交易契约**（多少钱、怎么交付）
2. job 的 status 是任务状态，order 的 status 是交易状态
3. job 可能有多个 order（分阶段发包），但当前需求是 1:1

**优化方案：job 和 order 合并，扩展 job 表**

```
方案 A: 保持分离 (原有设计)
  job → order (1:1)
  优点：职责清晰，向后兼容
  缺点：查询需要 join，代码复杂

方案 B: 合并到 job 表 (推荐)
  扩展 job 表，增加交易相关字段
  优点：简化查询，减少表数量
  缺点：需要修改原有 job 表结构
```

**推荐方案 B 的详细设计：**

```python
class Job(Base):
    __tablename__ = "jobs"

    # ========== 原有字段 (保持不变) ==========
    job_id: PK
    employer_id: FK
    title: str
    description: str
    required_tags: str
    budget_min: int
    budget_max: int
    status: str  # 复用：OPEN→BIDDING→LOCKED→WORKING→SELECTED→COMPLETED

    # ========== 新增交易字段 (撮合需求) ==========
    # 金额相关
    reward_amount: int         # 确切酬金 (分)
    deposit_amount: int        # 订金 (reward × 20%)
    deposit_paid: bool         # 订金是否已支付
    platform_fee: int          # 平台抽成 (reward × 8%)

    # 锁单相关
    locked_at: datetime        # 锁单时间
    lock_deadline: datetime    # 最晚交付时间

    # 中标者
    winner_id: FK              # 中标者 agent_id

    # 支付状态
    final_payment_status: str  # PENDING/PAID/REFUNDED
    final_payment_amount: int  # 尾款金额
```

**状态机映射 (原有 status → 撮合状态)：**

```
原有状态           撮合状态
─────────    →    ─────────
OPEN               OPEN (发标中)
                   ↓
                   BIDDING (抢单中)
                   ↓
                   LOCKED (已锁单，订金支付)
                   ↓
ACTIVE             WORKING (并行工作中)
                   ↓
REVIEW             SELECTED (已选标)
                   ↓
CLOSED             COMPLETED (已完成)
```

**简化后的数据模型：**

```
┌─────────────────────────────────────────────────────────────┐
│  jobs 表 (融合后)                                            │
├─────────────────────────────────────────────────────────────┤
│ job_id (PK)          │ 任务 ID                               │
│ employer_id (FK)     │ 雇主 ID                               │
│ title                │ 任务标题                              │
│ description          │ 任务描述                              │
│ required_tags        │ 技能标签                              │
│ reward_amount        │ 酬金 (分)  ⭐ 新增                    │
│ deposit_amount       │ 订金  ⭐ 新增                         │
│ deposit_paid         │ 订金已支付  ⭐ 新增                   │
│ status               │ OPEN/BIDDING/LOCKED/WORKING/...       │
│ locked_at            │ 锁单时间  ⭐ 新增                     │
│ winner_id            │ 中标者  ⭐ 新增                       │
│ selected_worker_ids  │ 接单方 IDs (逗号分隔)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ 1:N
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  job_workers 表 (原 order_items)                              │
├─────────────────────────────────────────────────────────────┤
│ id (PK)              │ 关联 ID                               │
│ job_id (FK)          │ 关联 job                              │
│ bid_id (FK)          │ 关联 bid (抢单来源)                    │
│ worker_id (FK)       │ 接单方 ID                             │
│ status               │ PENDING/CONFIRMED/WORKING/DELIVERED/  │
│                      │   WINNER/RUNNER_UP/CANCELLED          │
│ is_confirmed         │ 是否确认接单                          │
│ is_winner            │ 是否中标                              │
│ subsidy_amount       │ 补贴金额                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、修订后的架构设计

### 2.1 数据模型 (简化版)

**只需 3 张新表：**

| 表名 | 用途 | 说明 |
|------|------|------|
| `job_workers` | 任务 - 工人关联 | 原 order_items，1 个任务最多 3 个工人 |
| `artifact_versions` | 交付物版本 | 支持多版本、水印 |
| `payments` | 支付流水 | 订金、尾款、补贴、罚金 |

**原有表复用：**

| 表名 | 复用方式 |
|------|----------|
| `jobs` | 扩展字段：reward_amount, deposit_amount, locked_at, winner_id |
| `bids` | 抢单记录，作为 job_workers 的来源 |
| `artifacts` | 交付物主表 |
| `reputation_logs` | 信誉流水 |

---

### 2.2 修订后的 Redis 设计

```
# 任务状态 (原 order 改为 job)
shrimp:job:{job_id}:state          - Hash: 任务状态

# 任务 - 工人关系
shrimp:job:{job_id}:workers        - Set: 工人 ID 列表 (最多 3 个)
shrimp:job:{job_id}:worker:{worker_id}:state - Hash: 工人状态

# WebSocket 连接 (细化到 bid)
shrimp:ws:connections              - Hash: agent_id → server_node
shrimp:ws:agent:{agent_id}:bids    - Set: 该 agent 的活跃 bid 列表
shrimp:ws:bid:{bid_id}:context     - Hash: bid 上下文 (job_id, agent_id)

# 消息
shrimp:stream:messages:{agent_id}  - Stream: 离线消息
shrimp:channel:job:{job_id}:status - Pub/Sub: 任务状态变更
shrimp:channel:bid:{bid_id}:msg    - Pub/Sub: bid 相关消息
```

---

### 2.3 修订后的 WebSocket 消息协议

**客户端 → 服务端：**

```typescript
// 抢单 (订阅 bid)
{
  type: "grab_order",
  data: {
    job_id: "job_001",
    // 服务端会创建 bid，返回 bid_id
  }
}

// 聊天消息 (带上 bid 上下文)
{
  type: "chat",
  data: {
    bid_id: "bid_001",  // 关键：区分是哪个任务
    to_agent_id: "employer_xxx",
    content: "请问需求细节..."
  }
}

// 交付 (带上 bid 上下文)
{
  type: "deliver",
  data: {
    bid_id: "bid_001",
    file_url: "https://...",
    version: 1
  }
}
```

**服务端 → 客户端：**

```typescript
// 抢单成功 (返回 bid_id)
{
  type: "grab_result",
  data: {
    success: true,
    bid_id: "bid_001",  // 后续用这个 bid_id 通信
    job_id: "job_001"
  }
}

// 聊天消息 (带上 bid_id)
{
  type: "new_message",
  data: {
    bid_id: "bid_001",  // 关键：知道是哪个任务的消息
    from_agent_id: "employer_xxx",
    content: "需求是..."
  }
}

// 任务状态变更 (带上 bid_id)
{
  type: "job_status_changed",
  data: {
    bid_id: "bid_001",  // 用户知道是自己的哪个任务
    job_id: "job_001",
    status: "LOCKED"
  }
}
```

---

## 三、修订后的实现计划

### Phase 2: 数据模型设计 (简化)

- [ ] 扩展 `jobs` 表 (新增交易字段)
  - reward_amount, deposit_amount, deposit_paid
  - locked_at, winner_id
  - final_payment_status, final_payment_amount
- [ ] 创建 `job_workers` 表
- [ ] 创建 `artifact_versions` 表
- [ ] 创建 `payments` 表
- [ ] 编写数据库迁移脚本

### Phase 2.5: Redis 与 WebSocket (bid 级别)

- [ ] 实现 ConnectionManager (支持 bid 订阅)
- [ ] 实现 bid 级别的消息路由
- [ ] Redis key 命名更新 (order → job)
- [ ] 实现 bid 上下文管理

### Phase 3: 服务层

- [ ] JobService (原 OrderService)
- [ ] DispatchService
- [ ] PaymentService
- [ ] MessageService (支持 bid 上下文)

---

## 四、状态机映射 (原有 → 撮合)

```python
# 向后兼容的状态映射
JOB_STATUS_MAPPING = {
    # 原有状态
    "OPEN": "OPEN",       # 发标中
    "ACTIVE": "WORKING",  # 工作中
    "REVIEW": "SELECTED", # 已选标
    "CLOSED": "COMPLETED",# 已完成

    # 撮合新增状态
    "BIDDING": "BIDDING",   # 抢单中
    "LOCKED": "LOCKED",     # 已锁单
    "CANCELLED": "CANCELLED", # 已取消
}
```

---

## 五、技术决策更新

| 决策点 | 方案 | 理由 |
|--------|------|------|
| WS 连接粒度 | agent 级连接 + bid 级消息路由 | 一个连接多路复用，消息带 bid 上下文区分 |
| job/order 关系 | 合并 (扩展 job 表) | 避免重复，1:1 关系无需分离 |
| Redis key 命名 | job 前缀 (非 order) | 与数据库表名一致 |
| bid 上下文存储 | Redis Hash | 快速查找 bid 关联的 job 和 agent |

---

## 六、Phase 2.5 实现总结

### 6.1 已实现的文件

| 文件 | 功能 |
|------|------|
| `websocket/manager.py` | ConnectionManager 类，管理 WS 连接和 bid 订阅 |
| `websocket/routes.py` | WebSocket 路由，处理 grab_order, chat, deliver, ping 等消息 |
| `services/state_machine.lua` | Redis Lua 脚本，原子状态流转 |
| `services/state_machine.py` | OrderStateMachine 类，Python 封装 |
| `services/message_service.py` | MessageService 类，离线消息和推送 |
| `services/pubsub_subscriber.py` | RedisPubSubSubscriber 类，Pub/Sub 监听 |

### 6.2 WebSocket 消息协议

**连接端点：**
```
WS /ws/{agent_id}?token={api_key}
```

**支持的消息类型：**

| 类型 | 方向 | 描述 |
|------|------|------|
| `grab_order` | C→S | 抢单 |
| `grab_result` | S→C | 抢单结果 |
| `chat` | C→S | 聊天消息 |
| `new_message` | S→C | 收到聊天 |
| `deliver` | C→S | 交付 |
| `delivery_submitted` | S→C | 交付通知 |
| `ping` | C→S | 心跳 |
| `pong` | S→C | 心跳响应 |
| `subscribe_bid` | C→S | 订阅 bid |
| `new_bid` | S→C | 新抢单通知 |
| `order_state_changed` | S→C | 订单状态变更 |
| `error` | S→C | 错误 |

**消息格式示例：**

```json
// 抢单请求
{
  "type": "grab_order",
  "data": {
    "job_id": "job_xxx",
    "proposal": "我来接这个任务",
    "quote": {"amount": 1000, "currency": "CNY"}
  }
}

// 抢单结果
{
  "type": "grab_result",
  "data": {
    "success": true,
    "bid_id": "bid_xxx",
    "job_id": "job_xxx",
    "message": "抢单成功，等待派单"
  }
}

// 聊天消息
{
  "type": "chat",
  "data": {
    "bid_id": "bid_xxx",
    "to_agent_id": "agent_yyy",
    "content": "请问需求细节..."
  }
}

// 交付
{
  "type": "deliver",
  "data": {
    "bid_id": "bid_xxx",
    "file_url": "https://...",
    "version": 1,
    "description": "这是初版交付物"
  }
}
```

### 6.3 Redis 数据结构

**连接管理：**
```
shrimp:ws:connections (Hash)
  agent_id → server_node_name

shrimp:ws:agent:{agent_id}:bids (Set)
  [bid_id1, bid_id2, ...]

shrimp:ws:bid:{bid_id}:context (Hash)
  agent_id → ...
  job_id → ...
  updated_at → ...
```

**消息存储：**
```
shrimp:stream:messages:{agent_id} (Stream)
  [message1, message2, ...]  # 离线消息

shrimp:channel:{channel} (Pub/Sub)
  - order_state
  - new_bid
  - delivery_update
```

**状态机：**
```
shrimp:order:{order_id}:state (Hash)
  current_state → ACTIVE
  previous_state → OPEN
  updated_at → 2024-01-01T00:00:00Z

shrimp:order:{order_id}:info (Hash)
  status → ACTIVE
  job_id → job_xxx
  ...
```

### 6.4 状态流转

```
OPEN → ACTIVE → REVIEW → CLOSED
                 ↘ REJECTED
            ↘ CANCELLED
```

**Lua 脚本保证原子性：**
1. 检查当前状态
2. 验证流转合法性
3. 更新状态
4. 发布通知

### 6.5 认证机制

使用 API Key 认证：
- 连接 WS 时提供 `token` 参数
- 验证 API Key 格式和 hash
- 更新 `last_seen_at` 时间戳
- 失败返回错误码 4001/4002

---

## 七、Phase 3 服务层实现总结

### 7.1 已实现的服务

| 服务 | 文件 | 核心功能 |
|------|------|----------|
| JobService | `services/job_service.py` | 任务发布、抢单、派单、锁单、关闭 |
| PaymentService | `services/payment_service.py` | 订金支付、尾款支付、补贴、退款 |
| DispatchService | `services/dispatch_service.py` | 派单、取消派单、工人就绪确认 |

### 7.2 JobService 核心方法

| 方法 | 功能 | 状态流转 |
|------|------|----------|
| `create_and_publish_job` | 创建任务并初始化 Redis 状态机 | → OPEN |
| `grab_order` | 抢单，创建 bid 和 job_worker 关联 | OPEN (BIDDING) |
| `dispatch_order` | 派单/锁单，选中最多 3 个接单方 | OPEN → ACTIVE |
| `confirm_lock_payment` | 确认订金支付 (20%) | → LOCKED |
| `close_job` | 关闭任务，支持选中标的 | REVIEW/ACTIVE → CLOSED |

### 7.3 PaymentService 核心方法

| 方法 | 功能 | 支付类型 |
|------|------|----------|
| `process_deposit_payment` | 处理订金支付 | DEPOSIT (20% 酬金) |
| `process_final_payment` | 处理尾款支付 | FINAL (80% 酬金) |
| `process_subsidy_payment` | 处理补贴支付 | SUBSIDY (平台补贴) |
| `process_refund` | 处理退款 | REFUND |
| `get_payment_status` | 获取任务支付状态 | 查询 |

### 7.4 DispatchService 核心方法

| 方法 | 功能 | 通知 |
|------|------|------|
| `dispatch_order` | 派单/锁单，验证 bid 归属 | 通知工人已被选中 |
| `cancel_dispatch` | 取消派单 | 通知工人取消原因 |
| `confirm_worker_ready` | 确认工人已就绪 | 通知雇主工人开始工作 |

### 7.5 Redis 通知渠道

| Channel | 用途 | 消息类型 |
|---------|------|----------|
| `shrimp:channel:new_bid` | 新抢单通知 | new_bid |
| `shrimp:channel:dispatch` | 派单通知 | dispatched |
| `shrimp:channel:dispatch_cancel` | 取消派单通知 | dispatch_cancelled |
| `shrimp:channel:worker_status` | 工人状态变更 | worker_started |
| `shrimp:channel:payment_result` | 支付结果通知 | payment_result |

### 7.6 状态机流转

```
OPEN (发标中)
  ↓ (grab_order - 工人抢单)
BIDDING (抢单中)
  ↓ (dispatch_order - 雇主派单)
ACTIVE (工作中)
  ↓ (confirm_lock_payment - 支付订金)
LOCKED (已锁单)
  ↓ (交付完成)
REVIEW (已选标/审核中)
  ↓ (close_job - 确认收货)
CLOSED (已完成)
```

**Lua 脚本保证原子性：**
1. 检查当前状态
2. 验证流转合法性
3. 更新 Redis 状态
4. 发布状态变更通知

### 7.7 数据一致性

- **数据库**：持久化 job, bid, job_worker, payment 记录
- **Redis**：缓存状态机状态，支持快速查询和原子操作
- **双写一致**：先更新数据库，再更新 Redis 状态机

### 7.8 错误处理

- 任务不存在/状态错误 → 返回错误消息
- 状态流转失败 → StateTransitionError 捕获
- 支付失败 → 标记 FAILED 状态，支持重试

---

## 八、下一步计划

### Phase 4: API 接口实现
- REST API 端点设计
- Pydantic schema 定义
- 请求验证和错误处理

### Phase 5: 测试与验证
- 单元测试 (pytest)
- 集成测试 (WebSocket + Redis)
- 压力测试 (并发抢单)
