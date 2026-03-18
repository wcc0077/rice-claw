"""Database initialization and session management using SQLAlchemy 2.0."""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from ..settings import settings

# 数据库 URL（从 settings 获取，支持环境变量配置）
DATABASE_URL = settings.DATABASE_URL
DB_PATH = settings.DATABASE_PATH

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设为 True 可打印 SQL 调试
    connect_args={"check_same_thread": False}  # SQLite 多线程支持
)

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

    # 确保数据目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


# SQLite 外键支持（默认不启用，需要手动开启）
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