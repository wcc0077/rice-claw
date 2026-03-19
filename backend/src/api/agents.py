"""Agent management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from ..db.database import get_db
from ..db import agents as agent_dal
from ..db import bids as bid_dal
from ..models.schemas import AgentCreate, AgentUpdate, AgentEdit, AgentResponse, AgentListResponse
from ..models.db_models import AdminUser
from ..auth.dependencies import get_current_admin_user, get_current_admin_user_with_role, get_current_user, get_current_agent

router = APIRouter()


@router.post("", response_model=AgentResponse)
async def register_agent(
    request: AgentCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Register a new agent (requires authentication).

    The agent will be owned by the current user.
    """
    try:
        # 设置 owner_id 为当前登录用户
        request.owner_id = current_user.user_id
        agent = agent_dal.create_agent(db, request)
        return AgentResponse(**agent.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_endpoint(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get agent information."""
    agent = agent_dal.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**agent.to_dict())


@router.put("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status_endpoint(
    agent_id: str,
    request: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update agent status."""
    if not request.status:
        raise HTTPException(status_code=400, detail="Status is required")

    try:
        agent = agent_dal.update_agent_status(db, agent_id, request.status)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        return AgentResponse(**agent.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=AgentListResponse)
async def list_agents_endpoint(
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """List agents owned by the current user."""
    if page < 1:
        page = 1
    if limit > 100:
        limit = 100

    result = agent_dal.list_agents(
        db,
        owner_id=current_user.user_id,  # 只返回当前用户的 agents
        status=status,
        page=page,
        limit=limit
    )
    return AgentListResponse(**result)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent_endpoint(
    agent_id: str,
    request: AgentEdit,
    db: Session = Depends(get_db)
):
    """Update agent details (name, capabilities, description)."""
    agent = agent_dal.update_agent(
        db, agent_id,
        name=request.name,
        capabilities=request.capabilities,
        description=request.description
    )
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**agent.to_dict())


@router.delete("/{agent_id}")
async def delete_agent_endpoint(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Delete an agent with all related data (hard delete).

    Users can only delete their own agents.

    This permanently deletes the agent and all associated data:
    - Jobs (as employer) with bids, messages, artifacts, payments
    - Bids (as worker)
    - Messages (sent and received)
    - Artifacts and artifact versions
    - Payments, WebSocket connections, reputation logs, audit logs

    Warning: This operation cannot be undone!
    """
    # 验证 agent 属于当前用户
    agent = agent_dal.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    if agent.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own agents")

    try:
        success = agent_dal.delete_agent(db, agent_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        return {"agent_id": agent_id, "deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# API Key Management Endpoints
# ============================================================

@router.post("/{agent_id}/api-key")
async def generate_api_key_endpoint(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Generate a new API key for an agent.

    Users can only generate keys for their own agents.
    The API key is only returned once - store it securely!

    Returns:
        Dict containing agent_id and the new api_key (plain text)

    Warning:
        The plain text API key is only shown once. Store it securely!
    """
    # 验证 agent 属于当前用户
    agent = agent_dal.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    if agent.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only manage your own agents")

    result = agent_dal.set_agent_api_key(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return result


@router.post("/{agent_id}/api-key/regenerate")
async def regenerate_api_key_endpoint(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Regenerate an agent's API key.

    Users can only regenerate keys for their own agents.
    The API key is only returned once - store it securely!

    Returns:
        Dict containing agent_id and the new api_key (plain text)
    """
    # 验证 agent 属于当前用户
    agent = agent_dal.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    if agent.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only manage your own agents")

    result = agent_dal.regenerate_agent_api_key(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return result


@router.delete("/{agent_id}/api-key")
async def revoke_api_key_endpoint(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Revoke an agent's API key.

    Users can only revoke keys for their own agents.
    The agent will no longer be able to authenticate until a new key is generated.
    """
    # 验证 agent 属于当前用户
    agent = agent_dal.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    if agent.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only manage your own agents")

    success = agent_dal.revoke_agent_api_key(db, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {"agent_id": agent_id, "api_key_revoked": True}


@router.post("/{agent_id}/verify")
async def verify_agent_endpoint(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Mark an agent as verified.

    Users can only verify their own agents.
    This should be called after confirming identity and securely storing the API key.
    """
    # 验证 agent 属于当前用户
    agent = agent_dal.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    if agent.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only manage your own agents")

    agent = agent_dal.verify_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {"agent_id": agent_id, "is_verified": True}


# ============================================================
# Reputation Endpoints
# ============================================================

@router.get("/{agent_id}/reputation")
async def get_reputation_endpoint(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get agent's reputation detail with score breakdown.

    Returns total score, level, and breakdown by dimension:
    - fulfillment: based on completed/cancelled orders
    - quality: based on employer ratings
    - activity: based on recent 30-day orders
    """
    detail = agent_dal.get_agent_reputation_detail(db, agent_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return detail


@router.get("/{agent_id}/reputation/logs")
async def get_reputation_logs_endpoint(
    agent_id: str,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get agent's reputation change history.

    Returns paginated list of reputation change events.
    """
    result = agent_dal.get_agent_reputation_logs(db, agent_id, page=page, limit=limit)
    return result


# =============================================================================
# OpenClaw Skill API Endpoints - "me" routes for authenticated agents
# =============================================================================


@router.get("/me", response_model=AgentResponse)
async def get_current_agent_endpoint(
    current_agent = Depends(get_current_agent)
):
    """Get the current authenticated agent's information."""
    return AgentResponse(**current_agent.to_dict())


@router.put("/me/capabilities", response_model=AgentResponse)
async def update_current_agent_capabilities(
    capabilities: List[str],
    name: str | None = None,
    current_agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Update the current agent's capabilities.

    Workers use this to register their skills and receive matching job notifications.
    """
    agent = agent_dal.update_agent(
        db,
        current_agent.agent_id,
        name=name,
        capabilities=capabilities
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(**agent.to_dict())


@router.put("/me/status", response_model=AgentResponse)
async def update_current_agent_status(
    status: str,
    current_agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Update the current agent's availability status.

    Valid statuses: 'idle', 'busy', 'offline'
    """
    valid_statuses = ["idle", "busy", "offline"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    agent = agent_dal.update_agent_status(db, current_agent.agent_id, status)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(**agent.to_dict())


@router.get("/me/bids")
async def get_current_agent_bids_endpoint(
    current_agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get all bids submitted by the current agent.

    Workers use this to track their bid status across all jobs.
    """
    bids = bid_dal.get_bids_by_worker(db, current_agent.agent_id)
    return {
        "bids": bids,
        "total": len(bids),
        "agent_id": current_agent.agent_id
    }