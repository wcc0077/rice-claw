"""Database access layer for artifact_versions using SQLAlchemy 2.0."""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update

from ..models.db_models import ArtifactVersion


def generate_id() -> str:
    """生成 artifact_version ID"""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    short_uuid = uuid.uuid4().hex[:6]
    return f"av_{timestamp}_{short_uuid}"


def create_artifact_version(
    db: Session,
    version_data: Dict[str, Any]
) -> ArtifactVersion:
    """创建交付物版本

    Args:
        db: 数据库会话
        version_data: 版本数据，包含 artifact_id, version_number, file_url 等

    Returns:
        创建的 ArtifactVersion 对象
    """
    version_id = generate_id()

    db_version = ArtifactVersion(
        version_id=version_id,
        artifact_id=version_data["artifact_id"],
        version_number=version_data["version_number"],
        file_url=version_data["file_url"],
        preview_url=version_data.get("preview_url"),
        is_watermarked=version_data.get("is_watermarked", False),
        worker_id=version_data["worker_id"],
        is_final=version_data.get("is_final", False),
        description=version_data.get("description"),
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


def get_artifact_version(
    db: Session,
    version_id: str
) -> Optional[ArtifactVersion]:
    """获取单个版本

    Args:
        db: 数据库会话
        version_id: 版本 ID

    Returns:
        ArtifactVersion 对象或 None
    """
    return db.execute(
        select(ArtifactVersion).where(ArtifactVersion.version_id == version_id)
    ).scalar_one_or_none()


def get_versions_for_artifact(
    db: Session,
    artifact_id: str,
    include_final_only: bool = False
) -> List[Dict[str, Any]]:
    """获取交付物的所有版本

    Args:
        db: 数据库会话
        artifact_id: 交付物 ID
        include_final_only: 是否只返回最终版本

    Returns:
        版本列表
    """
    query = select(ArtifactVersion).where(
        ArtifactVersion.artifact_id == artifact_id
    )

    if include_final_only:
        query = query.where(ArtifactVersion.is_final == True)

    query = query.order_by(ArtifactVersion.version_number.asc())

    results = db.execute(query).scalars().all()
    return [v.to_dict() for v in results]


def get_versions_for_worker(
    db: Session,
    worker_id: str
) -> List[Dict[str, Any]]:
    """获取工人的所有交付版本

    Args:
        db: 数据库会话
        worker_id: 工人 ID

    Returns:
        版本列表
    """
    query = select(ArtifactVersion).where(
        ArtifactVersion.worker_id == worker_id
    ).order_by(ArtifactVersion.created_at.desc())

    results = db.execute(query).scalars().all()
    return [v.to_dict() for v in results]


def update_version_as_final(
    db: Session,
    version_id: str
) -> Optional[ArtifactVersion]:
    """标记版本为最终版本

    Args:
        db: 数据库会话
        version_id: 版本 ID

    Returns:
        更新后的 ArtifactVersion 对象或 None
    """
    version = get_artifact_version(db, version_id)
    if not version:
        return None

    # 先将同 artifact 的其他版本取消最终标记
    db.execute(
        update(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == version.artifact_id)
        .where(ArtifactVersion.is_final == True)
        .values(is_final=False)
    )

    version.is_final = True
    db.commit()
    db.refresh(version)
    return version


def update_version_watermark(
    db: Session,
    version_id: str,
    preview_url: str
) -> Optional[ArtifactVersion]:
    """更新版本水印预览 URL

    Args:
        db: 数据库会话
        version_id: 版本 ID
        preview_url: 带水印的预览 URL

    Returns:
        更新后的 ArtifactVersion 对象或 None
    """
    version = get_artifact_version(db, version_id)
    if not version:
        return None

    version.preview_url = preview_url
    version.is_watermarked = True
    db.commit()
    db.refresh(version)
    return version


def get_latest_version_for_artifact(
    db: Session,
    artifact_id: str
) -> Optional[Dict[str, Any]]:
    """获取交付物的最新版本

    Args:
        db: 数据库会话
        artifact_id: 交付物 ID

    Returns:
        最新版本信息或 None
    """
    version = db.execute(
        select(ArtifactVersion)
        .where(ArtifactVersion.artifact_id == artifact_id)
        .order_by(ArtifactVersion.version_number.desc())
        .limit(1)
    ).scalar_one_or_none()

    return version.to_dict() if version else None


def get_next_version_number(
    db: Session,
    artifact_id: str
) -> int:
    """获取下一个版本号

    Args:
        db: 数据库会话
        artifact_id: 交付物 ID

    Returns:
        下一个版本号 (从 1 开始)
    """
    latest = db.execute(
        select(func.max(ArtifactVersion.version_number))
        .where(ArtifactVersion.artifact_id == artifact_id)
    ).scalar_one_or_none()

    return (latest or 0) + 1


# 导入 func 用于 max 查询
from sqlalchemy import func
