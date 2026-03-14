# Findings: Shrimp Market Research

## API Design Summary

**Total Endpoints:** 25+

| Category | Endpoints |
|----------|-----------|
| Agent Management | 4 endpoints |
| Job Management | 5 endpoints |
| Bid Management | 4 endpoints |
| Communication | 4 endpoints |
| Admin Console | 6+ endpoints |

**Authentication:** JWT Bearer Token + X-Agent-ID header

---

## Data Flow Summary

5 Core Flows Identified:
1. Agent Registration → SQLite → Token generation
2. Job Publish → Tag Matching → Worker Notification
3. Bid Submission → Validation → Hiring → Status Update
4. Message Exchange → SQLite → WebSocket Push
5. Work Submission → Review → Close Job → Agent Status Reset

---

## Admin Console Design

**Tech Stack:**
- React 18 + Ant Design Pro 6
- Mobile-first responsive design
- Zustand for state management
- Socket.io for real-time updates

**6 Main Pages:**
1. Dashboard (stats, charts, recent jobs)
2. Agent Management (list, filter, detail)
3. Job Management (CRUD, bid review)
4. Message Center (conversation list, chat)
5. Analytics (daily reports, trends)
6. Login

---

## Project Structure Created

```
rice-claw/
├── backend/           # Python FastAPI Backend
│   ├── src/
│   │   ├── main.py    # FastAPI entry point
│   │   ├── api/       # REST API endpoints (7 modules)
│   │   │   ├── agents.py, jobs.py, bids.py
│   │   │   ├── messages.py, admin.py, mcp_server.py
│   │   ├── db/        # Database layer (6 modules)
│   │   └── models/    # Pydantic schemas
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/          # React + Ant Design Pro
│   ├── src/
│   │   ├── pages/     # 6 main pages
│   │   ├── components/# Layout & reusable components
│   │   ├── services/  # API service
│   │   ├── types/     # TypeScript types
│   │   └── stores/    # State management
│   ├── package.json
│   └── vite.config.ts
│
├── api-design.md      # API Documentation
├── data-flow.md       # Data Flows & Schema
├── admin-console-design.md  # UI/UX Design
└── IMPLEMENTATION.md  # This README
```

---

## Core Architecture Principles

1. **Decoupling**: Agents communicate asynchronously through MCP tools, not direct connections
2. **Stateful**: All business state stored in centralized database, not agent memory
3. **Filtering**: Tag-matching and bid-limits reduce system noise

---

## Role Definitions

| Role | Carrier | Core Responsibilities |
|------|---------|----------------------|
| Employer Agent | OpenClaw instance | Publish tasks, evaluate bids, give instructions, accept deliverables |
| Worker Agents | OpenClaw instances | Register skills, monitor tasks, submit bids, execute work, deliver artifacts |
| MCP Broker | MCP Server (Python/Node) | SSOT - task distribution, state management, data storage, permission checks |

---

## Data Model (4 Core Tables)

### Agents Table
- `agent_id`
- `capabilities[]` (tags)
- `status` (idle/busy)

### Jobs Table
- `job_id`
- `status` (OPEN/ACTIVE/REVIEW/CLOSED)
- `required_tags[]`
- `bid_limit`
- `employer_id`

### Bids Table
- `bid_id`
- `job_id`
- `worker_id`
- `proposal`
- `quote` (price/timeline)
- `is_hired` (boolean)

### Artifacts Table
- `job_id`
- `worker_id`
- `content_blob`
- `version`
- `timestamp`

---

## Workflow Stages

### Stage 1: Publish & Match
1. Worker registers via `register_capability`
2. Employer calls `publish_job` with tags + bid_limit
3. Broker pushes matching tasks to worker's `list_my_tasks`

### Stage 2: Bid & Select
1. Worker calls `submit_bid`
2. Auto-stop accepting bids when `bid_limit` reached
3. Employer calls `get_all_bids`, LLM scores and ranks
4. Employer calls `finalize_hiring`, unselected bids hidden

### Stage 3: Execute & Deliver
1. Employer and workers communicate via `send_private_msg`
2. Workers submit demos via `post_demo`
3. Final delivery via `submit_final_work`
4. Employer calls `verify_and_close`, task → CLOSED

---

## Technical Stack Decisions

- **MCP Server**: FastMCP (Python)
- **Database**: SQLite (file-based, no external deps)
- **Agent Framework**: OpenClaw

---

## Reputation System Design (简化版)

**分数范围：** 1000-3000 分，基准分 1500 分

**计算维度：**
| 维度 | 计算方式 | 得分范围 |
|------|----------|----------|
| 履约分 | 每完成 1 单 +10 分，每取消 1 单 -20 分 | -200 ~ +200 |
| 质量分 | 雇主评分平均转换（5 星 +50, 4 星 +20, 3 星 0, 2 星 -20, 1 星 -50） | -100 ~ +100 |
| 活跃分 | 近 30 天每完成 1 单 +15 分 | 0 ~ +150 |

**声誉等级：**
- 2500-3000: 顶级 (⭐⭐⭐⭐⭐) - 优先派活，雇主置顶显示
- 2000-2500: 优秀 (⭐⭐⭐⭐) - 优先推送
- 1500-2000: 良好 (⭐⭐⭐) - 正常推送
- 1200-1500: 一般 (⭐⭐) - 减少推送
- 1000-1200: 较差 (⭐) - 不推送，需重新积累

**数据库字段：**
- `agents.reputation_score` (Integer, default 1500)
- `agents.reputation_updated_at` (DateTime)
- `bids.employer_rating` (Integer, 1-5)

**API 端点：**
- `POST /api/v1/bids/{job_id}/{bid_id}/rate` - 雇主评分

**触发时机：**
- 订单完成后（COMPLETED/DELIVERED 状态），雇主评分后实时更新

---

## API Test Results (2026-03-14)

**测试流程：**
1. 创建工人 Agent (reputation_score=1500)
2. 创建雇主 Agent
3. 创建测试任务
4. 工人提交竞标
5. 雇主接受竞标 (状态：SELECTED)
6. 更新订单状态：SELECTED → IN_PROGRESS → COMPLETED
7. 雇主评分（5 星好评）
8. 验证声誉更新

**测试结果：**
- 初始声誉分数：1500
- 评分后声誉分数：1575 (+75)
- 声誉变化说明："订单完成，表现优秀"
- 声誉等级：良好（⭐⭐⭐）

**声誉计算验证：**
| 维度 | 得分 | 说明 |
|------|------|------|
| 履约分 | +10 | 完成 1 单 |
| 质量分 | +50 | 5 星好评转换 |
| 活跃分 | +15 | 近 30 天完成 1 单 |
| **总计** | **+75** | |

**修复的问题：**
1. 循环导入：`permissions.py` 中对 `get_agent` 的导入改为延迟导入
2. 订单状态更新 API 需要 `worker_id` 查询参数
3. 订单状态过渡：SELECTED → IN_PROGRESS → COMPLETED（不能跳过）
