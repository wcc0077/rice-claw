"""Agent management endpoints."""

import time

from fastapi import APIRouter, HTTPException

from ..db.agents import create_agent, get_agent, update_agent_status, list_agents
from ..models.schemas import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse

router = APIRouter()


@router.post("", response_model=AgentResponse)
async def register_agent(request: AgentCreate):
    """Register a new agent."""
    try:
        agent = create_agent(request)
        return AgentResponse(**agent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_endpoint(agent_id: str):
    """Get agent information."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**agent)


@router.put("/{agent_id}/status", response_model=AgentResponse)
async def update_agent_status_endpoint(agent_id: str, request: AgentUpdate):
    """Update agent status."""
    if not request.status:
        raise HTTPException(status_code=400, detail="Status is required")

    agent = update_agent_status(agent_id, request.status)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AgentResponse(**agent)


@router.get("", response_model=AgentListResponse)
async def list_agents_endpoint(status: str | None = None, page: int = 1, limit: int = 20):
    """List agents."""
    if page < 1:
        page = 1
    if limit > 100:
        limit = 100

    result = list_agents(status=status, page=page, limit=limit)
    return AgentListResponse(**result)
