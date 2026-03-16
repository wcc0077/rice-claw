"""Database access layer for payments using SQLAlchemy 2.0."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models.db_models import Payment


def generate_id() -> str:
    """生成 payment ID"""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    short_uuid = uuid.uuid4().hex[:6]
    return f"pay_{timestamp}_{short_uuid}"


def create_payment(db: Session, payment_data: Dict[str, Any]) -> Payment:
    """创建支付记录

    Args:
        db: 数据库会话
        payment_data: 支付数据

    Returns:
        创建的 Payment 对象
    """
    payment_id = generate_id()

    db_payment = Payment(
        payment_id=payment_id,
        job_id=payment_data["job_id"],
        payer_id=payment_data["payer_id"],
        payee_id=payment_data["payee_id"],
        amount=payment_data["amount"],
        type=payment_data["type"],  # DEPOSIT/REWARD/SUBSIDY/PENALTY/PLATFORM_FEE
        status=payment_data.get("status", "PENDING"),
        transaction_id=payment_data.get("transaction_id"),
        description=payment_data.get("description"),
        job_worker_id=payment_data.get("job_worker_id"),
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def get_payment(db: Session, payment_id: str) -> Optional[Payment]:
    """获取单个支付记录

    Args:
        db: 数据库会话
        payment_id: 支付 ID

    Returns:
        Payment 对象或 None
    """
    return db.execute(
        select(Payment).where(Payment.payment_id == payment_id)
    ).scalar_one_or_none()


def get_payments_for_job(
    db: Session,
    job_id: str,
    payment_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取任务的所有支付记录

    Args:
        db: 数据库会话
        job_id: 任务 ID
        payment_type: 支付类型筛选 (可选)

    Returns:
        支付记录列表
    """
    query = select(Payment).where(Payment.job_id == job_id)

    if payment_type:
        query = query.where(Payment.type == payment_type)

    results = db.execute(query).scalars().all()
    return [p.to_dict() for p in results]


def update_payment_status(
    db: Session,
    payment_id: str,
    new_status: str,
    transaction_id: Optional[str] = None
) -> Optional[Payment]:
    """更新支付状态

    Args:
        db: 数据库会话
        payment_id: 支付 ID
        new_status: 新状态 (SUCCESS/FAILED/REFUNDED)
        transaction_id: 第三方交易 ID (可选)

    Returns:
        更新后的 Payment 对象或 None
    """
    payment = get_payment(db, payment_id)
    if not payment:
        return None

    payment.status = new_status
    if transaction_id:
        payment.transaction_id = transaction_id
    if new_status in ("SUCCESS", "REFUNDED"):
        payment.settled_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(payment)
    return payment


def mark_payment_success(
    db: Session,
    payment_id: str,
    transaction_id: Optional[str] = None
) -> Optional[Payment]:
    """标记支付成功

    Args:
        db: 数据库会话
        payment_id: 支付 ID
        transaction_id: 第三方交易 ID

    Returns:
        更新后的 Payment 对象或 None
    """
    return update_payment_status(db, payment_id, "SUCCESS", transaction_id)


def mark_payment_failed(
    db: Session,
    payment_id: str
) -> Optional[Payment]:
    """标记支付失败

    Args:
        db: 数据库会话
        payment_id: 支付 ID

    Returns:
        更新后的 Payment 对象或 None
    """
    return update_payment_status(db, payment_id, "FAILED")


def get_deposit_payment(
    db: Session,
    job_id: str
) -> Optional[Dict[str, Any]]:
    """获取订金支付记录

    Args:
        db: 数据库会话
        job_id: 任务 ID

    Returns:
        订金支付记录或 None
    """
    payment = db.execute(
        select(Payment)
        .where(Payment.job_id == job_id)
        .where(Payment.type == "DEPOSIT")
    ).scalar_one_or_none()

    return payment.to_dict() if payment else None


def get_pending_payments_for_job(
    db: Session,
    job_id: str
) -> List[Dict[str, Any]]:
    """获取任务中待处理的支付

    Args:
        db: 数据库会话
        job_id: 任务 ID

    Returns:
        待处理支付列表
    """
    payments = db.execute(
        select(Payment)
        .where(Payment.job_id == job_id)
        .where(Payment.status == "PENDING")
    ).scalars().all()
    return [p.to_dict() for p in payments]


def get_total_paid_amount(
    db: Session,
    job_id: str,
    payee_id: Optional[str] = None
) -> int:
    """获取任务已支付总额

    Args:
        db: 数据库会话
        job_id: 任务 ID
        payee_id: 收款人 ID (可选)

    Returns:
        已支付总额 (分)
    """
    query = select(func.sum(Payment.amount)).where(
        Payment.job_id == job_id,
        Payment.status == "SUCCESS"
    )

    if payee_id:
        query = query.where(Payment.payee_id == payee_id)

    result = db.execute(query).scalar()
    return result or 0


def refund_payment(
    db: Session,
    payment_id: str,
    refund_amount: Optional[int] = None
) -> Optional[Payment]:
    """退款/罚金处理

    Args:
        db: 数据库会话
        payment_id: 原支付 ID
        refund_amount: 退款金额 (不填则全额退款)

    Returns:
        新创建的退款支付记录
    """
    original = get_payment(db, payment_id)
    if not original:
        return None

    # 创建退款记录
    refund_data = {
        "job_id": original.job_id,
        "payer_id": original.payee_id,  # 原收款人变成退款人
        "payee_id": original.payer_id,  # 原付款人变成收款人
        "amount": refund_amount or original.amount,
        "type": "REFUND",
        "status": "PENDING",
        "description": f"Refund for payment {payment_id}",
    }

    return create_payment(db, refund_data)
