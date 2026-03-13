"""Database initialization and schema creation."""

import sqlite3
from pathlib import Path

# Get project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "shrimp_market.db"


def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Create agents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id VARCHAR(64) PRIMARY KEY,
            agent_type VARCHAR(16) NOT NULL,
            name VARCHAR(128) NOT NULL,
            capabilities TEXT,
            description TEXT,
            status VARCHAR(16) DEFAULT 'idle',
            rating DECIMAL(3,2) DEFAULT 0.0,
            completed_jobs INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id VARCHAR(64) PRIMARY KEY,
            employer_id VARCHAR(64) NOT NULL,
            title VARCHAR(256) NOT NULL,
            description TEXT,
            required_tags TEXT,
            budget_min INTEGER,
            budget_max INTEGER,
            currency VARCHAR(8) DEFAULT 'CNY',
            deadline TIMESTAMP,
            bid_limit INTEGER DEFAULT 5,
            priority VARCHAR(16) DEFAULT 'normal',
            status VARCHAR(16) DEFAULT 'OPEN',
            selected_worker_ids TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            FOREIGN KEY (employer_id) REFERENCES agents(agent_id)
        )
    """)

    # Create bids table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bids (
            bid_id VARCHAR(64) PRIMARY KEY,
            job_id VARCHAR(64) NOT NULL,
            worker_id VARCHAR(64) NOT NULL,
            proposal TEXT,
            quote_amount INTEGER,
            quote_currency VARCHAR(8),
            delivery_days INTEGER,
            portfolio_links TEXT,
            is_hired BOOLEAN DEFAULT 0,
            status VARCHAR(16) DEFAULT 'PENDING',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id),
            FOREIGN KEY (worker_id) REFERENCES agents(agent_id)
        )
    """)

    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id VARCHAR(64) PRIMARY KEY,
            job_id VARCHAR(64) NOT NULL,
            from_agent_id VARCHAR(64) NOT NULL,
            to_agent_id VARCHAR(64) NOT NULL,
            content TEXT NOT NULL,
            message_type VARCHAR(16) DEFAULT 'text',
            attachments TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id),
            FOREIGN KEY (from_agent_id) REFERENCES agents(agent_id),
            FOREIGN KEY (to_agent_id) REFERENCES agents(agent_id)
        )
    """)

    # Create artifacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id VARCHAR(64) PRIMARY KEY,
            job_id VARCHAR(64) NOT NULL,
            worker_id VARCHAR(64) NOT NULL,
            artifact_type VARCHAR(16),
            title VARCHAR(256),
            content TEXT,
            attachments TEXT,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id),
            FOREIGN KEY (worker_id) REFERENCES agents(agent_id)
        )
    """)

    # Create admin_users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            user_id VARCHAR(64) PRIMARY KEY,
            username VARCHAR(64) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            role VARCHAR(16) DEFAULT 'admin',
            status BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_employer ON jobs(employer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bids_job ON bids(job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bids_worker ON bids(worker_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bids_status ON bids(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_job ON messages(job_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type)")

    conn.commit()
    conn.close()

    print("Database initialized successfully!")


def get_connection() -> sqlite3.Connection:
    """Get database connection, ensuring schema is created."""
    if not DB_PATH.exists():
        init_database()
    return get_db_connection()


if __name__ == "__main__":
    init_database()
