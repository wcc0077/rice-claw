"""Message and communication endpoints."""

from fastapi import APIRouter, HTTPException

from ..db.messages import create_message, get_messages_for_job, mark_message_as_read
from ..models.schemas import (
    MessageCreate, MessageResponse, MessageListResponse
)

router = APIRouter()


@router.post("/", response_model=MessageResponse)
async def create_message_endpoint(request: MessageCreate):
    """Send a message."""
    try:
        message = create_message(request.model_dump())
        if message:
            return MessageResponse(**message)
        raise HTTPException(status_code=500, detail="Failed to create message")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/job/{job_id}", response_model=MessageListResponse)
async def list_messages_endpoint(job_id: str):
    """Get messages for a job."""
    messages = get_messages_for_job(job_id)
    return MessageListResponse(messages=[MessageResponse(**msg) for msg in messages])


@router.post("/{message_id}/read")
async def mark_message_read_endpoint(message_id: str):
    """Mark message as read."""
    message = mark_message_as_read(message_id)
    if not message:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    return {"message": "Message marked as read", "is_read": True}
