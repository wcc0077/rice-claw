"""Database access layer for messages using SQLAlchemy 2.0."""

import uuid
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..models.db_models import Message


def create_message(db: Session, message_data: Dict[str, Any]) -> Message:
    """创建新消息

    Args:
        db: 数据库会话
        message_data: 消息数据

    Returns:
        创建的消息对象
    """
    # 生成消息ID
    message_id = f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # 处理附件
    attachments = message_data.get("attachments")
    attachments_json = json.dumps(attachments) if attachments else ""

    db_message = Message(
        message_id=message_id,
        job_id=message_data["job_id"],
        from_agent_id=message_data["from_agent_id"],
        to_agent_id=message_data["to_agent_id"],
        content=message_data["content"],
        message_type=message_data.get("message_type", "text"),
        attachments=attachments_json,
        is_read=False,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_message(db: Session, message_id: str) -> Optional[Message]:
    """获取单个消息

    Args:
        db: 数据库会话
        message_id: 消息ID

    Returns:
        消息对象或 None
    """
    return db.execute(
        select(Message).where(Message.message_id == message_id)
    ).scalar_one_or_none()


def get_messages_for_job(db: Session, job_id: str) -> List[Dict[str, Any]]:
    """获取任务的所有消息

    Args:
        db: 数据库会话
        job_id: 任务ID

    Returns:
        消息字典列表
    """
    messages = db.execute(
        select(Message)
        .where(Message.job_id == job_id)
        .order_by(Message.created_at.asc())
    ).scalars().all()

    return [msg.to_dict() for msg in messages]


def get_conversations_for_agent(db: Session, agent_id: str) -> List[Dict[str, Any]]:
    """获取代理的所有对话

    Args:
        db: 数据库会话
        agent_id: 代理ID

    Returns:
        对话列表（包含最后消息和未读数）
    """
    # 获取与该代理相关的所有消息
    messages = db.execute(
        select(Message)
        .where(
            (Message.from_agent_id == agent_id) | (Message.to_agent_id == agent_id)
        )
        .order_by(Message.created_at.desc())
    ).scalars().all()

    # 按任务和对话对象分组
    conversations = {}
    for msg in messages:
        # 确定对话对方
        other_agent_id = msg.to_agent_id if msg.from_agent_id == agent_id else msg.from_agent_id
        key = (msg.job_id, other_agent_id)

        if key not in conversations:
            # 获取未读数
            unread_count = db.execute(
                select(func.count())
                .where(Message.to_agent_id == agent_id)
                .where(Message.is_read == False)
                .where(Message.job_id == msg.job_id)
                .where(Message.from_agent_id == other_agent_id)
            ).scalar()

            conversations[key] = {
                "job_id": msg.job_id,
                "agent_id": other_agent_id,
                "last_message": msg.content[:100] if msg.content else "",
                "last_message_time": msg.created_at.isoformat() if msg.created_at else None,
                "unread_count": unread_count or 0,
            }

    return list(conversations.values())


def mark_message_as_read(db: Session, message_id: str) -> Optional[Message]:
    """标记消息为已读

    Args:
        db: 数据库会话
        message_id: 消息ID

    Returns:
        更新后的消息对象或 None
    """
    message = get_message(db, message_id)
    if not message:
        return None

    message.is_read = True
    db.commit()
    db.refresh(message)
    return message


def mark_message_as_read_dict(db: Session, message_id: str) -> Optional[Dict[str, Any]]:
    """标记消息为已读（返回字典）"""
    message = mark_message_as_read(db, message_id)
    return message.to_dict() if message else None


def get_unread_message_count(db: Session, agent_id: str) -> int:
    """获取代理的未读消息数

    Args:
        db: 数据库会话
        agent_id: 代理ID

    Returns:
        未读消息数量
    """
    return db.execute(
        select(func.count())
        .where(Message.to_agent_id == agent_id)
        .where(Message.is_read == False)
    ).scalar() or 0


def mark_all_as_read_for_agent(db: Session, agent_id: str) -> int:
    """标记代理的所有消息为已读

    Args:
        db: 数据库会话
        agent_id: 代理ID

    Returns:
        更新的消息数量
    """
    messages = db.execute(
        select(Message)
        .where(Message.to_agent_id == agent_id)
        .where(Message.is_read == False)
    ).scalars().all()

    for msg in messages:
        msg.is_read = True

    db.commit()
    return len(messages)


# =============================================================================
# 向后兼容的函数
# =============================================================================

def row_to_message(row) -> Dict[str, Any]:
    """向后兼容：将数据库行转换为字典"""
    if hasattr(row, 'to_dict'):
        return row.to_dict()

    # sqlite3.Row 兼容
    return {
        "message_id": row["message_id"],
        "job_id": row["job_id"],
        "from_agent_id": row["from_agent_id"],
        "to_agent_id": row["to_agent_id"],
        "content": row["content"],
        "message_type": row["message_type"],
        "attachments": row["attachments"],
        "is_read": bool(row["is_read"]),
        "created_at": row["created_at"],
    }