"""SQLAlchemy 2.0 ORM models for Shrimp Market database."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class Agent(Base):
    """代理模型 - 雇主或打工人"""
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'employer' | 'worker'
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
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    api_key_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
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
            "reputation_score": self.reputation_score,
            "reputation_level": name,
            "reputation_stars": stars,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Job(Base):
    """任务模型"""
    __tablename__ = "jobs"

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
    status: Mapped[str] = mapped_column(String(16), default="OPEN")  # 'OPEN' | 'ACTIVE' | 'REVIEW' | 'CLOSED'
    selected_worker_ids: Mapped[str] = mapped_column(Text, default="")  # 逗号分隔
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关系
    employer: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="jobs_as_employer",
        foreign_keys=[employer_id]
    )
    bids: Mapped[List["Bid"]] = relationship("Bid", back_populates="job")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="job")
    artifacts: Mapped[List["Artifact"]] = relationship("Artifact", back_populates="job")

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
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="admin")
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.current_timestamp())

    def to_dict(self) -> dict:
        """转换为字典（不包含密码）"""
        return {
            "user_id": self.user_id,
            "username": self.username,
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