"""SQLAlchemy 2.0 ORM models for Shrimp Market database."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class Agent(Base):
    """代理模型 - 雇主、打工人或两者兼可"""
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(16), nullable=False, default="all")  # 'employer' | 'worker' | 'all'
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    capabilities: Mapped[str] = mapped_column(Text, default="")  # 逗号分隔
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="idle")  # 'idle' | 'busy' | 'offline'
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    # 声誉体系字段
    reputation_score: Mapped[int] = mapped_column(Integer, default=1500)  # 1000-3000
    reputation_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # API Key authentication fields
    api_key_id: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True)
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    api_key_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    # Agent ownership
    owner_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("admin_users.user_id"),
        nullable=True,
        index=True
    )
    # Soft delete fields
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # 关系
    jobs_as_employer: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="employer",
        foreign_keys="Job.employer_id"
    )
    bids: Mapped[List["Bid"]] = relationship("Bid", back_populates="worker")
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="sender",
        foreign_keys="Message.from_agent_id"
    )
    received_messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="receiver",
        foreign_keys="Message.to_agent_id"
    )
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="worker")
    # Agent ownership relationship
    owner: Mapped[Optional["AdminUser"]] = relationship(
        "AdminUser",
        foreign_keys=[owner_id]
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        from ..utils.reputation import get_reputation_level
        name, stars = get_reputation_level(self.reputation_score)
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "capabilities": self.capabilities.split(",") if self.capabilities else [],
            "description": self.description,
            "status": self.status,
            "rating": float(self.rating) if self.rating is not None else 0.0,
            "completed_jobs": self.completed_jobs,
            # 声誉体系字段
            "reputation_score": self.reputation_score,
            "reputation_level": name,
            "reputation_stars": stars,
            # API Key status fields
            "has_api_key": bool(self.api_key_hash),
            "api_key_created_at": self.api_key_created_at.isoformat() if self.api_key_created_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "is_verified": self.is_verified,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Job(Base):
    """任务模型 - 撮合平台 (扩展交易字段)"""
    __tablename__ = "jobs"

    # ========== 原有字段 (保持不变) ==========
    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    employer_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_tags: Mapped[str] = mapped_column(Text, default="")  # 逗号分隔
    budget_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bid_limit: Mapped[int] = mapped_column(Integer, default=5)
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # 'OPEN' | 'BIDDING' | 'LOCKED' | 'WORKING' | 'SELECTED' | 'COMPLETED' | 'CANCELLED'
    selected_worker_ids: Mapped[str] = mapped_column(Text, default="")  # 逗号分隔
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ========== 新增交易字段 (撮合需求) ==========
    # 金额相关 (单位：分)
    reward_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 确切酬金
    deposit_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 订金 (reward × 20%)
    deposit_paid: Mapped[bool] = mapped_column(Boolean, default=False)  # 订金支付状态
    platform_fee: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 平台抽成 (reward × 8%)

    # 锁单相关
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 锁单时间
    lock_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 最晚交付时间

    # 中标者
    winner_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("agents.agent_id"),
        nullable=True
    )  # 中标者 agent_id

    # 支付状态
    final_payment_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING"
    )  # PENDING/PAID/REFUNDED
    final_payment_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 尾款金额

    # 关系
    employer: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="jobs_as_employer",
        foreign_keys=[employer_id]
    )
    bids: Mapped[List["Bid"]] = relationship("Bid", back_populates="job")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="job")
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="job")
    workers: Mapped[List["JobWorker"]] = relationship(
        "JobWorker",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "job_id": self.job_id,
            "employer_id": self.employer_id,
            "title": self.title,
            "description": self.description,
            "required_tags": self.required_tags.split(",") if self.required_tags else [],
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "currency": self.currency,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "bid_limit": self.bid_limit,
            "priority": self.priority,
            "status": self.status,
            "selected_worker_ids": self.selected_worker_ids.split(",") if self.selected_worker_ids else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            # 撮合交易字段
            "reward_amount": self.reward_amount,
            "deposit_amount": self.deposit_amount,
            "deposit_paid": self.deposit_paid,
            "platform_fee": self.platform_fee,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "lock_deadline": self.lock_deadline.isoformat() if self.lock_deadline else None,
            "winner_id": self.winner_id,
            "final_payment_status": self.final_payment_status,
            "final_payment_amount": self.final_payment_amount,
        }


class Bid(Base):
    """竞标模型"""
    __tablename__ = "bids"

    bid_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    proposal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quote_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quote_currency: Mapped[str] = mapped_column(String(8), default="CNY")
    delivery_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    portfolio_links: Mapped[str] = mapped_column(Text, default="")  # 逗号分隔
    is_hired: Mapped[bool] = mapped_column(Boolean, default=False)
    # 订单状态: BIDDING(竞标中) | SELECTED(中标) | NOT_SELECTED(未中标) | IN_PROGRESS(实施中) | COMPLETED(实施完成) | DELIVERED(已交付) | CANCELLED(已取消)
    status: Mapped[str] = mapped_column(String(16), default="BIDDING")
    # 声誉体系字段
    employer_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 星
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    # 关系
    job: Mapped["Job"] = relationship("Job", back_populates="bids")
    worker: Mapped["Agent"] = relationship("Agent", back_populates="bids")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "bid_id": self.bid_id,
            "job_id": self.job_id,
            "worker_id": self.worker_id,
            "proposal": self.proposal,
            "quote_amount": self.quote_amount,
            "quote_currency": self.quote_currency,
            "delivery_days": self.delivery_days,
            "portfolio_links": self.portfolio_links.split(",") if self.portfolio_links else [],
            "is_hired": self.is_hired,
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }

    def to_dict_with_quote(self) -> dict:
        """转换为字典（包含 quote 结构）"""
        result = self.to_dict()
        result["quote"] = {
            "amount": self.quote_amount,
            "currency": self.quote_currency,
            "delivery_days": self.delivery_days,
        }
        return result


class Message(Base):
    """消息模型"""
    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False)
    from_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    to_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(16), default="text")
    attachments: Mapped[str] = mapped_column(Text, default="")  # JSON 字符串
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    # 关系
    job: Mapped["Job"] = relationship("Job", back_populates="messages")
    sender: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="sent_messages",
        foreign_keys=[from_agent_id]
    )
    receiver: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="received_messages",
        foreign_keys=[to_agent_id]
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        import json
        attachments = []
        if self.attachments:
            try:
                attachments = json.loads(self.attachments)
            except json.JSONDecodeError:
                attachments = []

        return {
            "message_id": self.message_id,
            "job_id": self.job_id,
            "from_agent_id": self.from_agent_id,
            "to_agent_id": self.to_agent_id,
            "content": self.content,
            "message_type": self.message_type,
            "attachments": attachments,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Artifact(Base):
    """交付物模型"""
    __tablename__ = "artifacts"

    artifact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(16))  # 'demo' | 'final'
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[str] = mapped_column(Text, default="")  # JSON 字符串
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    # 关系
    job: Mapped["Job"] = relationship("Job", back_populates="artifacts")
    worker: Mapped["Agent"] = relationship("Agent", back_populates="artifacts")

    def to_dict(self) -> dict:
        """转换为字典"""
        import json
        attachments = []
        if self.attachments:
            try:
                attachments = json.loads(self.attachments)
            except json.JSONDecodeError:
                attachments = []

        return {
            "artifact_id": self.artifact_id,
            "job_id": self.job_id,
            "worker_id": self.worker_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "content": self.content,
            "attachments": attachments,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AdminUser(Base):
    """管理员用户模型"""
    __tablename__ = "admin_users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)  # Optional for phone-only users
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(16), default="admin")
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    def to_dict(self) -> dict:
        """转换为字典（不包含密码）"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "phone": self.phone,
            "phone_verified": self.phone_verified,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    """审计日志模型 - 记录所有 API 和 MCP 调用"""
    __tablename__ = "audit_logs"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # tool_call, api_request
    resource_type: Mapped[str] = mapped_column(String(32), nullable=True)  # job, bid, message, agent
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    request_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    response_status: Mapped[int] = mapped_column(Integer, default=200)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    def to_dict(self) -> dict:
        """转换为字典"""
        import json
        request_data_parsed = None
        if self.request_data:
            try:
                request_data_parsed = json.loads(self.request_data)
            except json.JSONDecodeError:
                request_data_parsed = self.request_data

        return {
            "log_id": self.log_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "request_data": request_data_parsed,
            "response_status": self.response_status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReputationLog(Base):
    """声誉变化流水记录"""
    __tablename__ = "reputation_logs"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), ForeignKey("agents.agent_id"), nullable=False, index=True)
    # 变化类型: order_completed, order_cancelled, rating_received, activity_bonus, manual_adjustment
    change_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # 关联资源 (如 bid_id)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # bid, job
    # 分数变化
    score_before: Mapped[int] = mapped_column(Integer, nullable=False)
    score_after: Mapped[int] = mapped_column(Integer, nullable=False)
    score_change: Mapped[int] = mapped_column(Integer, nullable=False)  # +10, -20, etc.
    # 各维度变化
    fulfillment_change: Mapped[int] = mapped_column(Integer, default=0)
    quality_change: Mapped[int] = mapped_column(Integer, default=0)
    activity_change: Mapped[int] = mapped_column(Integer, default=0)
    # 描述
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "log_id": self.log_id,
            "agent_id": self.agent_id,
            "change_type": self.change_type,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "score_before": self.score_before,
            "score_after": self.score_after,
            "score_change": self.score_change,
            "fulfillment_change": self.fulfillment_change,
            "quality_change": self.quality_change,
            "activity_change": self.activity_change,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SmsVerificationCode(Base):
    """短信验证码模型"""
    __tablename__ = "sms_verification_codes"

    code_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    purpose: Mapped[str] = mapped_column(String(16), nullable=False, default="login")  # 'login' | 'bind_phone'
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)  # 验证尝试次数
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "code_id": self.code_id,
            "phone": self.phone,
            "purpose": self.purpose,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used": self.used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SmsRateLimit(Base):
    """短信发送频率限制模型"""
    __tablename__ = "sms_rate_limits"

    phone: Mapped[str] = mapped_column(String(20), primary_key=True)
    send_count: Mapped[int] = mapped_column(Integer, default=1)
    window_start: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())
    last_sent_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "phone": self.phone,
            "send_count": self.send_count,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
        }


