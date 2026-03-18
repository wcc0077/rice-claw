"""Bid management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db import bids as bid_dal
from ..db import jobs as job_dal
from ..db import agents as agent_dal
from ..models.schemas import (
    BidCreate, BidResponse, BidListResponse,
    ReputationRating
)
from ..models.db_models import AdminUser
from ..utils.reputation import update_agent_reputation, get_reputation_change_description
from ..services import BidService, BidValidationError
from ..auth.dependencies import get_current_admin_user
from ..auth.permissions import PermissionDeniedError

router = APIRouter()


def verify_job_owner(db: Session, job_id: str, admin: AdminUser) -> bool:
    """验证 job 是否属于当前管理员的 Agent"""
    job = job_dal.get_job(db, job_id)
    if not job:
        return False
    employer = agent_dal.get_agent(db, job.employer_id)
    if not employer:
        return False
    return employer.owner_id == admin.user_id


@router.get("/detail/{bid_id}")
async def get_bid_detail_endpoint(
    bid_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Get bid details by bid_id.

    Returns bid info with associated job and worker details.
    Only admin users can access this endpoint.
    """
    bid = bid_dal.get_bid_detail(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")

    # 验证权限：检查 bid 关联的 job 是否属于当前用户
    if bid.get("job"):
        job = job_dal.get_job(db, bid["job"]["job_id"])
        if job:
            employer = agent_dal.get_agent(db, job.employer_id)
            if not employer or employer.owner_id != current_admin.user_id:
                # 也允许 bid 的 worker 查看
                worker = agent_dal.get_agent(db, bid["worker_id"])
                if not worker or worker.owner_id != current_admin.user_id:
                    raise HTTPException(status_code=403, detail="You don't have permission to view this bid")

    return bid


@router.post("/{job_id}", response_model=BidResponse)
async def create_bid_endpoint(
    job_id: str,
    request: BidCreate,
    db: Session = Depends(get_db)
):
    """Submit a bid for a job."""
    bid_service = BidService(db)

    try:
        bid = bid_service.create_bid(
            job_id=job_id,
            worker_id=request.worker_id,
            proposal=request.proposal,
            quote={
                "amount": request.quote.amount,
                "currency": request.quote.currency,
                "delivery_days": request.quote.delivery_days,
            },
            portfolio_links=request.portfolio_links
        )
        return BidResponse(**bid)
    except BidValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{job_id}", response_model=BidListResponse)
async def list_bids_endpoint(
    job_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """List all bids for a job (only if job is owned by current user's agent)."""
    # 验证 job 属于当前用户
    if not verify_job_owner(db, job_id, current_admin):
        raise HTTPException(status_code=403, detail="You don't have permission to view this job's bids")

    bid_service = BidService(db)

    try:
        bids = bid_service.get_bids_for_job(job_id)
    except BidValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 获取 job 信息
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bid_responses = [BidResponse(**bid) for bid in bids]

    return BidListResponse(
        bids=bid_responses,
        bid_limit=job.bid_limit,
        current_count=len(bids)
    )


@router.post("/{job_id}/{bid_id}/accept")
async def accept_bid_endpoint(
    job_id: str,
    bid_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Accept a bid (marks as SELECTED, others as NOT_SELECTED).

    Only the job owner (admin who owns the employer agent) can accept bids.
    """
    # 验证 job 属于当前用户
    if not verify_job_owner(db, job_id, current_admin):
        raise HTTPException(status_code=403, detail="You don't have permission to accept bids for this job")

    bid_service = BidService(db)

    try:
        # 获取 job 的 employer_id
        job = job_dal.get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        updated_bid = bid_service.accept_bid(
            job_id=job_id,
            bid_id=bid_id,
            employer_id=job.employer_id
        )
        return {"message": "Bid accepted", "bid": BidResponse(**updated_bid)}
    except BidValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{job_id}/{bid_id}/reject")
async def reject_bid_endpoint(
    job_id: str,
    bid_id: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """Reject a bid (marks as NOT_SELECTED).

    Only the job owner (admin who owns the employer agent) can reject bids.
    """
    # 验证 job 属于当前用户
    if not verify_job_owner(db, job_id, current_admin):
        raise HTTPException(status_code=403, detail="You don't have permission to reject bids for this job")

    bid_service = BidService(db)

    try:
        # 获取 job 的 employer_id
        job = job_dal.get_job(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        updated_bid = bid_service.reject_bid(
            job_id=job_id,
            bid_id=bid_id,
            employer_id=job.employer_id
        )
        return {"message": "Bid rejected", "bid": BidResponse(**updated_bid)}
    except BidValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/{job_id}/{bid_id}/rate")
async def rate_bid_endpoint(
    job_id: str,
    bid_id: str,
    request: ReputationRating,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """雇主对完成的订单进行评分（影响 worker 声誉）

    仅在订单状态为 COMPLETED 或 DELIVERED 时可用。
    仅 job 所有者可以评分。
    """
    # 验证 job 属于当前用户
    if not verify_job_owner(db, job_id, current_admin):
        raise HTTPException(status_code=403, detail="You don't have permission to rate this job")

    # 验证订单存在
    bid = bid_dal.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid.job_id != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to job")

    # 验证订单状态
    if bid.status not in ['COMPLETED', 'DELIVERED']:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot rate bid with status {bid.status}. Must be COMPLETED or DELIVERED."
        )

    # 验证评分范围
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # 更新评分
    bid = bid_dal.update_bid_employer_rating(db, bid_id, request.rating)
    if not bid:
        raise HTTPException(status_code=500, detail="Failed to update rating")

    # 更新 worker 声誉
    old_score = bid.worker.reputation_score
    worker = update_agent_reputation(db, bid.worker_id)
    change_desc = get_reputation_change_description(old_score, worker.reputation_score)

    return {
        "message": "Rating submitted",
        "bid_id": bid_id,
        "rating": request.rating,
        "comment": request.comment,
        "worker_reputation": {
            "score": worker.reputation_score,
            "change": change_desc
        }
    }