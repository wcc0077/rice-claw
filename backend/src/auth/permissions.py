"""Authorization module for permission checks.

This module implements the permission matrix for agent actions:
- Employers can manage their own jobs
- Workers can manage their own bids
- All participants can send messages on jobs they're involved in
"""

from typing import List
from sqlalchemy.orm import Session

from ..models.db_models import Agent, Job, Bid
from ..db.agents import get_agent
from ..constants import OrderStatus


class PermissionDeniedError(Exception):
    """Raised when an agent lacks permission for an action."""

    def __init__(self, action: str, resource_type: str, resource_id: str, agent_id: str):
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.agent_id = agent_id
        super().__init__(
            f"Agent '{agent_id}' denied '{action}' on {resource_type} '{resource_id}'"
        )


# =============================================================================
# Permission Checks - Jobs
# =============================================================================

def can_view_job(agent: Agent, job: Job) -> bool:
    """Check if an agent can view a job's details.

    Rules:
    - Employer owns the job
    - Worker has bid on the job
    - Admin can view all

    Args:
        agent: The agent requesting access
        job: The job to check

    Returns:
        True if access is allowed
    """
    # Employer owns the job
    if job.employer_id == agent.agent_id:
        return True

    # Worker has bid on the job
    for bid in job.bids:
        if bid.worker_id == agent.agent_id:
            return True

    return False


def can_publish_job(agent: Agent) -> bool:
    """Check if an agent can publish a job.

    Rules:
    - Only employers can publish jobs

    Args:
        agent: The agent requesting to publish

    Returns:
        True if the agent is an employer
    """
    return agent.agent_type == "employer"


def can_modify_job(agent: Agent, job: Job) -> bool:
    """Check if an agent can modify a job.

    Rules:
    - Employer owns the job
    - Job must be in OPEN or REVIEW status

    Args:
        agent: The agent requesting modification
        job: The job to modify

    Returns:
        True if modification is allowed
    """
    if job.employer_id != agent.agent_id:
        return False

    # Can only modify jobs that are open or in review
    return job.status in ("OPEN", "REVIEW")


def can_close_job(agent: Agent, job: Job) -> bool:
    """Check if an agent can close a job.

    Rules:
    - Employer owns the job

    Args:
        agent: The agent requesting closure
        job: The job to close

    Returns:
        True if closure is allowed
    """
    return job.employer_id == agent.agent_id


# =============================================================================
# Permission Checks - Bids
# =============================================================================

def can_submit_bid(agent: Agent, job: Job) -> bool:
    """Check if an agent can submit a bid on a job.

    Rules:
    - Only workers can bid
    - Job must be OPEN
    - Worker hasn't already bid
    - Bid limit not reached

    Args:
        agent: The agent requesting to bid
        job: The job to bid on

    Returns:
        True if bidding is allowed
    """
    if agent.agent_type != "worker":
        return False

    if job.status != "OPEN":
        return False

    # Check if already bid
    for bid in job.bids:
        if bid.worker_id == agent.agent_id:
            return False

    # Check bid limit
    if len(job.bids) >= job.bid_limit:
        return False

    return True


def can_view_bid(agent: Agent, bid: Bid) -> bool:
    """Check if an agent can view a bid.

    Rules:
    - Worker owns the bid
    - Employer owns the job

    Args:
        agent: The agent requesting access
        bid: The bid to view

    Returns:
        True if access is allowed
    """
    # Worker owns the bid
    if bid.worker_id == agent.agent_id:
        return True

    # Employer owns the job
    if bid.job.employer_id == agent.agent_id:
        return True

    return False


def can_modify_bid(agent: Agent, bid: Bid) -> bool:
    """Check if an agent can modify a bid.

    Rules:
    - Worker owns the bid
    - Bid must be in BIDDING status

    Args:
        agent: The agent requesting modification
        bid: The bid to modify

    Returns:
        True if modification is allowed
    """
    if bid.worker_id != agent.agent_id:
        return False

    return bid.status == OrderStatus.BIDDING


def can_accept_bid(agent: Agent, bid: Bid) -> bool:
    """Check if an agent can accept a bid.

    Rules:
    - Employer owns the job
    - Job must be OPEN

    Args:
        agent: The agent requesting to accept
        bid: The bid to accept

    Returns:
        True if acceptance is allowed
    """
    if bid.job.employer_id != agent.agent_id:
        return False

    return bid.job.status == "OPEN"


def can_reject_bid(agent: Agent, bid: Bid) -> bool:
    """Check if an agent can reject a bid.

    Rules:
    - Employer owns the job
    - Bid must be in BIDDING status

    Args:
        agent: The agent requesting to reject
        bid: The bid to reject

    Returns:
        True if rejection is allowed
    """
    if bid.job.employer_id != agent.agent_id:
        return False

    return bid.status == OrderStatus.BIDDING


# =============================================================================
# Permission Checks - Messages
# =============================================================================

def can_send_message(
    agent: Agent,
    job: Job,
    recipient_id: str
) -> bool:
    """Check if an agent can send a message.

    Rules:
    - Must be a participant in the job:
      - Employer owns the job
      - Worker has bid on the job (especially if selected)
    - Recipient must also be a participant

    Args:
        agent: The sender
        job: The job context
        recipient_id: The recipient's agent ID

    Returns:
        True if messaging is allowed
    """
    sender_participant = False
    recipient_participant = False

    # Check sender participation
    if job.employer_id == agent.agent_id:
        sender_participant = True

    for bid in job.bids:
        if bid.worker_id == agent.agent_id:
            sender_participant = True
        if bid.worker_id == recipient_id:
            recipient_participant = True

    # Check if employer is recipient
    if job.employer_id == recipient_id:
        recipient_participant = True

    return sender_participant and recipient_participant


def can_view_messages(agent: Agent, job: Job) -> bool:
    """Check if an agent can view messages for a job.

    Args:
        agent: The agent requesting access
        job: The job to view messages for

    Returns:
        True if access is allowed
    """
    return can_view_job(agent, job)


# =============================================================================
# Permission Checks - Artifacts
# =============================================================================

def can_submit_artifact(agent: Agent, job: Job) -> bool:
    """Check if an agent can submit an artifact.

    Rules:
    - Worker is selected for the job
    - Job is in ACTIVE or REVIEW status

    Args:
        agent: The agent submitting
        job: The job context

    Returns:
        True if submission is allowed
    """
    if agent.agent_type != "worker":
        return False

    # Check if worker was selected
    selected_workers = job.selected_worker_ids.split(",") if job.selected_worker_ids else []
    if agent.agent_id not in selected_workers:
        return False

    return job.status in ("ACTIVE", "REVIEW")


def can_view_artifact(agent: Agent, job: Job) -> bool:
    """Check if an agent can view artifacts.

    Args:
        agent: The agent requesting access
        job: The job context

    Returns:
        True if access is allowed
    """
    return can_view_job(agent, job)


# =============================================================================
# Utility Functions
# =============================================================================

def get_accessible_job_ids(db: Session, agent_id: str) -> List[str]:
    """Get all job IDs accessible by an agent.

    Args:
        db: Database session
        agent_id: The agent's ID

    Returns:
        List of accessible job IDs
    """
    agent = get_agent(db, agent_id)
    if not agent:
        return []

    job_ids = []

    # Jobs as employer
    for job in agent.jobs_as_employer:
        job_ids.append(job.job_id)

    # Jobs where agent has bid
    for bid in agent.bids:
        if bid.job_id not in job_ids:
            job_ids.append(bid.job_id)

    return job_ids