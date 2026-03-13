"""Public marketplace endpoints - no authentication required."""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from typing import Optional, List
from collections import Counter

from ..db.database import get_db
from ..db import jobs as job_dal
from ..db import agents as agent_dal
from ..models.db_models import Job, Agent, Bid

router = APIRouter()


@router.get("/jobs")
async def list_public_jobs(
    tag: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    sort: str = "latest",
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List public jobs for marketplace."""
    # Build query
    query = (
        select(Job, func.count(Bid.bid_id).label("bid_count"))
        .outerjoin(Bid, Job.job_id == Bid.job_id)
        .where(Job.status != "DELETED")
    )

    # Filter by status (default to OPEN for marketplace)
    if status:
        query = query.where(Job.status == status)
    else:
        query = query.where(Job.status.in_(["OPEN", "ACTIVE"]))

    # Filter by tag
    if tag:
        query = query.where(Job.required_tags.like(f"%{tag}%"))

    # Filter by keyword
    if keyword:
        query = query.where(
            or_(
                Job.title.like(f"%{keyword}%"),
                Job.description.like(f"%{keyword}%")
            )
        )

    # Group by job
    query = query.group_by(Job.job_id)

    # Sort
    if sort == "budget_high":
        query = query.order_by(Job.budget_max.desc().nullslast())
    elif sort == "bid_low":
        query = query.order_by(func.count(Bid.bid_id).asc())
    else:  # latest
        query = query.order_by(Job.created_at.desc())

    # Count total
    count_query = select(func.count()).select_from(Job).where(Job.status != "DELETED")
    if status:
        count_query = count_query.where(Job.status == status)
    else:
        count_query = count_query.where(Job.status.in_(["OPEN", "ACTIVE"]))
    if tag:
        count_query = count_query.where(Job.required_tags.like(f"%{tag}%"))
    if keyword:
        count_query = count_query.where(
            or_(
                Job.title.like(f"%{keyword}%"),
                Job.description.like(f"%{keyword}%")
            )
        )
    total = db.execute(count_query).scalar()

    # Paginate
    offset = (page - 1) * limit
    query = query.limit(limit).offset(offset)

    # Execute
    results = db.execute(query).all()

    # Format response
    jobs = []
    for job, bid_count in results:
        job_dict = job.to_dict()
        job_dict["bid_count"] = bid_count or 0
        jobs.append(job_dict)

    return {
        "jobs": jobs,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": offset + limit < total,
        },
    }


@router.get("/jobs/{job_id}")
async def get_public_job(job_id: str, db: Session = Depends(get_db)):
    """Get public job detail."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = job.to_dict()
    result["bid_count"] = job_dal.count_job_bids(db, job_id)
    return result


@router.get("/agents")
async def list_public_agents(
    capability: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    sort: str = "rating",
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List public agents for marketplace."""
    # Build query
    query = select(Agent)

    # Filter by status
    if status:
        query = query.where(Agent.status == status)
    else:
        # Default: show idle and busy agents
        query = query.where(Agent.status.in_(["idle", "busy"]))

    # Filter by capability
    if capability:
        query = query.where(Agent.capabilities.like(f"%{capability}%"))

    # Filter by keyword
    if keyword:
        query = query.where(
            or_(
                Agent.name.like(f"%{keyword}%"),
                Agent.description.like(f"%{keyword}%")
            )
        )

    # Count total
    count_query = select(func.count()).select_from(Agent)
    if status:
        count_query = count_query.where(Agent.status == status)
    else:
        count_query = count_query.where(Agent.status.in_(["idle", "busy"]))
    if capability:
        count_query = count_query.where(Agent.capabilities.like(f"%{capability}%"))
    if keyword:
        count_query = count_query.where(
            or_(
                Agent.name.like(f"%{keyword}%"),
                Agent.description.like(f"%{keyword}%")
            )
        )
    total = db.execute(count_query).scalar()

    # Sort
    if sort == "completed":
        query = query.order_by(Agent.completed_jobs.desc())
    elif sort == "latest":
        query = query.order_by(Agent.updated_at.desc())
    else:  # rating (default)
        query = query.order_by(Agent.rating.desc())

    # Paginate
    offset = (page - 1) * limit
    query = query.limit(limit).offset(offset)

    # Execute
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


@router.get("/agents/{agent_id}")
async def get_public_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get public agent detail."""
    agent = agent_dal.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent.to_dict()


@router.get("/tags")
async def get_popular_tags(db: Session = Depends(get_db)):
    """Get popular tags from jobs and agents."""
    # Get all tags from jobs
    jobs = db.execute(select(Job.required_tags).where(Job.status == "OPEN")).scalars().all()
    agents = db.execute(select(Agent.capabilities).where(Agent.status.in_(["idle", "busy"]))).scalars().all()

    # Parse and count tags
    tag_counter = Counter()

    for tags_str in jobs:
        if tags_str:
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    tag_counter[tag] += 1

    for caps_str in agents:
        if caps_str:
            for cap in caps_str.split(","):
                cap = cap.strip()
                if cap:
                    tag_counter[cap] += 1

    # Return top 10 tags
    return {
        "tags": [
            {"name": tag, "count": count}
            for tag, count in tag_counter.most_common(10)
        ]
    }