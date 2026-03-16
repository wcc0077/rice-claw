"""Payment Service - 支付领域服务

负责：
- 订金支付
- 尾款支付
- 退款处理
- 补贴发放
- 罚金处理
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from redis import asyncio as aioredis

from ..db.payments import (
    create_payment,
    get_payment,
    get_payments_for_job,
    update_payment_status,
    mark_payment_success,
    mark_payment_failed,
    get_deposit_payment,
    get_pending_payments_for_job,
    get_total_paid_amount,
    refund_payment,
)
from ..db.jobs import get_job
from ..db.job_workers import get_job_workers_for_job
from ..services.state_machine import OrderStateMachine, OrderState
from ..constants import PaymentStatus, JobWorkerStatus


class PaymentService:
    """支付服务"""

    def __init__(
        self,
        db: Session,
        redis: aioredis.Redis,
        key_prefix: str = "shrimp:"
    ):
        self.db = db
        self.redis = redis
        self.key_prefix = key_prefix

    async def process_deposit_payment(
        self,
        job_id: str,
        worker_id: str,
        transaction_id: str
    ) -> Dict[str, Any]:
        """处理订金支付

        Args:
            job_id: 任务 ID
            worker_id: 工人 ID (用于验证)
            transaction_id: 第三方支付交易 ID

        Returns:
            支付结果
        """
        # 1. 检查任务是否存在
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        # 2. 检查订金支付记录是否存在
        deposit_payment = get_deposit_payment(self.db, job_id)
        if not deposit_payment:
            return {"success": False, "message": "订金支付记录不存在"}

        # 3. 更新支付状态为成功
        payment = mark_payment_success(
            self.db,
            deposit_payment["payment_id"],
            transaction_id
        )
        if not payment:
            return {"success": False, "message": "更新支付状态失败"}

        # 4. 更新 job_worker 状态为 LOCKED
        job_workers = get_job_workers_for_job(self.db, job_id)
        for jw in job_workers:
            if jw.get("worker_id") == worker_id:
                from ..db.job_workers import update_job_worker_status
                update_job_worker_status(self.db, jw["id"], JobWorkerStatus.LOCKED)
                break

        # 5. 更新任务状态
        from ..db.jobs import update_job
        update_job(self.db, job_id, {
            "status": JobWorkerStatus.LOCKED,
            "deposit_paid": True,
            "locked_at": datetime.now(timezone.utc)
        })

        # 6. 更新状态机
        state_machine = OrderStateMachine(self.redis, job_id, self.key_prefix)
        try:
            await state_machine.transition(
                OrderState.OPEN,
                OrderState.ACTIVE,
                {"deposit_paid": True, "transaction_id": transaction_id}
            )
        except Exception:
            # 状态机可能已经是 ACTIVE 状态，忽略错误
            pass

        # 7. 发布支付成功通知
        await self._notify_payment_result(
            job_id=job_id,
            payment_type="deposit",
            success=True,
            amount=deposit_payment["amount"],
            transaction_id=transaction_id
        )

        return {
            "success": True,
            "payment_id": deposit_payment["payment_id"],
            "amount": deposit_payment["amount"],
            "message": "订金支付成功"
        }

    async def process_final_payment(
        self,
        job_id: str,
        winner_bid_id: str,
        transaction_id: str
    ) -> Dict[str, Any]:
        """处理尾款支付

        Args:
            job_id: 任务 ID
            winner_bid_id: 中标 bid ID
            transaction_id: 第三方支付交易 ID

        Returns:
            支付结果
        """
        # 1. 检查任务是否存在
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        # 2. 计算尾款金额
        final_amount = (job.reward_amount or 0) - (job.deposit_amount or 0)
        if final_amount <= 0:
            return {"success": False, "message": "尾款金额无效"}

        # 3. 获取中标者信息
        job_workers = get_job_workers_for_job(self.db, job_id)
        winner = None
        for jw in job_workers:
            if jw.get("bid_id") == winner_bid_id:
                winner = jw
                break

        if not winner:
            return {"success": False, "message": "中标者信息不存在"}

        # 4. 创建尾款支付记录
        payment_data = {
            "job_id": job_id,
            "payer_id": job.employer_id,
            "payee_id": winner["worker_id"],
            "amount": final_amount,
            "type": "FINAL",
            "status": "SUCCESS",
            "transaction_id": transaction_id,
            "job_worker_id": winner["id"],
        }
        payment = create_payment(self.db, payment_data)

        # 5. 更新任务状态
        from ..db.jobs import update_job
        update_job(self.db, job_id, {
            "status": OrderState.REVIEW,
            "final_payment_status": "PAID",
            "final_payment_amount": final_amount,
        })

        # 6. 更新状态机
        state_machine = OrderStateMachine(self.redis, job_id, self.key_prefix)
        try:
            await state_machine.transition(
                OrderState.ACTIVE,
                OrderState.REVIEW,
                {"final_payment_paid": True, "transaction_id": transaction_id}
            )
        except Exception:
            pass

        # 7. 发布支付成功通知
        await self._notify_payment_result(
            job_id=job_id,
            payment_type="final",
            success=True,
            amount=final_amount,
            transaction_id=transaction_id
        )

        return {
            "success": True,
            "payment_id": payment.payment_id,
            "amount": final_amount,
            "message": "尾款支付成功"
        }

    async def process_subsidy_payment(
        self,
        job_worker_id: str,
        subsidy_amount: int,
        transaction_id: str
    ) -> Dict[str, Any]:
        """处理补贴支付

        Args:
            job_worker_id: 任务 - 工人关联 ID
            subsidy_amount: 补贴金额
            transaction_id: 第三方支付交易 ID

        Returns:
            支付结果
        """
        # 1. 获取 job_worker 信息
        from ..db.job_workers import get_job_worker
        jw = get_job_worker(self.db, job_worker_id)
        if not jw:
            return {"success": False, "message": "任务 - 工人关联不存在"}

        # 2. 创建补贴支付记录
        payment_data = {
            "job_id": jw.job_id,
            "payer_id": "PLATFORM",  # 平台支付补贴
            "payee_id": jw.worker_id,
            "amount": subsidy_amount,
            "type": "SUBSIDY",
            "status": "SUCCESS",
            "transaction_id": transaction_id,
            "job_worker_id": job_worker_id,
        }
        payment = create_payment(self.db, payment_data)

        return {
            "success": True,
            "payment_id": payment.payment_id,
            "amount": subsidy_amount,
            "message": "补贴支付成功"
        }

    async def process_refund(
        self,
        payment_id: str,
        refund_amount: Optional[int] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """处理退款

        Args:
            payment_id: 原支付 ID
            refund_amount: 退款金额 (不填则全额退款)
            reason: 退款原因

        Returns:
            退款结果
        """
        # 1. 获取原支付记录
        original_payment = get_payment(self.db, payment_id)
        if not original_payment:
            return {"success": False, "message": "支付记录不存在"}

        if original_payment.status != "SUCCESS":
            return {"success": False, "message": "只能退款成功的支付"}

        # 2. 创建退款记录
        refund = refund_payment(self.db, payment_id, refund_amount)
        if not refund:
            return {"success": False, "message": "创建退款记录失败"}

        # 3. 标记退款成功
        refund = mark_payment_success(self.db, refund.payment_id)

        # 4. 发布退款通知
        await self._notify_payment_result(
            job_id=original_payment.job_id,
            payment_type="refund",
            success=True,
            amount=refund.amount if refund else 0,
            reason=reason
        )

        return {
            "success": True,
            "refund_payment_id": refund.payment_id if refund else None,
            "amount": refund.amount if refund else 0,
            "message": "退款成功"
        }

    async def get_payment_status(
        self,
        job_id: str
    ) -> Dict[str, Any]:
        """获取任务支付状态

        Args:
            job_id: 任务 ID

        Returns:
            支付状态信息
        """
        job = get_job(self.db, job_id)
        if not job:
            return {"success": False, "message": "任务不存在"}

        # 获取所有支付记录
        all_payments = get_payments_for_job(self.db, job_id)

        # 计算总额
        deposit_paid = sum(
            p["amount"] for p in all_payments
            if p["type"] == "DEPOSIT" and p["status"] == "SUCCESS"
        )
        final_paid = sum(
            p["amount"] for p in all_payments
            if p["type"] == "FINAL" and p["status"] == "SUCCESS"
        )
        subsidy_paid = sum(
            p["amount"] for p in all_payments
            if p["type"] == "SUBSIDY" and p["status"] == "SUCCESS"
        )

        return {
            "success": True,
            "job_id": job_id,
            "deposit_amount": job.deposit_amount or 0,
            "deposit_paid": deposit_paid,
            "deposit_paid_status": PaymentStatus.PAID if deposit_paid >= (job.deposit_amount or 0) else PaymentStatus.PENDING,
            "reward_amount": job.reward_amount or 0,
            "final_amount": (job.reward_amount or 0) - (job.deposit_amount or 0),
            "final_paid": final_paid,
            "final_paid_status": PaymentStatus.PAID if final_paid > 0 else PaymentStatus.PENDING,
            "subsidy_paid": subsidy_paid,
            "total_paid": deposit_paid + final_paid + subsidy_paid,
            "payments": all_payments,
        }

    async def _notify_payment_result(
        self,
        job_id: str,
        payment_type: str,
        success: bool,
        amount: int = 0,
        transaction_id: str = "",
        reason: str = ""
    ):
        """发布支付结果通知

        通过 Redis Pub/Sub 推送
        """
        message = json.dumps({
            "type": "payment_result",
            "data": {
                "job_id": job_id,
                "payment_type": payment_type,
                "success": success,
                "amount": amount,
                "transaction_id": transaction_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
        await self.redis.publish(
            f"{self.key_prefix}channel:payment_result",
            message
        )


# ========== 便捷函数 ==========

def create_payment_service(
    db: Session,
    redis: aioredis.Redis
) -> PaymentService:
    """创建 PaymentService 实例"""
    return PaymentService(db, redis)
