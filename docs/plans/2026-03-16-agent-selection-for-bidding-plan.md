# Agent Selection for Bidding Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement agent selection UI when accepting jobs, with validation that agents belong to the current user and cannot bid on their own jobs.

**Architecture:** Extend AdminUser with role field, add owner_id to Agent table, create new users API endpoint, add validation to grab_order, and build AgentSelector dropdown component in frontend.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic (backend); React, TypeScript, Ant Design (frontend)

---

## Task 1: Database Model Changes

**Files:**
- Modify: `backend/src/models/db_models.py:332-356` (AdminUser)
- Modify: `backend/src/models/db_models.py:14-86` (Agent)
- Create: `backend/alembic/versions/xxx_add_owner_to_agent.py`

**Step 1: Add role field to AdminUser model**

In `backend/src/models/db_models.py`, find the AdminUser class and add the role field:

```python
# After line 341 (after status field)
role: Mapped[str] = mapped_column(String(16), default="user")  # "admin" | "user"
```

**Step 2: Add owner_id field to Agent model**

In `backend/src/models/db_models.py`, find the Agent class and add after line 34 (after is_verified):

```python
# Agent ownership
owner_id: Mapped[Optional[str]] = mapped_column(
    ForeignKey("admin_users.user_id"),
    nullable=True,
    index=True
)
```

Add the relationship in the Agent class after the existing relationships (around line 59):

```python
owner: Mapped[Optional["AdminUser"]] = relationship(
    "AdminUser",
    foreign_keys=[owner_id]
)
```

Update the `to_dict` method in Agent class to include owner_id:

```python
# Add after line 82 in to_dict method
"owner_id": self.owner_id,
```

**Step 3: Create Alembic migration**

Run the command to create a new migration:

```bash
cd backend && uv run alembic revision --autogenerate -m "add_role_to_admin_user_and_owner_to_agent"
```

**Step 4: Verify migration file**

Check the generated migration file in `backend/alembic/versions/` and ensure it contains:
- Adding `role` column to `admin_users` table
- Adding `owner_id` column to `agents` table
- Creating foreign key constraint

**Step 5: Commit**

```bash
git add backend/src/models/db_models.py backend/alembic/versions/
git commit -m "feat(db): add role to AdminUser and owner_id to Agent

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Add Database Access Layer Function

**Files:**
- Modify: `backend/src/db/agents.py`

**Step 1: Add function to get agents by owner_id**

Add the following function to `backend/src/db/agents.py` at the end of the file:

```python
def get_agents_by_owner(
    db: Session,
    owner_id: str,
    agent_type: Optional[str] = None
) -> List[Agent]:
    """获取用户拥有的所有 Agent

    Args:
        db: 数据库会话
        owner_id: 用户 ID
        agent_type: Agent 类型筛选 (可选): 'worker' | 'employer' | 'all'

    Returns:
        Agent 列表
    """
    query = select(Agent).where(Agent.owner_id == owner_id)

    if agent_type:
        # Filter by agent_type: 'worker' or 'all' can accept jobs
        if agent_type == "worker":
            query = query.where(
                Agent.agent_type.in_(["worker", "all"])
            )
        elif agent_type == "employer":
            query = query.where(
                Agent.agent_type.in_(["employer", "all"])
            )

    query = query.order_by(Agent.created_at.desc())
    return db.execute(query).scalars().all()
```

Make sure to add the import at the top if not present:

```python
from sqlalchemy import select
```

**Step 2: Commit**

```bash
git add backend/src/db/agents.py
git commit -m "feat(db): add get_agents_by_owner function

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Add User Agents API Endpoint

**Files:**
- Create: `backend/src/api/users.py`
- Modify: `backend/src/api/__init__.py`

**Step 1: Create users API file**

Create `backend/src/api/users.py`:

```python
"""User-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..db.database import get_db
from ..db import agents as agent_dal
from ..models.schemas import AgentResponse

router = APIRouter()

# JWT settings (should be shared with auth.py in production)
import secrets
JWT_SECRET_KEY = secrets.token_urlsafe(32)  # In production, use shared secret
JWT_ALGORITHM = "HS256"

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract user ID from JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/me/agents", response_model=List[AgentResponse])
async def get_my_agents(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取当前用户拥有的 Agent 列表

    用于接单时的 Agent 选择下拉框。
    只返回可以接单的 Agent (agent_type 为 'worker' 或 'all')
    """
    agents = agent_dal.get_agents_by_owner(db, user_id, agent_type="worker")

    return [AgentResponse(**agent.to_dict()) for agent in agents]
```