# =============================================================================
# 撮合平台新增模型
# =============================================================================


class JobWorker(Base):
    """任务 - 工人关联表 (原 order_items)
    一个任务最多 3 个接单方，独立并行工作
    """
    __tablename__ = "job_workers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False, index=True)
    bid_id: Mapped[str] = mapped_column(ForeignKey("bids.bid_id"), nullable=False)  # 抢单来源
    worker_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)

    # 状态：PENDING/CONFIRMED/WORKING/DELIVERED/WINNER/RUNNER_UP/CANCELLED
    status: Mapped[str] = mapped_column(String(32), default="PENDING")

    # 确认状态
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 交付状态
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 中标结果
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)

    # 补贴 (单位：分)
    subsidy_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 信誉扣分 (取消时)
    credit_penalty: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # 关系
    job: Mapped["Job"] = relationship("Job", back_populates="workers")
    bid: Mapped["Bid"] = relationship("Bid")
    worker: Mapped["Agent"] = relationship("Agent")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "bid_id": self.bid_id,
            "worker_id": self.worker_id,
            "status": self.status,
            "is_confirmed": self.is_confirmed,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "is_winner": self.is_winner,
            "subsidy_amount": self.subsidy_amount,
            "credit_penalty": self.credit_penalty,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ArtifactVersion(Base):
    """交付物版本管理表
    支持多版本迭代，预览图带水印
    """
    __tablename__ = "artifact_versions"

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    artifact_id: Mapped[str] = mapped_column(ForeignKey("artifacts.artifact_id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3...

    # 文件 URL
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    preview_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # 带水印预览

    # 水印状态
    is_watermarked: Mapped[bool] = mapped_column(Boolean, default=False)

    # 上传者
    worker_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)

    # 是否最终版本
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)

    # 版本说明
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    # 关系
    artifact: Mapped["Artifact"] = relationship("Artifact", back_populates="versions")
    worker: Mapped["Agent"] = relationship("Agent")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "version_id": self.version_id,
            "artifact_id": self.artifact_id,
            "version_number": self.version_number,
            "file_url": self.file_url,
            "preview_url": self.preview_url,
            "is_watermarked": self.is_watermarked,
            "worker_id": self.worker_id,
            "is_final": self.is_final,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# 更新 Artifact 模型，添加 versions 关系
