"""Database access layer for bids using SQLAlchemy 2.0."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, update

from ..models.db_models import Bid, Job, Agent
from ..constants import (
    OrderStatus,
    VALID_ORDER_STATUSES,
    ORDER_STATUS_LABELS,
    STATUS_NORMALIZE,
)


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
    """获取单个竞标（字典格式）"""
    bid = get_bid(db, bid_id)
    if not bid:
        return None
    return bid.to_dict_with_quote()


def get_bids_for_job(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务的所有竞标"""
    bids = db.execute(
        select(Bid)
        .where(Bid.job_id == job_id)
        .order_by(Bid.is_hired.desc(), Bid.submitted_at.asc())
    ).scalars().all()

    return [bid.to_dict_with_quote() for bid in bids]


def get_bids_with_worker_info(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务的竞标（包含工人信息）- 使用 eager loading 避免 N+1 查询"""
    bids = db.execute(
        select(Bid)
        .options(selectinload(Bid.worker))
        .where(Bid.job_id == job_id)
        .order_by(Bid.is_hired.desc(), Bid.submitted_at.asc())
    ).scalars().all()

    results = []
    for bid in bids:
        result = bid.to_dict_with_quote()
        if bid.worker:
            result["worker_name"] = bid.worker.name
            result["worker_rating"] = float(bid.worker.rating)
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
        status: 新状态
        is_hired: 是否被雇佣

    Returns:
        更新后的竞标对象或 None

    Raises:
        ValueError: 无效的状态值
    """
    if status not in VALID_ORDER_STATUSES:
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
    return bid.to_dict_with_quote() if bid else None


def get_hired_bids_for_job(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务中被雇佣的竞标"""
    bids = db.execute(
        select(Bid)
        .where(Bid.job_id == job_id)
        .where(Bid.is_hired == True)
    ).scalars().all()

    return [bid.to_dict_with_quote() for bid in bids]


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


# =============================================================================
# 订单相关函数 (Order functions)
# =============================================================================


def _build_order_dict(bid: Bid, job: Optional[Job] = None, employer: Optional[Agent] = None) -> Dict[str, Any]:
    """构建订单字典的辅助函数"""
    return {
        "bid_id": bid.bid_id,
        "job_id": bid.job_id,
        "job_title": job.title if job else "Unknown Job",
        "job_description": job.description if job else None,
        "employer_id": job.employer_id if job else None,
        "employer_name": employer.name if employer else None,
        "status": bid.status,
        "status_label": ORDER_STATUS_LABELS.get(bid.status, bid.status),
        "proposal": bid.proposal,
        "quote_amount": bid.quote_amount,
        "quote_currency": bid.quote_currency,
        "delivery_days": bid.delivery_days,
        "submitted_at": bid.submitted_at.isoformat() if bid.submitted_at else None,
    }


def get_worker_orders(
    db: Session,
    worker_id: str,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> Dict[str, Any]:
    """获取工人的订单列表 - 使用 eager loading 避免 N+1 查询"""
    # 构建基础查询
    base_query = select(Bid).where(Bid.worker_id == worker_id)

    # 状态过滤 - 支持新旧状态名称
    if status:
        # Get legacy status if applicable
        legacy_status = {
            OrderStatus.BIDDING: OrderStatus.PENDING,
            OrderStatus.SELECTED: OrderStatus.ACCEPTED,
            OrderStatus.NOT_SELECTED: OrderStatus.REJECTED,
        }.get(status)

        if legacy_status:
            base_query = base_query.where(
                (Bid.status == status) | (Bid.status == legacy_status)
            )
        else:
            base_query = base_query.where(Bid.status == status)

    # 计算总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total = db.execute(count_query).scalar() or 0

    # 分页查询 - 使用 selectinload 预加载 job 和 employer
    offset = (page - 1) * limit
    orders_query = (
        base_query
        .options(selectinload(Bid.job).selectinload(Job.employer))
        .order_by(Bid.submitted_at.desc())
        .offset(offset)
        .limit(limit)
    )
    bids = db.execute(orders_query).scalars().all()

    # 获取状态统计
    status_counts_query = (
        select(Bid.status, func.count().label("count"))
        .where(Bid.worker_id == worker_id)
        .group_by(Bid.status)
    )
    status_counts_result = db.execute(status_counts_query).all()
    raw_counts = {row.status: row.count for row in status_counts_result}
    status_counts = {}
    for st, count in raw_counts.items():
        normalized = STATUS_NORMALIZE.get(st, st)
        status_counts[normalized] = status_counts.get(normalized, 0) + count

    # 构建订单列表 - 无需额外查询
    orders = [_build_order_dict(bid, bid.job, bid.job.employer if bid.job else None) for bid in bids]

    return {
        "orders": orders,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": total > page * limit,
        },
        "status_counts": status_counts,
    }


def bulk_update_bids_status(
    db: Session,
    job_id: str,
    exclude_bid_id: str,
    new_status: str = "NOT_SELECTED"
) -> int:
    """批量更新任务的其他竞标状态

    Args:
        db: 数据库会话
        job_id: 任务ID
        exclude_bid_id: 排除的竞标ID
        new_status: 新状态

    Returns:
        更新的记录数
    """
    result = db.execute(
        update(Bid)
        .where(Bid.job_id == job_id)
        .where(Bid.bid_id != exclude_bid_id)
        .where(Bid.status == "BIDDING")
        .values(status=new_status, is_hired=False)
    )
    db.commit()
    return result.rowcount


def get_order_detail(db: Session, bid_id: str, worker_id: str) -> Optional[Dict[str, Any]]:
    """获取订单详情 - 使用 eager loading 避免 N+1 查询"""
    bid = db.execute(
        select(Bid)
        .options(selectinload(Bid.job).selectinload(Job.employer))
        .where(Bid.bid_id == bid_id, Bid.worker_id == worker_id)
    ).scalar_one_or_none()

    if not bid:
        return None

    return _build_order_dict(bid, bid.job, bid.job.employer if bid.job else None)