**Step 2: Register router in __init__.py**

Modify `backend/src/api/__init__.py` to include the users router:

```python
# Add import at top
from . import users

# Add after other router includes (around line 19)
router.include_router(users.router, prefix="/users", tags=["users"])
```

**Step 3: Commit**

```bash
git add backend/src/api/users.py backend/src/api/__init__.py
git commit -m "feat(api): add GET /users/me/agents endpoint

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Add Validation to grab_order

**Files:**
- Modify: `backend/src/services/job_service.py:113-196`
- Modify: `backend/src/api/matching.py:158-202`

**Step 1: Add validation in job_service.py**

In `backend/src/services/job_service.py`, modify the `grab_order` method to add validation.

Add validation after line 147 (after checking worker exists):

```python
# 3. 检查是否已抢过该任务
existing_bids = get_bids_for_job(self.db, job_id)
for bid in existing_bids:
    if bid.get("worker_id") == worker_id:
        return {"success": False, "message": "您已抢过此任务"}

# 4. 检查是否已达接单上限
bid_limit = job.bid_limit or 3
if len(existing_bids) >= bid_limit:
    return {"success": False, "message": "该任务已达最大接单数"}

# 5. 验证不能接自己发的单（同一 agent 不能接自己的单）
if job.employer_id == worker_id:
    return {"success": False, "message": "不能接自己发布的任务"}
```

**Step 2: Update matching.py to pass current_user_id for ownership validation**

In `backend/src/api/matching.py`, we need to add user authentication. First, add the dependency:

```python
# Add import at top
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Add security scheme
security = HTTPBearer()

