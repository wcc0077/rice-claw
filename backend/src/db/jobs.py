"""Database access layer for jobs."""

import sqlite3
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import get_connection


def row_to_job(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row to job dict."""
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
    }


def create_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new job."""
    conn = get_connection()
    cursor = conn.cursor()

    job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    required_tags = ",".join(job_data.get("required_tags", []))
    budget_min = job_data.get("budget_min")
    budget_max = job_data.get("budget_max")
    deadline = job_data.get("deadline")

    cursor.execute("""
        INSERT INTO jobs (
            job_id, employer_id, title, description, required_tags,
            budget_min, budget_max, currency, deadline, bid_limit, priority, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
    """, (
        job_id,
        job_data["employer_id"],
        job_data["title"],
        job_data["description"],
        required_tags,
        budget_min,
        budget_max,
        job_data.get("currency", "CNY"),
        deadline,
        job_data.get("bid_limit", 5),
        job_data.get("priority", "normal"),
    ))

    conn.commit()

    # Return created job
    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row_to_job(row)
    return None


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row_to_job(row)
    return None


def list_jobs(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Dict[str, Any]:
    """List jobs with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT j.*, COUNT(b.bid_id) as bid_count
        FROM jobs j
        LEFT JOIN bids b ON j.job_id = b.job_id
    """
    count_query = "SELECT COUNT(*) FROM jobs j"

    conditions = []
    params = []

    if status:
        conditions.append("j.status = ?")
        params.append(status)

    if tag:
        conditions.append("j.required_tags LIKE ?")
        params.append(f"%{tag}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        count_query += " WHERE " + " AND ".join(conditions) + " AND j.status != 'DELETED'"
    else:
        query += " WHERE j.status != 'DELETED'"
        count_query += " WHERE j.status != 'DELETED'"

    query += " GROUP BY j.job_id"

    # Get total count
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Get paginated results (bid_count already computed via JOIN)
    offset = (page - 1) * limit
    cursor.execute(query + " LIMIT ? OFFSET ?", params + [limit, offset])

    rows = cursor.fetchall()
    conn.close()

    # Build jobs with bid_count from query results
    jobs = []
    for row in rows:
        job = row_to_job(row)
        job["bid_count"] = row["bid_count"] if "bid_count" in row.keys() else 0
        jobs.append(job)

    return {
        "jobs": jobs,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": offset + limit < total,
        },
    }


def update_job(job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update job status or other fields."""
    conn = get_connection()
    cursor = conn.cursor()

    # Build update query dynamically
    update_fields = []
    params = []

    if "status" in updates:
        update_fields.append("status = ?")
        params.append(updates["status"])

    if "selected_worker_ids" in updates:
        selected_ids = ",".join(updates["selected_worker_ids"])
        update_fields.append("selected_worker_ids = ?")
        params.append(selected_ids)

    if "closed_at" in updates:
        update_fields.append("closed_at = ?")
        params.append(updates["closed_at"])

    if not update_fields:
        conn.close()
        return None

    params.append(job_id)
    update_fields.append("updated_at = CURRENT_TIMESTAMP")

    cursor.execute(f"""
        UPDATE jobs SET {", ".join(update_fields)} WHERE job_id = ?
    """, params)

    conn.commit()

    # Return updated job
    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        result = row_to_job(row)
        result["bid_count"] = count_job_bids(job_id)
        return result
    return None


def delete_job(job_id: str) -> bool:
    """Delete a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()

    return deleted


def count_job_bids(job_id: str) -> int:
    """Count bids for a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM bids WHERE job_id = ?", (job_id,))
    count = cursor.fetchone()[0]
    conn.close()

    return count


def match_jobs_by_tags(tags: List[str]) -> List[str]:
    """Find job IDs matching the given tags."""
    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?" for _ in tags])
    cursor.execute(f"""
        SELECT job_id FROM jobs
        WHERE status = 'OPEN'
        AND (
            {placeholders}
            IN (SELECT value FROM json_each('["' || replace(required_tags, ',', '","') || '"]'))
        )
    """, tags)

    job_ids = [row["job_id"] for row in cursor.fetchall()]
    conn.close()

    return job_ids
