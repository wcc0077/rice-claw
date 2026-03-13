"""Bid management endpoints."""

from fastapi import APIRouter, HTTPException

from ..db.bids import create_bid, get_bids_for_job, update_bid_status, get_bid
from ..db.jobs import get_job, count_job_bids
from ..db.agents import get_agent
from ..models.schemas import (
    BidCreate, Quote, BidResponse, BidListResponse
)

router = APIRouter()


@router.post("/{job_id}", response_model=BidResponse)
async def create_bid_endpoint(job_id: str, request: BidCreate):
    """Submit a bid for a job."""
    # Verify job exists and is open
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job["status"] != "OPEN":
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not accepting bids")

    # Verify worker exists
    worker = get_agent(request.worker_id)
    if not worker:
        raise HTTPException(status_code=400, detail=f"Worker {request.worker_id} not found")
    if worker["agent_type"] != "worker":
        raise HTTPException(status_code=400, detail=f"Agent {request.worker_id} is not a worker")

    # Check bid limit
    bid_count = count_job_bids(job_id)
    if bid_count >= job["bid_limit"]:
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

        bid = create_bid(bid_data)
        if bid:
            return BidResponse(**bid)
        raise HTTPException(status_code=500, detail="Failed to create bid")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{job_id}", response_model=BidListResponse)
async def list_bids_endpoint(job_id: str):
    """List all bids for a job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bids = get_bids_for_job(job_id)
    bid_responses = [BidResponse(**bid) for bid in bids]

    return BidListResponse(
        bids=bid_responses,
        bid_limit=job["bid_limit"],
        current_count=len(bids)
    )


@router.post("/{job_id}/{bid_id}/accept")
async def accept_bid_endpoint(job_id: str, bid_id: str):
    """Accept a bid."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bid = get_bid(bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid["job_id"] != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to job")

    if bid["is_hired"]:
        raise HTTPException(status_code=400, detail="Bid already accepted")

    # Update bid status
    updated_bid = update_bid_status(bid_id, "ACCEPTED", is_hired=True)

    # Update job status if all bids are processed
    return {"message": "Bid accepted", "bid": BidResponse(**updated_bid)}


@router.post("/{job_id}/{bid_id}/reject")
async def reject_bid_endpoint(job_id: str, bid_id: str):
    """Reject a bid."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    bid = get_bid(bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")
    if bid["job_id"] != job_id:
        raise HTTPException(status_code=400, detail="Bid does not belong to job")

    updated_bid = update_bid_status(bid_id, "REJECTED", is_hired=False)

    return {"message": "Bid rejected", "bid": BidResponse(**updated_bid)}