# Add helper function (similar to users.py)
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract user ID from JWT token."""
    from ..api.auth import JWT_SECRET_KEY, JWT_ALGORITHM
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

Then modify the `grab_order` endpoint to add user validation:

```python
@router.post("/jobs/{job_id}/grab", response_model=GrabOrderResponse)
async def grab_order(
    job_id: str,
    request: GrabOrderRequest,
    redis: RedisSession,
    guard: PromptGuardStrict,
    service: JobService = Depends(get_job_service),
    user_id: str = Depends(get_current_user_id)  # Add this
):
    """抢单

    工人抢单，创建 bid 和 job_worker 关联
    """
    # 验证用户输入
    validated = await validate_user_input(
        redis=redis,
        guard=guard,
        user_id=user_id,
        rate_limit_type=RateLimitType.BID_SUBMIT_HOUR,
        proposal=request.proposal
    )

    # 验证 worker_id 是否属于当前用户
    worker = agent_dal.get_agent(service.db, request.worker_id)
    if not worker:
        raise HTTPException(status_code=400, detail=f"工人 {request.worker_id} 不存在")

    if worker.owner_id and worker.owner_id != user_id:
        raise HTTPException(status_code=403, detail="该 Agent 不属于您")

    quote_data = request.quote.model_dump() if request.quote else None

    result = await service.grab_order(
        job_id=job_id,
        worker_id=request.worker_id,
        proposal=validated.get("proposal", request.proposal),
        quote=quote_data
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return GrabOrderResponse(
        success=True,
        bid_id=result["bid_id"],
        job_id=job_id,
        message=result["message"]
    )
```

**Step 3: Update GrabOrderRequest schema**

In `backend/src/models/schemas.py`, ensure `GrabOrderRequest` has `worker_id` as required:

```python
class GrabOrderRequest(BaseModel):
    """抢单请求"""
    worker_id: str  # 必填，用户选择要使用的 agent
    proposal: str = ""
    quote: Optional[Quote] = None
```

**Step 4: Commit**

```bash
git add backend/src/services/job_service.py backend/src/api/matching.py backend/src/models/schemas.py
git commit -m "feat(api): add validation to grab_order for agent ownership

- Validate worker_id belongs to current user
- Prevent agent from accepting own jobs

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Share JWT Secret Between Auth Modules

**Files:**
- Modify: `backend/src/api/auth.py`
- Create: `backend/src/auth/jwt_config.py`

**Step 1: Create shared JWT config**

Create `backend/src/auth/jwt_config.py`:

```python
"""Shared JWT configuration."""

import secrets

# JWT settings - in production, load from environment
JWT_SECRET_KEY = secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24
```

**Step 2: Update auth.py to use shared config**

Modify `backend/src/api/auth.py` to import from shared config:

```python
# Replace lines 30-33 with:
from ..auth.jwt_config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS

# Remove the local definitions of these constants
```

**Step 3: Commit**

```bash
git add backend/src/auth/jwt_config.py backend/src/api/auth.py
git commit -m "refactor(auth): share JWT config between modules

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Create Frontend AgentSelector Component

**Files:**
- Create: `frontend/src/components/AgentSelector/index.tsx`
- Create: `frontend/src/components/AgentSelector/useAgentList.ts`

**Step 1: Create useAgentList hook**

Create `frontend/src/components/AgentSelector/useAgentList.ts`:

```typescript
import { useState, useEffect } from 'react'
import { message } from 'antd'
import api from '@/services/api'

export interface AgentInfo {
  agent_id: string
  name: string
  agent_type: string
  status: string
  rating: number
}

export function useAgentList() {
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAgents = async () => {
    try {
      setLoading(true)
      const response = await api.get('/users/me/agents')
      setAgents(response.data)
      setError(null)
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || '获取 Agent 列表失败'
      setError(errorMsg)
      // Don't show message on 401 - user might not be logged in
      if (err?.response?.status !== 401) {
        message.error(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [])

  return { agents, loading, error, refetch: fetchAgents }
}
```

**Step 2: Create AgentSelector component**

Create `frontend/src/components/AgentSelector/index.tsx`:

```typescript
import { Select, Tag, Space, Empty } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import { useAgentList, AgentInfo } from './useAgentList'

interface AgentSelectorProps {
  value?: string
  onChange?: (agentId: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

const statusColorMap: Record<string, string> = {
  idle: 'green',
  busy: 'orange',
  offline: 'default',
}

/**
 * AgentSelector - Agent 选择下拉框
 *
 * 用于接单时选择要使用的 Agent
 */
export function AgentSelector({
  value,
  onChange,
  placeholder = '选择接单 Agent',
  disabled = false,
  className,
}: AgentSelectorProps) {
  const { agents, loading, error } = useAgentList()

  // No agents available
  if (!loading && agents.length === 0 && !error) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <span className="text-gray-400">
            暂无可用 Agent，请先创建
          </span>
        }
      />
    )
  }

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled || !!error}
      loading={loading}
      className={className}
      style={{ minWidth: 200 }}
      optionLabelProp="label"
    >
      {agents.map((agent) => (
        <Select.Option
          key={agent.agent_id}
          value={agent.agent_id}
          label={
            <Space>
              <UserOutlined />
              {agent.name}
            </Space>
          }
        >
          <div className="flex justify-between items-center">
            <span>{agent.name}</span>
            <Space>
              <Tag color={statusColorMap[agent.status] || 'default'}>
                {agent.status}
              </Tag>
              {agent.rating > 0 && (
                <span className="text-yellow-500">
                  ★ {agent.rating.toFixed(1)}
                </span>
              )}
            </Space>
          </div>
        </Select.Option>
      ))}
    </Select>
  )
}

export default AgentSelector
```

**Step 3: Commit**

```bash
git add frontend/src/components/AgentSelector/
git commit -m "feat(frontend): add AgentSelector component

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Update MatchingTestPage to Use AgentSelector

**Files:**
- Modify: `frontend/src/pages/MatchingTest/components/ActionPanel.tsx`
- Modify: `frontend/src/pages/MatchingTest/MatchingTestPage.tsx`

**Step 1: Add AgentSelector to ActionPanel**

Modify `frontend/src/pages/MatchingTest/components/ActionPanel.tsx`:

Add imports at top:

```typescript
import { AgentSelector } from '@/components/AgentSelector'
```

Add new props to the interface:

```typescript
interface ActionPanelProps {
  jobId: string | null
  jobStatus: string
  selectedBidId: string | null
  workerId: string | null
  selectedAgentId: string | null  // New
  onAgentChange: (agentId: string) => void  // New
  onActionComplete: () => void
}
```

Update the component to use selectedAgentId:

```typescript
const ActionPanel = ({
  jobId,
  jobStatus,
  selectedBidId,
  workerId,
  selectedAgentId,  // New
  onAgentChange,    // New
  onActionComplete,
}: ActionPanelProps) => {
  // ... existing code ...

  // Update handleGrabOrder to use selectedAgentId
  const handleGrabOrder = async () => {
    if (!jobId || !selectedAgentId) {
      message.warning('请先选择接单 Agent')
      return
    }

    try {
      setLoading('grab')
      await matchingApi.grabOrder(jobId, {
        worker_id: selectedAgentId,  // Use selected agent
        proposal: TEST_FIXTURES.DEFAULT_PROPOSAL,
        quote: TEST_FIXTURES.DEFAULT_QUOTE,
      })
      message.success('抢单成功')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to grab order:', err)
      const errorMsg = err?.response?.data?.detail || '抢单失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Add AgentSelector UI before the buttons
  // In the render, add before the button grid:
  return (
    <>
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">操作面板</h3>

        {/* Agent Selector */}
        <div className="mb-4">
          <label className="block text-sm text-slate-300 mb-2">
            接单 Agent
          </label>
          <AgentSelector
            value={selectedAgentId || undefined}
            onChange={onAgentChange}
            placeholder="选择要使用的 Agent"
          />
        </div>

        {/* Button grid - existing code */}
        <div className="grid grid-cols-4 gap-3">
          {/* ... existing buttons ... */}
        </div>

        {/* ... rest of component ... */}
      </div>
    </>
  )
}
```

**Step 2: Update MatchingTestPage to manage selectedAgentId state**

Modify `frontend/src/pages/MatchingTest/MatchingTestPage.tsx`:

```typescript
// Add state for selectedAgentId
const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)

// Pass to ActionPanel
<ActionPanel
  jobId={selectedJobId}
  jobStatus={selectedJob?.status || ''}
  selectedBidId={selectedBidId}
  workerId={selectedBid?.worker_id || null}
  selectedAgentId={selectedAgentId}
  onAgentChange={setSelectedAgentId}
  onActionComplete={fetchJobs}
/>
```

**Step 3: Commit**

```bash
git add frontend/src/pages/MatchingTest/
git commit -m "feat(frontend): integrate AgentSelector in MatchingTestPage

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Add Frontend API Method

**Files:**
- Modify: `frontend/src/services/api.ts`

**Step 1: Add users API**

Add to `frontend/src/services/api.ts`:

```typescript
// Users API
export const usersApi = {
  getMyAgents: () => api.get('/users/me/agents'),
}
```

Export at the bottom:

```typescript
export { usersApi }
```

**Step 2: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat(frontend): add usersApi.getMyAgents method

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 9: Run Migration and Test

**Step 1: Run database migration**

```bash
cd backend && uv run alembic upgrade head
```

**Step 2: Start backend server**

```bash
cd backend && uv run uvicorn src.main:app --reload
```

**Step 3: Start frontend server**

```bash
cd frontend && npm run dev
```

**Step 4: Test the flow**

1. Login to the application
2. Navigate to Matching Test page
3. Create a job with an employer agent
4. Try to grab the order:
   - Select an agent from the dropdown
   - Click "抢单" button
   - Verify: should succeed if agent belongs to user
   - Verify: should fail if trying to use agent that doesn't belong to user
   - Verify: should fail if agent is the employer of the job

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete agent selection for bidding feature

- Add role field to AdminUser
- Add owner_id to Agent with foreign key
- Add GET /users/me/agents endpoint
- Add validation in grab_order for agent ownership
- Add AgentSelector component with useAgentList hook
- Integrate AgentSelector in MatchingTestPage

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

| Phase | Tasks | Files Changed |
|-------|-------|---------------|
| 1. Database | Task 1, 2 | db_models.py, alembic migration, agents.py |
| 2. Backend API | Task 3, 4, 5 | users.py, matching.py, auth.py, jwt_config.py |
| 3. Frontend | Task 6, 7, 8 | AgentSelector/*, ActionPanel.tsx, MatchingTestPage.tsx, api.ts |
| 4. Testing | Task 9 | Migration + manual testing |