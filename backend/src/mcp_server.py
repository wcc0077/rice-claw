"""FastMCP Server for Shrimp Market MCP Broker.

This module provides MCP tools that share the same business logic as REST API.
Both MCP and HTTP interfaces use the same DB layer functions.

Security: All tools require Bearer token authentication via Authorization header.
Agents are authenticated by their API key, and authorization is enforced per-operation.
"""

from contextlib import contextmanager
from sqlalchemy import select, func

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token

from .db.database import SessionLocal
from .db.agents import get_agent, update_agent_status
from .db.jobs import match_jobs_by_tags, get_job_dict, get_job, get_active_job_for_employer
from .db.messages import create_message, get_messages_for_job, get_conversations_for_agent, get_unread_message_count
from .db.artifacts import create_artifact
from .db.bids import get_worker_orders, get_active_bid_for_worker

# Import Service layer
from .services import JobService, BidService, JobValidationError, BidValidationError

# Import models for direct queries
from .models.db_models import Job, Bid

# Import constants
from .constants import OrderStatus

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


@contextmanager
def mcp_db():
    """Context manager for MCP tool database sessions.

    Automatically handles session cleanup. Yields the db session.
    Use when you don't need the agent info.
    """
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def mcp_auth_db():
    """Context manager for MCP tool with auth and database.

    Provides both authenticated agent info and db session.
    Automatically handles session cleanup.
    Yields tuple of (agent_dict, db_session).
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        yield agent, db
    finally:
        db.close()


# Active status sets for single-task constraint
ACTIVE_JOB_STATUSES = {"OPEN", "ACTIVE", "REVIEW"}
ACTIVE_BID_STATUSES = {
    OrderStatus.BIDDING, OrderStatus.PENDING,
    OrderStatus.SELECTED, OrderStatus.ACCEPTED, OrderStatus.IN_PROGRESS
}


# ============================================================
# Agent Tools - Same DB functions as api/agents.py
# ============================================================

@mcp.tool()
def get_my_profile() -> dict:
    """Get the current agent's profile information.

    Returns:
        Agent profile including type, capabilities, status, rating, etc.
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        agent_record = get_agent(db, agent["agent_id"])
        if not agent_record:
            raise ValueError(f"Agent {agent['agent_id']} not found")

        # Use the model's to_dict() which includes reputation level calculation
        return agent_record.to_dict()
    finally:
        db.close()


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


