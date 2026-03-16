"""消息服务 - 处理离线消息存储和推送

功能:
- 离线消息存储 (Redis Stream)
- 消息推送 (Redis Pub/Sub)
- 消息历史记录
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from redis import asyncio as aioredis


class MessageService:
    """消息服务"""

    def __init__(self, redis: aioredis.Redis, key_prefix: str = "shrimp:"):
        self.redis = redis
        self.key_prefix = key_prefix

    async def store_offline_message(
        self,
        agent_id: str,
        message: Dict[str, Any],
        max_length: int = 1000
    ) -> str:
        """存储离线消息到 Redis Stream

        Args:
            agent_id: 接收方 Agent ID
            message: 消息内容
            max_length: Stream 最大长度

        Returns:
            消息 ID
        """
        stream_key = f"{self.key_prefix}stream:messages:{agent_id}"
        message_id = await self.redis.xadd(  # type: ignore
            stream_key,
            {"data": json.dumps(message)},
            maxlen=max_length
        )
        return message_id

    async def get_offline_messages(
        self,
        agent_id: str,
        count: int = 100,
        delete_after_read: bool = True
    ) -> List[Dict[str, Any]]:
        """获取离线消息

        Args:
            agent_id: Agent ID
            count: 最多获取的消息数
            delete_after_read: 是否在读取后删除

        Returns:
            消息列表
        """
        stream_key = f"{self.key_prefix}stream:messages:{agent_id}"
        messages = await self.redis.xrange(stream_key, count=count)  # type: ignore

        if not messages:
            return []

        result = []
        message_ids = []

        for msg_id, msg_data in messages:
            try:
                result.append(json.loads(msg_data[b"data"].decode()))
                message_ids.append(msg_id)
            except (KeyError, json.JSONDecodeError):
                continue

        if delete_after_read and message_ids:
            await self.redis.xdel(stream_key, *message_ids)  # type: ignore

        return result

    async def publish_message(
        self,
        channel: str,
        message: Dict[str, Any]
    ) -> int:
        """发布消息到 Redis Pub/Sub

        Args:
            channel: 频道名
            message: 消息内容

        Returns:
            订阅者数量
        """
        full_channel = f"{self.key_prefix}channel:{channel}"
        return await self.redis.publish(full_channel, json.dumps(message))  # type: ignore

    async def store_message_delivery_status(
        self,
        message_id: str,
        to_agent_id: str,
        status: str = "PENDING"
    ):
        """存储消息送达状态

        Args:
            message_id: 消息 ID
            to_agent_id: 接收方 Agent ID
            status: 状态 (PENDING/DELIVERED/READ)
        """
        key = f"{self.key_prefix}message:delivery:{message_id}"
        await self.redis.hset(key, mapping={  # type: ignore
            "to_agent_id": to_agent_id,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        # 设置过期时间（7 天）
        await self.redis.expire(key, 7 * 24 * 60 * 60)  # type: ignore

    async def update_message_delivery_status(
        self,
        message_id: str,
        status: str
    ):
        """更新消息送达状态

        Args:
            message_id: 消息 ID
            status: 新状态
        """
        key = f"{self.key_prefix}message:delivery:{message_id}"
        await self.redis.hset(key, "status", status)  # type: ignore
        await self.redis.hset(key, "updated_at", datetime.now(timezone.utc).isoformat())  # type: ignore

    async def get_message_delivery_status(
        self,
        message_id: str
    ) -> Optional[Dict[str, str]]:
        """获取消息送达状态

        Args:
            message_id: 消息 ID

        Returns:
            送达状态字典
        """
        key = f"{self.key_prefix}message:delivery:{message_id}"
        status = await self.redis.hgetall(key)  # type: ignore
        return status if status else None

    async def record_ws_connection(
        self,
        agent_id: str,
        node_name: str,
        connection_id: str
    ):
        """记录 WebSocket 连接

        Args:
            agent_id: Agent ID
            node_name: 服务器节点名
            connection_id: 连接 ID
        """
        conn_key = f"{self.key_prefix}ws:connections"
        await self.redis.hset(conn_key, agent_id, node_name)  # type: ignore

        # 记录连接历史
        history_key = f"{self.key_prefix}ws:history:{agent_id}"
        await self.redis.rpush(history_key, json.dumps({  # type: ignore
            "connection_id": connection_id,
            "node_name": node_name,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }))
        # 保留最近 100 条连接记录
        await self.redis.ltrim(history_key, -100, -1)  # type: ignore

    async def record_ws_disconnection(self, agent_id: str):
        """记录 WebSocket 断开"""
        conn_key = f"{self.key_prefix}ws:connections"
        await self.redis.hdel(conn_key, agent_id)  # type: ignore

    async def get_agent_connection_node(self, agent_id: str) -> Optional[str]:
        """获取 Agent 当前连接的服务器节点

        Args:
            agent_id: Agent ID

        Returns:
            节点名或 None
        """
        conn_key = f"{self.key_prefix}ws:connections"
        node = await self.redis.hget(conn_key, agent_id)  # type: ignore
        return node.decode() if isinstance(node, bytes) else node

    async def subscribe_bid(
        self,
        agent_id: str,
        bid_id: str,
        job_id: str
    ):
        """订阅 Bid 消息

        Args:
            agent_id: Agent ID
            bid_id: Bid ID
            job_id: Job ID
        """
        # 更新 agent 的 bids 集合
        agent_bids_key = f"{self.key_prefix}ws:agent:{agent_id}:bids"
        await self.redis.sadd(agent_bids_key, bid_id)  # type: ignore

        # 更新 bid 的上下文
        bid_context_key = f"{self.key_prefix}ws:bid:{bid_id}:context"
        await self.redis.hset(bid_context_key, mapping={  # type: ignore
            "agent_id": agent_id,
            "job_id": job_id,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

    async def unsubscribe_bid(self, agent_id: str, bid_id: str):
        """取消订阅 Bid

        Args:
            agent_id: Agent ID
            bid_id: Bid ID
        """
        agent_bids_key = f"{self.key_prefix}ws:agent:{agent_id}:bids"
        await self.redis.srem(agent_bids_key, bid_id)  # type: ignore

        bid_context_key = f"{self.key_prefix}ws:bid:{bid_id}:context"
        await self.redis.delete(bid_context_key)  # type: ignore

    async def get_agent_bids(self, agent_id: str) -> List[str]:
        """获取 Agent 订阅的所有 Bids

        Args:
            agent_id: Agent ID

        Returns:
            Bid ID 列表
        """
        agent_bids_key = f"{self.key_prefix}ws:agent:{agent_id}:bids"
        bids = await self.redis.smembers(agent_bids_key)  # type: ignore
        return [b.decode() if isinstance(b, bytes) else b for b in bids]


# ========== 便捷函数 ==========

def create_message_service(redis: aioredis.Redis, key_prefix: str = "shrimp:") -> MessageService:
    """创建消息服务实例

    Args:
        redis: Redis 连接
        key_prefix: Redis key 前缀

    Returns:
        MessageService 实例
    """
    return MessageService(redis, key_prefix)
