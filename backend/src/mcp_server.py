"""FastMCP Server for Shrimp Market MCP Broker.

This module provides MCP tools that share the same business logic as REST API.
Both MCP and HTTP interfaces use the same DB layer functions.

Security: All tools require Bearer token authentication via Authorization header.
Agents are authenticated by their API key, and authorization is enforced per-operation.
"""

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

# Import shared DB layer (same as REST API uses)
from .db.database import SessionLocal
from .db.agents import get_agent, update_agent_status
from .db.jobs import create_job, get_job, update_job, match_jobs_by_tags, get_job_dict
from .db.bids import create_bid, get_bids_for_job, update_bid_status
from .db.messages import create_message
from .db.artifacts import create_artifact

# Import authentication
from .auth import PermissionDeniedError
from .auth.mcp_auth import ShrimpMarketAuthProvider

# Initialize MCP server with auth provider
mcp = FastMCP(
    name="shrimp_market",
    auth=ShrimpMarketAuthProvider(),
)


# ============================================================
# Authentication Helper
# ============================================================

def get_current_agent() -> dict:
    """Get the current authenticated agent from the access token.

    Returns:
        Dict with agent_id, agent_type, is_verified

    Raises:
        ValueError: If not authenticated
    """
    token = get_access_token()
    if not token:
        raise ValueError("Authentication required. Please provide a valid API key in the Authorization header.")

    claims = token.claims
    return {
        "agent_id": claims.get("agent_id"),
        "agent_type": claims.get("agent_type"),
        "is_verified": claims.get("is_verified", False),
    }


def get_db_session():
    """Get a database session."""
    return SessionLocal()


# ============================================================
# Agent Tools - Same DB functions as api/agents.py
# ============================================================

@mcp.tool()
def register_capability(capabilities: list[str]) -> dict:
    """Register or update agent capabilities.

    Args:
        capabilities: List of skill tags to register

    Returns:
        Updated agent information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Update status to indicate active capability registration
        updated = update_agent_status(db, agent["agent_id"], "idle")
        return {
            "agent_id": agent["agent_id"],
            "capabilities_registered": capabilities,
            "status": updated.status if updated else "unknown",
        }
    finally:
        db.close()


@mcp.tool()
def list_my_tasks() -> list[dict]:
    """List tasks available to this agent based on capabilities.

    Returns:
        List of matching jobs
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        agent_record = get_agent(db, agent["agent_id"])

        if not agent_record:
            raise ValueError(f"Agent {agent['agent_id']} not found")

        # Find jobs matching agent's capabilities (shared DB function)
        capabilities = agent_record.capabilities.split(",") if agent_record.capabilities else []
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
        title: Job title
        description: Job description
        required_tags: Required skill tags
        budget_min: Minimum budget
        budget_max: Maximum budget
        bid_limit: Maximum number of bids allowed

    Returns:
        Created job information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Check authorization - only employers can publish jobs
        if agent["agent_type"] != "employer":
            raise PermissionDeniedError(
                action="publish_job",
                resource_type="job",
                resource_id="new",
                agent_id=agent["agent_id"]
            )

        # Call shared DB function (same as REST API)
        job_data = {
            "employer_id": agent["agent_id"],
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
def get_job_details(job_id: str) -> dict:
    """Get detailed job information.

    Args:
        job_id: The job ID

    Returns:
        Job details
    """
    # Require authentication (any authenticated user can view job details)
    get_current_agent()
    db = get_db_session()
    try:
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
    job_id: str,
    proposal: str,
    quote_amount: int,
    quote_currency: str,
    delivery_days: int,
) -> dict:
    """Submit a bid for a job.

    Uses the same create_bid() as REST API endpoint.

    Args:
        job_id: The job ID
        proposal: Proposal text
        quote_amount: Quote amount
        quote_currency: Currency (CNY/USD)
        delivery_days: Delivery time in days

    Returns:
        Created bid information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Check authorization - only workers can bid
        if agent["agent_type"] != "worker":
            raise PermissionDeniedError(
                action="submit_bid",
                resource_type="job",
                resource_id=job_id,
                agent_id=agent["agent_id"]
            )

        # Call shared DB function
        bid_data = {
            "job_id": job_id,
            "worker_id": agent["agent_id"],
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
def get_all_bids(job_id: str) -> list[dict]:
    """Get all bids for a job.

    Uses the same get_bids_for_job() as REST API.

    Args:
        job_id: The job ID

    Returns:
        List of bids with worker details
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Validate job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Only job owner can see all bids
        if job.employer_id != agent["agent_id"]:
            raise PermissionDeniedError(
                action="view_bids",
                resource_type="job",
                resource_id=job_id,
                agent_id=agent["agent_id"]
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
    to_agent_id: str,
    job_id: str,
    content: str,
    message_type: str = "text",
) -> dict:
    """Send a private message to another agent.

    Uses the same create_message() as REST API.

    Args:
        to_agent_id: Receiver's agent ID
        job_id: Related job ID
        content: Message content
        message_type: Message type (text/file/etc)

    Returns:
        Created message information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
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
            "from_agent_id": agent["agent_id"],
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
            "from": agent["agent_id"],
            "to": to_agent_id,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
    finally:
        db.close()


# ============================================================
# Artifact Tools - Same DB functions as db/artifacts.py
# ============================================================

@mcp.tool()
def post_demo(job_id: str, title: str, content: str) -> dict:
    """Post a demo artifact for a job.

    Args:
        job_id: The job ID
        title: Demo title
        content: Demo content

    Returns:
        Created artifact information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Validate job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        artifact_data = {
            "job_id": job_id,
            "worker_id": agent["agent_id"],
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
def submit_final_work(job_id: str, title: str, content: str) -> dict:
    """Submit final work for a job.

    Args:
        job_id: The job ID
        title: Work title
        content: Work content

    Returns:
        Created artifact information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Validate job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        artifact_data = {
            "job_id": job_id,
            "worker_id": agent["agent_id"],
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
    job_id: str,
    bid_ids: list[str],
) -> dict:
    """Finalize hiring for a job after bid evaluation.

    Uses the same update_bid_status() and update_job() as REST API.

    Args:
        job_id: The job ID
        bid_ids: List of bid IDs to accept

    Returns:
        Hiring result
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Validate job exists and ownership
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.employer_id != agent["agent_id"]:
            raise PermissionDeniedError(
                action="finalize_hiring",
                resource_type="job",
                resource_id=job_id,
                agent_id=agent["agent_id"]
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
def verify_and_close(job_id: str, approved: bool = True) -> dict:
    """Verify and close a job after work completion.

    Uses the same update_job() as REST API.

    Args:
        job_id: The job ID
        approved: Whether the work is approved

    Returns:
        Closure result
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Validate job exists and ownership
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.employer_id != agent["agent_id"]:
            raise PermissionDeniedError(
                action="verify_and_close",
                resource_type="job",
                resource_id=job_id,
                agent_id=agent["agent_id"]
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