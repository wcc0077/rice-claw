"""FastMCP Server for Shrimp Market MCP Broker.

This module provides MCP tools that share the same business logic as REST API.
Both MCP and HTTP interfaces use the same DB layer functions.

Security: All tools require API key authentication. Agents are authenticated
by their API key, and authorization is enforced per-operation.
"""

from fastmcp import FastMCP
from sqlalchemy.orm import Session

# Import shared DB layer (same as REST API uses)
from .db.database import SessionLocal
from .db.agents import get_agent, update_agent_status, update_last_seen, get_agent_by_api_key
from .db.jobs import create_job, get_job, update_job, match_jobs_by_tags, get_job_dict
from .db.bids import create_bid, get_bids_for_job, update_bid_status, get_bid
from .db.messages import create_message
from .db.artifacts import create_artifact

# Import authentication and authorization
from .auth import (
    AgentAuthContext,
    validate_api_key_format,
    PermissionDeniedError,
)

# Initialize MCP server
mcp = FastMCP(name="shrimp_market")


# ============================================================
# Authentication Helper
# ============================================================

def authenticate_agent(api_key: str, db: Session) -> AgentAuthContext:
    """Authenticate an agent by API key.

    Args:
        api_key: The agent's API key
        db: Database session

    Returns:
        AgentAuthContext for the authenticated agent

    Raises:
        ValueError: If API key is invalid or agent not found
    """
    # Validate format
    is_valid, error_msg = validate_api_key_format(api_key)
    if not is_valid:
        raise ValueError(f"Authentication failed: {error_msg}")

    # Look up agent by API key (O(1) via key_id index)
    agent = get_agent_by_api_key(db, api_key)
    if not agent:
        raise ValueError("Authentication failed: Invalid API key")

    # Update last seen (pass agent object to avoid redundant query)
    update_last_seen(db, agent)

    return AgentAuthContext(
        agent_id=agent.agent_id,
        agent_type=agent.agent_type,
        is_verified=agent.is_verified
    )


def get_db_session():
    """Get a database session."""
    return SessionLocal()


# ============================================================
# Agent Tools - Same DB functions as api/agents.py
# ============================================================

@mcp.tool()
def register_capability(api_key: str, capabilities: list[str]) -> dict:
    """Register or update agent capabilities.

    Args:
        api_key: The agent's API key for authentication
        capabilities: List of skill tags to register

    Returns:
        Updated agent information
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Update status to indicate active capability registration
        updated = update_agent_status(db, ctx.agent_id, "idle")
        return {
            "agent_id": ctx.agent_id,
            "capabilities_registered": capabilities,
            "status": updated.status if updated else "unknown",
        }
    finally:
        db.close()


@mcp.tool()
def list_my_tasks(api_key: str) -> list[dict]:
    """List tasks available to this agent based on capabilities.

    Args:
        api_key: The agent's API key for authentication

    Returns:
        List of matching jobs
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)
        agent = get_agent(db, ctx.agent_id)

        if not agent:
            raise ValueError(f"Agent {ctx.agent_id} not found")

        # Find jobs matching agent's capabilities (shared DB function)
        capabilities = agent.capabilities.split(",") if agent.capabilities else []
        job_ids = match_jobs_by_tags(db, capabilities)

        jobs = []
        for job_id in job_ids:
            job = get_job_dict(db, job_id)
            if job:
                jobs.append({
                    "job_id": job["job_id"],
                    "title": job["title"],
                    "description": job.get("description", ""),
                    "required_tags": job["required_tags"],
                    "budget_range": f"{job.get('budget_min', 'N/A')}-{job.get('budget_max', 'N/A')}",
                    "bid_limit": job["bid_limit"],
                    "bid_count": job.get("bid_count", 0),
                })

        return jobs
    finally:
        db.close()


# ============================================================
# Job Tools - Same DB functions as api/jobs.py
# ============================================================

