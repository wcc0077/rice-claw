"""User-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..db.database import get_db
from ..db import agents as agent_dal
from ..models.schemas import AgentResponse
from ..auth import JWT_SECRET_KEY, JWT_ALGORITHM

router = APIRouter()

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Extract user ID from JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return str(user_id)
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