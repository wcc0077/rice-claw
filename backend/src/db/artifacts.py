"""Database access layer for artifacts using SQLAlchemy 2.0."""

import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models.db_models import Artifact


def create_artifact(db: Session, artifact_data: Dict[str, Any]) -> Artifact:
    """创建新交付物

    Args:
        db: 数据库会话
        artifact_data: 交付物数据

    Returns:
        创建的交付物对象
    """
    # 生成交付物ID
    artifact_id = f"art_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # 处理附件
    attachments = artifact_data.get("attachments")
    attachments_json = json.dumps(attachments) if attachments else ""

    db_artifact = Artifact(
        artifact_id=artifact_id,
        job_id=artifact_data["job_id"],
        worker_id=artifact_data["worker_id"],
        artifact_type=artifact_data.get("artifact_type", "demo"),
        title=artifact_data.get("title"),
        content=artifact_data.get("content"),
        attachments=attachments_json,
        version=1,
    )
    db.add(db_artifact)
    db.commit()
    db.refresh(db_artifact)
    return db_artifact


def get_artifact(db: Session, artifact_id: str) -> Optional[Artifact]:
    """获取单个交付物

    Args:
        db: 数据库会话
        artifact_id: 交付物ID

    Returns:
        交付物对象或 None
    """
    return db.execute(
        select(Artifact).where(Artifact.artifact_id == artifact_id)
    ).scalar_one_or_none()


def get_artifacts_for_job(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务的所有交付物

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        交付物字典列表
    """
    artifacts = db.execute(
        select(Artifact)
        .where(Artifact.job_id == job_id)
        .order_by(Artifact.created_at.asc())
    ).scalars().all()

    return [art.to_dict() for art in artifacts]


def get_latest_artifact(db: Session, job_id: str) -> Optional[Dict[str, Any]]:
    """获取任务的最新交付物

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        交付物字典或 None
    """
    artifact = db.execute(
        select(Artifact)
        .where(Artifact.job_id == job_id)
        .order_by(Artifact.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    return artifact.to_dict() if artifact else None


def update_artifact_version(db: Session, artifact_id: str) -> Optional[Artifact]:
    """增加交付物版本号

    Args:
        db: 数据库会话
        artifact_id: 交付物ID

    Returns:
        更新后的交付物对象或 None
    """
    artifact = get_artifact(db, artifact_id)
    if not artifact:
        return None

    artifact.version = (artifact.version or 1) + 1
    db.commit()
    db.refresh(artifact)
    return artifact


# =============================================================================
# 向后兼容的函数
# =============================================================================

def row_to_artifact(row) -> Dict[str, Any]:
    """向后兼容：将数据库行转换为字典"""
    if hasattr(row, 'to_dict'):
        return row.to_dict()

    # sqlite3.Row 兼容
    return {
        "artifact_id": row["artifact_id"],
        "job_id": row["job_id"],
        "worker_id": row["worker_id"],
        "artifact_type": row["artifact_type"],
        "title": row["title"],
        "content": row["content"],
        "attachments": row["attachments"],
        "version": row["version"],
        "created_at": row["created_at"],
    }