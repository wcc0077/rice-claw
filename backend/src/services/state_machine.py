"""订单状态机 - 基于 Redis 的原子状态流转

状态流转图:
    OPEN → ACTIVE → REVIEW → CLOSED
                     ↘ REJECTED
                ↘ CANCELLED

用法:
    state_machine = OrderStateMachine(redis, order_id)
    await state_machine.transition("OPEN", "ACTIVE")
"""

import json
import asyncio
from typing import Optional, Dict, Any, Set
from datetime import datetime, timezone
from pathlib import Path

from redis import asyncio as aioredis


# 状态定义
class OrderState:
    OPEN = "OPEN"
    ACTIVE = "ACTIVE"
    REVIEW = "REVIEW"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


# 合法的状态流转
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    OrderState.OPEN: {OrderState.ACTIVE, OrderState.CLOSED},
    OrderState.ACTIVE: {OrderState.REVIEW, OrderState.CLOSED, OrderState.CANCELLED},
    OrderState.REVIEW: {OrderState.CLOSED, OrderState.REJECTED},
    OrderState.CLOSED: set(),  # 终态
    OrderState.CANCELLED: set(),  # 终态
    OrderState.REJECTED: set(),  # 终态
}


class StateTransitionError(Exception):
    """状态流转错误"""

    def __init__(self, message: str, current_state: Optional[str] = None):
        self.message = message
        self.current_state = current_state
        super().__init__(message)


class OrderStateMachine:
    """订单状态机"""

    def __init__(self, redis: aioredis.Redis, order_id: str, key_prefix: str = "shrimp:"):
        self.redis = redis
        self.order_id = order_id
        self.key_prefix = key_prefix

        # Redis keys
        self.state_key = f"{key_prefix}order:{order_id}:state"
        self.info_key = f"{key_prefix}order:{order_id}:info"
        self.channel = f"{key_prefix}channel:order_state"

        # Lua 脚本
        self._lua_script: Optional[Any] = None

    async def _get_lua_script(self) -> Any:
        """获取 Lua 脚本（懒加载）"""
        if self._lua_script is None:
            lua_path = Path(__file__).parent / "state_machine.lua"
            with open(lua_path, "r", encoding="utf-8") as f:
                lua_code = f.read()
            self._lua_script = self.redis.register_script(lua_code)
        return self._lua_script

    async def get_current_state(self) -> Optional[str]:
        """获取当前状态"""
        result = await self.redis.hget(self.state_key, "current_state")  # type: ignore
        return result.decode() if isinstance(result, bytes) else result

    async def get_state_history(self) -> list:
        """获取状态历史"""
        history = await self.redis.hgetall(f"{self.state_key}:history")  # type: ignore
        if not history:
            return []
        return sorted(history.items(), key=lambda x: x[0])

    async def transition(
        self,
        expected_state: str,
        new_state: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行状态流转

        Args:
            expected_state: 期望的当前状态（设为 "*" 接受任何状态）
            new_state: 新状态
            extra_data: 额外数据（可选）

        Returns:
            流转结果字典

        Raises:
            StateTransitionError: 状态流转失败
        """
        # 验证状态流转合法性
        if expected_state != "*" and new_state not in VALID_TRANSITIONS.get(expected_state, set()):
            raise StateTransitionError(
                f"Invalid transition: {expected_state} -> {new_state}",
                expected_state
            )

        script = await self._get_lua_script()
        timestamp = datetime.now(timezone.utc).isoformat()
        extra_json = json.dumps(extra_data or {})

        try:
            result = await script(
                keys=[self.state_key, self.info_key, self.channel],
                args=[expected_state, new_state, self.order_id, timestamp, extra_json]
            )

            success, status, *rest = result

            if not success:
                error_code = status
                current_state = rest[0] if rest else None

                if error_code == "STATE_NOT_FOUND":
                    raise StateTransitionError(f"Order {self.order_id} state not found")
                elif error_code == "STATE_MISMATCH":
                    raise StateTransitionError(
                        f"State mismatch: expected {expected_state}, got {current_state}",
                        current_state
                    )
                elif error_code == "INVALID_TRANSITION":
                    raise StateTransitionError(
                        f"Invalid transition: {rest[0]}",
                        expected_state
                    )
                else:
                    raise StateTransitionError(f"Unknown error: {error_code}", current_state)

            return {
                "success": True,
                "previous_state": rest[0],
                "new_state": rest[1],
                "timestamp": timestamp
            }

        except Exception as e:
            if isinstance(e, StateTransitionError):
                raise
            raise StateTransitionError(f"Redis error: {str(e)}")

    async def initialize_state(self, initial_state: str = OrderState.OPEN) -> bool:
        """初始化订单状态

        Args:
            initial_state: 初始状态

        Returns:
            是否初始化成功（如果已存在则返回 False）
        """
        current = await self.get_current_state()
        if current is not None:
            return False

        await self.redis.hset(self.state_key, mapping={  # type: ignore
            "current_state": initial_state,
            "previous_state": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        return True

    async def record_action(self, action: str, actor_id: str, details: Optional[Dict] = None):
        """记录订单操作日志

        Args:
            action: 操作名称
            actor_id: 操作者 ID
            details: 详细信息
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        pipe = self.redis.pipeline()

        # 添加到操作历史
        action_key = f"{self.state_key}:actions"
        action_data = json.dumps({
            "action": action,
            "actor_id": actor_id,
            "timestamp": timestamp,
            "details": details or {}
        })
        pipe.rpush(action_key, action_data)  # type: ignore

        # 设置过期时间（保留 90 天）
        pipe.expire(action_key, 90 * 24 * 60 * 60)  # type: ignore

        await pipe.execute()  # type: ignore

    async def get_action_history(self, limit: int = 50) -> list:
        """获取操作历史

        Args:
            limit: 最多返回的条数

        Returns:
            操作历史列表
        """
        action_key = f"{self.state_key}:actions"
        actions = await self.redis.lrange(action_key, -limit, -1)  # type: ignore
        if not actions:
            return []
        return [json.loads(a) for a in actions]


# ========== 便捷函数 ==========

async def create_order_state_machine(
    redis: aioredis.Redis,
    order_id: str,
    initial_state: str = OrderState.OPEN,
    key_prefix: str = "shrimp:"
) -> OrderStateMachine:
    """创建并初始化订单状态机

    Args:
        redis: Redis 连接
        order_id: 订单 ID
        initial_state: 初始状态
        key_prefix: Redis key 前缀

    Returns:
        OrderStateMachine 实例
    """
    state_machine = OrderStateMachine(redis, order_id, key_prefix)
    await state_machine.initialize_state(initial_state)
    return state_machine


async def transition_order(
    redis: aioredis.Redis,
    order_id: str,
    expected_state: str,
    new_state: str,
    extra_data: Optional[Dict[str, Any]] = None,
    key_prefix: str = "shrimp:"
) -> Dict[str, Any]:
    """便捷函数：执行订单状态流转

    Args:
        redis: Redis 连接
        order_id: 订单 ID
        expected_state: 期望的当前状态
        new_state: 新状态
        extra_data: 额外数据
        key_prefix: Redis key 前缀

    Returns:
        流转结果
    """
    state_machine = OrderStateMachine(redis, order_id, key_prefix)
    return await state_machine.transition(expected_state, new_state, extra_data)