# @mcp.tool()
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
def list_jobs(
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """List all jobs in the market for worker agent to bid with optional filtering.

    Args:
        status: Filter by job status (OPEN, ACTIVE, REVIEW, CLOSED)
        page: Page number (1-indexed)
        limit: Maximum number of jobs to return (default 20, max 100)

    Returns:
        List of jobs with total count
    """
    get_current_agent()  # Require authentication
    db = get_db_session()
    try:
        job_service = JobService(db)
        result = job_service.list_jobs(
            status=status,
            page=page,
            limit=min(limit, 100),
        )

        pagination = result["pagination"]
        return {
            "total": pagination["total"],
            "page": pagination["page"],
            "has_more": pagination["has_more"],
            "jobs": [
                {
                    "job_id": job["job_id"],
                    "employer_id": job["employer_id"],
                    "title": job["title"],
                    "required_tags": job["required_tags"],
                    "budget": {"min": job.get("budget_min"), "max": job.get("budget_max")},
                    "status": job["status"],
                    "bid_count": job.get("bid_count", 0),
                    "bid_limit": job.get("bid_limit", 5),
                    "created_at": job.get("created_at"),
                }
                for job in result["jobs"]
            ],
        }
    finally:
        db.close()


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

    NOTE: One employer can only have ONE active job at a time.
    Must wait for current job to complete (CLOSED/REJECTED) before publishing new one.

    Uses the same JobService.create_job() as REST API endpoint.

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
        # Check authorization - employers and 'all' type can publish jobs
        if agent["agent_type"] not in ("employer", "all"):
            raise PermissionDeniedError(
                action="publish_job",
                resource_type="job",
                resource_id="new",
                agent_id=agent["agent_id"]
            )

        # Check if employer already has an active job (single-task constraint)
        active_job = get_active_job_for_employer(db, agent["agent_id"])
        if active_job:
            raise ValueError(
                f"您已有一个进行中的任务「{active_job.title}」(状态: {active_job.status})。"
                f"请等待该任务完成后再发布新任务。"
            )

        # Use JobService (same as REST API)
        job_service = JobService(db)
        job = job_service.create_job(
            employer_id=agent["agent_id"],
            title=title,
            description=description,
            required_tags=required_tags,
            budget_min=budget_min,
            budget_max=budget_max,
            bid_limit=bid_limit,
        )

        return {
            "job_id": job["job_id"],
            "title": job["title"],
            "status": job["status"],
            "required_tags": job["required_tags"],
            "created_at": job["created_at"],
        }
    except JobValidationError as e:
        raise ValueError(str(e))
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
        job_service = JobService(db)
        job = job_service.get_job(job_id)

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
    except JobValidationError as e:
        raise ValueError(str(e))
    finally:
        db.close()


@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """Delete a job (soft delete).

    Only the job owner can delete their own jobs.
    Only OPEN, CLOSED, or REJECTED jobs can be deleted.

    Args:
        job_id: The job ID to delete

    Returns:
        Deletion result
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        job_service = JobService(db)

        # Delete the job (soft delete) - service handles authorization
        job_service.delete_job(job_id=job_id, operator_id=agent["agent_id"])

        return {
            "job_id": job_id,
            "status": "DELETED",
            "message": f"Job {job_id} has been deleted",
        }
    except JobValidationError as e:
        raise ValueError(str(e))
    except PermissionDeniedError as e:
        raise e
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

    NOTE: One worker can only have ONE active bid at a time.
    Must wait for current bid to resolve (REJECTED or job completed) before bidding on new jobs.

    Uses the same BidService.create_bid() as REST API endpoint.

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
        # Check if worker already has an active bid (single-task constraint)
        active_bid = get_active_bid_for_worker(db, agent["agent_id"])
        if active_bid:
            # Get job title for better error message
            job = get_job(db, active_bid.job_id)
            status_msg = "等待雇主选择" if active_bid.status in ("BIDDING", "PENDING") else "已中标，正在执行"
            raise ValueError(
                f"您已有一个进行中的竞标「{job.title if job else active_bid.job_id}」(状态: {status_msg})。"
                f"请等待该竞标结束后再竞标新任务。"
            )

        # Use BidService (same as REST API)
        bid_service = BidService(db)
        bid = bid_service.create_bid(
            job_id=job_id,
            worker_id=agent["agent_id"],
            proposal=proposal,
            quote={
                "amount": quote_amount,
                "currency": quote_currency,
                "delivery_days": delivery_days,
            },
        )

        return {
            "bid_id": bid["bid_id"],
            "job_id": bid["job_id"],
            "worker_id": bid["worker_id"],
            "status": bid["status"],
        }
    except BidValidationError as e:
        raise ValueError(str(e))
    except PermissionDeniedError as e:
        raise e
    finally:
        db.close()


@mcp.tool()
def get_all_bids(job_id: str) -> list[dict]:
    """Get all bids for a job.

    Uses the same BidService.get_bids_for_job() as REST API.

    Args:
        job_id: The job ID

    Returns:
        List of bids with worker details
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        bid_service = BidService(db)

        # Use BidService - handles validation and authorization
        bids = bid_service.get_bids_for_job(job_id)

        # Verify caller is job owner
        if bids and bids[0].get("employer_id") != agent["agent_id"]:
            raise PermissionDeniedError(
                action="view_bids",
                resource_type="job",
                resource_id=job_id,
                agent_id=agent["agent_id"]
            )

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
    except BidValidationError as e:
        raise ValueError(str(e))
    except PermissionDeniedError as e:
        raise e
    finally:
        db.close()


@mcp.tool()
def get_bid_detail(bid_id: str) -> dict:
    """Get detailed information about a specific bid.

    Returns bid info with associated job and worker details.
    Requires authentication as either the job owner (employer) or the bid owner (worker).

    Args:
        bid_id: The bid ID to retrieve

    Returns:
        Bid details including:
        - bid_id: The bid identifier
        - job_id: Associated job ID
        - worker_id: Worker agent ID
        - proposal: The proposal text
        - quote: Quote details (amount, currency, delivery_days)
        - status: Current bid status
        - job: Related job information
        - worker: Worker agent information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        from .db.bids import get_bid_detail as get_bid_detail_db

        bid = get_bid_detail_db(db, bid_id)
        if not bid:
            raise ValueError(f"Bid {bid_id} not found")

        # Verify caller is either job owner or bid owner
        job_id = bid.get("job", {}).get("job_id")
        worker_id = bid.get("worker_id")

        # Check if caller is the worker
        if worker_id == agent["agent_id"]:
            return bid

        # Check if caller is the job owner
        if job_id:
            job = get_job(db, job_id)
            if job and job.employer_id == agent["agent_id"]:
                return bid

        # Neither worker nor employer - deny access
        raise PermissionDeniedError(
            action="view_bid_detail",
            resource_type="bid",
            resource_id=bid_id,
            agent_id=agent["agent_id"]
        )
    except PermissionDeniedError as e:
        raise e
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


@mcp.tool()
def get_messages(job_id: str) -> dict:
    """Get all messages for a specific job.

    Returns complete message history as context for understanding the conversation.

    Args:
        job_id: The job ID

    Returns:
        List of all messages for this job, sorted chronologically
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Verify job exists
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Get all messages for this job
        messages = get_messages_for_job(db, job_id)

        # Format messages with direction indicator (sent vs received)
        formatted_messages = []
        for msg in messages:
            is_sent = msg["from_agent_id"] == agent["agent_id"]
            formatted_messages.append({
                "message_id": msg["message_id"],
                "direction": "sent" if is_sent else "received",
                "from_agent_id": msg["from_agent_id"],
                "to_agent_id": msg["to_agent_id"],
                "content": msg["content"],
                "is_read": msg.get("is_read", True),
                "created_at": msg.get("created_at"),
            })

        return {
            "job_id": job_id,
            "total": len(formatted_messages),
            "messages": formatted_messages,
        }
    finally:
        db.close()


@mcp.tool()
def get_my_messages() -> dict:
    """Get all conversations for the current agent.

    Returns conversation list with unread counts for quick overview.

    Returns:
        List of conversations with last message, unread count, and counterpart info
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Get all conversations
        conversations = get_conversations_for_agent(db, agent["agent_id"])

        # Get total unread count
        total_unread = get_unread_message_count(db, agent["agent_id"])

        return {
            "agent_id": agent["agent_id"],
            "total_unread": total_unread,
            "conversations": conversations,
        }
    finally:
        db.close()


# ============================================================
# Artifact Tools - Same DB functions as db/artifacts.py
# ============================================================

def _create_artifact(
    job_id: str,
    title: str,
    content: str,
    artifact_type: str,
) -> dict:
    """Internal helper to create an artifact.

    Args:
        job_id: The job ID
        title: Artifact title
        content: Artifact content
        artifact_type: Type of artifact ("demo" or "final")

    Returns:
        Created artifact information
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        job = get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        artifact_data = {
            "job_id": job_id,
            "worker_id": agent["agent_id"],
            "artifact_type": artifact_type,
            "title": title,
            "content": content,
        }

        artifact = create_artifact(db, artifact_data)
        if not artifact:
            raise RuntimeError("Failed to create artifact")

        return {
            "artifact_id": artifact.artifact_id,
            "job_id": artifact.job_id,
            "type": artifact_type,
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        }
    finally:
        db.close()


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
    return _create_artifact(job_id, title, content, "demo")


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
    return _create_artifact(job_id, title, content, "final")


# ============================================================
# Admin Tools - Same DB functions as REST API
# ============================================================

@mcp.tool()
def finalize_hiring(
    job_id: str,
    bid_ids: list[str],
) -> dict:
    """Finalize hiring for a job after bid evaluation.

    Uses the same BidService.accept_bid() as REST API.

    Args:
        job_id: The job ID
        bid_ids: List of bid IDs to accept

    Returns:
        Hiring result
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        bid_service = BidService(db)

        hired_workers = []
        for bid_id in bid_ids:
            # Use BidService.accept_bid() - handles authorization and state transitions
            updated_bid = bid_service.accept_bid(
                job_id=job_id,
                bid_id=bid_id,
                employer_id=agent["agent_id"]
            )
            hired_workers.append(updated_bid["worker_id"])

        return {
            "job_id": job_id,
            "hired_workers": hired_workers,
            "status": "ACTIVE",
        }
    except BidValidationError as e:
        raise ValueError(str(e))
    except PermissionDeniedError as e:
        raise e
    finally:
        db.close()


@mcp.tool()
def verify_and_close(job_id: str, approved: bool = True) -> dict:
    """Verify and close a job after work completion.

    Uses the same JobService.update_job_status() as REST API.

    Args:
        job_id: The job ID
        approved: Whether the work is approved

    Returns:
        Closure result
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        job_service = JobService(db)

        new_status = "CLOSED" if approved else "REVIEW"

        # Use JobService.update_job_status() - handles authorization and state transitions
        updated_job = job_service.update_job_status(
            job_id=job_id,
            new_status=new_status,
            operator_id=agent["agent_id"]
        )

        return {
            "job_id": job_id,
            "status": updated_job["status"],
            "approved": approved,
        }
    except JobValidationError as e:
        raise ValueError(str(e))
    except PermissionDeniedError as e:
        raise e
    finally:
        db.close()


# ============================================================
# My Jobs/Bids Tools - Agent's own jobs and bids
# ============================================================

@mcp.tool()
def get_my_jobs(status: str | None = None) -> dict:
    """Get all jobs published by the current agent.

    Args:
        status: Optional status filter (OPEN, ACTIVE, REVIEW, CLOSED)

    Returns:
        List of jobs with status and bid count
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        # Query jobs where employer_id matches the current agent
        query = (
            select(Job, func.count(Bid.bid_id).label("bid_count"))
            .outerjoin(Bid, (Job.job_id == Bid.job_id) & (Bid.deleted == False))
            .where(Job.employer_id == agent["agent_id"])
            .where(Job.status != "DELETED")
        )

        count_query = (
            select(func.count())
            .select_from(Job)
            .where(Job.employer_id == agent["agent_id"])
            .where(Job.status != "DELETED")
        )

        if status:
            query = query.where(Job.status == status)
            count_query = count_query.where(Job.status == status)

        query = query.group_by(Job.job_id).order_by(Job.created_at.desc())

        total = db.execute(count_query).scalar() or 0
        results = db.execute(query).all()

        jobs = []
        for job, bid_count in results:
            job_dict = job.to_dict()
            job_dict["bid_count"] = bid_count or 0
            jobs.append({
                "job_id": job_dict["job_id"],
                "title": job_dict["title"],
                "status": job_dict["status"],
                "bid_count": job_dict["bid_count"],
                "bid_limit": job_dict.get("bid_limit", 5),
                "created_at": job_dict.get("created_at"),
                "updated_at": job_dict.get("updated_at"),
            })

        return {
            "total": total,
            "jobs": jobs,
        }
    finally:
        db.close()


@mcp.tool()
def get_my_bids(status: str | None = None) -> dict:
    """Get all bids submitted by the current agent.

    Args:
        status: Optional status filter (PENDING, ACCEPTED, REJECTED, etc.)

    Returns:
        List of bids with job info and status
    """
    agent = get_current_agent()
    db = get_db_session()
    try:
        result = get_worker_orders(
            db,
            worker_id=agent["agent_id"],
            status=status,
            page=1,
            limit=100,
        )

        return {
            "total": result["pagination"]["total"],
            "bids": [
                {
                    "bid_id": bid["bid_id"],
                    "job_id": bid["job_id"],
                    "job_title": bid.get("job_title"),
                    "status": bid["status"],
                    "status_label": bid.get("status_label"),
                    "quote_amount": bid.get("quote_amount"),
                    "quote_currency": bid.get("quote_currency"),
                    "employer_name": bid.get("employer_name"),
                    "submitted_at": bid.get("submitted_at"),
                    "updated_at": bid.get("updated_at"),
                }
                for bid in result["orders"]
            ],
            "status_counts": result["status_counts"],
        }
    finally:
        db.close()