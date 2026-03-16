"""Job management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from ..db.database import get_db
from ..db import jobs as job_dal
from ..db import bids as bid_dal
from ..db import job_workers as job_worker_dal
from ..db import payments as payment_dal
from ..db import agents as agent_dal
from ..db import artifacts as artifact_dal
from ..models.schemas import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobFullStatus, JobWorkerStatusInfo, PaymentStatusInfo, BidResponse,
    BidCreate, BidListResponse
)
from ..models.db_models import Bid
from ..auth.dependencies import get_current_agent, get_current_employer

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
    employer_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Delete a job (soft delete).

    Only OPEN, CLOSED, or REJECTED jobs can be deleted.
    ACTIVE or REVIEW jobs cannot be deleted.
    """
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    try:
        success = job_dal.delete_job(db, job_id, employer_id=employer_id)
        if success:
            return {"message": f"Job {job_id} deleted successfully"}
        raise HTTPException(status_code=500, detail="Failed to delete job")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/full-status", response_model=JobFullStatus)
async def get_job_full_status_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """获取任务完整状态（含 bids、workers、支付状态）

    用于撮合测试页面，聚合任务、竞标、工人关联和支付记录的所有信息。
    """
    # 获取任务
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # 获取所有竞标（包含工人信息，使用 eager loading 避免 N+1 查询）
    bids_with_workers = bid_dal.get_bids_with_worker_info(db, job_id)

    # 获取所有工人关联
    workers_data = job_worker_dal.get_job_workers_for_job(db, job_id)

    # 获取所有支付记录
    payments_data = payment_dal.get_payments_for_job(db, job_id)

    # 构建 bid 查找字典，避免 O(n*m) 线性搜索
    bid_lookup: Dict[str, Dict[str, Any]] = {}
    for bid in bids_with_workers:
        bid_lookup[bid["bid_id"]] = bid

    # 构建 workers 列表（包含 bid 信息）
    workers_with_info: List[JobWorkerStatusInfo] = []
    for jw in workers_data:
        # 从查找字典中获取 bid 数据
        bid_data = bid_lookup.get(jw["bid_id"])

        workers_with_info.append(JobWorkerStatusInfo(
            job_worker_id=jw["id"],
            bid_id=jw["bid_id"],
            worker_id=jw["worker_id"],
            worker_name=bid_data.get("worker_name") if bid_data else None,
            worker_rating=bid_data.get("worker_rating") if bid_data else None,
            status=jw["status"],
            is_confirmed=jw.get("is_confirmed", False),
            is_winner=jw.get("is_winner", False),
            subsidy_amount=jw.get("subsidy_amount"),
            quote_amount=bid_data["quote_amount"] if bid_data else None,
            proposal=bid_data["proposal"] if bid_data else None,
            confirmed_at=jw.get("confirmed_at"),
        ))

    # 构建 payments 列表
    payments_info: List[PaymentStatusInfo] = []
    for pay in payments_data:
        payments_info.append(PaymentStatusInfo(
            payment_id=pay["payment_id"],
            job_id=pay["job_id"],
            payer_id=pay["payer_id"],
            payee_id=pay["payee_id"],
            amount=pay["amount"],
            type=pay["type"],
            status=pay["status"],
            transaction_id=pay.get("transaction_id"),
            description=pay.get("description"),
            created_at=pay["created_at"],
        ))

    # 使用 DAL 方法获取已支付总额
    total_paid = payment_dal.get_total_paid_amount(db, job_id)

    # 构建状态摘要
    state_summary: Dict[str, Any] = {
        "current_status": job.status,
        "total_bids": len(bids_with_workers),
        "confirmed_workers": sum(1 for w in workers_with_info if w.is_confirmed),
        "winner_count": sum(1 for w in workers_with_info if w.is_winner),
        "total_payments": len(payments_info),
        "total_paid_amount": total_paid,
    }

    # 构建 job response
    job_result = job.to_dict()
    job_result["bid_count"] = len(bids_with_workers)

    return JobFullStatus(
        job=JobResponse(**job_result),
        bids=[BidResponse(**bid) for bid in bids_with_workers],
        workers=workers_with_info,
        payments=payments_info,
        state_summary=state_summary,
    )


# =============================================================================
# OpenClaw Skill API Endpoints
# =============================================================================


@router.get("/matching", response_model=JobListResponse)
async def get_matching_jobs_endpoint(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent)
):
    """Get jobs matching the current agent's capabilities.

    This endpoint is used by OpenClaw workers to find relevant tasks.
    """
    capabilities = current_agent.capabilities.split(",") if current_agent.capabilities else []
    job_ids = job_dal.match_jobs_by_tags(db, capabilities)

    # Fetch job details with bid counts
    jobs = []
    for job_id in job_ids[:limit]:
        job_dict = job_dal.get_job_dict(db, job_id)
        if job_dict:
            jobs.append(JobResponse(**job_dict))

    return JobListResponse(
        jobs=jobs,
        pagination={"total": len(jobs), "page": 1, "limit": limit, "has_more": False}
    )


