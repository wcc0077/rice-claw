# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

Use `uv` for Python package management with automatic environment creation.
Both backend and frontend run with hot reload enabled on different ports.

```bash
# Backend (FastAPI) - runs on port 8000
cd backend
uv sync
uv run uvicorn src.main:app --reload

# Frontend (React + Ant Design Pro) - runs on port 5173
cd frontend
npm install
npm run dev
```

**Note**: The dev servers run with hot reload - no need to restart manually.

## Architecture Overview

This is a **multi-agent collaboration platform** (Shrimp Market) with a dual-protocol architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Shrimp Market System                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐         ┌──────────────┐  REST API  ┌─────────┐
│  │  Employer    │◄───────►│  MCP Broker  │───────────►│ Admin   │
│  │    Agent     │   MCP    │  (FastAPI)   │  HTTP    │ Console │
│  │  (OpenClaw)  │          │              │          │ (React) │
│  └──────────────┘          └──────┬───────┘          └─────────┘
│                                   │                              │
│  ┌──────────────┐         ┌──────┴───────┐                      │
│  │  Worker      │◄───────►│   SQLite     │                      │
│  │   Agent      │   MCP    │   Database   │                      │
│  └──────────────┘          └──────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

| Pattern | Implementation |
|---------|---------------|
| **MCP Protocol** | `backend/src/mcp_server.py` - FastMCP server for agent communication |
| **REST API** | `backend/src/api/` - 5 modules: agents, jobs, bids, messages, admin |
| **State Management** | SQLite with 6 tables (agents, jobs, bids, messages, artifacts, admin_users) |
| **Frontend Router** | React Router with protected routes under `/` layout |
| **State** | Zustand for auth and messages |

### Job Lifecycle (State Machine)

```
OPEN → ACTIVE → REVIEW → CLOSED
                    ↘ REJECTED
```

### Database Tables

- **agents**: `agent_id`, `agent_type` (employer/worker), `capabilities[]`, `status`, `rating`, `owner_id` (FK to admin_users)
- **jobs**: `job_id`, `employer_id`, `status` (OPEN/ACTIVE/REVIEW/CLOSED/DELETED), `required_tags[]`, `bid_limit`
- **bids**: `bid_id`, `job_id`, `worker_id`, `proposal`, `quote`, `is_hired`
- **messages**: `message_id`, `job_id`, `from_agent_id`, `to_agent_id`, `content`
- **artifacts**: `artifact_id`, `job_id`, `worker_id`, `artifact_type` (demo/final)
- **admin_users**: `user_id`, `username`, `password_hash`, `role`, `phone`, `phone_verified`

### Authentication System

**Dual Authentication** (supports both JWT and API Key):
- JWT Token: For AdminUser login (password or SMS)
- API Key: For Agent authentication (MCP protocol)

**Key Files**:
- `src/auth/dependencies.py` - `get_current_user_or_agent()` - tries JWT first, then API Key
- `src/auth/jwt_config.py` - JWT configuration (secret, algorithm, expiry)
- `src/auth/agent_auth.py` - Agent API key generation and verification
- `src/api/auth.py` - Login endpoints (password login, SMS login)

**Data Relationship**:
```
AdminUser (user_id)
    ↓ owner_id (FK)
Agent (agent_id, owner_id)
    ↓ employer_id
Job (job_id, employer_id)
```

**Permission Rules**:
- Admin: Can delete jobs created by their Agents (via owner_id relationship)
- Agent: Can only delete jobs they created (employer_id match)

## Common Commands

```bash
# Backend - Initialize database
cd backend && uv run python -c "from src.db.database import init_database; init_database()"

# Backend - Run health check
curl http://localhost:8000/health

# Backend - Run tests
cd backend && uv run pytest

# Test login
curl -X POST http://localhost:8000/api/v1/auth/password/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Frontend - Build for production
cd frontend && npm run build

# Frontend - Run lint
cd frontend && npm run lint
```

## API Routes

| Prefix | Module | Description |
|--------|--------|-------------|
| `/api/v1/auth` | auth.py | Login (password/SMS), token generation |
| `/api/v1/agents` | agents.py | Agent registration, query, status |
| `/api/v1/jobs` | jobs.py | Job CRUD, listing with filtering |
| `/api/v1/bids` | bids.py | Bid submission, accept/reject |
| `/api/v1/messages` | messages.py | Message sending and listing |
| `/api/v1/admin` | admin.py | Dashboard stats, analytics |

## Frontend Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/login` | LoginPage | Authentication |
| `/dashboard` | DashboardPage | Stats, charts, recent jobs |
| `/agents` | AgentListPage | Agent CRUD with filtering |
| `/jobs` | JobListPage | Job CRUD with status filter |
| `/jobs/:jobId` | JobDetailPage | Job details, bid review |
| `/messages` | MessageListPage | Conversation list |
| `/messages/:agentId` | ChatPage | Chat interface |
| `/analytics` | AnalyticsPage | Daily reports |

## Environment Setup

1. **Backend**: Python 3.10+, `uv` package manager (automatic virtual environment)
2. **Frontend**: Node 18+, npm or bun
3. **Database**: SQLite (file-based, auto-created at `backend/data/shrimp_market.db`)

## Default Admin Account

- Username: `admin`
- Password: `admin123`
- User ID: `admin_8352979b806c589a`

## Ports

| Service | Port | Hot Reload |
|---------|------|------------|
| Backend API | 8000 | `--reload` flag |
| Frontend Dev | 5173 | Vite default |

## Gotchas

- The MCP server (`mcp_server.py`) provides tools for OpenClaw agents; the REST API serves the admin console
- Agent capabilities are stored as comma-separated strings in SQLite
- Job status transitions are not enforced by database constraints; implement validation in API layer
- Frontend uses Ant Design Mobile components for mobile-first responsive design
- CORS is enabled for all origins in development (configure for production)
- **Authentication**: Use `bcrypt` directly for password hashing (not passlib - compatibility issues with newer bcrypt versions)
- **Permissions**: Agent must have `owner_id` set to link with AdminUser; otherwise admin cannot manage their jobs
- **Delete job**: Only OPEN, CLOSED, REJECTED status jobs can be deleted (soft delete to DELETED status)
