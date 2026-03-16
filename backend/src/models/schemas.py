"""Pydantic models for Shrimp Market API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from ..constants import ORDER_STATUS_LABELS


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
    agent_type: str = "all"  # 'employer' | 'worker' | 'all' (default: 'all')
    name: str
    capabilities: List[str]
    description: Optional[str] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    status: Optional[str] = None  # 'idle' | 'busy' | 'offline'
    rating: Optional[float] = None


class AgentEdit(BaseModel):
    """For editing agent details"""
    name: Optional[str] = None
    capabilities: Optional[List[str]] = None
    description: Optional[str] = None


class AgentResponse(AgentBase):
    status: str
    rating: float
    completed_jobs: int
    reputation_score: int
    reputation_level: str
    reputation_stars: str
    created_at: datetime
    updated_at: datetime
    # API Key status fields
    has_api_key: bool = False
    api_key_created_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    is_verified: bool = False

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


# SMS Auth models
class SendSMSRequest(BaseModel):
    phone: str


class SMSLoginRequest(BaseModel):
    phone: str
    code: str


class SMSLoginResponse(BaseModel):
    success: bool = True
    token: str
    user: Dict[str, Any]
    is_new_user: bool = False


class SendSMSResponse(BaseModel):
    success: bool = True
    message: str = "验证码已发送"


# =============================================================================
# 撮合平台 Schemas (Matching Platform Schemas)
# =============================================================================

# Job Service schemas
class JobPublishRequest(BaseModel):
    """发布任务请求"""
    title: str
    description: str = ""
    required_tags: List[str] = []
    reward_amount: int = 0  # 酬金 (分)
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    bid_limit: int = 3
    deadline: Optional[datetime] = None
    priority: str = "normal"


class JobPublishResponse(BaseModel):
    """发布任务响应"""
    job_id: str
    title: str
    status: str
    reward_amount: int
    deposit_amount: int
    bid_limit: int
    created_at: Optional[datetime] = None


class GrabOrderRequest(BaseModel):
    """抢单请求"""
    proposal: str = ""
    quote: Optional[Quote] = None


class GrabOrderResponse(BaseModel):
    """抢单响应"""
    success: bool
    bid_id: str
    job_id: str
    message: str


class DispatchOrderRequest(BaseModel):
    """派单请求"""
    selected_bid_ids: List[str]
    employer_id: str


class DispatchOrderResponse(BaseModel):
    """派单响应"""
    success: bool
    message: str
    job_id: str
    selected_bid_ids: List[str]


class LockPaymentRequest(BaseModel):
    """锁单支付确认请求"""
    bid_id: str
    worker_id: str
    transaction_id: str


class LockPaymentResponse(BaseModel):
    """锁单支付响应"""
    success: bool
    payment_id: str
    deposit_amount: int
    lock_deadline: str


class CloseJobRequest(BaseModel):
    """关闭任务请求"""
    winner_bid_id: Optional[str] = None
    closer_id: str = ""


class CloseJobResponse(BaseModel):
    """关闭任务响应"""
    success: bool
    job_id: str
    winner_bid_id: Optional[str]
    message: str


# Payment Service schemas
class DepositPaymentRequest(BaseModel):
    """订金支付请求"""
    worker_id: str
    transaction_id: str


class FinalPaymentRequest(BaseModel):
    """尾款支付请求"""
    winner_bid_id: str
    transaction_id: str


class SubsidyPaymentRequest(BaseModel):
    """补贴支付请求"""
    job_worker_id: str
    subsidy_amount: int
    transaction_id: str


class RefundRequest(BaseModel):
    """退款请求"""
    payment_id: str
    refund_amount: Optional[int] = None
    reason: str = ""


class PaymentStatusResponse(BaseModel):
    """支付状态响应"""
    success: bool
    job_id: str
    deposit_amount: int
    deposit_paid: int
    deposit_paid_status: str
    reward_amount: int
    final_amount: int
    final_paid: int
    final_paid_status: str
    subsidy_paid: int
    total_paid: int
    payments: List[Dict[str, Any]]


# Dispatch Service schemas
class CancelDispatchRequest(BaseModel):
    """取消派单请求"""
    bid_id: str
    employer_id: str
    reason: str = ""


class ConfirmWorkerReadyRequest(BaseModel):
    """工人就绪确认请求"""
    worker_id: str