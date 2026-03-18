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
    BidCreate, BidListResponse, Pagination
)
from ..models.db_models import Bid, AdminUser
from ..auth.dependencies import get_current_agent, get_current_employer, get_current_user_or_agent, get_current_admin_user
from ..auth.permissions import PermissionDeniedError
from ..services import JobService, JobValidationError
from ..services import BidService, BidValidationError

router = APIRouter()


@router.post("", response_model=JobResponse)
async def create_job_endpoint(
    request: JobCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Publish a new job (requires admin authentication).

    The job must be created by an agent owned by the current admin user.
    """
    # 验证 employer_id 属于当前用户
    employer = agent_dal.get_agent(db, request.employer_id)
    if not employer:
        raise HTTPException(status_code=404, detail=f"Agent {request.employer_id} not found")
    # 雇主必须明确属于当前用户（owner_id 不能为空或不匹配）
    if employer.owner_id != current_admin.user_id:
        raise HTTPException(status_code=403, detail="You can only create jobs with your own agents")

    job_service = JobService(db)

    try:
        job = job_service.create_job(
            employer_id=request.employer_id,
            title=request.title,
            description=request.description,
            required_tags=request.required_tags or [],
            budget_min=request.budget.min if request.budget else None,
            budget_max=request.budget.max if request.budget else None,
            bid_limit=request.bid_limit or 5,
            deadline=request.deadline.isoformat() if request.deadline else None
        )
        return JobResponse(**job)
    except JobValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("", response_model=JobListResponse)
async def list_jobs_endpoint(
    status: str | None = None,
    tag: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """List jobs owned by the current admin user's agents."""
    if page < 1:
        page = 1
    if limit > 100:
        limit = 100

    job_service = JobService(db)
    result = job_service.list_jobs(
        owner_id=current_admin.user_id,
        status=status,
        tag=tag,
        page=page,
        limit=limit
    )
    return JobListResponse(**result)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Get job details (only if owned by current user's agents)."""
    # 先获取 job 验证存在
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # 验证 job 属于当前用户的 Agent
    employer = agent_dal.get_agent(db, job.employer_id)
    if not employer or employer.owner_id != current_admin.user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to view this job")

    job_service = JobService(db)

    try:
        job = job_service.get_job(job_id)
        return JobResponse(**job)
    except JobValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{job_id}", response_model=JobResponse)
async def update_job_endpoint(
    job_id: str,
    request: JobUpdate,
    current_agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Update job status."""
    job_service = JobService(db)

    try:
        if request.status:
            job = job_service.update_job_status(
                job_id=job_id,
                new_status=request.status,
                operator_id=current_agent.agent_id
            )
        else:
            job = job_service.get_job(job_id)

        return JobResponse(**job)
    except JobValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{job_id}")
async def delete_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    auth = Depends(get_current_user_or_agent)
):
    """Delete a job (soft delete).

    Only OPEN, CLOSED, or REJECTED jobs can be deleted.
    ACTIVE or REVIEW jobs cannot be deleted.

    Supports both JWT (Admin) and API Key (Agent) authentication.
    Admin users can delete any job, agents can only delete their own jobs.
    """
    job_service = JobService(db)

    try:
        success = job_service.delete_job(
            job_id=job_id,
            operator_id=auth.user_id,
            operator_type=auth.user_type
        )
        if success:
            return {"message": f"Job {job_id} deleted successfully"}
        raise HTTPException(status_code=500, detail="Failed to delete job")
    except JobValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{job_id}/hard")
async def hard_delete_job_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Hard delete a job and all related data.

    WARNING: This is irreversible! Use for testing/cleanup only.

    Deletes:
    - Job record
    - All Bid records
    - All Message records
    - All Artifact records
    - All JobWorker records
    - All Payment records

    Only admin users can perform hard delete.
    """
    from ..db.jobs import hard_delete_job

    # Verify job belongs to current admin's agents
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    employer = agent_dal.get_agent(db, job.employer_id)
    if not employer or employer.owner_id != current_admin.user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this job")

    success = hard_delete_job(db, job_id)
    if success:
        return {"message": f"Job {job_id} and all related data permanently deleted"}
    raise HTTPException(status_code=500, detail="Failed to delete job")


@router.get("/{job_id}/full-status", response_model=JobFullStatus)
async def get_job_full_status_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """获取任务完整状态（含 bids、workers、支付状态）

    用于撮合测试页面，聚合任务、竞标、工人关联和支付记录的所有信息。
    """
    job_service = JobService(db)

    try:
        job = job_service.get_job(job_id)
    except JobValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))

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
        "current_status": job["status"],
        "total_bids": len(bids_with_workers),
        "confirmed_workers": sum(1 for w in workers_with_info if w.is_confirmed),
        "winner_count": sum(1 for w in workers_with_info if w.is_winner),
        "total_payments": len(payments_info),
        "total_paid_amount": total_paid,
    }

    # 构建 job response
    job_result = job.copy()
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
        pagination=Pagination(total=len(jobs), page=1, limit=limit, has_more=False)
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
    Any agent can bid for a job except the employer who created the job.
    """
    # Get the target worker agent
    worker_agent = agent_dal.get_agent(db, request.worker_id)
    if not worker_agent:
        raise HTTPException(
            status_code=404,
            detail=f"Worker agent {request.worker_id} not found"
        )

    # Validate worker can submit bid
    # Condition: worker must be type 'worker' or 'all'
    if worker_agent.agent_type not in ['worker', 'all']:
        raise HTTPException(
            status_code=403,
            detail=f"Agent {request.worker_id} is not a worker agent (type: {worker_agent.agent_type})"
        )

    # Get the job to check if worker is the employer
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    # An agent cannot bid for their own job (employer cannot be worker)
    if job.employer_id == request.worker_id:
        raise HTTPException(
            status_code=403,
            detail="Agent cannot bid for their own job"
        )

    bid_service = BidService(db)

    try:
        bid = bid_service.create_bid(
            job_id=job_id,
            worker_id=request.worker_id,
            proposal=request.proposal,
            quote=request.quote.model_dump() if request.quote else {},
            portfolio_links=request.portfolio_links or []
        )
        return BidResponse(**bid)
    except BidValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/bids", response_model=BidListResponse)
async def get_job_bids_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Get all bids for a specific job (only if job is owned by current user's agent)."""
    # 验证 job 属于当前用户
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    employer = agent_dal.get_agent(db, job.employer_id)
    if not employer or employer.owner_id != current_admin.user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to view this job's bids")

    bid_service = BidService(db)

    try:
        bids = bid_service.get_bids_for_job(job_id)
    except BidValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 获取 job 信息
    job_service = JobService(db)
    job = job_service.get_job(job_id)

    return BidListResponse(
        bids=[BidResponse(**bid) for bid in bids],
        bid_limit=job["bid_limit"],
        current_count=len(bids)
    )


