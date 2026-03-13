"""FastMCP Server for Shrimp Market MCP Broker.

This module provides MCP tools that bridge the REST API with agent communication.
"""

from fastmcp import FastMCP
from fastapi import HTTPException

from .db.agents import get_agent, get_agent_status
from .db.jobs import get_job, match_jobs_by_tags
from .db.bids import get_bids_for_job, update_bid_status
from .db.messages import get_messages_for_job

# Initialize MCP server
mcp = FastMCP(name="shrimp_market")


# Agent Tools
@mcp.tool()
def register_capability(agent_id: str, capabilities: list[str]) -> str:
    """Register or update agent capabilities.

    Args:
        agent_id: The agent's ID
        capabilities: List of skill tags to register

    Returns:
        Success message
    """
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # TODO: Update agent capabilities in database
    return f"Registered capabilities for {agent_id}: {', '.join(capabilities)}"


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
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Find jobs matching agent's capabilities
    job_ids = match_jobs_by_tags(agent.get("capabilities", []))

    jobs = []
    for job_id in job_ids:
        job = get_job(job_id)
        if job:
            jobs.append({
                "job_id": job["job_id"],
                "title": job["title"],
                "required_tags": job["required_tags"],
                "bid_limit": job["bid_limit"],
            })

    return jobs


# Job Tools
@mcp.tool()
def publish_job(
    employer_id: str,
    title: str,
    description: str,
    required_tags: list[str],
    bid_limit: int = 5,
) -> dict:
    """Publish a new job for workers to bid on.

    Args:
        employer_id: The employer's agent ID
        title: Job title
        description: Job description
        required_tags: Required skill tags
        bid_limit: Maximum number of bids allowed

    Returns:
        Created job information
    """
    # TODO: Create job in database
    return {
        "job_id": f"job_{employer_id}",
        "title": title,
        "status": "OPEN",
        "created_at": "2026-03-13T00:00:00Z",
    }


@mcp.tool()
def get_all_bids(job_id: str) -> list[dict]:
    """Get all bids for a job.

    Args:
        job_id: The job ID

    Returns:
        List of bids with worker details
    """
    bids = get_bids_for_job(job_id)

    return [
        {
            "bid_id": bid["bid_id"],
            "worker_id": bid["worker_id"],
            "proposal": bid["proposal"],
            "quote": f"{bid['quote_amount']} {bid['quote_currency']}/{bid['delivery_days']}d",
            "is_hired": bid["is_hired"],
        }
        for bid in bids
    ]


# Communication Tools
@mcp.tool()
def send_private_msg(
    from_agent_id: str,
    to_agent_id: str,
    job_id: str,
    content: str,
) -> str:
    """Send a private message to another agent.

    Args:
        from_agent_id: Sender's agent ID
        to_agent_id: Receiver's agent ID
        job_id: Related job ID
        content: Message content

    Returns:
        Message ID
    """
    # TODO: Create message in database
    return f"msg_{from_agent_id}_{to_agent_id}"


@mcp.tool()
def post_demo(job_id: str, worker_id: str, content: str) -> str:
    """Post a demo artifact for a job.

    Args:
        job_id: The job ID
        worker_id: Worker's agent ID
        content: Demo content description

    Returns:
        Artifact ID
    """
    # TODO: Create artifact in database
    return f"art_{job_id}_{worker_id}"


@mcp.tool()
def submit_final_work(job_id: str, worker_id: str, content: str) -> str:
    """Submit final work for a job.

    Args:
        job_id: The job ID
        worker_id: Worker's agent ID
        content: Final work description

    Returns:
        Artifact ID
    """
    # TODO: Create final artifact in database
    return f"final_{job_id}_{worker_id}"


# Admin Tools
@mcp.tool()
def finalize_hiring(
    employer_id: str,
    job_id: str,
    worker_ids: list[str],
) -> dict:
    """Finalize hiring for a job after bid evaluation.

    Args:
        employer_id: Employer's agent ID
        job_id: The job ID
        worker_ids: List of selected worker IDs

    Returns:
        Hiring result
    """
    # TODO: Mark selected bids as hired
    return {
        "job_id": job_id,
        "hired_workers": worker_ids,
        "status": "ACTIVE",
    }


@mcp.tool()
def verify_and_close(job_id: str, employer_id: str, approved: bool = True) -> dict:
    """Verify and close a job after work completion.

    Args:
        job_id: The job ID
        employer_id: Employer's agent ID
        approved: Whether the work is approved

    Returns:
        Closure result
    """
    # TODO: Update job status to CLOSED
    return {
        "job_id": job_id,
        "status": "CLOSED" if approved else "REJECTED",
        "approved": approved,
    }
