"""Agent management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db import agents as agent_dal
from ..models.schemas import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse

router = APIRouter()


@router.post("", response_model=AgentResponse)
async def register_agent(
    request: AgentCreate,
    db: Session = Depends(get_db)
):
    """Register a new agent."""
    try:
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
    db: Session = Depends(get_db)
):
    """List agents."""
    if page < 1:
        page = 1
    if limit > 100:
        limit = 100

    result = agent_dal.list_agents(db, status=status, page=page, limit=limit)
    return AgentListResponse(**result)


# ============================================================
# API Key Management Endpoints
# ============================================================

@router.post("/{agent_id}/api-key")
async def generate_api_key_endpoint(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Generate a new API key for an agent.

    This endpoint should be called by admins to generate API keys
    for agents. The API key is only returned once - store it securely!

    Returns:
        Dict containing agent_id and the new api_key (plain text)

    Warning:
        The plain text API key is only shown once. Store it securely!
    """
    result = agent_dal.set_agent_api_key(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return result


@router.post("/{agent_id}/api-key/regenerate")
async def regenerate_api_key_endpoint(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Regenerate an agent's API key.

    Invalidates the old key and generates a new one.
    The API key is only returned once - store it securely!

    Returns:
        Dict containing agent_id and the new api_key (plain text)
    """
    result = agent_dal.regenerate_agent_api_key(db, agent_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return result


@router.delete("/{agent_id}/api-key")
async def revoke_api_key_endpoint(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Revoke an agent's API key.

    The agent will no longer be able to authenticate until a new key is generated.
    """
    success = agent_dal.revoke_agent_api_key(db, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {"agent_id": agent_id, "api_key_revoked": True}


@router.post("/{agent_id}/verify")
async def verify_agent_endpoint(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Mark an agent as verified.

    This should be called after the agent owner has confirmed
    their identity and the API key has been securely delivered.
    """
    agent = agent_dal.verify_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {"agent_id": agent_id, "is_verified": True}