"""Database access layer for bids."""

import sqlite3
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from .database import get_connection


def row_to_bid(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert database row to bid dict."""
    portfolio_links = row["portfolio_links"] or ""
    return {
        "bid_id": row["bid_id"],
        "job_id": row["job_id"],
        "worker_id": row["worker_id"],
        "proposal": row["proposal"],
        "quote": {
            "amount": row["quote_amount"],
            "currency": row["quote_currency"],
            "delivery_days": row["delivery_days"],
        },
        "portfolio_links": portfolio_links.split(",") if portfolio_links else [],
        "is_hired": bool(row["is_hired"]),
        "status": row["status"],
        "submitted_at": row["submitted_at"],
    }


def create_bid(bid_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new bid."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check job status
    cursor.execute("SELECT status, bid_limit FROM jobs WHERE job_id = ?", (bid_data["job_id"],))
    job_row = cursor.fetchone()

    if not job_row:
        conn.close()
        raise ValueError("Job not found")

    if job_row["status"] != "OPEN":
        conn.close()
        raise ValueError("Job is not accepting bids")

    # Check bid limit
    cursor.execute("SELECT COUNT(*) FROM bids WHERE job_id = ?", (bid_data["job_id"],))
    current_count = cursor.fetchone()[0]

    if current_count >= job_row["bid_limit"]:
        conn.close()
        raise ValueError("Bid limit reached")

    bid_id = f"bid_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    portfolio_links = ",".join(bid_data.get("portfolio_links", [])) if bid_data.get("portfolio_links") else ""

    cursor.execute("""
        INSERT INTO bids (
            bid_id, job_id, worker_id, proposal, quote_amount,
            quote_currency, delivery_days, portfolio_links, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
    """, (
        bid_id,
        bid_data["job_id"],
        bid_data["worker_id"],
        bid_data["proposal"],
        bid_data["quote"]["amount"],
        bid_data["quote"]["currency"],
        bid_data["quote"]["delivery_days"],
        portfolio_links,
    ))

    conn.commit()

    # Return created bid
    cursor.execute("SELECT * FROM bids WHERE bid_id = ?", (bid_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_bid(row) if row else None


def get_bid(bid_id: str) -> Optional[Dict[str, Any]]:
    """Get bid by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bids WHERE bid_id = ?", (bid_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row_to_bid(row)
    return None


def get_bids_for_job(job_id: str) -> List[Dict[str, Any]]:
    """Get all bids for a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM bids WHERE job_id = ? ORDER BY is_hired DESC, submitted_at ASC
    """, (job_id,))

    bids = [row_to_bid(row) for row in cursor.fetchall()]
    conn.close()

    return bids


def update_bid_status(bid_id: str, status: str, is_hired: bool = False) -> Optional[Dict[str, Any]]:
    """Update bid status (accept/reject)."""
    if status not in ["ACCEPTED", "REJECTED", "PENDING"]:
        raise ValueError(f"Invalid status: {status}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bids SET status = ?, is_hired = ?, updated_at = CURRENT_TIMESTAMP
        WHERE bid_id = ?
    """, (status, is_hired, bid_id))

    conn.commit()

    # Return updated bid
    cursor.execute("SELECT * FROM bids WHERE bid_id = ?", (bid_id,))
    row = cursor.fetchone()
    conn.close()

    return row_to_bid(row) if row else None


def get_hired_bids_for_job(job_id: str) -> List[Dict[str, Any]]:
    """Get hired bids for a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM bids WHERE job_id = ? AND is_hired = 1
    """, (job_id,))

    bids = [row_to_bid(row) for row in cursor.fetchall()]
    conn.close()

    return bids
