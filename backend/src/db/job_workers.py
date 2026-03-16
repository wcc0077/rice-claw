"""Database access layer for job_workers using SQLAlchemy 2.0."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models.db_models import JobWorker, Job, Bid, Agent


def generate_id() -> str:
    """生成 job_worker ID"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    short_uuid = uuid.uuid4().hex[:6]
    return f"jw_{timestamp}_{short_uuid}"


def create_job_worker(db: Session, job_worker_data: Dict[str, Any]) -> JobWorker:
    """创建任务 - 工人关联

    Args:
        db: 数据库会话
        job_worker_data: 关联数据，包含 job_id, bid_id, worker_id

    Returns:
        创建的 JobWorker 对象
    """
    job_worker_id = generate_id()

    db_job_worker = JobWorker(
        id=job_worker_id,
        job_id=job_worker_data["job_id"],
        bid_id=job_worker_data["bid_id"],
        worker_id=job_worker_data["worker_id"],
        status=job_worker_data.get("status", "PENDING"),
    )
    db.add(db_job_worker)
    db.commit()
    db.refresh(db_job_worker)
    return db_job_worker


def get_job_worker(db: Session, job_worker_id: str) -> Optional[JobWorker]:
    """获取单个任务 - 工人关联

    Args:
        db: 数据库会话
        job_worker_id: 关联 ID

    Returns:
        JobWorker 对象或 None
    """
    return db.execute(
        select(JobWorker).where(JobWorker.id == job_worker_id)
    ).scalar_one_or_none()


def get_job_workers_for_job(
    db: Session,
    job_id: str,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取任务的所有工人关联

    Args:
        db: 数据库会话
        job_id: 任务 ID
        status: 状态筛选 (可选)

    Returns:
        工人关联列表
    """
    query = select(JobWorker).where(JobWorker.job_id == job_id)

    if status:
        query = query.where(JobWorker.status == status)

    results = db.execute(query).scalars().all()
    return [jw.to_dict() for jw in results]


def get_job_workers_for_worker(
    db: Session,
    worker_id: str,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """获取工人的所有任务关联

    Args:
        db: 数据库会话
        worker_id: 工人 ID
        status: 状态筛选 (可选)

    Returns:
        任务关联列表
    """
    query = select(JobWorker).where(JobWorker.worker_id == worker_id)

    if status:
        query = query.where(JobWorker.status == status)

    results = db.execute(query).scalars().all()
    return [jw.to_dict() for jw in results]


def update_job_worker_status(
    db: Session,
    job_worker_id: str,
    new_status: str
) -> Optional[JobWorker]:
    """更新工人关联状态

    Args:
        db: 数据库会话
        job_worker_id: 关联 ID
        new_status: 新状态

    Returns:
        更新后的 JobWorker 对象或 None
    """
    job_worker = get_job_worker(db, job_worker_id)
    if not job_worker:
        return None

    job_worker.status = new_status
    db.commit()
    db.refresh(job_worker)
    return job_worker


def confirm_job_worker(
    db: Session,
    job_worker_id: str
) -> Optional[JobWorker]:
    """确认接单

    Args:
        db: 数据库会话
        job_worker_id: 关联 ID

    Returns:
        更新后的 JobWorker 对象或 None
    """
    job_worker = get_job_worker(db, job_worker_id)
    if not job_worker:
        return None

    job_worker.is_confirmed = True
    job_worker.confirmed_at = datetime.utcnow()
    job_worker.status = "CONFIRMED"
    db.commit()
    db.refresh(job_worker)
    return job_worker


def mark_as_winner(
    db: Session,
    job_worker_id: str,
    subsidy_amount: Optional[int] = None
) -> Optional[JobWorker]:
    """标记为中标者

    Args:
        db: 数据库会话
        job_worker_id: 关联 ID
        subsidy_amount: 补贴金额 (可选)

    Returns:
        更新后的 JobWorker 对象或 None
    """
    job_worker = get_job_worker(db, job_worker_id)
    if not job_worker:
        return None

    job_worker.is_winner = True
    job_worker.status = "WINNER"
    if subsidy_amount is not None:
        job_worker.subsidy_amount = subsidy_amount
    db.commit()
    db.refresh(job_worker)
    return job_worker


def mark_as_runner_up(
    db: Session,
    job_worker_id: str,
    subsidy_amount: Optional[int] = None
) -> Optional[JobWorker]:
    """标记为陪标方

    Args:
        db: 数据库会话
        job_worker_id: 关联 ID
        subsidy_amount: 补贴金额 (可选)

    Returns:
        更新后的 JobWorker 对象或 None
    """
    job_worker = get_job_worker(db, job_worker_id)
    if not job_worker:
        return None

    job_worker.is_winner = False
    job_worker.status = "RUNNER_UP"
    if subsidy_amount is not None:
        job_worker.subsidy_amount = subsidy_amount
    db.commit()
    db.refresh(job_worker)
    return job_worker


def cancel_job_worker(
    db: Session,
    job_worker_id: str,
    credit_penalty: int = 50
) -> Optional[JobWorker]:
    """取消关联 (扣信誉分)

    Args:
        db: 数据库会话
        job_worker_id: 关联 ID
        credit_penalty: 信誉扣分 (默认 50)

    Returns:
        更新后的 JobWorker 对象或 None
    """
    job_worker = get_job_worker(db, job_worker_id)
    if not job_worker:
        return None

    job_worker.status = "CANCELLED"
    job_worker.credit_penalty = credit_penalty
    db.commit()
    db.refresh(job_worker)
    return job_worker


def count_job_workers_for_job(db: Session, job_id: str) -> int:
    """统计任务的工人关联数

    Args:
        db: 数据库会话
        job_id: 任务 ID

    Returns:
        数量
    """
    return db.execute(
        select(func.count()).where(JobWorker.job_id == job_id)
    ).scalar() or 0


def get_confirmed_workers_for_job(
    db: Session,
    job_id: str
) -> List[Dict[str, Any]]:
    """获取任务中已确认的工人

    Args:
        db: 数据库会话
        job_id: 任务 ID

    Returns:
        工人列表
    """
    results = db.execute(
        select(JobWorker)
        .where(JobWorker.job_id == job_id)
        .where(JobWorker.is_confirmed == True)
    ).scalars().all()
    return [jw.to_dict() for jw in results]


def get_winner_for_job(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
    """获取任务的中标者

    Args:
        db: 数据库会话
        job_id: 任务 ID

    Returns:
        中标者信息或 None
    """
    job_worker = db.execute(
        select(JobWorker)
        .where(JobWorker.job_id == job_id)
        .where(JobWorker.is_winner == True)
    ).scalar_one_or_none()

    return job_worker.to_dict() if job_worker else None
