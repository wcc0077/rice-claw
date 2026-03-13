"""Database access layer for artifacts."""

import sqlite3
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import get_connection


def row_to_artifact(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row to artifact dict."""
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


def create_artifact(artifact_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new artifact (demo or final work)."""
    conn = get_connection()
    cursor = conn.cursor()

    artifact_id = f"art_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    attachments = artifact_data.get("attachments")
    attachments_json = str(attachments) if attachments else ""

    cursor.execute("""
        INSERT INTO artifacts (
            artifact_id, job_id, worker_id, artifact_type,
            title, content, attachments, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        artifact_id,
        artifact_data["job_id"],
        artifact_data["worker_id"],
        artifact_data.get("artifact_type", "demo"),
        artifact_data["title"],
        artifact_data["content"],
        attachments_json,
    ))

    conn.commit()

    # Return created artifact
    cursor.execute("SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_artifact(row) if row else None


def get_artifacts_for_job(job_id: str) -> List[Dict[str, Any]]:
    """Get all artifacts for a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM artifacts WHERE job_id = ? ORDER BY created_at ASC
    """, (job_id,))

    artifacts = [row_to_artifact(row) for row in cursor.fetchall()]
    conn.close()

    return artifacts


def get_latest_artifact(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest artifact for a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM artifacts WHERE job_id = ? ORDER BY created_at DESC LIMIT 1
    """, (job_id,))

    row = cursor.fetchone()
    conn.close()

    return row_to_artifact(row) if row else None
