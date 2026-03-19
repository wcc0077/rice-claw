"""Database initialization and session management using SQLAlchemy 2.0."""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from ..settings import settings

# 数据库 URL（从 settings 获取，支持 PostgreSQL 和 SQLite）
DATABASE_URL = settings.DATABASE_URL
DB_TYPE = settings.DB_TYPE

# 创建引擎（根据数据库类型配置）
engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    # SQLite 特定配置
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库会话

    用法:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库（创建所有表）

    幂等操作：如果表已存在则跳过，不会覆盖数据。
    """
    from ..models.db_models import Base

    # SQLite 需要确保数据目录存在
    if DATABASE_URL.startswith("sqlite"):
        from pathlib import Path
        db_path = Path(str(settings.DATABASE_PATH))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized successfully! (type={DB_TYPE})")


# SQLite 外键支持（默认不启用，需要手动开启）
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record):
        """为每个连接启用 SQLite 外键约束"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# 向后兼容的别名
get_connection = get_db


if __name__ == "__main__":
    init_database()