Artifact.versions = relationship(
    "ArtifactVersion",
    back_populates="artifact",
    cascade="all, delete-orphan",
    order_by="ArtifactVersion.version_number"
)


class Payment(Base):
    """支付流水表
    记录所有交易：订金、尾款、补贴、罚金、平台抽成
    """
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False, index=True)

    # 交易双方
    payer_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    payee_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)

    # 金额 (单位：分)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    # 支付类型
    # DEPOSIT(订金) / REWARD(酬金) / SUBSIDY(补贴) / PENALTY(罚金) / PLATFORM_FEE(平台抽成) / REFUND(退款)
    type: Mapped[str] = mapped_column(String(32), nullable=False)

    # 支付状态
    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING/SUCCESS/FAILED/REFUNDED

    # 第三方交易 ID
    transaction_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # 描述
    description: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # 关联的 job_worker (可选，用于补贴)
    job_worker_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("job_workers.id"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 结算时间

    # 关系
    job: Mapped["Job"] = relationship("Job", back_populates="payments")
    payer: Mapped["Agent"] = relationship("Agent", foreign_keys=[payer_id])
    payee: Mapped["Agent"] = relationship("Agent", foreign_keys=[payee_id])
    job_worker: Mapped["JobWorker"] = relationship("JobWorker")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "payment_id": self.payment_id,
            "job_id": self.job_id,
            "payer_id": self.payer_id,
            "payee_id": self.payee_id,
            "amount": self.amount,
            "type": self.type,
            "status": self.status,
            "transaction_id": self.transaction_id,
            "description": self.description,
            "job_worker_id": self.job_worker_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "settled_at": self.settled_at.isoformat() if self.settled_at else None,
        }


class WsConnection(Base):
    """WebSocket 连接历史表 (用于审计和离线分析)"""
    __tablename__ = "ws_connections"

    connection_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)
    server_node: Mapped[str] = mapped_column(String(64), nullable=False)  # 服务器节点名

    # 连接时间
    connected_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disconnect_reason: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "connection_id": self.connection_id,
            "agent_id": self.agent_id,
            "server_node": self.server_node,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "disconnected_at": self.disconnected_at.isoformat() if self.disconnected_at else None,
            "disconnect_reason": self.disconnect_reason,
        }


class MessageDelivery(Base):
    """消息送达状态表"""
    __tablename__ = "message_delivery"

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False, index=True)

    # 送达/阅读状态
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "recipient_id": self.recipient_id,
            "delivered": self.delivered,
            "read": self.read,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }