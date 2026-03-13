"""Database access layer for bids using SQLAlchemy 2.0."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models.db_models import Bid, Job, Agent


def create_bid(db: Session, bid_data: Dict[str, Any]) -> Bid:
    """创建新竞标

    Args:
        db: 数据库会话
        bid_data: 竞标数据

    Returns:
        创建的竞标对象

    Raises:
        ValueError: 任务不存在、任务状态不对、或竞标数已达上限
    """
    # 检查任务状态
    job = db.execute(
        select(Job).where(Job.job_id == bid_data["job_id"])
    ).scalar_one_or_none()

    if not job:
        raise ValueError("Job not found")
    if job.status != "OPEN":
        raise ValueError("Job is not accepting bids")

    # 检查竞标上限
    current_count = db.execute(
        select(func.count()).where(Bid.job_id == bid_data["job_id"])
    ).scalar()

    if current_count >= job.bid_limit:
        raise ValueError("Bid limit reached")

    # 生成竞标ID
    bid_id = f"bid_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # 处理报价数据
    quote = bid_data.get("quote", {})
    portfolio_links = bid_data.get("portfolio_links", [])

    db_bid = Bid(
        bid_id=bid_id,
        job_id=bid_data["job_id"],
        worker_id=bid_data["worker_id"],
        proposal=bid_data.get("proposal"),
        quote_amount=quote.get("amount"),
        quote_currency=quote.get("currency", "CNY"),
        delivery_days=quote.get("delivery_days"),
        portfolio_links=",".join(portfolio_links) if portfolio_links else "",
    )
    db.add(db_bid)
    db.commit()
    db.refresh(db_bid)
    return db_bid


def get_bid(db: Session, bid_id: str) -> Optional[Bid]:
    """获取单个竞标

    Args:
        db: 数据库会话
        bid_id: 竞标ID

    Returns:
        竞标对象或 None
    """
    return db.execute(
        select(Bid).where(Bid.bid_id == bid_id)
    ).scalar_one_or_none()


def get_bid_dict(db: Session, bid_id: str) -> Optional[Dict[str, Any]]:
    """获取单个竞标（字典格式）

    Args:
        db: 数据库会话
        bid_id: 竞标ID

    Returns:
        竞标字典或 None
    """
    bid = get_bid(db, bid_id)
    if not bid:
        return None

    result = bid.to_dict()
    # 添加报价结构
    result["quote"] = {
        "amount": bid.quote_amount,
        "currency": bid.quote_currency,
        "delivery_days": bid.delivery_days,
    }
    return result


def get_bids_for_job(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务的所有竞标

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        竞标字典列表
    """
    bids = db.execute(
        select(Bid)
        .where(Bid.job_id == job_id)
        .order_by(Bid.is_hired.desc(), Bid.submitted_at.asc())
    ).scalars().all()

    results = []
    for bid in bids:
        result = bid.to_dict()
        result["quote"] = {
            "amount": bid.quote_amount,
            "currency": bid.quote_currency,
            "delivery_days": bid.delivery_days,
        }
        results.append(result)

    return results


def get_bids_with_worker_info(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务的竞标（包含工人信息）

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        竞标字典列表（包含 worker_name 和 worker_rating）
    """
    bids = db.execute(
        select(Bid)
        .where(Bid.job_id == job_id)
        .order_by(Bid.is_hired.desc(), Bid.submitted_at.asc())
    ).scalars().all()

    results = []
    for bid in bids:
        result = bid.to_dict()
        result["quote"] = {
            "amount": bid.quote_amount,
            "currency": bid.quote_currency,
            "delivery_days": bid.delivery_days,
        }

        # 获取工人信息
        worker = db.execute(
            select(Agent).where(Agent.agent_id == bid.worker_id)
        ).scalar_one_or_none()

        if worker:
            result["worker_name"] = worker.name
            result["worker_rating"] = float(worker.rating)

        results.append(result)

    return results


def update_bid_status(
    db: Session,
    bid_id: str,
    status: str,
    is_hired: bool = False
) -> Optional[Bid]:
    """更新竞标状态

    Args:
        db: 数据库会话
        bid_id: 竞标ID
        status: 新状态 ('ACCEPTED' | 'REJECTED' | 'PENDING')
        is_hired: 是否被雇佣

    Returns:
        更新后的竞标对象或 None

    Raises:
        ValueError: 无效的状态值
    """
    valid_statuses = ["ACCEPTED", "REJECTED", "PENDING"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}")

    bid = get_bid(db, bid_id)
    if not bid:
        return None

    bid.status = status
    bid.is_hired = is_hired
    db.commit()
    db.refresh(bid)
    return bid


def update_bid_status_dict(
    db: Session,
    bid_id: str,
    status: str,
    is_hired: bool = False
) -> Optional[Dict[str, Any]]:
    """更新竞标状态（返回字典）"""
    bid = update_bid_status(db, bid_id, status, is_hired)
    if not bid:
        return None

    result = bid.to_dict()
    result["quote"] = {
        "amount": bid.quote_amount,
        "currency": bid.quote_currency,
        "delivery_days": bid.delivery_days,
    }
    return result


def get_hired_bids_for_job(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务中被雇佣的竞标

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        竞标字典列表
    """
    bids = db.execute(
        select(Bid)
        .where(Bid.job_id == job_id)
        .where(Bid.is_hired == True)
    ).scalars().all()

    results = []
    for bid in bids:
        result = bid.to_dict()
        result["quote"] = {
            "amount": bid.quote_amount,
            "currency": bid.quote_currency,
            "delivery_days": bid.delivery_days,
        }
        results.append(result)

    return results


# =============================================================================
# 向后兼容的函数
# =============================================================================

def row_to_bid(row) -> Dict[str, Any]:
    """向后兼容：将数据库行转换为字典"""
    if hasattr(row, 'to_dict'):
        result = row.to_dict()
        result["quote"] = {
            "amount": row.quote_amount,
            "currency": row.quote_currency,
            "delivery_days": row.delivery_days,
        }
        return result

    # sqlite3.Row 兼容
    portfolio_links = row["portfolio_links"] or ""
    return {
        "bid_id": row["bid_id"],
        "job_id": row["job_id"],
        "worker_id": row["worker_id"],
        "proposal": row["proposal"],
        "quote": {
            "amount": row["quote_amount"],
            "currency": row["quote_currency"],
            "delivery_days": row["delivery_days"],
        },
        "portfolio_links": portfolio_links.split(",") if portfolio_links else [],
        "is_hired": bool(row["is_hired"]),
        "status": row["status"],
        "submitted_at": row["submitted_at"],
    }