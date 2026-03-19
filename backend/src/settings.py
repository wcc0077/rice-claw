"""应用配置设置"""

import os
from pathlib import Path


class Settings:
    """应用配置"""

    # ===== 数据库配置 =====
    # settings.py is at backend/src/settings.py, so .parent.parent = backend/
    PROJECT_ROOT = Path(__file__).parent.parent
    DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "shrimp_market.db"
    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))

    @property
    def DATABASE_URL(self) -> str:
        """Get database URL with correct SQLite path format.

        SQLite URL format:
        - Relative path: sqlite:///relative/path.db (3 slashes)
        - Unix absolute path: sqlite:////absolute/path.db (4 slashes)
        - Windows absolute path: sqlite:///C:/path/to/db.db (3 slashes)
        """
        db_path = str(self.DATABASE_PATH)
        import platform
        if platform.system() == "Windows":
            return f"sqlite:///{db_path}"
        else:
            # On Unix, absolute paths need 4 slashes
            if db_path.startswith("/"):
                return f"sqlite:///{db_path}"
            return f"sqlite:///{db_path}"

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
