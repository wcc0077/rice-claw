"""Bid management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db import bids as bid_dal
from ..db import jobs as job_dal
from ..db import agents as agent_dal
from ..models.schemas import (
    BidCreate, Quote, BidResponse, BidListResponse
)

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
        raise HTTPException(status_code=400, detail=f"Worker {request.worker_id} not found")
    if worker.agent_type != "worker":
        raise HTTPException(status_code=400, detail=f"Agent {request.worker_id} is not a worker")

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
            result = bid.to_dict()
            result["quote"] = {
                "amount": bid.quote_amount,
                "currency": bid.quote_currency,
                "delivery_days": bid.delivery_days,
            }
            return BidResponse(**result)
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
    """Accept a bid."""
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

    # Update bid status
    updated_bid = bid_dal.update_bid_status(db, bid_id, "ACCEPTED", is_hired=True)

    # Update job status to active
    job_dal.update_job(db, job_id, {"status": "ACTIVE"})

    result = updated_bid.to_dict()
    result["quote"] = {
        "amount": updated_bid.quote_amount,
        "currency": updated_bid.quote_currency,
        "delivery_days": updated_bid.delivery_days,
    }

    return {"message": "Bid accepted", "bid": BidResponse(**result)}


@router.post("/{job_id}/{bid_id}/reject")
async def reject_bid_endpoint(
    job_id: str,
    bid_id: str,
    db: Session = Depends(get_db)
):
    """Reject a bid."""
    job = job_dal.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bid = bid_dal.get_bid(db, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid.job_id != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to job")

    updated_bid = bid_dal.update_bid_status(db, bid_id, "REJECTED", is_hired=False)

    result = updated_bid.to_dict()
    result["quote"] = {
        "amount": updated_bid.quote_amount,
        "currency": updated_bid.quote_currency,
        "delivery_days": updated_bid.delivery_days,
    }

    return {"message": "Bid rejected", "bid": BidResponse(**result)}