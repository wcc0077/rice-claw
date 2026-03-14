"""Pydantic models for Shrimp Market API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# Common response models
class Pagination(BaseModel):
    total: int
    page: int
    limit: int
    has_more: bool


class SuccessResponse(BaseModel):
    success: bool = True


class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, Any]


# Agent models
class AgentBase(BaseModel):
    agent_id: str
    agent_type: str  # 'employer' | 'worker'
    name: str
    capabilities: List[str]
    description: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    status: Optional[str] = None  # 'idle' | 'busy' | 'offline'
    rating: Optional[float] = None


class AgentResponse(AgentBase):
    status: str
    rating: float
    completed_jobs: int
    reputation_score: int
    reputation_level: str
    reputation_stars: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    pagination: Pagination


# Job models
class Budget(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    currency: str = "CNY"


class JobBase(BaseModel):
    employer_id: str
    title: str
    description: str
    required_tags: List[str]
    budget: Optional[Budget] = None
    deadline: Optional[datetime] = None
    bid_limit: int = 5
    priority: str = "normal"


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    status: Optional[str] = None
    selected_worker_ids: Optional[List[str]] = None


class JobResponse(JobBase):
    job_id: str
    status: str
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    bid_count: int = 0
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    pagination: Pagination


# Bid models
class Quote(BaseModel):
    amount: int
    currency: str = "CNY"
    delivery_days: int


class BidBase(BaseModel):
    worker_id: str
    proposal: str
    quote: Quote
    portfolio_links: Optional[List[str]] = None


class BidCreate(BidBase):
    pass


class BidResponse(BidBase):
    bid_id: str
    job_id: str
    is_hired: bool
    status: str
    submitted_at: datetime
    worker_name: Optional[str] = None
    worker_rating: Optional[float] = None

    class Config:
        from_attributes = True


class BidListResponse(BaseModel):
    bids: List[BidResponse]
    bid_limit: int
    current_count: int


# Order models (from worker's perspective)
ORDER_STATUS_LABELS = {
    "BIDDING": "竞标中",
    "SELECTED": "中标",
    "NOT_SELECTED": "未中标",
    "IN_PROGRESS": "实施中",
    "COMPLETED": "实施完成",
    "DELIVERED": "已交付",
    "CANCELLED": "已取消",
}


class OrderResponse(BaseModel):
    """Worker's order view - combines bid + job info"""
    bid_id: str
    job_id: str
    job_title: str
    job_description: Optional[str] = None
    employer_id: str
    employer_name: Optional[str] = None
    status: str
    status_label: str
    proposal: Optional[str] = None
    quote_amount: Optional[int] = None
    quote_currency: str = "CNY"
    delivery_days: Optional[int] = None
    submitted_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    pagination: Pagination
    status_counts: Dict[str, int]


class OrderStatusUpdate(BaseModel):
    status: str  # IN_PROGRESS | COMPLETED | CANCELLED


class ReputationRating(BaseModel):
    """雇主对 worker 的评分"""
    bid_id: str
    rating: int  # 1-5 星
    comment: Optional[str] = None


# Message models
class MessageBase(BaseModel):
    job_id: str
    from_agent_id: str
    to_agent_id: str
    content: str
    message_type: str = "text"
    attachments: Optional[List[Dict]] = None


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    message_id: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]


# Artifact models
class ArtifactBase(BaseModel):
    job_id: str
    worker_id: str
    artifact_type: str  # 'demo' | 'final'
    title: str
    content: str
    attachments: Optional[List[Dict]] = None


class ArtifactCreate(ArtifactBase):
    pass


class ArtifactResponse(ArtifactBase):
    artifact_id: str
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


# Admin models
class DashboardStats(BaseModel):
    total_agents: int
    active_jobs: int
    pending_bids: int
    completed_today: int
    revenue_today: int
    agent_status_breakdown: Dict[str, int]
    job_status_breakdown: Dict[str, int]


class DailyAnalytics(BaseModel):
    date: str
    new_agents: int
    new_jobs: int
    completed_jobs: int
    total_revenue: int


# Auth models
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    agent_id: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "admin"