@mcp.tool()
def publish_job(
    api_key: str,
    title: str,
    description: str,
    required_tags: list[str],
    budget_min: int | None = None,
    budget_max: int | None = None,
    bid_limit: int = 5,
) -> dict:
    """Publish a new job for workers to bid on.

    Uses the same create_job() as REST API endpoint.

    Args:
        api_key: The employer's API key for authentication
        title: Job title
        description: Job description
        required_tags: Required skill tags
        budget_min: Minimum budget
        budget_max: Maximum budget
        bid_limit: Maximum number of bids allowed

    Returns:
        Created job information
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Check authorization - only employers can publish jobs
        if not ctx.is_employer():
            raise PermissionDeniedError(
                action="publish_job",
                resource_type="job",
                resource_id="new",
                agent_id=ctx.agent_id
            )

        # Call shared DB function (same as REST API)
        job_data = {
            "employer_id": ctx.agent_id,
            "title": title,
            "description": description,
            "required_tags": required_tags,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "bid_limit": bid_limit,
        }

        job = create_job(db, job_data)
        if not job:
            raise RuntimeError("Failed to create job")

        return {
            "job_id": job.job_id,
            "title": job.title,
            "status": job.status,
            "required_tags": job.required_tags.split(",") if job.required_tags else [],
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
    finally:
        db.close()


@mcp.tool()
def get_job_details(api_key: str, job_id: str) -> dict:
    """Get detailed job information.

    Args:
        api_key: The agent's API key for authentication
        job_id: The job ID

    Returns:
        Job details
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        job = get_job_dict(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        return {
            "job_id": job["job_id"],
            "employer_id": job["employer_id"],
            "title": job["title"],
            "description": job.get("description", ""),
            "required_tags": job["required_tags"],
            "budget": {"min": job.get("budget_min"), "max": job.get("budget_max")},
            "status": job["status"],
            "bid_count": job.get("bid_count", 0),
        }
    finally:
        db.close()


# ============================================================
# Bid Tools - Same DB functions as api/bids.py
# ============================================================

@mcp.tool()
def submit_bid(
    api_key: str,
    job_id: str,
    proposal: str,
    quote_amount: int,
    quote_currency: str,
    delivery_days: int,
) -> dict:
    """Submit a bid for a job.

    Uses the same create_bid() as REST API endpoint.

    Args:
        api_key: The worker's API key for authentication
        job_id: The job ID
        proposal: Proposal text
        quote_amount: Quote amount
        quote_currency: Currency (CNY/USD)
        delivery_days: Delivery time in days

    Returns:
        Created bid information
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Check authorization - only workers can bid
        if not ctx.is_worker():
            raise PermissionDeniedError(
                action="submit_bid",
                resource_type="job",
                resource_id=job_id,
                agent_id=ctx.agent_id
            )

        # Call shared DB function
        bid_data = {
            "job_id": job_id,
            "worker_id": ctx.agent_id,
            "proposal": proposal,
            "quote": {
                "amount": quote_amount,
                "currency": quote_currency,
                "delivery_days": delivery_days,
            },
        }

        try:
            bid = create_bid(db, bid_data)
            if not bid:
                raise RuntimeError("Failed to create bid")
            return {
                "bid_id": bid.bid_id,
                "job_id": bid.job_id,
                "worker_id": bid.worker_id,
                "status": bid.status,
            }
        except ValueError as e:
            raise ValueError(str(e))
    finally:
        db.close()


@mcp.tool()
def get_all_bids(api_key: str, job_id: str) -> list[dict]:
    """Get all bids for a job.

    Uses the same get_bids_for_job() as REST API.

    Args:
        api_key: The agent's API key for authentication
        job_id: The job ID

    Returns:
        List of bids with worker details
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Validate job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Only job owner can see all bids
        if job.employer_id != ctx.agent_id:
            raise PermissionDeniedError(
                action="view_bids",
                resource_type="job",
                resource_id=job_id,
                agent_id=ctx.agent_id
            )

        bids = get_bids_for_job(db, job_id)

        return [
            {
                "bid_id": bid["bid_id"],
                "worker_id": bid["worker_id"],
                "proposal": bid["proposal"],
                "quote": bid["quote"],
                "is_hired": bid["is_hired"],
                "status": bid["status"],
            }
            for bid in bids
        ]
    finally:
        db.close()


# ============================================================
# Communication Tools - Same DB functions as api/messages.py
# ============================================================

@mcp.tool()
def send_private_msg(
    api_key: str,
    to_agent_id: str,
    job_id: str,
    content: str,
    message_type: str = "text",
) -> dict:
    """Send a private message to another agent.

    Uses the same create_message() as REST API.

    Args:
        api_key: The sender's API key for authentication
        to_agent_id: Receiver's agent ID
        job_id: Related job ID
        content: Message content
        message_type: Message type (text/file/etc)

    Returns:
        Created message information
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Validate job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Validate recipient exists
        recipient = get_agent(db, to_agent_id)
        if not recipient:
            raise ValueError(f"Recipient {to_agent_id} not found")

        # Call shared DB function
        message_data = {
            "job_id": job_id,
            "from_agent_id": ctx.agent_id,
            "to_agent_id": to_agent_id,
            "content": content,
            "message_type": message_type,
        }

        message = create_message(db, message_data)
        if not message:
            raise RuntimeError("Failed to create message")

        return {
            "message_id": message.message_id,
            "job_id": message.job_id,
            "from": ctx.agent_id,
            "to": to_agent_id,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
    finally:
        db.close()


# ============================================================
# Artifact Tools - Same DB functions as db/artifacts.py
# ============================================================

@mcp.tool()
def post_demo(api_key: str, job_id: str, title: str, content: str) -> dict:
    """Post a demo artifact for a job.

    Args:
        api_key: The worker's API key for authentication
        job_id: The job ID
        title: Demo title
        content: Demo content

    Returns:
        Created artifact information
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Validate job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        artifact_data = {
            "job_id": job_id,
            "worker_id": ctx.agent_id,
            "artifact_type": "demo",
            "title": title,
            "content": content,
        }

        artifact = create_artifact(db, artifact_data)
        if not artifact:
            raise RuntimeError("Failed to create artifact")

        return {
            "artifact_id": artifact.artifact_id,
            "job_id": artifact.job_id,
            "type": "demo",
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        }
    finally:
        db.close()


@mcp.tool()
def submit_final_work(api_key: str, job_id: str, title: str, content: str) -> dict:
    """Submit final work for a job.

    Args:
        api_key: The worker's API key for authentication
        job_id: The job ID
        title: Work title
        content: Work content

    Returns:
        Created artifact information
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Validate job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        artifact_data = {
            "job_id": job_id,
            "worker_id": ctx.agent_id,
            "artifact_type": "final",
            "title": title,
            "content": content,
        }

        artifact = create_artifact(db, artifact_data)
        if not artifact:
            raise RuntimeError("Failed to create artifact")

        return {
            "artifact_id": artifact.artifact_id,
            "job_id": artifact.job_id,
            "type": "final",
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        }
    finally:
        db.close()


# ============================================================
# Admin Tools - Same DB functions as REST API
# ============================================================

@mcp.tool()
def finalize_hiring(
    api_key: str,
    job_id: str,
    bid_ids: list[str],
) -> dict:
    """Finalize hiring for a job after bid evaluation.

    Uses the same update_bid_status() and update_job() as REST API.

    Args:
        api_key: The employer's API key for authentication
        job_id: The job ID
        bid_ids: List of bid IDs to accept

    Returns:
        Hiring result
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Validate job exists and ownership
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.employer_id != ctx.agent_id:
            raise PermissionDeniedError(
                action="finalize_hiring",
                resource_type="job",
                resource_id=job_id,
                agent_id=ctx.agent_id
            )

        hired_workers = []
        for bid_id in bid_ids:
            updated_bid = update_bid_status(db, bid_id, "SELECTED", is_hired=True)
            if updated_bid:
                hired_workers.append(updated_bid.worker_id)

        # Update job status to ACTIVE
        update_job(db, job_id, {"status": "ACTIVE", "selected_worker_ids": hired_workers})

        return {
            "job_id": job_id,
            "hired_workers": hired_workers,
            "status": "ACTIVE",
        }
    finally:
        db.close()


@mcp.tool()
def verify_and_close(api_key: str, job_id: str, approved: bool = True) -> dict:
    """Verify and close a job after work completion.

    Uses the same update_job() as REST API.

    Args:
        api_key: The employer's API key for authentication
        job_id: The job ID
        approved: Whether the work is approved

    Returns:
        Closure result
    """
    db = get_db_session()
    try:
        ctx = authenticate_agent(api_key, db)

        # Validate job exists and ownership
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.employer_id != ctx.agent_id:
            raise PermissionDeniedError(
                action="verify_and_close",
                resource_type="job",
                resource_id=job_id,
                agent_id=ctx.agent_id
            )

        new_status = "CLOSED" if approved else "REVIEW"
        updated_job = update_job(db, job_id, {"status": new_status})

        return {
            "job_id": job_id,
            "status": updated_job.status if updated_job else new_status,
            "approved": approved,
        }
    finally:
        db.close()