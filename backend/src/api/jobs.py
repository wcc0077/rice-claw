"""Job management endpoints."""

from fastapi import APIRouter, HTTPException

from ..db.jobs import create_job, get_job, list_jobs, update_job, delete_job
from ..db.agents import get_agent
from ..models.schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse
)

router = APIRouter()


@router.post("", response_model=JobResponse)
async def create_job_endpoint(request: JobCreate):
    """Publish a new job."""
    # Verify employer exists
    employer = get_agent(request.employer_id)
    if not employer:
        raise HTTPException(status_code=400, detail=f"Employer {request.employer_id} not found")
    if employer["agent_type"] != "employer":
        raise HTTPException(status_code=400, detail=f"Agent {request.employer_id} is not an employer")

    try:
        job_data = request.model_dump()
        job_data["budget_min"] = request.budget.min if request.budget else None
        job_data["budget_max"] = request.budget.max if request.budget else None
        job_data["deadline"] = request.deadline.isoformat() if request.deadline else None

        job = create_job(job_data)
        if job:
            return JobResponse(**job)
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
):
    """List jobs with filtering."""
    if page < 1:
        page = 1
    if limit > 100:
        limit = 100

    result = list_jobs(status=status, tag=tag, page=page, limit=limit)
    return JobListResponse(**result)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_endpoint(job_id: str):
    """Get job details."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobResponse(**job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job_endpoint(job_id: str, request: JobUpdate):
    """Update job status."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    updates = {}
    if request.status:
        updates["status"] = request.status
    if request.selected_worker_ids is not None:
        updates["selected_worker_ids"] = request.selected_worker_ids

    if not updates:
        return JobResponse(**job)

    updated_job = update_job(job_id, updates)
    if not updated_job:
        raise HTTPException(status_code=500, detail="Failed to update job")
    return JobResponse(**updated_job)


@router.delete("/{job_id}")
async def delete_job_endpoint(job_id: str):
    """Delete a job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    success = delete_job(job_id)
    if success:
        return {"message": f"Job {job_id} deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete job")
