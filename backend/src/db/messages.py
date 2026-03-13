"""Database access layer for messages."""

import sqlite3
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import get_connection


def row_to_message(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row to message dict."""
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


def create_message(message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new message."""
    conn = get_connection()
    cursor = conn.cursor()

    message_id = f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    attachments = message_data.get("attachments")
    attachments_json = str(attachments) if attachments else ""

    cursor.execute("""
        INSERT INTO messages (
            message_id, job_id, from_agent_id, to_agent_id,
            content, message_type, attachments, is_read
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        message_id,
        message_data["job_id"],
        message_data["from_agent_id"],
        message_data["to_agent_id"],
        message_data["content"],
        message_data.get("message_type", "text"),
        attachments_json,
    ))

    conn.commit()

    # Return created message
    cursor.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_message(row) if row else None


def get_messages_for_job(job_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM messages WHERE job_id = ? ORDER BY created_at ASC
    """, (job_id,))

    messages = [row_to_message(row) for row in cursor.fetchall()]
    conn.close()

    return messages


def mark_message_as_read(message_id: str) -> Optional[Dict[str, Any]]:
    """Mark a message as read."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE messages SET is_read = 1, updated_at = CURRENT_TIMESTAMP
        WHERE message_id = ?
    """, (message_id,))

    conn.commit()

    # Return updated message
    cursor.execute("SELECT * FROM messages WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_message(row) if row else None


def get_unread_message_count(agent_id: str) -> int:
    """Get count of unread messages for an agent."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM messages
        WHERE to_agent_id = ? AND is_read = 0
    """, (agent_id,))

    count = cursor.fetchone()[0]
    conn.close()

    return count
