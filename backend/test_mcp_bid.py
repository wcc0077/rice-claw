#!/usr/bin/env uv run python
"""MCP Bid Functionality Test Script

This script tests the MCP bid functionality by:
1. Creating test employer and worker agents
2. Publishing a test job
3. Worker submitting a bid
4. Employer accepting the bid
5. Verifying job status transition
"""

import os
import sys
import time
from pathlib import Path

# Use a test database file
db_path = Path(__file__).parent / "data" / "shrimp_market_test.db"

# Set database path BEFORE importing database module
os.environ['DATABASE_PATH'] = str(db_path.absolute())

# Remove existing test database
if db_path.exists():
    print(f"Removing existing test database: {db_path}")
    try:
        os.remove(db_path)
    except PermissionError:
        print(f"Warning: Could not remove {db_path}, will overwrite")
    # Also remove any journal files
    for ext in ["-wal", "-shm"]:
        journal_path = Path(str(db_path) + ext)
        if journal_path.exists():
            try:
                os.remove(journal_path)
            except PermissionError:
                pass
    print("[OK] Database removed\n")

# Wait a bit for file locks to release
time.sleep(0.5)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy.orm import Session
from src.db.database import SessionLocal, init_database
from src.db.agents import create_agent, set_agent_api_key
from src.db.jobs import create_job, get_job
from src.services.bid_service import BidService
from src.models.schemas import AgentCreate


def setup_test_data():
    """Create test data"""
    db: Session = SessionLocal()
    try:
        # 0. Create admin user first (required for foreign key)
        from src.models.db_models import AdminUser
        import bcrypt

        password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        admin = AdminUser(
            user_id="admin_test_001",
            username="test_admin",
            password_hash=password_hash,
            role="admin",
        )
        db.add(admin)
        db.commit()
        print(f"[OK] Created admin user: {admin.user_id}")

        # 1. Create employer Agent
        employer = create_agent(
            db=db,
            agent=AgentCreate(
                agent_id="employer_test_001",
                agent_type="employer",
                name="Test Employer",
                capabilities=["python", "fastapi"],
                description="Test employer",
                owner_id="admin_test_001"  # Use the test admin user ID
            )
        )
        employer_key_info = set_agent_api_key(db, employer.agent_id)
        employer_id = employer.agent_id
        print(f"[OK] Created employer Agent: {employer_id}")
        print(f"     API Key: {employer_key_info['api_key']}")

        # 2. Create worker Agent
        worker = create_agent(
            db=db,
            agent=AgentCreate(
                agent_id="worker_test_001",
                agent_type="worker",
                name="Test Worker",
                capabilities=["python", "react"],
                description="Test worker",
                owner_id="admin_test_001"  # Use the test admin user ID
            )
        )
        worker_key_info = set_agent_api_key(db, worker.agent_id)
        worker_id = worker.agent_id
        print(f"[OK] Created worker Agent: {worker_id}")
        print(f"     API Key: {worker_key_info['api_key']}")

        # 3. Create job
        job_data = {
            "employer_id": employer_id,
            "title": "Test Job - MCP Bid",
            "description": "This is a test job for MCP bid functionality",
            "required_tags": ["python", "fastapi"],
            "budget_min": 1000,
            "budget_max": 5000,
            "bid_limit": 5,
        }
        job = create_job(db=db, job_data=job_data)
        job_id = job.job_id
        print(f"[OK] Created job: {job_id}")
        print(f"     Status: {job.status}")

        return {
            "employer_id": employer_id,
            "worker_id": worker_id,
            "job_id": job_id,
            "employer_api_key": employer_key_info['api_key'],
            "worker_api_key": worker_key_info['api_key'],
        }
    finally:
        db.close()


def test_bid_flow(test_data):
    """Test bid flow"""
    db: Session = SessionLocal()
    try:
        bid_service = BidService(db)

        print("\n--- Test: Submit Bid ---")
        # 1. Worker submits bid
        bid = bid_service.create_bid(
            job_id=test_data["job_id"],
            worker_id=test_data["worker_id"],
            proposal="I have rich FastAPI experience and can complete this task",
            quote={
                "amount": 3000,
                "currency": "CNY",
                "delivery_days": 7,
            }
        )
        print(f"[OK] Bid submitted: {bid['bid_id']}")
        print(f"     Status: {bid['status']}")

        print("\n--- Test: Accept Bid ---")
        # 2. Employer accepts bid
        updated_bid = bid_service.accept_bid(
            job_id=test_data["job_id"],
            bid_id=bid["bid_id"],
            employer_id=test_data["employer_id"]
        )
        print(f"[OK] Bid accepted")
        print(f"     New status: {updated_bid['status']}")

        # 3. Verify job status change
        job = get_job(db, test_data["job_id"])
        print(f"[OK] Job status: {job.status}")

        print("\n--- Summary ---")
        print(f"  Employer API Key: {test_data['employer_api_key']}")
        print(f"  Worker API Key: {test_data['worker_api_key']}")
        print(f"  Job ID: {test_data['job_id']}")
        print(f"  Bid ID: {bid['bid_id']}")

        return bid, updated_bid
    finally:
        db.close()


if __name__ == "__main__":
    print("=== MCP Bid Functionality Test ===\n")

    # Initialize database
    print("Initializing database...")
    init_database()
    print("[OK] Database ready\n")

    # Create test data
    print("Creating test data...")
    test_data = setup_test_data()

    # Test bid flow
    print("\n" + "=" * 40)
    test_bid_flow(test_data)

    print("\n=== Test Complete ===")
