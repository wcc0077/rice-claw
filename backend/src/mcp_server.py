"""FastMCP Server for Shrimp Market MCP Broker.

This module provides MCP tools that share the same business logic as REST API.
Both MCP and HTTP interfaces use the same DB layer functions.
"""

from fastmcp import FastMCP

# Import shared DB layer (same as REST API uses)
from .db.agents import get_agent, update_agent_status
from .db.jobs import create_job, get_job, update_job, match_jobs_by_tags
from .db.bids import create_bid, get_bids_for_job, update_bid_status
from .db.messages import create_message
from .db.artifacts import create_artifact

# Initialize MCP server
mcp = FastMCP(name="shrimp_market")


# ============================================================
# Agent Tools - Same DB functions as api/agents.py
# ============================================================

@mcp.tool()
def register_capability(agent_id: str, capabilities: list[str]) -> dict:
    """Register or update agent capabilities.

    Args:
        agent_id: The agent's ID
        capabilities: List of skill tags to register

    Returns:
        Updated agent information
    """
    agent = get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    # Update status to indicate active capability registration
    updated = update_agent_status(agent_id, "idle")
    return {
        "agent_id": agent_id,
        "capabilities_registered": capabilities,
        "status": updated.get("status") if updated else "unknown",
    }


@mcp.tool()
def list_my_tasks(agent_id: str) -> list[dict]:
    """List tasks available to this agent based on capabilities.

    Args:
        agent_id: The agent's ID

    Returns:
        List of matching jobs
    """
    agent = get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    # Find jobs matching agent's capabilities (shared DB function)
    job_ids = match_jobs_by_tags(agent.get("capabilities", []))

    jobs = []
    for job_id in job_ids:
        job = get_job(job_id)
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


# ============================================================
# Job Tools - Same DB functions as api/jobs.py
# ============================================================