@router.post("/{job_id}/bids/{bid_id}/accept")
async def accept_bid_endpoint(
    job_id: str,
    bid_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Accept a worker's bid and hire them for the job.

    Only the job owner (admin who owns the employer agent) can accept bids.
    """
    # 验证 job 属于当前用户
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    employer = agent_dal.get_agent(db, job.employer_id)
    if not employer or employer.owner_id != current_admin.user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to accept bids for this job")

    bid_service = BidService(db)

    try:
        updated_bid = bid_service.accept_bid(
            job_id=job_id,
            bid_id=bid_id,
            employer_id=job.employer_id
        )
        return {
            "bid_id": bid_id,
            "job_id": job_id,
            "status": "ACCEPTED",
            "worker_id": updated_bid["worker_id"],
            "message": f"Worker {updated_bid['worker_id']} has been hired for this job."
        }
    except BidValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{job_id}/bids/{bid_id}/reject")
async def reject_bid_endpoint(
    job_id: str,
    bid_id: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Reject a worker's bid.

    Only the job owner (admin who owns the employer agent) can reject bids.
    """
    # 验证 job 属于当前用户
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    employer = agent_dal.get_agent(db, job.employer_id)
    if not employer or employer.owner_id != current_admin.user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to reject bids for this job")

    bid_service = BidService(db)

    try:
        bid_service.reject_bid(
            job_id=job_id,
            bid_id=bid_id,
            employer_id=job.employer_id,
            reason=reason
        )
        return {
            "bid_id": bid_id,
            "job_id": job_id,
            "status": "REJECTED",
            "reason": reason
        }
    except BidValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{job_id}/artifacts")
async def get_job_artifacts_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get all artifacts/deliverables for a job."""
    job_service = JobService(db)

    try:
        job_service.get_job(job_id)
    except JobValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))

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
    job_service = JobService(db)

    # Validate rating
    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    try:
        # Update job status to CLOSED
        job_service.update_job_status(
            job_id=job_id,
            new_status="CLOSED",
            operator_id=current_agent.agent_id
        )
    except JobValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

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
    job_service = JobService(db)

    try:
        # Update job status back to ACTIVE
        job_service.update_job_status(
            job_id=job_id,
            new_status="ACTIVE",
            operator_id=current_agent.agent_id
        )
    except JobValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # TODO: Notify worker via WebSocket about revision request

    return {
        "job_id": job_id,
        "status": "ACTIVE",
        "feedback": feedback,
        "message": "Revision requested. Job status set back to ACTIVE."
    }