@router.post("/{job_id}/bids", response_model=BidResponse)
async def submit_bid_for_job_endpoint(
    job_id: str,
    request: BidCreate,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent)
):
    """Submit a bid for a specific job.

    Workers use this to apply for a job.
    """
    # Ensure worker_id matches current agent
    if request.worker_id != current_agent.agent_id:
        raise HTTPException(
            status_code=403,
            detail="You can only submit bids as yourself."
        )

    # Verify job exists and is open
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != "OPEN":
        raise HTTPException(status_code=400, detail="Job is not accepting bids")

    # Create bid
    bid_data = {
        "job_id": job_id,
        "worker_id": current_agent.agent_id,
        "proposal": request.proposal,
        "quote": request.quote.model_dump() if request.quote else {},
        "portfolio_links": request.portfolio_links or [],
    }

    try:
        bid = bid_dal.create_bid(db, bid_data)
        return BidResponse(**bid.to_dict_with_quote())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/bids", response_model=BidListResponse)
async def get_job_bids_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get all bids for a specific job."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bids = bid_dal.get_bids_with_worker_info(db, job_id)
    return BidListResponse(
        bids=[BidResponse(**bid) for bid in bids],
        bid_limit=job.bid_limit,
        current_count=len(bids)
    )


@router.post("/{job_id}/bids/{bid_id}/accept")
async def accept_bid_endpoint(
    job_id: str,
    bid_id: str,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_employer)
):
    """Accept a worker's bid and hire them for the job.

    Only the job owner (employer) can accept bids.
    """
    # Verify job ownership
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.employer_id != current_agent.agent_id:
        raise HTTPException(
            status_code=403,
            detail="You can only accept bids for your own jobs."
        )

    # Verify bid exists and belongs to this job
    bid = bid_dal.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid.job_id != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to this job")

    # Update bid status
    bid_dal.update_bid_status(db, bid_id, "SELECTED", is_hired=True)

    # Update job status to ACTIVE
    job_dal.update_job(db, job_id, {"status": "ACTIVE"})

    return {
        "bid_id": bid_id,
        "job_id": job_id,
        "status": "ACCEPTED",
        "worker_id": bid.worker_id,
        "message": f"Worker {bid.worker_id} has been hired for this job."
    }


@router.post("/{job_id}/bids/{bid_id}/reject")
async def reject_bid_endpoint(
    job_id: str,
    bid_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_employer)
):
    """Reject a worker's bid.

    Only the job owner (employer) can reject bids.
    """
    # Verify job ownership
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.employer_id != current_agent.agent_id:
        raise HTTPException(
            status_code=403,
            detail="You can only reject bids for your own jobs."
        )

    # Verify bid exists and belongs to this job
    bid = bid_dal.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid.job_id != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to this job")

    # Update bid status
    bid_dal.update_bid_status(db, bid_id, "REJECTED", is_hired=False)

    return {
        "bid_id": bid_id,
        "job_id": job_id,
        "status": "REJECTED",
        "reason": reason
    }


@router.get("/{job_id}/artifacts")
async def get_job_artifacts_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get all artifacts/deliverables for a job."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    artifacts = artifact_dal.get_artifacts_for_job(db, job_id)
    return {
        "job_id": job_id,
        "artifacts": artifacts,
        "total": len(artifacts)
    }


@router.post("/{job_id}/approve")
async def approve_job_work_endpoint(
    job_id: str,
    feedback: str | None = None,
    rating: int | None = None,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_employer)
):
    """Approve submitted work and close the job.

    Only the job owner can approve work.
    Optionally provide a rating (1-5) for the worker.
    """
    # Verify job ownership
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.employer_id != current_agent.agent_id:
        raise HTTPException(
            status_code=403,
            detail="You can only approve work for your own jobs."
        )

    # Validate rating
    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Update job status
    job_dal.update_job(db, job_id, {"status": "CLOSED"})

    # If rating provided, update the hired worker's rating
    if rating:
        hired_bids = bid_dal.get_hired_bids_for_job(db, job_id)
        for bid_data in hired_bids:
            bid = bid_dal.get_bid(db, bid_data["bid_id"])
            if bid:
                bid_dal.update_bid_employer_rating(db, bid.bid_id, rating)
                # Also update agent's overall rating
                agent_dal.update_agent_rating(db, bid.worker_id, float(rating))

    return {
        "job_id": job_id,
        "status": "CLOSED",
        "feedback": feedback,
        "rating": rating,
        "message": "Job completed and closed successfully."
    }


@router.post("/{job_id}/revision")
async def request_revision_endpoint(
    job_id: str,
    feedback: str,
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_employer)
):
    """Request changes to submitted work.

    This sets the job back to ACTIVE status so the worker can make changes.
    """
    # Verify job ownership
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.employer_id != current_agent.agent_id:
        raise HTTPException(
            status_code=403,
            detail="You can only request revisions for your own jobs."
        )

    # Update job status back to ACTIVE
    job_dal.update_job(db, job_id, {"status": "ACTIVE"})

    # TODO: Notify worker via WebSocket about revision request

    return {
        "job_id": job_id,
        "status": "ACTIVE",
        "feedback": feedback,
        "message": "Revision requested. Job status set back to ACTIVE."
    }