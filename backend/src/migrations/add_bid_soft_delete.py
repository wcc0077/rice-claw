"""数据库迁移脚本 - Bid 软删除

添加字段：
- bids.deleted (布尔值，默认 False)
- bids.deleted_at (datetime)

运行方式：
    cd backend
    uv run python -m src.migrations.add_bid_soft_delete
"""

from pathlib import Path
from sqlalchemy import text
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import engine


def migrate_upgrade():
    """执行升级迁移"""
    print("Starting bid soft delete migration...")

    with engine.connect() as conn:
        # 1. 添加 bids.deleted
        try:
            conn.execute(text(
                "ALTER TABLE bids ADD COLUMN deleted BOOLEAN DEFAULT 0"
            ))
            print("  [OK] Added bids.deleted")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  [SKIP] bids.deleted already exists")
            else:
                raise

        # 2. 添加 bids.deleted_at
        try:
            conn.execute(text(
                "ALTER TABLE bids ADD COLUMN deleted_at DATETIME"
            ))
            print("  [OK] Added bids.deleted_at")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("  [SKIP] bids.deleted_at already exists")
            else:
                raise

        conn.commit()

    print("Migration completed successfully!")


def migrate_downgrade():
    """执行回滚（慎用，会丢失数据）"""
    print("Rolling back bid soft delete migration...")

    confirm = input("WARNING: This will delete soft delete data. Continue? (yes/no): ")
    if confirm != "yes":
        print("Cancelled.")
        return

    with engine.connect() as conn:
        # 删除字段
        conn.execute(text("ALTER TABLE bids DROP COLUMN deleted"))
        conn.execute(text("ALTER TABLE bids DROP COLUMN deleted_at"))
        conn.commit()

    print("Rollback completed.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bid 软删除数据库迁移")
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