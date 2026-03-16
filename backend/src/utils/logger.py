"""结构化日志配置模块

提供：
1. 统一的日志格式（JSON 格式，便于机器解析）
2. 请求链路追踪（Request ID）
3. 日志级别管理
"""

import sys
from datetime import datetime
from loguru import logger
from typing import Optional


def setup_logger(
    log_level: str = "INFO",
    log_file: str = "logs/app.log",
) -> None:
    """配置 loguru 日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径
        enable_json: 是否启用 JSON 格式
    """
    # 移除默认 handler
    logger.remove()

    # 控制台输出 - 带颜色的格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 文件输出 - JSON 格式（便于机器解析）
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} | {message}"
    )

    # 添加控制台 handler
    logger.add(
        sys.stderr,
        format=console_format,
        level=log_level,
        colorize=True,
    )

    # 添加文件 handler
    logger.add(
        log_file,
        format=file_format,
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True,  # 异步写入
    )

    # 添加错误日志专用文件
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )


def get_logger(name: str = __name__):
    """获取日志记录器

    Args:
        name: 日志记录器名称，通常为模块名

    Returns:
        loguru logger 实例
    """
    return logger.bind(name=name)


# 上下文日志绑定
class ContextLogger:
    """上下文哲理日志 - 支持绑定 request_id, agent_id 等上下文"""

    _context: dict = {}

    @classmethod
    def bind(cls, **kwargs) -> None:
        """绑定上下文键值对"""
        cls._context.update(kwargs)

    @classmethod
    def clear(cls) -> None:
        """清空上下文"""
        cls._context = {}

    @classmethod
    def get(cls, key: str, default=None):
        """获取上下文值"""
        return cls._context.get(key, default)

    @classmethod
    def log(cls, level: str = "INFO", message: str = "", **extra):
        """带上下文的日志记录"""
        log_data = {
            "context": cls._context.copy(),
            "extra": extra,
        }
        logger.opt(depth=1).log(level, f"{message} | {log_data}")


# 慢查询日志
def log_slow_query(query_desc: str, duration_ms: float, threshold_ms: float = 100.0) -> None:
    """记录慢查询日志

    Args:
        query_desc: 查询描述
        duration_ms: 执行时长（毫秒）
        threshold_ms: 慢查询阈值（毫秒）
    """
    if duration_ms > threshold_ms:
        logger.warning(
            f"SLOW QUERY ({duration_ms:.2f}ms > {threshold_ms}ms): {query_desc}"
        )


# 工具函数：计算耗时
class Timer:
    """上下文管理器，用于测量代码块执行时间"""

    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self):
        self.start_time = datetime.now().timestamp()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None) -> bool:
        self.end_time = datetime.now().timestamp()
        duration_ms = (self.end_time - self.start_time) * 1000
        status = "FAILED" if exc_type else "OK"
        logger.info(f"{self.description}: {duration_ms:.2f}ms [{status}]")
        return False

    @property
    def duration_ms(self) -> float:
        """返回执行时长（毫秒）"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else datetime.now().timestamp()
        return (end - self.start_time) * 1000


# 初始化日志
setup_logger()