@mcp.tool()
def publish_job(
    employer_id: str,
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
        employer_id: The employer's agent ID
        title: Job title
        description: Job description
        required_tags: Required skill tags
        budget_min: Minimum budget
        budget_max: Maximum budget
        bid_limit: Maximum number of bids allowed

    Returns:
        Created job information
    """
    # Validate employer (same logic as REST API)
    employer = get_agent(employer_id)
    if not employer:
        raise ValueError(f"Employer {employer_id} not found")
    if employer["agent_type"] != "employer":
        raise ValueError(f"Agent {employer_id} is not an employer")

    # Call shared DB function (same as REST API)
    job_data = {
        "employer_id": employer_id,
        "title": title,
        "description": description,
        "required_tags": required_tags,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "bid_limit": bid_limit,
    }

    job = create_job(job_data)
    if not job:
        raise RuntimeError("Failed to create job")

    return {
        "job_id": job["job_id"],
        "title": job["title"],
        "status": job["status"],
        "required_tags": job["required_tags"],
        "created_at": job["created_at"],
    }


@mcp.tool()
def get_job_details(job_id: str) -> dict:
    """Get detailed job information.

    Args:
        job_id: The job ID

    Returns:
        Job details
    """
    job = get_job(job_id)
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


# ============================================================
# Bid Tools - Same DB functions as api/bids.py
# ============================================================

@mcp.tool()
def submit_bid(
    job_id: str,
    worker_id: str,
    proposal: str,
    quote_amount: int,
    quote_currency: str,
    delivery_days: int,
) -> dict:
    """Submit a bid for a job.

    Uses the same create_bid() as REST API endpoint.

    Args:
        job_id: The job ID
        worker_id: Worker's agent ID
        proposal: Proposal text
        quote_amount: Quote amount
        quote_currency: Currency (CNY/USD)
        delivery_days: Delivery time in days

    Returns:
        Created bid information
    """
    # Validate worker (same logic as REST API)
    worker = get_agent(worker_id)
    if not worker:
        raise ValueError(f"Worker {worker_id} not found")
    if worker["agent_type"] != "worker":
        raise ValueError(f"Agent {worker_id} is not a worker")

    # Call shared DB function
    bid_data = {
        "job_id": job_id,
        "worker_id": worker_id,
        "proposal": proposal,
        "quote": {
            "amount": quote_amount,
            "currency": quote_currency,
            "delivery_days": delivery_days,
        },
    }

    try:
        bid = create_bid(bid_data)
        if not bid:
            raise RuntimeError("Failed to create bid")
        return {
            "bid_id": bid["bid_id"],
            "job_id": bid["job_id"],
            "worker_id": bid["worker_id"],
            "status": bid["status"],
        }
    except ValueError as e:
        raise ValueError(str(e))


@mcp.tool()
def get_all_bids(job_id: str) -> list[dict]:
    """Get all bids for a job.

    Uses the same get_bids_for_job() as REST API.

    Args:
        job_id: The job ID

    Returns:
        List of bids with worker details
    """
    # Validate job exists
    job = get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    bids = get_bids_for_job(job_id)

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


# ============================================================
# Communication Tools - Same DB functions as api/messages.py
# ============================================================

@mcp.tool()
def send_private_msg(
    from_agent_id: str,
    to_agent_id: str,
    job_id: str,
    content: str,
    message_type: str = "text",
) -> dict:
    """Send a private message to another agent.

    Uses the same create_message() as REST API.

    Args:
        from_agent_id: Sender's agent ID
        to_agent_id: Receiver's agent ID
        job_id: Related job ID
        content: Message content
        message_type: Message type (text/file/etc)

    Returns:
        Created message information
    """
    # Validate agents and job
    if not get_agent(from_agent_id):
        raise ValueError(f"Sender {from_agent_id} not found")
    if not get_agent(to_agent_id):
        raise ValueError(f"Receiver {to_agent_id} not found")
    if not get_job(job_id):
        raise ValueError(f"Job {job_id} not found")

    # Call shared DB function
    message_data = {
        "job_id": job_id,
        "from_agent_id": from_agent_id,
        "to_agent_id": to_agent_id,
        "content": content,
        "message_type": message_type,
    }

    message = create_message(message_data)
    if not message:
        raise RuntimeError("Failed to create message")

    return {
        "message_id": message["message_id"],
        "job_id": message["job_id"],
        "from": from_agent_id,
        "to": to_agent_id,
        "created_at": message["created_at"],
    }


# ============================================================
# Artifact Tools - Same DB functions as db/artifacts.py
# ============================================================

@mcp.tool()
def post_demo(job_id: str, worker_id: str, title: str, content: str) -> dict:
    """Post a demo artifact for a job.

    Args:
        job_id: The job ID
        worker_id: Worker's agent ID
        title: Demo title
        content: Demo content

    Returns:
        Created artifact information
    """
    # Validate
    if not get_job(job_id):
        raise ValueError(f"Job {job_id} not found")
    if not get_agent(worker_id):
        raise ValueError(f"Worker {worker_id} not found")

    artifact_data = {
        "job_id": job_id,
        "worker_id": worker_id,
        "artifact_type": "demo",
        "title": title,
        "content": content,
    }

    artifact = create_artifact(artifact_data)
    if not artifact:
        raise RuntimeError("Failed to create artifact")

    return {
        "artifact_id": artifact["artifact_id"],
        "job_id": artifact["job_id"],
        "type": "demo",
        "created_at": artifact["created_at"],
    }


@mcp.tool()
def submit_final_work(job_id: str, worker_id: str, title: str, content: str) -> dict:
    """Submit final work for a job.

    Args:
        job_id: The job ID
        worker_id: Worker's agent ID
        title: Work title
        content: Work content

    Returns:
        Created artifact information
    """
    # Validate
    if not get_job(job_id):
        raise ValueError(f"Job {job_id} not found")
    if not get_agent(worker_id):
        raise ValueError(f"Worker {worker_id} not found")

    artifact_data = {
        "job_id": job_id,
        "worker_id": worker_id,
        "artifact_type": "final",
        "title": title,
        "content": content,
    }

    artifact = create_artifact(artifact_data)
    if not artifact:
        raise RuntimeError("Failed to create artifact")

    return {
        "artifact_id": artifact["artifact_id"],
        "job_id": artifact["job_id"],
        "type": "final",
        "created_at": artifact["created_at"],
    }


# ============================================================
# Admin Tools - Same DB functions as REST API
# ============================================================

@mcp.tool()
def finalize_hiring(
    employer_id: str,
    job_id: str,
    bid_ids: list[str],
) -> dict:
    """Finalize hiring for a job after bid evaluation.

    Uses the same update_bid_status() and update_job() as REST API.

    Args:
        employer_id: Employer's agent ID
        job_id: The job ID
        bid_ids: List of bid IDs to accept

    Returns:
        Hiring result
    """
    # Validate
    job = get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    if job["employer_id"] != employer_id:
        raise ValueError("Only the job owner can finalize hiring")

    hired_workers = []
    for bid_id in bid_ids:
        updated_bid = update_bid_status(bid_id, "ACCEPTED", is_hired=True)
        if updated_bid:
            hired_workers.append(updated_bid["worker_id"])

    # Update job status to ACTIVE
    update_job(job_id, {"status": "ACTIVE", "selected_worker_ids": hired_workers})

    return {
        "job_id": job_id,
        "hired_workers": hired_workers,
        "status": "ACTIVE",
    }


@mcp.tool()
def verify_and_close(job_id: str, employer_id: str, approved: bool = True) -> dict:
    """Verify and close a job after work completion.

    Uses the same update_job() as REST API.

    Args:
        job_id: The job ID
        employer_id: Employer's agent ID
        approved: Whether the work is approved

    Returns:
        Closure result
    """
    # Validate
    job = get_job(job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")
    if job["employer_id"] != employer_id:
        raise ValueError("Only the job owner can close the job")

    new_status = "CLOSED" if approved else "REVIEW"
    updated_job = update_job(job_id, {"status": new_status})

    return {
        "job_id": job_id,
        "status": updated_job["status"] if updated_job else new_status,
        "approved": approved,
    }