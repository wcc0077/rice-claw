"""Message and communication endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from redis import asyncio as aioredis
from loguru import logger

from ..db.database import get_db
from ..db import messages as message_dal
from ..security import PromptGuard, ThreatLevel, raise_if_rate_limited
from ..models.schemas import (
    MessageCreate, MessageResponse, MessageListResponse
)

router = APIRouter()


def get_redis() -> aioredis.Redis:
    """获取 Redis 连接实例"""
    return aioredis.from_url(
        "redis://localhost:6379/0",
        decode_responses=True
    )


def get_prompt_guard() -> PromptGuard:
    """获取 PromptGuard 实例"""
    return PromptGuard(strict_mode=True)


@router.post("/", response_model=MessageResponse)
async def create_message_endpoint(
    request: MessageCreate,
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    guard: PromptGuard = Depends(get_prompt_guard)
):
    """Send a message.

    包含速率限制和 Prompt Injection 检测
    """
    # 速率限制
    await raise_if_rate_limited(redis, request.from_agent_id, "message_send_minute")

    # Prompt Injection 检测
    if request.content:
        result = guard.analyze(request.content)
        if result.threat_level == ThreatLevel.DANGEROUS:
            logger.warning(f"Message content contains dangerous patterns: {result.detected_patterns}")
            raise HTTPException(
                status_code=400,
                detail=f"消息内容包含危险内容：{result.detected_patterns[0] if result.detected_patterns else 'unknown'}"
            )
        if result.threat_level == ThreatLevel.SUSPICIOUS:
            logger.info(f"Message content sanitized, detected patterns: {result.detected_patterns}")
            # 使用净化后的内容
            request.content = result.sanitized_content

    try:
        message = message_dal.create_message(db, request.model_dump())
        if message:
            return MessageResponse(**message.to_dict())
        raise HTTPException(status_code=500, detail="Failed to create message")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/job/{job_id}", response_model=MessageListResponse)
async def list_messages_endpoint(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get messages for a job."""
    messages = message_dal.get_messages_for_job(db, job_id)
    return MessageListResponse(messages=[MessageResponse(**msg) for msg in messages])


@router.post("/{message_id}/read")
async def mark_message_read_endpoint(
    message_id: str,
    db: Session = Depends(get_db)
):
    """Mark message as read."""
    message = message_dal.mark_message_as_read(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    return {"message": "Message marked as read", "is_read": True}