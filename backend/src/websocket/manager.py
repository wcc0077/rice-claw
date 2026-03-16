"""WebSocket 连接管理器

功能:
- 管理所有活跃的 WebSocket 连接
- 支持 bid 级别的消息路由
- Redis 集成：连接注册、离线消息
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import WebSocket
from redis import asyncio as aioredis

from src.settings import settings


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

        # agent_id -> WebSocket (内存中的活跃连接)
        self.active_connections: Dict[str, WebSocket] = {}

        # agent_id -> Set of bid_ids (该 agent 订阅的 bid)
        self.agent_bids: Dict[str, Set[str]] = defaultdict(set)

        # bid_id -> agent_id (bid 到 agent 的映射)
        self.bid_agents: Dict[str, str] = {}

    async def connect(
        self,
        websocket: WebSocket,
        agent_id: str
    ) -> str:
        """建立 WebSocket 连接

        Args:
            websocket: WebSocket 连接对象
            agent_id: Agent ID

        Returns:
            connection_id
        """
        await websocket.accept()

        # 存入内存
        self.active_connections[agent_id] = websocket

        # 注册到 Redis
        await self.redis.hset(
            settings.redis_key("ws:connections"),
            agent_id,
            settings.SERVER_NODE_NAME
        )

        # 生成 connection_id
        connection_id = f"conn_{agent_id}_{int(datetime.now(timezone.utc).timestamp())}"

        # 记录连接历史
        await self.redis.hset(
            settings.redis_key("ws:agent_bids"),
            agent_id,
            json.dumps([])
        )

        return connection_id

    async def disconnect(self, agent_id: str):
        """断开 WebSocket 连接

        Args:
            agent_id: Agent ID
        """
        # 从内存移除
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]

        # 从 Redis 移除
        await self.redis.hdel(
            settings.redis_key("ws:connections"),
            agent_id
        )

        # 清理该 agent 的 bid 订阅
        if agent_id in self.agent_bids:
            for bid_id in self.agent_bids[agent_id]:
                self.bid_agents.pop(bid_id, None)
            del self.agent_bids[agent_id]

    async def subscribe_bid(self, agent_id: str, bid_id: str):
        """订阅某个 bid 的消息

        Args:
            agent_id: Agent ID
            bid_id: Bid ID
        """
        # 存入内存
        self.agent_bids[agent_id].add(bid_id)
        self.bid_agents[bid_id] = agent_id

        # 更新 Redis
        await self.redis.sadd(
            settings.redis_key(f"ws:agent:{agent_id}:bids"),
            bid_id
        )

        # 更新 bid 上下文
        await self.redis.hset(
            settings.redis_key(f"ws:bid:{bid_id}:context"),
            mapping={
                "agent_id": agent_id,
                "updated_at": str(int(datetime.now(timezone.utc).timestamp()))
            }
        )

        # 更新 agent_bids 列表
        bids_list = list(self.agent_bids[agent_id])
        await self.redis.hset(
            settings.redis_key("ws:agent_bids"),
            agent_id,
            json.dumps(bids_list)
        )

    async def unsubscribe_bid(self, agent_id: str, bid_id: str):
        """取消订阅 bid

        Args:
            agent_id: Agent ID
            bid_id: Bid ID
        """
        # 从内存移除
        self.agent_bids[agent_id].discard(bid_id)
        self.bid_agents.pop(bid_id, None)

        # 从 Redis 移除
        await self.redis.srem(
            settings.redis_key(f"ws:agent:{agent_id}:bids"),
            bid_id
        )

        # 删除 bid 上下文
        await self.redis.delete(
            settings.redis_key(f"ws:bid:{bid_id}:context")
        )

    async def send_to_agent(
        self,
        agent_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """发送消息给指定 agent

        Args:
            agent_id: Agent ID
            message: 消息字典

        Returns:
            是否发送成功
        """
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
                return True
            except Exception:
                return False
        else:
            # 离线消息存入 Redis Stream
            await self.redis.xadd(
                settings.redis_key(f"stream:messages:{agent_id}"),
                {"data": json.dumps(message)},
                maxlen=1000
            )
            return False

    async def send_to_bid(
        self,
        bid_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """发送消息给某个 bid 关联的 agent

        Args:
            bid_id: Bid ID
            message: 消息字典 (会自动带上 bid_id)

        Returns:
            是否发送成功
        """
        # 从 bid 找到 agent
        agent_id = self.bid_agents.get(bid_id)

        if not agent_id:
            # 尝试从 Redis 恢复
            context = await self.redis.hgetall(
                settings.redis_key(f"ws:bid:{bid_id}:context")
            )
            if context:
                agent_id_bytes = context.get(b"agent_id")
                agent_id = agent_id_bytes.decode() if agent_id_bytes else None

        if agent_id:
            # 消息中带上 bid_id 上下文
            message["data"] = message.get("data", {})
            message["data"]["bid_id"] = bid_id
            return await self.send_to_agent(agent_id, message)

        return False

    async def broadcast(
        self,
        channel: str,
        message: Dict[str, Any]
    ):
        """广播消息到 Redis Pub/Sub

        Args:
            channel: 频道名
            message: 消息字典
        """
        await self.redis.publish(
            settings.redis_key(f"channel:{channel}"),
            json.dumps(message)
        )

    async def get_offline_messages(self, agent_id: str) -> list:
        """获取离线消息

        Args:
            agent_id: Agent ID

        Returns:
            离线消息列表
        """
        messages = await self.redis.xrange(
            settings.redis_key(f"stream:messages:{agent_id}"),
            count=100
        )

        if messages:
            # 读取后删除
            await self.redis.xtrim(
                settings.redis_key(f"stream:messages:{agent_id}"),
                0
            )

        return [json.loads(msg[1]["data"]) for msg in messages]

    async def get_agent_bids(self, agent_id: str) -> Set[str]:
        """获取 agent 订阅的所有 bid

        Args:
            agent_id: Agent ID

        Returns:
            bid_id 集合
        """
        # 优先从内存获取
        if agent_id in self.agent_bids:
            return self.agent_bids[agent_id].copy()

        # 从 Redis 恢复
        bids_json = await self.redis.hget(
            settings.redis_key("ws:agent_bids"),
            agent_id
        )
        if bids_json:
            return set(json.loads(bids_json))

        return set()


# 全局 Redis 连接池
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 连接"""
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = await aioredis.from_url(
            settings.get_redis_url(),
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT
        )

    return _redis_pool


# 全局 ConnectionManager 实例
_manager: Optional[ConnectionManager] = None


async def get_connection_manager() -> ConnectionManager:
    """获取 ConnectionManager 单例"""
    global _manager

    if _manager is None:
        redis = await get_redis()
        _manager = ConnectionManager(redis)

    return _manager
