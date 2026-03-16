"""Dispatch Service - 派单领域服务

负责：
- 派单/锁单
- 选中接单方
- 通知工人
- 处理拒单/取消
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from redis import asyncio as aioredis

from ..db.jobs import get_job, update_job
from ..db.bids import get_bid, get_bids_for_job
from ..db.job_workers import (
    get_job_workers_for_job,
    confirm_job_worker,
    update_job_worker_status,
    cancel_job_worker,
)
from ..db.agents import get_agent
from ..services.state_machine import OrderStateMachine, OrderState, StateTransitionError
from ..utils.notification import notify_worker_dispatch
from ..constants import JobWorkerStatus


class DispatchService:
    """派单服务"""

    def __init__(
        self,
        db: Session,
        redis: aioredis.Redis,
        key_prefix: str = "shrimp:"
    ):
        self.db = db
        self.redis = redis
        self.key_prefix = key_prefix

    async def dispatch_order(
        self,
        job_id: str,
        selected_bid_ids: List[str],
        employer_id: str
    ) -> Dict[str, Any]:
        """派单/锁单

        Args:
            job_id: 任务 ID
            selected_bid_ids: 选中的 bid ID 列表 (最多 3 个)
            employer_id: 雇主 ID

        Returns:
            派单结果
        """
        # 1. 检查任务状态
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        if job.status != OrderState.OPEN:
            return {"success": False, "message": f"任务状态为 {job.status}，无法派单"}

        # 2. 验证选中的 bid 数量 (最多 3 个)
        if len(selected_bid_ids) > 3:
            return {"success": False, "message": "最多只能选择 3 个接单方"}

        if len(selected_bid_ids) == 0:
            return {"success": False, "message": "请至少选择 1 个接单方"}

        # 3. 验证所有 bid 都属于该任务
        all_bids = get_bids_for_job(self.db, job_id)
        all_bid_ids = {bid.get("bid_id") for bid in all_bids}
        for bid_id in selected_bid_ids:
            if bid_id not in all_bid_ids:
                return {"success": False, "message": f"bid {bid_id} 不属于该任务"}

        # 4. 更新状态机：OPEN → ACTIVE
        state_machine = OrderStateMachine(self.redis, job_id, self.key_prefix)
        try:
            await state_machine.transition(OrderState.OPEN, OrderState.ACTIVE, {
                "selected_bid_ids": selected_bid_ids,
                "dispatched_by": employer_id,
                "dispatched_at": datetime.now(timezone.utc).isoformat()
            })
        except StateTransitionError as e:
            return {"success": False, "message": f"状态流转失败：{e.message}"}

        # 5. 更新数据库状态
        update_job(self.db, job_id, {"status": OrderState.ACTIVE})

        # 6. 更新选中的 job_worker 状态为 CONFIRMED/LOCKED
        job_workers = get_job_workers_for_job(self.db, job_id)
        for jw in job_workers:
            if jw.get("bid_id") in selected_bid_ids:
                confirm_job_worker(self.db, jw["id"])

        # 7. 通知所有被选中的工人
        for bid_id in selected_bid_ids:
            bid = get_bid(self.db, bid_id)
            if bid:
                await notify_worker_dispatch(self.redis, job_id, bid_id)

        # 8. 记录操作日志
        await state_machine.record_action("dispatch", employer_id, {
            "selected_bid_ids": selected_bid_ids
        })

        return {
            "success": True,
            "message": f"成功派单给 {len(selected_bid_ids)} 个接单方",
            "job_id": job_id,
            "selected_bid_ids": selected_bid_ids
        }

    async def cancel_dispatch(
        self,
        job_id: str,
        bid_id: str,
        employer_id: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """取消派单

        Args:
            job_id: 任务 ID
            bid_id: 要取消的 bid ID
            employer_id: 雇主 ID
            reason: 取消原因

        Returns:
            取消结果
        """
        # 1. 检查任务状态
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        if job.status != OrderState.ACTIVE:
            return {"success": False, "message": f"任务状态为 {job.status}，无法取消派单"}

        # 2. 检查 bid 是否存在
        bid = get_bid(self.db, bid_id)
        if not bid:
            return {"success": False, "message": "bid 不存在"}

        # 3. 找到对应的 job_worker
        job_workers = get_job_workers_for_job(self.db, job_id)
        job_worker = None
        for jw in job_workers:
            if jw.get("bid_id") == bid_id:
                job_worker = jw
                break

        if not job_worker:
            return {"success": False, "message": "job_worker 不存在"}

        # 4. 取消 job_worker
        cancel_job_worker(self.db, job_worker["id"])

        # 5. 检查是否还有其他活跃的 job_worker
        remaining_workers = [
            jw for jw in job_workers
            if jw.get("bid_id") != bid_id and jw.get("status") != JobWorkerStatus.CANCELLED
        ]

        # 6. 如果没有剩余的工人，关闭任务
        if not remaining_workers:
            update_job(self.db, job_id, {"status": OrderState.CLOSED})
            state_machine = OrderStateMachine(self.redis, job_id, self.key_prefix)
            try:
                await state_machine.transition(OrderState.ACTIVE, OrderState.CLOSED, {
                    "cancelled_by": employer_id,
                    "reason": reason
                })
            except StateTransitionError:
                pass

        # 7. 通知工人
        await self._notify_dispatch_cancel(bid.worker_id, job_id, bid_id, reason)

        return {
            "success": True,
            "message": "已成功取消派单",
            "job_id": job_id,
            "bid_id": bid_id
        }

    async def confirm_worker_ready(
        self,
        job_id: str,
        worker_id: str
    ) -> Dict[str, Any]:
        """确认工人已就绪 (开始工作)

        Args:
            job_id: 任务 ID
            worker_id: 工人 ID

        Returns:
            确认结果
        """
        # 1. 检查任务状态
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        if job.status != OrderState.ACTIVE:
            return {"success": False, "message": f"任务状态为 {job.status}"}

        # 2. 找到对应的 job_worker
        job_workers = get_job_workers_for_job(self.db, job_id)
        job_worker = None
        for jw in job_workers:
            if jw.get("worker_id") == worker_id:
                job_worker = jw
                break

        if not job_worker:
            return {"success": False, "message": "未找到该工人的接单记录"}

        # 3. 更新状态为 WORKING
        update_job_worker_status(self.db, job_worker["id"], "WORKING")

        # 4. 记录操作日志
        state_machine = OrderStateMachine(self.redis, job_id, self.key_prefix)
        await state_machine.record_action("worker_ready", worker_id, {
            "job_worker_id": job_worker["id"],
            "started_at": datetime.now(timezone.utc).isoformat()
        })

        # 5. 通知雇主
        await self._notify_worker_started(job.employer_id, job_id, worker_id)

        return {
            "success": True,
            "message": "工人已就绪，开始工作"
        }

    async def _notify_dispatch_cancel(
        self,
        worker_id: str,
        job_id: str,
        bid_id: str,
        reason: str = ""
    ):
        """通知工人派单已被取消

        通过 Redis Pub/Sub 推送
        """
        message = json.dumps({
            "type": "dispatch_cancelled",
            "data": {
                "job_id": job_id,
                "bid_id": bid_id,
                "reason": reason,
                "cancelled_at": datetime.now(timezone.utc).isoformat()
            }
        })
        await self.redis.publish(
            f"{self.key_prefix}channel:dispatch_cancel",
            message
        )

    async def _notify_worker_started(
        self,
        employer_id: str,
        job_id: str,
        worker_id: str
    ):
        """通知雇主工人已开始工作

        通过 Redis Pub/Sub 推送
        """
        message = json.dumps({
            "type": "worker_started",
            "data": {
                "job_id": job_id,
                "worker_id": worker_id,
                "message": "工人已确认并开始工作"
            }
        })
        await self.redis.publish(
            f"{self.key_prefix}channel:worker_status",
            message
        )


# ========== 便捷函数 ==========

def create_dispatch_service(
    db: Session,
    redis: aioredis.Redis
) -> DispatchService:
    """创建 DispatchService 实例"""
    return DispatchService(db, redis)
