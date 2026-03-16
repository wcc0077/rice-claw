"""Notification utilities for dispatch and status updates."""

import json
from redis import asyncio as aioredis


async def notify_worker_dispatch(
    redis: aioredis.Redis,
    job_id: str,
    bid_id: str,
    key_prefix: str = "shrimp:"
):
    """通知工人已被选中

    通过 Redis Pub/Sub 推送通知

    Args:
        redis: Redis connection
        job_id: Job ID
        bid_id: Bid ID
        key_prefix: Redis key prefix
    """
    message = json.dumps({
        "type": "dispatched",
        "data": {
            "job_id": job_id,
            "bid_id": bid_id,
            "status": "LOCKED",
            "message": "您已被选中，请支付订金并开始工作"
        }
    })
    await redis.publish(f"{key_prefix}channel:dispatch", message)
