"""API routes aggregation."""

from fastapi import APIRouter

from . import agents, jobs, bids, messages, admin

router = APIRouter()

# Include sub-routers
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(bids.router, prefix="/bids", tags=["bids"])
router.include_router(messages.router, prefix="/messages", tags=["messages"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
