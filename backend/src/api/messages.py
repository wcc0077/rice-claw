"""Message and communication endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from loguru import logger

from ..db.database import get_db
from ..db import messages as message_dal
from ..security import RateLimitType, validate_content_field, raise_if_rate_limited
from ..dependencies import RedisSession, PromptGuardStrict
from ..models.schemas import (
    MessageCreate, MessageResponse, MessageListResponse
)

router = APIRouter()


@router.post("/", response_model=MessageResponse)
async def create_message_endpoint(
    request: MessageCreate,
    redis: RedisSession,
    guard: PromptGuardStrict,
    db: Session = Depends(get_db)
):
    """Send a message.

    包含速率限制和 Prompt Injection 检测
    """
    # 速率限制
    await raise_if_rate_limited(redis, request.from_agent_id, RateLimitType.MESSAGE_SEND_MINUTE)

    # Prompt Injection 检测 - 使用统一的验证函数
    if request.content:
        request.content = await validate_content_field(guard, request.content, "content")

    try:
        message = message_dal.create_message(db, request.model_dump())
        if message:
            return MessageResponse(**message.to_dict())
        raise HTTPException(status_code=500, detail="Failed to create message")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error creating message")
        raise HTTPException(status_code=500, detail="Internal server error")


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