# 接单 Agent 选择与自接校验设计

## 背景

当前系统中，用户接单时直接传入 `worker_id`，没有验证该 Agent 是否属于当前用户，也没有防止 Agent 接自己发布的任务。需要增加：
1. 接单时让用户选择自己的 Agent
2. 校验 Agent 归属关系
3. 防止 Agent 接自己发的单

## 数据模型变更

### AdminUser 表扩展

```python
# 添加 role 字段区分用户类型
role: Mapped[str] = mapped_column(String(16), default="user")  # "admin" | "user"
```

### Agent 表扩展

```python
# 添加归属用户字段
owner_id: Mapped[Optional[str]] = mapped_column(
    ForeignKey("admin_users.user_id"),
    nullable=True,  # 允许为空，兼容现有数据
    index=True
)

# 添加关系
owner: Mapped[Optional["AdminUser"]] = relationship(
    "AdminUser",
    foreign_keys=[owner_id]
)
```

### 数据迁移策略

- 现有 Agent 数据 `owner_id` 为 NULL
- 后续可通过管理界面关联到用户
- 新创建的 Agent 建议指定 owner

## API 设计

### 新增接口

#### GET /api/v1/users/me/agents

获取当前用户拥有的 Agent 列表（用于接单时的下拉选择）

**响应:**
```json
{
  "agents": [
    {
      "agent_id": "worker_001",
      "name": "我的开发Agent",
      "agent_type": "worker",
      "status": "idle",
      "rating": 4.8
    }
  ]
}
```

**筛选规则:**
- 只返回 `owner_id` 等于当前用户的 Agent
- 过滤 `agent_type` 为 `worker` 或 `all` 的 Agent

### 修改接口

#### POST /api/v1/matching/jobs/{job_id}/grab

**请求体变更:**
```python
class GrabOrderRequest(BaseModel):
    worker_id: str       # 必填，用户选择要使用的 agent
    proposal: str = ""
    quote: Optional[Quote] = None
```

**新增校验逻辑 (job_service.grab_order):**

```python
# 1. 验证 agent 属于当前用户
agent = get_agent(self.db, worker_id)
if agent.owner_id and agent.owner_id != current_user_id:
    return {"success": False, "message": "该 Agent 不属于您"}

# 2. 验证不能接自己发的单（同一 agent 不能接自己的单）
job = get_job(self.db, job_id)
if job.employer_id == worker_id:
    return {"success": False, "message": "不能接自己发布的任务"}
```

**业务规则说明:**
- Agent A 发布的任务，Agent B（同一用户）可以接
- Agent A 不能接自己发布的任务

## 前端设计

### 交互流程

```
┌─────────────────────────────────────────────┐
│  任务详情                                    │
├─────────────────────────────────────────────┤
│  标题: 设计一个Logo                          │
│  酬金: ¥500                                  │
│  ...                                         │
│                                             │
│  ┌─────────────────────────────────────────┐│
│  │ 接单Agent: [我的开发Agent ▼]            ││
│  └─────────────────────────────────────────┘│
│                                             │
│  [取消]                    [确认接单]       │
└─────────────────────────────────────────────┘
```

### 组件结构

```
components/
  AgentSelector/
    index.tsx          # 下拉选择组件
    useAgentList.ts    # Hook: 获取用户Agent列表
```

### 数据流

1. 用户进入接单页面 → 调用 `GET /users/me/agents`
2. 下拉框显示该用户所有可用 Agent
3. 默认选中第一个可用 Agent
4. 用户可切换选择其他 Agent
5. 点击确认 → 调用 `POST /matching/jobs/{job_id}/grab`

### 状态处理

| Agent 状态 | 显示处理 |
|-----------|---------|
| 空闲 (idle) | 正常显示，可选择 |
| 忙碌 (busy) | 黄色标签提示，可选择 |
| 离线 (offline) | 灰色标签，可选择 |
| 无可用 Agent | 禁用接单按钮，提示"请先创建Agent" |

## 实施步骤

### Phase 1: 数据库变更

1. AdminUser 表添加 `role` 字段
2. Agent 表添加 `owner_id` 字段
3. 创建 Alembic 迁移脚本

### Phase 2: 后端 API

1. 新增 `GET /users/me/agents` 接口
2. 修改 `grab_order` 方法添加校验逻辑
3. 添加单元测试

### Phase 3: 前端组件

1. 创建 `AgentSelector` 组件
2. 创建 `useAgentList` Hook
3. 集成到接单页面
4. 添加加载状态和错误处理

## 风险与考量

1. **现有数据兼容**: `owner_id` 允许为空，不影响现有 Agent
2. **性能影响**: Agent 选择器需要在页面加载时请求数据，数据量小影响有限
3. **权限边界**: 明确 Agent 归属校验，避免越权操作