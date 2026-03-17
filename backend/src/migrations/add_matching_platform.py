"""数据库迁移脚本 - 撮合平台 [已弃用 - DEPRECATED]

⚠️ 此脚本已弃用，请使用 Alembic 进行数据库迁移。

使用 Alembic 迁移：
    cd backend
    alembic upgrade head

此脚本保留用于向后兼容，但所有迁移已整合到 Alembic 中：
    - alembic/versions/60c268102f26_initial_tables.py
    - alembic/versions/d044622a3747_add_owner_to_agent.py
    - alembic/versions/e8f7a9b2c4d1_add_matching_platform_tables.py

添加新表：
- job_workers (任务 - 工人关联表)
- artifact_versions (交付物版本表)
- payments (支付流水表)
- ws_connections (WebSocket 连接历史)
- message_delivery (消息送达状态)

扩展表：
- jobs (添加交易字段：reward_amount, deposit_amount, locked_at, winner_id 等)

"""

from pathlib import Path
from sqlalchemy import text
import sys
import uuid

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import engine


def generate_id(prefix: str) -> str:
    """生成 ID"""
    from datetime import datetime
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    short_uuid = uuid.uuid4().hex[:6]
    return f"{prefix}_{timestamp}_{short_uuid}"


def migrate_upgrade():
    """执行升级迁移"""
    print("Starting matching platform migration...")
    print("=" * 60)

    with engine.connect() as conn:
        # =====================================================================
        # Part 1: 扩展 jobs 表
        # =====================================================================
        print("\nPart 1: Extending jobs table...")

        jobs_fields = [
            ("reward_amount", "INTEGER", "ALTER TABLE jobs ADD COLUMN reward_amount INTEGER"),
            ("deposit_amount", "INTEGER", "ALTER TABLE jobs ADD COLUMN deposit_amount INTEGER"),
            ("deposit_paid", "BOOLEAN", "ALTER TABLE jobs ADD COLUMN deposit_paid BOOLEAN DEFAULT 0"),
            ("platform_fee", "INTEGER", "ALTER TABLE jobs ADD COLUMN platform_fee INTEGER"),
            ("locked_at", "DATETIME", "ALTER TABLE jobs ADD COLUMN locked_at DATETIME"),
            ("lock_deadline", "DATETIME", "ALTER TABLE jobs ADD COLUMN lock_deadline DATETIME"),
            ("winner_id", "VARCHAR(64)", "ALTER TABLE jobs ADD COLUMN winner_id VARCHAR(64)"),
            ("final_payment_status", "VARCHAR(32)", "ALTER TABLE jobs ADD COLUMN final_payment_status VARCHAR(32) DEFAULT 'PENDING'"),
            ("final_payment_amount", "INTEGER", "ALTER TABLE jobs ADD COLUMN final_payment_amount INTEGER"),
        ]

        for field_name, field_type, sql in jobs_fields:
            try:
                conn.execute(text(sql))
                print(f"  [+] Added jobs.{field_name}")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print(f"  [*] jobs.{field_name} already exists")
                else:
                    raise

        # =====================================================================
        # Part 2: 创建 job_workers 表
        # =====================================================================
        print("\nPart 2: Creating job_workers table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS job_workers (
                id VARCHAR(64) PRIMARY KEY,
                job_id VARCHAR(64) NOT NULL,
                bid_id VARCHAR(64) NOT NULL,
                worker_id VARCHAR(64) NOT NULL,
                status VARCHAR(32) DEFAULT 'PENDING',
                is_confirmed BOOLEAN DEFAULT 0,
                confirmed_at DATETIME,
                delivered_at DATETIME,
                is_winner BOOLEAN DEFAULT 0,
                subsidy_amount INTEGER,
                credit_penalty INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
                FOREIGN KEY (bid_id) REFERENCES bids(bid_id),
                FOREIGN KEY (worker_id) REFERENCES agents(agent_id)
            )
        """))
        print("  [+] Created job_workers table")

        # 创建索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_workers_job ON job_workers(job_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_job_workers_worker ON job_workers(worker_id)"))
        print("  [+] Created indexes on job_workers")

        # =====================================================================
        # Part 3: 创建 artifact_versions 表
        # =====================================================================
        print("\nPart 3: Creating artifact_versions table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS artifact_versions (
                version_id VARCHAR(64) PRIMARY KEY,
                artifact_id VARCHAR(64) NOT NULL,
                version_number INTEGER NOT NULL,
                file_url VARCHAR(512) NOT NULL,
                preview_url VARCHAR(512),
                is_watermarked BOOLEAN DEFAULT 0,
                worker_id VARCHAR(64) NOT NULL,
                is_final BOOLEAN DEFAULT 0,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
                FOREIGN KEY (worker_id) REFERENCES agents(agent_id)
            )
        """))
        print("  [+] Created artifact_versions table")

        # 创建索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_artifact_versions_artifact ON artifact_versions(artifact_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_artifact_versions_worker ON artifact_versions(worker_id)"))
        print("  [+] Created indexes on artifact_versions")

        # =====================================================================
        # Part 4: 创建 payments 表
        # =====================================================================
        print("\nPart 4: Creating payments table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id VARCHAR(64) PRIMARY KEY,
                job_id VARCHAR(64) NOT NULL,
                payer_id VARCHAR(64) NOT NULL,
                payee_id VARCHAR(64) NOT NULL,
                amount INTEGER NOT NULL,
                type VARCHAR(32) NOT NULL,
                status VARCHAR(32) DEFAULT 'PENDING',
                transaction_id VARCHAR(128),
                description VARCHAR(256),
                job_worker_id VARCHAR(64),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                settled_at DATETIME,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
                FOREIGN KEY (payer_id) REFERENCES agents(agent_id),
                FOREIGN KEY (payee_id) REFERENCES agents(agent_id),
                FOREIGN KEY (job_worker_id) REFERENCES job_workers(id)
            )
        """))
        print("  [+] Created payments table")

        # 创建索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_job ON payments(job_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_payer ON payments(payer_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_payee ON payments(payee_id)"))
        print("  [+] Created indexes on payments")

        # =====================================================================
        # Part 5: 创建 ws_connections 表
        # =====================================================================
        print("\nPart 5: Creating ws_connections table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ws_connections (
                connection_id VARCHAR(64) PRIMARY KEY,
                agent_id VARCHAR(64) NOT NULL,
                server_node VARCHAR(64) NOT NULL,
                connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                disconnected_at DATETIME,
                disconnect_reason VARCHAR(32),
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
            )
        """))
        print("  [+] Created ws_connections table")

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ws_connections_agent ON ws_connections(agent_id)"))
        print("  [+] Created indexes on ws_connections")

        # =====================================================================
        # Part 6: 创建 message_delivery 表
        # =====================================================================
        print("\nPart 6: Creating message_delivery table...")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS message_delivery (
                message_id VARCHAR(64) PRIMARY KEY,
                recipient_id VARCHAR(64) NOT NULL,
                delivered BOOLEAN DEFAULT 0,
                read BOOLEAN DEFAULT 0,
                delivered_at DATETIME,
                read_at DATETIME,
                FOREIGN KEY (recipient_id) REFERENCES agents(agent_id)
            )
        """))
        print("  [+] Created message_delivery table")

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_message_delivery_recipient ON message_delivery(recipient_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_message_delivery_delivered ON message_delivery(recipient_id, delivered)"))
        print("  [+] Created indexes on message_delivery")

        # =====================================================================
        # Part 7: 为 reputation_logs 添加新字段 (bid 关联)
        # =====================================================================
        print("\nPart 7: Extending reputation_logs table...")

        try:
            conn.execute(text("ALTER TABLE reputation_logs ADD COLUMN job_id VARCHAR(64)"))
            print("  [+] Added reputation_logs.job_id")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  [*] reputation_logs.job_id already exists")
            else:
                raise

        conn.commit()

        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("\nTables created:")
        print("  - job_workers")
        print("  - artifact_versions")
        print("  - payments")
        print("  - ws_connections")
        print("  - message_delivery")
        print("\nTables extended:")
        print("  - jobs (9 new fields)")
        print("  - reputation_logs (1 new field)")


def migrate_downgrade():
    """执行回滚（慎用，会删除数据）"""
    print("WARNING: Rolling back matching platform migration...")
    print("This will DELETE all data in new tables!")

    confirm = input("Continue? Type 'yes' to confirm: ")
    if confirm != "yes":
        print("Cancelled.")
        return

    with engine.connect() as conn:
        # 删除新表
        tables_to_drop = [
            "message_delivery",
            "ws_connections",
            "payments",
            "artifact_versions",
            "job_workers",
        ]

        for table in tables_to_drop:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            print(f"  ✓ Dropped {table}")

        # 删除 jobs 表的新字段 (SQLite 不支持 DROP COLUMN，需要重建表)
        print("\n  Note: jobs table fields cannot be dropped in SQLite.")
        print("  To fully rollback, delete the database and reinitialize.")

        conn.commit()

    print("\nRollback completed.")
    print("Note: jobs table fields still exist due to SQLite limitations.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="撮合平台数据库迁移")
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="回滚迁移"
    )
    args = parser.parse_args()

    if args.downgrade:
        migrate_downgrade()
    else:
        migrate_upgrade()
