"""Bid management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db import bids as bid_dal
from ..db import jobs as job_dal
from ..db import agents as agent_dal
from ..models.schemas import (
    BidCreate, Quote, BidResponse, BidListResponse,
    ReputationRating
)
from ..utils.reputation import update_agent_reputation, get_reputation_change_description

router = APIRouter()


@router.post("/{job_id}", response_model=BidResponse)
async def create_bid_endpoint(
    job_id: str,
    request: BidCreate,
    db: Session = Depends(get_db)
):
    """Submit a bid for a job."""
    # Verify job exists and is open
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != "OPEN":
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not accepting bids")

    # Verify worker exists
    worker = agent_dal.get_agent(db, request.worker_id)
    if not worker:
        raise HTTPException(status_code=400, detail=f"Lobster {request.worker_id} not found")

    # Check bid limit
    bid_count = bid_dal.get_bids_for_job(db, job_id)
    if len(bid_count) >= job.bid_limit:
        raise HTTPException(status_code=400, detail="Bid limit reached")

    try:
        bid_data = {
            "job_id": job_id,
            "worker_id": request.worker_id,
            "proposal": request.proposal,
            "quote": {
                "amount": request.quote.amount,
                "currency": request.quote.currency,
                "delivery_days": request.quote.delivery_days,
            },
            "portfolio_links": request.portfolio_links,
        }

        bid = bid_dal.create_bid(db, bid_data)
        if bid:
            return BidResponse(**bid.to_dict_with_quote())
        raise HTTPException(status_code=500, detail="Failed to create bid")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{job_id}", response_model=BidListResponse)
async def list_bids_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """List all bids for a job."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bids = bid_dal.get_bids_with_worker_info(db, job_id)
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
    db: Session = Depends(get_db)
):
    """Accept a bid (marks as SELECTED, others as NOT_SELECTED)."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bid = bid_dal.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid.job_id != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to job")

    if bid.is_hired:
        raise HTTPException(status_code=400, detail="Bid already accepted")

    # Mark this bid as SELECTED
    updated_bid = bid_dal.update_bid_status(db, bid_id, "SELECTED", is_hired=True)
    if not updated_bid:
        raise HTTPException(status_code=500, detail="Failed to update bid status")

    # Bulk update other bids to NOT_SELECTED (single query instead of N queries)
    bid_dal.bulk_update_bids_status(db, job_id, bid_id, "NOT_SELECTED")

    # Update job status to active
    job_dal.update_job(db, job_id, {"status": "ACTIVE"})

    return {"message": "Bid accepted", "bid": BidResponse(**updated_bid.to_dict_with_quote())}


@router.post("/{job_id}/{bid_id}/reject")
async def reject_bid_endpoint(
    job_id: str,
    bid_id: str,
    db: Session = Depends(get_db)
):
    """Reject a bid (marks as NOT_SELECTED)."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bid = bid_dal.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid.job_id != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to job")

    updated_bid = bid_dal.update_bid_status(db, bid_id, "NOT_SELECTED", is_hired=False)
    if not updated_bid:
        raise HTTPException(status_code=500, detail="Failed to update bid status")

    return {"message": "Bid rejected", "bid": BidResponse(**updated_bid.to_dict_with_quote())}


@router.post("/{job_id}/{bid_id}/rate")
async def rate_bid_endpoint(
    job_id: str,
    bid_id: str,
    request: ReputationRating,
    db: Session = Depends(get_db)
):
    """雇主对完成的订单进行评分（影响 worker 声誉）

    仅在订单状态为 COMPLETED 或 DELIVERED 时可用。
    """
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