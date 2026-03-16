"""Redis Pub/Sub 订阅器

功能:
- 监听订单状态变更通知
- 监听 bid 相关消息
- 将消息推送给订阅的 agent
"""

import json
import asyncio
from typing import Optional, Dict, Any, TYPE_CHECKING

from redis import asyncio as aioredis

if TYPE_CHECKING:
    from ..websocket.manager import ConnectionManager


class RedisPubSubSubscriber:
    """Redis Pub/Sub 订阅器"""

    def __init__(
        self,
        redis: aioredis.Redis,
        connection_manager: "ConnectionManager",
        key_prefix: str = "shrimp:"
    ):
        self.redis = redis
        self.connection_manager = connection_manager
        self.key_prefix = key_prefix
        self.pubsub: Optional[Any] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """启动 Pub/Sub 订阅"""
        self.pubsub = self.redis.pubsub()
        self._running = True

        # 订阅频道
        channels = [
            f"{self.key_prefix}channel:order_state",
            f"{self.key_prefix}channel:new_bid",
            f"{self.key_prefix}channel:delivery_update",
        ]
        await self.pubsub.subscribe(*channels)

        # 启动消息处理任务
        self._task = asyncio.create_task(self._listen_messages())

    async def stop(self):
        """停止 Pub/Sub 订阅"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()

    async def _listen_messages(self):
        """监听并处理 Pub/Sub 消息"""
        while self._running:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message["type"] == "message":
                    channel = message["channel"]
                    if isinstance(channel, bytes):
                        channel = channel.decode()

                    data = json.loads(message["data"])
                    await self._handle_message(channel, data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # 记录错误但继续运行
                print(f"[PubSub] Error processing message: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, channel: str, data: Dict[str, Any]):
        """处理 Pub/Sub 消息

        Args:
            channel: 频道名
            data: 消息数据
        """
        # 从频道名提取类型
        if "order_state" in channel:
            # 订单状态变更通知
            await self._handle_order_state_change(data)
        elif "new_bid" in channel:
            # 新 bid 通知
            await self._handle_new_bid(data)
        elif "delivery_update" in channel:
            # 交付更新通知
            await self._handle_delivery_update(data)

    async def _handle_order_state_change(self, data: Dict[str, Any]):
        """处理订单状态变更

        Args:
            data: {
                "order_id": "...",
                "previous_state": "...",
                "new_state": "...",
                "timestamp": "...",
                "extra": {}
            }
        """
        order_id = data.get("order_id")
        new_state = data.get("new_state")

        # 广播给所有连接的 agent (可根据需要优化为只通知相关 agent)
        message = {
            "type": "order_state_changed",
            "data": {
                "order_id": order_id,
                "new_state": new_state,
                "timestamp": data.get("timestamp")
            }
        }

        # 广播给所有在线 agent
        for agent_id in self.connection_manager.active_connections.keys():
            await self.connection_manager.send_to_agent(agent_id, message)

    async def _handle_new_bid(self, data: Dict[str, Any]):
        """处理新 bid 通知

        Args:
            data: {
                "job_id": "...",
                "bid_id": "...",
                "worker_id": "..."
            }
        """
        job_id = data.get("job_id")
        bid_id = data.get("bid_id")
        worker_id = data.get("worker_id")

        # 通知雇主 (根据 job_id 找到雇主)
        # 这里假设 data 中已经包含了雇主 ID
        employer_id = data.get("employer_id")
        if employer_id:
            message = {
                "type": "new_bid",
                "data": {
                    "job_id": job_id,
                    "bid_id": bid_id,
                    "worker_id": worker_id
                }
            }
            await self.connection_manager.send_to_agent(employer_id, message)

    async def _handle_delivery_update(self, data: Dict[str, Any]):
        """处理交付更新

        Args:
            data: {
                "job_id": "...",
                "bid_id": "...",
                "artifact_id": "...",
                "version": 1,
                "status": "..."
            }
        """
        job_id = data.get("job_id")
        bid_id = data.get("bid_id")

        # 通知雇主
        employer_id = data.get("employer_id")
        if employer_id:
            message = {
                "type": "delivery_update",
                "data": {
                    "job_id": job_id,
                    "bid_id": bid_id,
                    "artifact_id": data.get("artifact_id"),
                    "version": data.get("version"),
                    "status": data.get("status")
                }
            }
            await self.connection_manager.send_to_agent(employer_id, message)


async def create_pubsub_subscriber(
    redis: Optional[aioredis.Redis] = None,
    connection_manager: Optional["ConnectionManager"] = None
) -> "RedisPubSubSubscriber":
    """创建 Pub/Sub 订阅器

    Args:
        redis: Redis 连接 (如果不提供则创建新连接)
        connection_manager: ConnectionManager (如果不提供则创建新实例)

    Returns:
        RedisPubSubSubscriber 实例
    """
    if redis is None:
        from ..websocket.manager import get_redis
        redis = await get_redis()  # type: ignore

    if connection_manager is None:
        from ..websocket.manager import get_connection_manager
        connection_manager = await get_connection_manager()  # type: ignore

    subscriber = RedisPubSubSubscriber(redis, connection_manager)  # type: ignore
    await subscriber.start()
    return subscriber


# 全局订阅器实例
_subscriber: Optional[RedisPubSubSubscriber] = None


async def get_pubsub_subscriber() -> Optional[RedisPubSubSubscriber]:
    """获取全局 Pub/Sub 订阅器"""
    return _subscriber


async def init_pubsub_subscriber():
    """初始化全局 Pub/Sub 订阅器"""
    global _subscriber
    if _subscriber is None:
        _subscriber = await create_pubsub_subscriber()
    return _subscriber


async def shutdown_pubsub_subscriber():
    """关闭全局 Pub/Sub 订阅器"""
    global _subscriber
    if _subscriber:
        await _subscriber.stop()
        _subscriber = None
