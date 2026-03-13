"""Admin console endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.database import get_db
from ..db import agents as agent_dal
from ..db import jobs as job_dal
from ..db import bids as bid_dal
from ..models.schemas import DashboardStats, DailyAnalytics
from ..models.db_models import Agent, Job, Bid

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    try:
        # Total agents
        total_agents = db.execute(
            func.count().select_from(Agent)
        ).scalar() or 0

        # Active jobs
        active_jobs = db.execute(
            func.count().select_from(Job).where(Job.status == "ACTIVE")
        ).scalar() or 0

        # Pending bids
        pending_bids = db.execute(
            func.count().select_from(Bid).where(Bid.status == "PENDING")
        ).scalar() or 0

        # Stats for today (placeholder)
        completed_today = 0
        revenue_today = 0

        # Agent status breakdown
        agent_status = db.execute(
            func.count().select_from(Agent).group_by(Agent.status)
        ).all()
        agent_status_breakdown = {"idle": 0, "busy": 0, "offline": 0}

        for count, status in agent_status:
            agent_status_breakdown[status] = count

        # Job status breakdown
        job_status = db.execute(
            func.count().select_from(Job).group_by(Job.status)
        ).all()
        job_status_breakdown = {"OPEN": 0, "ACTIVE": 0, "REVIEW": 0, "CLOSED": 0}

        for count, status in job_status:
            job_status_breakdown[status] = count

        return DashboardStats(
            total_agents=total_agents,
            active_jobs=active_jobs,
            pending_bids=pending_bids,
            completed_today=completed_today,
            revenue_today=revenue_today,
            agent_status_breakdown=agent_status_breakdown,
            job_status_breakdown=job_status_breakdown,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/agents")
async def list_admin_agents(
    status: str | None = None,
    capability: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List all agents (admin only)."""
    result = agent_dal.list_agents(db, status=status, capability=capability, page=page, limit=limit)
    return result


@router.post("/agents/{agent_id}/ban")
async def ban_agent(agent_id: str, db: Session = Depends(get_db)):
    """Ban an agent (admin only)."""
    agent = agent_dal.update_agent_status(db, agent_id, "offline")
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return {"message": f"Agent {agent_id} banned"}


@router.get("/jobs")
async def list_admin_jobs(
    status: str | None = None,
    date_range: str = "7d",
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List all jobs (admin only)."""
    result = job_dal.list_jobs(db, status=status, page=page, limit=limit)
    return result


@router.post("/jobs/{job_id}/force_close")
async def force_close_job(job_id: str, db: Session = Depends(get_db)):
    """Force close a job (admin only)."""
    from datetime import datetime
    updated_job = job_dal.update_job(db, job_id, {
        "status": "CLOSED",
        "closed_at": datetime.utcnow()
    })
    if not updated_job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"message": f"Job {job_id} closed", "status": "CLOSED"}


@router.get("/bids/pending-review")
async def get_pending_bids(db: Session = Depends(get_db)):
    """Get pending bid review list."""
    # TODO: Implement pending bids listing
    return {"bids": []}


@router.get("/analytics/daily")
async def get_daily_analytics(
    start_date: str = "2026-03-01",
    end_date: str = "2026-03-13",
    db: Session = Depends(get_db)
):
    """Get daily analytics report."""
    # TODO: Implement daily analytics
    return []