"""Order management endpoints for workers."""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db import bids as bid_dal
from ..models.schemas import (
    OrderListResponse, OrderResponse, OrderStatusUpdate, Pagination
)

router = APIRouter()


@router.get("", response_model=OrderListResponse)
async def list_my_orders(
    worker_id: str = Query(..., description="Worker ID to fetch orders for"),
    status: str = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get orders for a worker (their bids with job info)."""
    result = bid_dal.get_worker_orders(
        db,
        worker_id=worker_id,
        status=status,
        page=page,
        limit=limit
    )

    return OrderListResponse(
        orders=[OrderResponse(**order) for order in result["orders"]],
        pagination=Pagination(**result["pagination"]),
        status_counts=result["status_counts"]
    )


@router.get("/{bid_id}", response_model=OrderResponse)
async def get_order_detail(
    bid_id: str,
    worker_id: str = Query(..., description="Worker ID for authorization"),
    db: Session = Depends(get_db)
):
    """Get details of a specific order."""
    order = bid_dal.get_order_detail(db, bid_id, worker_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderResponse(**order)


@router.patch("/{bid_id}/status")
async def update_order_status(
    bid_id: str,
    request: OrderStatusUpdate,
    worker_id: str = Query(..., description="Worker ID for authorization"),
    db: Session = Depends(get_db)
):
    """Update order status (worker actions: start work, complete, cancel)."""
    # Verify ownership
    order = bid_dal.get_order_detail(db, bid_id, worker_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate status transition
    current_status = order["status"]
    new_status = request.status

    # Define valid transitions
    valid_transitions = {
        "SELECTED": ["IN_PROGRESS", "CANCELLED"],      # 中标 -> 实施中/已取消
        "IN_PROGRESS": ["COMPLETED", "CANCELLED"],     # 实施中 -> 实施完成/已取消
        "COMPLETED": [],                                # 实施完成只能由雇主确认交付
        "DELIVERED": [],                                # 已交付不可更改
        "CANCELLED": [],                                # 已取消不可更改
        "BIDDING": ["CANCELLED"],                       # 竞标中可以取消竞标
        "NOT_SELECTED": [],                             # 未中标不可更改
    }

    # 向后兼容旧状态
    valid_transitions["ACCEPTED"] = ["IN_PROGRESS", "CANCELLED"]
    valid_transitions["PENDING"] = ["CANCELLED"]

    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {current_status} to {new_status}"
        )

    # Update status
    updated_bid = bid_dal.update_bid_status(db, bid_id, new_status)

    if not updated_bid:
        raise HTTPException(status_code=500, detail="Failed to update status")

    return {
        "message": "Status updated",
        "bid_id": bid_id,
        "old_status": current_status,
        "new_status": new_status
    }