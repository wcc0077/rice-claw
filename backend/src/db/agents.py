"""Database access layer for agents."""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import get_connection
from ..models.schemas import AgentCreate, AgentUpdate, AgentResponse


def row_to_agent(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row to agent dict."""
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


def create_agent(agent: AgentCreate) -> Dict[str, Any]:
    """Create a new agent."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if agent already exists
    cursor.execute("SELECT agent_id FROM agents WHERE agent_id = ?", (agent.agent_id,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Agent {agent.agent_id} already exists")

    # Insert new agent
    capabilities_json = ",".join(agent.capabilities) if agent.capabilities else ""

    cursor.execute("""
        INSERT INTO agents (agent_id, agent_type, name, capabilities, description, status)
        VALUES (?, ?, ?, ?, ?, 'idle')
    """, (agent.agent_id, agent.agent_type, agent.name, capabilities_json, agent.description))

    conn.commit()
    conn.close()

    return {
        "agent_id": agent.agent_id,
        "agent_type": agent.agent_type,
        "name": agent.name,
        "capabilities": agent.capabilities,
        "description": agent.description,
        "status": "idle",
        "rating": 0.0,
        "completed_jobs": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row_to_agent(row)
    return None


def update_agent_status(agent_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update agent status."""
    valid_statuses = ["idle", "busy", "offline"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE agents SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE agent_id = ?
    """, (status, agent_id))

    conn.commit()

    # Return updated agent
    cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row_to_agent(row)
    return None


def list_agents(
    status: Optional[str] = None,
    capability: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    """List agents with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    # Build query
    query = "SELECT * FROM agents"
    count_query = "SELECT COUNT(*) FROM agents"
    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if capability:
        conditions.append("capabilities LIKE ?")
        params.append(f"%{capability}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        count_query += " WHERE " + " AND ".join(conditions)

    # Get total count
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Get paginated results
    offset = (page - 1) * limit
    cursor.execute(query + " LIMIT ? OFFSET ?", params + [limit, offset])

    agents = [row_to_agent(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "agents": agents,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": offset + limit < total,
        },
    }


def update_agent_rating(agent_id: str, rating: float) -> Optional[Dict[str, Any]]:
    """Update agent rating and increment completed jobs."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get current rating and completed_jobs
    cursor.execute("""
        SELECT rating, completed_jobs FROM agents WHERE agent_id = ?
    """, (agent_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Calculate new average rating
    current_rating = float(row["rating"])
    completed_jobs = row["completed_jobs"]
    new_rating = (current_rating * completed_jobs + rating) / (completed_jobs + 1)

    cursor.execute("""
        UPDATE agents
        SET rating = ?, completed_jobs = completed_jobs + 1, updated_at = CURRENT_TIMESTAMP
        WHERE agent_id = ?
    """, (round(new_rating, 2), agent_id))

    conn.commit()

    # Return updated agent
    cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_agent(row) if row else None
