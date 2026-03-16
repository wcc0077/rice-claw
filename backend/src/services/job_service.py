"""Job Service - 任务领域服务

负责：
- 任务发布
- 抢单处理
- 派单/锁单
- 任务状态流转
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from redis import asyncio as aioredis

from ..db.jobs import get_job, create_job
from ..db.bids import get_bid, get_bids_for_job, create_bid
from ..db.job_workers import (
    create_job_worker,
    get_job_workers_for_job,
    update_job_worker_status,
)
from ..db.agents import get_agent
from ..db.payments import create_payment
from ..services.state_machine import OrderStateMachine, OrderState, StateTransitionError
from ..constants import OrderStatus, JobWorkerStatus, PaymentStatus
from ..models.db_models import Job
from ..utils.notification import notify_worker_dispatch


class JobService:
    """任务服务"""

    def __init__(
        self,
        db: Session,
        redis: aioredis.Redis,
        key_prefix: str = "shrimp:"
    ):
        self.db = db
        self.redis = redis
        self.key_prefix = key_prefix

    async def create_and_publish_job(
        self,
        employer_id: str,
        title: str,
        description: str = "",
        required_tags: Optional[List[str]] = None,
        reward_amount: int = 0,
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None,
        bid_limit: int = 3,
        deadline: Optional[datetime] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """创建并发布任务

        Args:
            employer_id: 雇主 ID
            title: 任务标题
            description: 任务描述
            required_tags: 所需技能标签列表
            reward_amount: 酬金金额 (分)
            budget_min: 最低预算
            budget_max: 最高预算
            bid_limit: 竞标上限 (默认 3)
            deadline: 截止时间
            priority: 优先级 (low/normal/high)

        Returns:
            创建的任务信息
        """
        # 计算订金 (20% 酬金)
        deposit_amount = int(reward_amount * 0.2) if reward_amount else 0

        # 创建任务
        job_data = {
            "employer_id": employer_id,
            "title": title,
            "description": description,
            "required_tags": required_tags or [],
            "reward_amount": reward_amount,
            "deposit_amount": deposit_amount,
            "budget_min": budget_min,
            "budget_max": budget_max,
            "bid_limit": bid_limit,
            "deadline": deadline,
            "priority": priority,
        }
        job = create_job(self.db, job_data)

        # 初始化 Redis 状态机
        state_machine = OrderStateMachine(self.redis, job.job_id, self.key_prefix)
        await state_machine.initialize_state(OrderState.OPEN)

        # 记录操作日志
        await state_machine.record_action("create", employer_id, {
            "title": title,
            "reward_amount": reward_amount,
            "deposit_amount": deposit_amount,
        })

        return {
            "job_id": job.job_id,
            "title": job.title,
            "status": OrderState.OPEN,
            "reward_amount": reward_amount,
            "deposit_amount": deposit_amount,
            "bid_limit": bid_limit,
        }

    async def grab_order(
        self,
        job_id: str,
        worker_id: str,
        proposal: str = "",
        quote: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """抢单

        Args:
            job_id: 任务 ID
            worker_id: 工人 ID
            proposal: 提案/方案
            quote: 报价

        Returns:
            抢单结果：
            {
                "success": bool,
                "bid_id": str,
                "message": str
            }
        """
        # 1. 检查任务是否存在且状态为 OPEN
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        if job.status != OrderState.OPEN:
            return {"success": False, "message": f"任务状态为 {job.status}，无法抢单"}

        # 2. 检查工人是否存在
        worker = get_agent(self.db, worker_id)
        if not worker:
            return {"success": False, "message": "工人账户不存在"}

        # 3. 验证不能接自己发的单（同一 agent 不能接自己的单）
        if job.employer_id == worker_id:
            return {"success": False, "message": "不能接自己发布的任务"}

        # 4. 检查是否已抢过该任务
        existing_bids = get_bids_for_job(self.db, job_id)
        for bid in existing_bids:
            # bid 是 Dict，使用字典方式访问
            if bid.get("worker_id") == worker_id:
                return {"success": False, "message": "您已抢过此任务"}

        # 5. 检查是否已达接单上限
        bid_limit = job.bid_limit or 3
        if len(existing_bids) >= bid_limit:
            return {"success": False, "message": "该任务已达最大接单数"}

        # 6. 创建 bid
        bid_data = {
            "job_id": job_id,
            "worker_id": worker_id,
            "proposal": proposal,
            "quote": quote or {},
            "status": OrderStatus.PENDING
        }
        bid = create_bid(self.db, bid_data)

        # 7. 创建 job_worker 关联
        job_worker_data = {
            "job_id": job_id,
            "bid_id": bid.bid_id,
            "worker_id": worker_id,
            "status": JobWorkerStatus.PENDING
        }
        create_job_worker(self.db, job_worker_data)

        # 8. 发布新 bid 通知 (通过 Redis Pub/Sub)
        await self.redis.publish(  # type: ignore
            f"{self.key_prefix}channel:new_bid",
            json.dumps({
                "type": "new_bid",
                "job_id": job_id,
                "bid_id": bid.bid_id,
                "worker_id": worker_id,
                "employer_id": job.employer_id
            })
        )

        return {
            "success": True,
            "bid_id": bid.bid_id,
            "message": "抢单成功，等待派单"
        }

    async def confirm_lock_payment(
        self,
        job_id: str,
        bid_id: str,
        worker_id: str
    ) -> Dict[str, Any]:
        """确认锁单支付 (订金)

        Args:
            job_id: 任务 ID
            bid_id: Bid ID
            worker_id: 工人 ID

        Returns:
            确认结果
        """
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        # 验证 bid 是否存在并属于该工人
        bid = get_bid(self.db, bid_id)
        if not bid:
            return {"success": False, "message": "bid 不存在"}
        if bid.worker_id != worker_id:
            return {"success": False, "message": "bid 不属于该工人"}

        # 获取订金金额
        deposit_amount = job.deposit_amount
        if not deposit_amount:
            deposit_amount = int(job.reward_amount * 0.2) if job.reward_amount else 0

        # 创建订金支付记录
        payment_data = {
            "job_id": job_id,
            "bid_id": bid_id,
            "payer_id": job.employer_id,  # 雇主支付订金
            "amount": deposit_amount,
            "payment_type": "deposit",
            "status": PaymentStatus.PENDING
        }
        payment = create_payment(self.db, payment_data)

        # 更新 job_worker 状态为 LOCKED
        job_workers = get_job_workers_for_job(self.db, job_id)
        for jw in job_workers:
            if jw["bid_id"] == bid_id:
                update_job_worker_status(self.db, jw["id"], "LOCKED")
                break

        # 记录锁单时间
        lock_deadline = datetime.now(timezone.utc) + timedelta(days=7)  # 默认 7 天交付期
        from sqlalchemy import update
        from ..models.db_models import Job
        self.db.execute(
            update(Job)
            .where(Job.job_id == job_id)
            .values(
                locked_at=datetime.now(timezone.utc),
                lock_deadline=lock_deadline
            )
        )
        self.db.commit()

        return {
            "success": True,
            "payment_id": payment.payment_id,
            "deposit_amount": deposit_amount,
            "lock_deadline": lock_deadline.isoformat()
        }

    async def close_job(
        self,
        job_id: str,
        winner_bid_id: Optional[str] = None,
        closer_id: str = ""
    ) -> Dict[str, Any]:
        """关闭任务

        Args:
            job_id: 任务 ID
            winner_bid_id: 中标 bid ID (可选)
            closer_id: 操作人 ID

        Returns:
            关闭结果
        """
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        # 获取当前状态
        state_machine = OrderStateMachine(self.redis, job_id, self.key_prefix)
        current_state = await state_machine.get_current_state()

        if not current_state:
            return {"success": False, "message": "任务状态未初始化"}

        # 状态流转到 CLOSED
        try:
            if current_state == OrderState.REVIEW:
                await state_machine.transition(OrderState.REVIEW, OrderState.CLOSED, {
                    "winner_bid_id": winner_bid_id,
                    "closed_by": closer_id,
                    "closed_at": datetime.now(timezone.utc).isoformat()
                })
            elif current_state == OrderState.ACTIVE:
                # 允许从 ACTIVE 直接到 CLOSED (取消任务)
                await state_machine.transition(OrderState.ACTIVE, OrderState.CLOSED, {
                    "winner_bid_id": winner_bid_id,
                    "closed_by": closer_id,
                    "closed_at": datetime.now(timezone.utc).isoformat()
                })
            else:
                return {"success": False, "message": f"当前状态 {current_state} 无法关闭"}
        except StateTransitionError as e:
            return {"success": False, "message": f"状态流转失败：{e.message}"}

        # 更新数据库
        update_data = {"status": OrderState.CLOSED}
        if winner_bid_id:
            update_data["winner_id"] = winner_bid_id

        from sqlalchemy import update
        from ..models.db_models import Job
        self.db.execute(
            update(Job)
            .where(Job.job_id == job_id)
            .values(**update_data)
        )
        self.db.commit()

        # 记录操作日志
        await state_machine.record_action("close", closer_id, {
            "winner_bid_id": winner_bid_id
        })

        return {
            "success": True,
            "job_id": job_id,
            "winner_bid_id": winner_bid_id,
            "message": "任务已关闭"
        }


# ========== 便捷函数 ==========

def create_job_service(db: Session, redis: aioredis.Redis) -> JobService:
    """创建 JobService 实例"""
    return JobService(db, redis)
