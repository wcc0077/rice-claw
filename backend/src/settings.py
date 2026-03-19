"""应用配置设置"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 加载 .env 文件
# 优先级: .env.local > .env.{ENVIRONMENT} > .env.development
# ENVIRONMENT 可通过环境变量预先设置
_env = os.getenv("ENVIRONMENT", "development")

# 按优先级尝试加载
env_files = [
    PROJECT_ROOT / ".env.local",
    PROJECT_ROOT / f".env.{_env}",
    PROJECT_ROOT / ".env.development",
]
for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file, override=True)
        break


class Settings:
    """应用配置"""

    # ===== 环境 =====
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production

    # ===== 数据库配置 =====
    # 默认使用 PostgreSQL，本地开发可通过环境变量切换
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")

    # PostgreSQL 配置
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "shrimp")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "shrimp123")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "shrimp_market")

    # SQLite 配置（仅用于测试）
    DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "shrimp_market.db"
    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库 URL

        优先级：
        1. DATABASE_URL 环境变量（直接指定完整 URL）
        2. DB_TYPE 环境变量决定使用 PostgreSQL 或 SQLite
        """
        # 如果直接设置了 DATABASE_URL，直接使用
        if os.getenv("DATABASE_URL"):
            return os.getenv("DATABASE_URL")

        # 根据 DB_TYPE 构建 URL
        if self.DB_TYPE == "postgresql":
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        else:
            # SQLite (用于测试)
            db_path = str(self.DATABASE_PATH)
            return f"sqlite:///{db_path}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """异步数据库 URL（用于异步操作）"""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # ===== Redis 配置 =====
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", 50))
    REDIS_SOCKET_TIMEOUT = int(os.getenv("REDIS_SOCKET_TIMEOUT", 5))

    # Redis Key 前缀
    REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "shrimp:")

    # ===== WebSocket 配置 =====
    WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", 30))  # 秒
    WS_PING_TIMEOUT = int(os.getenv("WS_PING_TIMEOUT", 10))    # 秒
    WS_MAX_CONNECTIONS_PER_AGENT = int(os.getenv("WS_MAX_CONNECTIONS_PER_AGENT", 3))
    WS_MESSAGE_RATE_LIMIT = int(os.getenv("WS_MESSAGE_RATE_LIMIT", 60))  # 条/分钟

    # ===== 服务器配置 =====
    SERVER_NODE_NAME = os.getenv("SERVER_NODE_NAME", "node-1")  # 用于多节点部署

    def get_redis_url(self) -> str:
        """获取 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def redis_key(self, key: str) -> str:
        """生成带前缀的 Redis Key"""
        return f"{self.REDIS_KEY_PREFIX}{key}"


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例 (用于依赖注入)"""
    return settings
