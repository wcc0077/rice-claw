"""Database access layer for jobs using SQLAlchemy 2.0."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from ..models.db_models import Job, Bid


def create_job(db: Session, job_data: Dict[str, Any]) -> Job:
    """创建新任务

    Args:
        db: 数据库会话
        job_data: 任务数据

    Returns:
        创建的任务对象
    """
    # 生成任务ID
    job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # 处理字段
    required_tags = ",".join(job_data.get("required_tags", []))

    db_job = Job(
        job_id=job_id,
        employer_id=job_data["employer_id"],
        title=job_data["title"],
        description=job_data.get("description"),
        required_tags=required_tags,
        budget_min=job_data.get("budget_min"),
        budget_max=job_data.get("budget_max"),
        currency=job_data.get("currency", "CNY"),
        deadline=job_data.get("deadline"),
        bid_limit=job_data.get("bid_limit", 5),
        priority=job_data.get("priority", "normal"),
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def get_job(db: Session, job_id: str) -> Optional[Job]:
    """获取单个任务

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        任务对象或 None
    """
    return db.execute(
        select(Job).where(Job.job_id == job_id)
    ).scalar_one_or_none()


def get_job_dict(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
    """获取单个任务（字典格式，包含竞标数）

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        任务字典或 None
    """
    job = get_job(db, job_id)
    if not job:
        return None

    result = job.to_dict()
    result["bid_count"] = count_job_bids(db, job_id)
    return result


def list_jobs(
    db: Session,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    """列出任务

    Args:
        db: 数据库会话
        status: 状态筛选
        tag: 标签筛选
        page: 页码
        limit: 每页数量

    Returns:
        包含 jobs 和 pagination 的字典
    """
    # 构建查询（带竞标数统计）
    query = (
        select(Job, func.count(Bid.bid_id).label("bid_count"))
        .outerjoin(Bid, Job.job_id == Bid.job_id)
        .where(Job.status != "DELETED")
    )
    count_query = select(func.count()).select_from(Job).where(Job.status != "DELETED")

    # 添加筛选条件
    if status:
        query = query.where(Job.status == status)
        count_query = count_query.where(Job.status == status)
    if tag:
        query = query.where(Job.required_tags.like(f"%{tag}%"))
        count_query = count_query.where(Job.required_tags.like(f"%{tag}%"))

    # 分组（用于竞标数统计）
    query = query.group_by(Job.job_id)

    # 获取总数
    total = db.execute(count_query).scalar()

    # 分页
    offset = (page - 1) * limit
    query = query.limit(limit).offset(offset)

    # 执行查询
    results = db.execute(query).all()

    # 构建结果
    jobs = []
    for job, bid_count in results:
        job_dict = job.to_dict()
        job_dict["bid_count"] = bid_count or 0
        jobs.append(job_dict)

    return {
        "jobs": jobs,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": offset + limit < total,
        },
    }


def update_job(db: Session, job_id: str, updates: Dict[str, Any]) -> Optional[Job]:
    """更新任务

    Args:
        db: 数据库会话
        job_id: 任务ID
        updates: 更新字段

    Returns:
        更新后的任务对象或 None
    """
    job = get_job(db, job_id)
    if not job:
        return None

    # 更新字段
    if "status" in updates:
        job.status = updates["status"]
    if "selected_worker_ids" in updates:
        job.selected_worker_ids = ",".join(updates["selected_worker_ids"])
    if "closed_at" in updates:
        job.closed_at = updates["closed_at"]

    db.commit()
    db.refresh(job)
    return job


def update_job_dict(db: Session, job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """更新任务（返回字典）

    Args:
        db: 数据库会话
        job_id: 任务ID
        updates: 更新字段

    Returns:
        更新后的任务字典或 None
    """
    job = update_job(db, job_id, updates)
    if not job:
        return None

    result = job.to_dict()
    result["bid_count"] = count_job_bids(db, job_id)
    return result


def delete_job(db: Session, job_id: str, employer_id: str | None = None) -> bool:
    """删除任务（软删除）

    Args:
        db: 数据库会话
        job_id: 任务ID
        employer_id: 雇主ID（可选，用于权限验证）

    Returns:
        是否删除成功

    Raises:
        ValueError: 任务不存在或权限不足或任务状态不允许删除
    """
    job = get_job(db, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    # 权限验证
    if employer_id and job.employer_id != employer_id:
        raise ValueError("You can only delete your own jobs")

    # 状态验证：只有 OPEN 状态的任务可以删除
    if job.status not in ["OPEN", "CLOSED", "REJECTED"]:
        raise ValueError(f"Cannot delete job with status '{job.status}'. Only OPEN, CLOSED, or REJECTED jobs can be deleted.")

    # 软删除：设置 status 为 DELETED
    job.status = "DELETED"
    db.commit()
    return True


def count_job_bids(db: Session, job_id: str) -> int:
    """统计任务竞标数

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        竞标数量
    """
    return db.execute(
        select(func.count()).where(Bid.job_id == job_id)
    ).scalar() or 0


def match_jobs_by_tags(db: Session, tags: List[str]) -> List[str]:
    """根据标签匹配任务

    Args:
        db: 数据库会话
        tags: 标签列表

    Returns:
        匹配的任务ID列表
    """
    if not tags:
        return []

    # 构建 OR 条件
    conditions = [Job.required_tags.like(f"%{tag}%") for tag in tags]

    query = (
        select(Job.job_id)
        .where(Job.status == "OPEN")
        .where(or_(*conditions))
    )

    results = db.execute(query).scalars().all()
    return list(results)


# =============================================================================
# 向后兼容的函数
# =============================================================================

def row_to_job(row) -> Dict[str, Any]:
    """向后兼容：将数据库行转换为字典"""
    if hasattr(row, 'to_dict'):
        result = row.to_dict()
        result["bid_count"] = getattr(row, 'bid_count', 0)
        return result

    # sqlite3.Row 兼容
    required_tags = row["required_tags"] or ""
    selected_worker_ids = row["selected_worker_ids"] or ""

    return {
        "job_id": row["job_id"],
        "employer_id": row["employer_id"],
        "title": row["title"],
        "description": row["description"],
        "required_tags": required_tags.split(",") if required_tags else [],
        "budget_min": row["budget_min"],
        "budget_max": row["budget_max"],
        "currency": row["currency"],
        "deadline": row["deadline"],
        "bid_limit": row["bid_limit"],
        "priority": row["priority"],
        "status": row["status"],
        "selected_worker_ids": selected_worker_ids.split(",") if selected_worker_ids else [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "closed_at": row["closed_at"],
        "bid_count": row["bid_count"] if "bid_count" in row.keys() else 0,
    }