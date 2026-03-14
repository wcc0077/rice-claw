"""Job management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db import jobs as job_dal
from ..db import agents as agent_dal
from ..models.schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse
)

router = APIRouter()


@router.post("", response_model=JobResponse)
async def create_job_endpoint(
    request: JobCreate,
    db: Session = Depends(get_db)
):
    """Publish a new job."""
    # Verify employer exists
    employer = agent_dal.get_agent(db, request.employer_id)
    if not employer:
        raise HTTPException(status_code=400, detail=f"Lobster {request.employer_id} not found")

    try:
        job_data = request.model_dump()
        job_data["budget_min"] = request.budget.min if request.budget else None
        job_data["budget_max"] = request.budget.max if request.budget else None
        job_data["deadline"] = request.deadline.isoformat() if request.deadline else None

        job = job_dal.create_job(db, job_data)
        if job:
            result = job.to_dict()
            result["bid_count"] = 0
            return JobResponse(**result)
        raise HTTPException(status_code=500, detail="Failed to create job")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("", response_model=JobListResponse)
async def list_jobs_endpoint(
    status: str | None = None,
    tag: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """List jobs with filtering."""
    if page < 1:
        page = 1
    if limit > 100:
        limit = 100

    result = job_dal.list_jobs(db, status=status, tag=tag, page=page, limit=limit)
    return JobListResponse(**result)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get job details."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    result = job.to_dict()
    result["bid_count"] = job_dal.count_job_bids(db, job_id)
    return JobResponse(**result)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job_endpoint(
    job_id: str,
    request: JobUpdate,
    db: Session = Depends(get_db)
):
    """Update job status."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    updates = {}
    if request.status:
        updates["status"] = request.status
    if request.selected_worker_ids is not None:
        updates["selected_worker_ids"] = request.selected_worker_ids

    if not updates:
        result = job.to_dict()
        result["bid_count"] = job_dal.count_job_bids(db, job_id)
        return JobResponse(**result)

    updated_job = job_dal.update_job(db, job_id, updates)
    if not updated_job:
        raise HTTPException(status_code=500, detail="Failed to update job")

    result = updated_job.to_dict()
    result["bid_count"] = job_dal.count_job_bids(db, job_id)
    return JobResponse(**result)


@router.delete("/{job_id}")
async def delete_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Delete a job."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    success = job_dal.delete_job(db, job_id)
    if success:
        return {"message": f"Job {job_id} deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete job")