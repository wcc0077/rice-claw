"""WebSocket module for real-time communication with OpenClaw agents."""

from .manager import ConnectionManager, get_connection_manager

__all__ = ["ConnectionManager", "get_connection_manager"]
