# SQLAlchemy 2.0 重构设计

**日期：** 2026-03-13
**状态：** 已确认
**决策：** 同步操作 + Alembic 迁移 + 声明式 ORM

---

## 概述

将后端数据访问层从原生 `sqlite3` 重构为 SQLAlchemy 2.0，使用声明式 ORM 模型和 Alembic 迁移管理。

---

## 1. 项目结构

```
backend/src/
├── db/
│   ├── __init__.py
│   ├── database.py      # 引擎、会话管理、Base
│   └── repositories/    # 仓库模式（可选，后续添加）
├── models/
│   ├── __init__.py
│   ├── schemas.py       # Pydantic schemas（保留，用于 API）
│   └── db_models.py     # SQLAlchemy ORM 模型（新增）
├── alembic/             # 迁移脚本目录
│   ├── versions/
│   └── env.py
└── alembic.ini          # Alembic 配置
```

**核心改动点：**
- 新增 `models/db_models.py`：定义 SQLAlchemy ORM 模型
- 重构 `db/database.py`：使用 `create_engine` + `sessionmaker`
- 新增 `alembic/` 目录：迁移版本控制
- 保留 `models/schemas.py`：Pydantic 用于 API 验证

**依赖更新：**
```toml
dependencies = [
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    # ... 其他保留
]
```

---

## 2. ORM 模型定义

```python
# models/db_models.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase

class Base(DeclarativeBase):
    """所有模型的基类"""
    pass

class Agent(Base):
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_type: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    capabilities: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="idle")
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    jobs_as_employer: Mapped[List["Job"]] = relationship(back_populates="employer")
    bids: Mapped[List["Bid"]] = relationship(back_populates="worker")

class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    employer_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_tags: Mapped[str] = mapped_column(Text, default="")
    budget_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    bid_limit: Mapped[int] = mapped_column(Integer, default=5)
    priority: Mapped[str] = mapped_column(String(16), default="normal")
    status: Mapped[str] = mapped_column(String(16), default="OPEN")
    selected_worker_ids: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 关系
    employer: Mapped["Agent"] = relationship(back_populates="jobs_as_employer")
    bids: Mapped[List["Bid"]] = relationship(back_populates="job")
    messages: Mapped[List["Message"]] = relationship(back_populates="job")

class Bid(Base):
    __tablename__ = "bids"

    bid_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    proposal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quote_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quote_currency: Mapped[str] = mapped_column(String(8), default="CNY")
    delivery_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    portfolio_links: Mapped[str] = mapped_column(Text, default="")
    is_hired: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    job: Mapped["Job"] = relationship(back_populates="bids")
    worker: Mapped["Agent"] = relationship(back_populates="bids")

class Message(Base):
    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False)
    from_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    to_agent_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(String(16), default="text")
    attachments: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    job: Mapped["Job"] = relationship(back_populates="messages")

class Artifact(Base):
    __tablename__ = "artifacts"

    artifact_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.job_id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(ForeignKey("agents.agent_id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(16))
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AdminUser(Base):
    __tablename__ = "admin_users"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="admin")
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**关键设计点：**
- 使用 `Mapped[T]` 类型注解，SQLAlchemy 2.0 推荐方式
- `mapped_column()` 替代传统 Column，支持类型推断
- 保留逗号分隔的字符串存储（如 `capabilities`），与现有数据兼容
- 定义双向关系：`relationship(back_populates=...)`

---

## 3. 数据库连接与会话管理

```python
# db/database.py
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "shrimp_market.db"

# 数据库 URL（SQLite）
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """初始化数据库（创建所有表）"""
    from ..models.db_models import Base
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

# SQLite 外键支持
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

**FastAPI 路由使用方式：**
```python
# api/agents.py
from fastapi import Depends
from sqlalchemy.orm import Session
from ..db.database import get_db

@router.get("/agents")
def list_agents(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    agents = db.query(Agent).filter(Agent.status == status).all()
    return {"agents": [agent_to_dict(a) for a in agents]}
```

---

## 4. 数据访问层重构示例

```python
# db/agents.py（重构后）
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models.db_models import Agent
from ..models.schemas import AgentCreate

def create_agent(db: Session, agent: AgentCreate) -> Agent:
    """创建新代理"""
    existing = db.execute(
        select(Agent).where(Agent.agent_id == agent.agent_id)
    ).scalar_one_or_none()

    if existing:
        raise ValueError(f"Agent {agent.agent_id} already exists")

    db_agent = Agent(
        agent_id=agent.agent_id,
        agent_type=agent.agent_type,
        name=agent.name,
        capabilities=",".join(agent.capabilities),
        description=agent.description,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

def get_agent(db: Session, agent_id: str) -> Optional[Agent]:
    """获取单个代理"""
    return db.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    ).scalar_one_or_none()

def list_agents(
    db: Session,
    status: Optional[str] = None,
    capability: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[List[Agent], int]:
    """列出代理"""
    query = select(Agent)
    count_query = select(func.count()).select_from(Agent)

    if status:
        query = query.where(Agent.status == status)
        count_query = count_query.where(Agent.status == status)

    if capability:
        query = query.where(Agent.capabilities.like(f"%{capability}%"))
        count_query = count_query.where(Agent.capabilities.like(f"%{capability}%"))

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    query = query.limit(limit).offset(offset)
    agents = db.execute(query).scalars().all()

    return agents, total

def update_agent_status(db: Session, agent_id: str, status: str) -> Optional[Agent]:
    """更新代理状态"""
    agent = get_agent(db, agent_id)
    if not agent:
        return None

    agent.status = status
    db.commit()
    db.refresh(agent)
    return agent
```

**API 层调用方式：**
```python
@router.post("/agents")
def register_agent(
    agent: AgentCreate,
    db: Session = Depends(get_db)
):
    try:
        db_agent = create_agent(db, agent)
        return {"success": True, "agent": agent_to_dict(db_agent)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 5. Alembic 迁移配置

**初始化：**
```bash
cd backend
alembic init alembic
```

**alembic.ini：**
```ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///data/shrimp_market.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

**alembic/env.py：**
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.db_models import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**常用命令：**
```bash
# 自动生成迁移
alembic revision --autogenerate -m "Initial tables"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1

# 查看历史
alembic history
```

---

## 改动汇总

| 模块 | 改动 |
|------|------|
| `models/db_models.py` | 新增 ORM 模型 |
| `db/database.py` | 重构为 SQLAlchemy 引擎+会话 |
| `db/agents.py` | 重构为 ORM 查询 |
| `db/jobs.py` | 重构为 ORM 查询 |
| `db/bids.py` | 重构为 ORM 查询 |
| `db/messages.py` | 重构为 ORM 查询 |
| `db/artifacts.py` | 重构为 ORM 查询 |
| `api/*.py` | 更新为 `Depends(get_db)` 注入 |
| `alembic/` | 新增迁移管理 |
| `pyproject.toml` | 添加 sqlalchemy, alembic 依赖 |

---

## 实施步骤

1. 更新 `pyproject.toml` 添加依赖
2. 创建 `models/db_models.py` 定义 ORM 模型
3. 重构 `db/database.py` 配置引擎和会话
4. 重构各 `db/*.py` 数据访问函数
5. 更新 `api/*.py` 路由使用依赖注入
6. 初始化 Alembic 并生成初始迁移
7. 测试所有 API 端点