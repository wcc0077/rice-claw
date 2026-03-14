"""Database access layer for agents using SQLAlchemy 2.0."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models.db_models import Agent
from ..models.schemas import AgentCreate
from ..auth.agent_auth import generate_api_key, hash_api_key, verify_api_key


def create_agent(db: Session, agent: AgentCreate) -> Agent:
    """创建新代理

    Args:
        db: 数据库会话
        agent: 代理创建数据

    Returns:
        创建的代理对象

    Raises:
        ValueError: 代理ID已存在
    """
    # 检查是否存在
    existing = db.execute(
        select(Agent).where(Agent.agent_id == agent.agent_id)
    ).scalar_one_or_none()

    if existing:
        raise ValueError(f"Agent {agent.agent_id} already exists")

    # 创建新记录
    db_agent = Agent(
        agent_id=agent.agent_id,
        agent_type=agent.agent_type,
        name=agent.name,
        capabilities=",".join(agent.capabilities) if agent.capabilities else "",
        description=agent.description,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
    """获取单个代理

    Args:
        db: 数据库会话
        agent_id: 代理ID

    Returns:
        代理对象或 None
    """
    return db.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    ).scalar_one_or_none()


def get_agent_dict(db: Session, agent_id: str) -> Optional[Dict[str, Any]]:
    """获取单个代理（字典格式）

    Args:
        db: 数据库会话
        agent_id: 代理ID

    Returns:
        代理字典或 None
    """
    agent = get_agent(db, agent_id)
    return agent.to_dict() if agent else None


def list_agents(
    db: Session,
    status: Optional[str] = None,
    capability: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    """列出代理

    Args:
        db: 数据库会话
        status: 状态筛选
        capability: 技能筛选
        page: 页码
        limit: 每页数量

    Returns:
        包含 agents 和 pagination 的字典
    """
    # 构建查询
    query = select(Agent)
    count_query = select(func.count()).select_from(Agent)

    # 添加筛选条件
    conditions = []
    if status:
        conditions.append(Agent.status == status)
    if capability:
        conditions.append(Agent.capabilities.like(f"%{capability}%"))

    if conditions:
        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)

    # 获取总数
    total = db.execute(count_query).scalar()

    # 分页
    offset = (page - 1) * limit
    query = query.limit(limit).offset(offset)

    # 执行查询
    agents = db.execute(query).scalars().all()

    return {
        "agents": [agent.to_dict() for agent in agents],
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": offset + limit < total,
        },
    }


def update_agent_status(db: Session, agent_id: str, status: str) -> Optional[Agent]:
    """更新代理状态

    Args:
        db: 数据库会话
        agent_id: 代理ID
        status: 新状态 ('idle' | 'busy' | 'offline')

    Returns:
        更新后的代理对象或 None

    Raises:
        ValueError: 无效的状态值
    """
    valid_statuses = ["idle", "busy", "offline"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}")

    agent = get_agent(db, agent_id)
    if not agent:
        return None

    agent.status = status
    db.commit()
    db.refresh(agent)
    return agent


def update_agent_rating(db: Session, agent_id: str, rating: float) -> Optional[Agent]:
    """更新代理评分

    计算新的平均评分并增加完成任务数

    Args:
        db: 数据库会话
        agent_id: 代理ID
        rating: 新评分 (0-5)

    Returns:
        更新后的代理对象或 None
    """
    agent = get_agent(db, agent_id)
    if not agent:
        return None

    # 计算新的平均评分
    current_rating = float(agent.rating)
    completed_jobs = agent.completed_jobs
    new_rating = (current_rating * completed_jobs + rating) / (completed_jobs + 1)

    agent.rating = round(new_rating, 2)
    agent.completed_jobs = completed_jobs + 1
    db.commit()
    db.refresh(agent)
    return agent


# =============================================================================
# API Key Authentication Functions
# =============================================================================

def get_agent_by_api_key(db: Session, api_key: str) -> Optional[Agent]:
    """Get an agent by their API key.

    This function validates the API key against the stored hash and returns
    the agent if the key is valid.

    Args:
        db: Database session
        api_key: The plain text API key to validate

    Returns:
        Agent object if API key is valid, None otherwise
    """
    # Get all agents with API keys (we need to check hashes)
    agents_with_keys = db.execute(
        select(Agent).where(Agent.api_key_hash.isnot(None))
    ).scalars().all()

    for agent in agents_with_keys:
        if agent.api_key_hash and verify_api_key(api_key, agent.api_key_hash):
            return agent

    return None


def update_last_seen(db: Session, agent_id: str) -> Optional[Agent]:
    """Update the last_seen_at timestamp for an agent.

    Called after each authenticated API/MCP request.

    Args:
        db: Database session
        agent_id: The agent's ID

    Returns:
        Updated agent object or None if not found
    """
    agent = get_agent(db, agent_id)
    if not agent:
        return None

    agent.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(agent)
    return agent


def set_agent_api_key(db: Session, agent_id: str, test: bool = False) -> Optional[Dict[str, Any]]:
    """Generate and set a new API key for an agent.

    This function generates a new API key, hashes it for storage,
    and returns the plain text key (only shown once).

    Args:
        db: Database session
        agent_id: The agent's ID
        test: If True, generate a test key instead of a live key

    Returns:
        Dict with agent_id and the new api_key (plain text), or None if agent not found

    Warning:
        The plain text API key is only returned once. Store it securely!
    """
    agent = get_agent(db, agent_id)
    if not agent:
        return None

    # Generate new API key
    new_api_key = generate_api_key(test=test)
    api_key_hash = hash_api_key(new_api_key)

    # Store hash and timestamp
    now = datetime.now(timezone.utc)
    agent.api_key_hash = api_key_hash
    agent.api_key_created_at = now
    db.commit()
    db.refresh(agent)

    return {
        "agent_id": agent_id,
        "api_key": new_api_key,  # Plain text - only shown once!
        "created_at": now.isoformat(),
    }


def regenerate_agent_api_key(db: Session, agent_id: str) -> Optional[Dict[str, Any]]:
    """Regenerate an agent's API key (alias for set_agent_api_key).

    Invalidates the old key and generates a new one.

    Args:
        db: Database session
        agent_id: The agent's ID

    Returns:
        Dict with agent_id and the new api_key (plain text), or None if agent not found
    """
    return set_agent_api_key(db, agent_id)


def revoke_agent_api_key(db: Session, agent_id: str) -> bool:
    """Revoke an agent's API key.

    Args:
        db: Database session
        agent_id: The agent's ID

    Returns:
        True if revoked, False if agent not found
    """
    agent = get_agent(db, agent_id)
    if not agent:
        return False

    agent.api_key_hash = None
    agent.api_key_created_at = None
    db.commit()
    return True


def verify_agent(db: Session, agent_id: str) -> Optional[Agent]:
    """Mark an agent as verified.

    Args:
        db: Database session
        agent_id: The agent's ID

    Returns:
        Updated agent or None if not found
    """
    agent = get_agent(db, agent_id)
    if not agent:
        return None

    agent.is_verified = True
    db.commit()
    db.refresh(agent)
    return agent


def delete_agent(db: Session, agent_id: str) -> bool:
    """删除代理

    Args:
        db: 数据库会话
        agent_id: 代理ID

    Returns:
        是否删除成功
    """
    agent = get_agent(db, agent_id)
    if not agent:
        return False

    db.delete(agent)
    db.commit()
    return True


# =============================================================================
# 向后兼容的函数（旧版 API，内部转换为 SQLAlchemy）
# =============================================================================

def row_to_agent(row) -> Dict[str, Any]:
    """向后兼容：将数据库行转换为字典

    注意：此函数保留用于向后兼容，新代码应使用 agent.to_dict()
    """
    if hasattr(row, 'to_dict'):
        return row.to_dict()
    # 如果传入的是 sqlite3.Row
    capabilities = row["capabilities"] or ""
    return {
        "agent_id": row["agent_id"],
        "agent_type": row["agent_type"],
        "name": row["name"],
        "capabilities": capabilities.split(",") if capabilities else [],
        "description": row["description"],
        "status": row["status"],
        "rating": float(row["rating"]),
        "completed_jobs": row["completed_jobs"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }