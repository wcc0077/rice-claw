"""数据库迁移脚本 - 声誉体系

添加字段：
- agents.reputation_score (整数，默认 1500)
- agents.reputation_updated_at (datetime)
- bids.employer_rating (整数，1-5 星)

运行方式：
    cd backend
    uv run python -m src.migrations.add_reputation_fields
"""

from pathlib import Path
from sqlalchemy import text
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import engine


def migrate_upgrade():
    """执行升级迁移"""
    print("Starting reputation system migration...")

    with engine.connect() as conn:
        # 1. 添加 agents.reputation_score
        try:
            conn.execute(text(
                "ALTER TABLE agents ADD COLUMN reputation_score INTEGER DEFAULT 1500"
            ))
            print("  ✓ Added agents.reputation_score")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  · agents.reputation_score already exists")
            else:
                raise

        # 2. 添加 agents.reputation_updated_at
        try:
            conn.execute(text(
                "ALTER TABLE agents ADD COLUMN reputation_updated_at DATETIME"
            ))
            print("  ✓ Added agents.reputation_updated_at")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  · agents.reputation_updated_at already exists")
            else:
                raise

        # 3. 添加 bids.employer_rating
        try:
            conn.execute(text(
                "ALTER TABLE bids ADD COLUMN employer_rating INTEGER"
            ))
            print("  ✓ Added bids.employer_rating")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  · bids.employer_rating already exists")
            else:
                raise

        conn.commit()

    print("Migration completed successfully!")


def migrate_downgrade():
    """执行回滚（慎用，会丢失数据）"""
    print("Rolling back reputation system migration...")

    confirm = input("WARNING: This will delete reputation data. Continue? (yes/no): ")
    if confirm != "yes":
        print("Cancelled.")
        return

    with engine.connect() as conn:
        # 删除字段
        conn.execute(text("ALTER TABLE agents DROP COLUMN reputation_score"))
        conn.execute(text("ALTER TABLE agents DROP COLUMN reputation_updated_at"))
        conn.execute(text("ALTER TABLE bids DROP COLUMN employer_rating"))
        conn.commit()

    print("Rollback completed.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="声誉体系数据库迁移")
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
