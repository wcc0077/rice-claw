"""Matching Platform API - 撮合平台接口

提供任务发布、抢单、派单、支付等撮合功能接口
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Annotated
from redis import asyncio as aioredis
from loguru import logger

from ..db.database import get_db
from ..db import agents as agent_dal
from ..services.job_service import JobService, create_job_service
from ..services.payment_service import PaymentService, create_payment_service
from ..services.dispatch_service import DispatchService, create_dispatch_service
from ..security import (
    PromptGuard,
    OutputGuard,
    ThreatLevel,
    raise_if_rate_limited,
)
from ..security.integration import rate_limit, validate_prompt
from ..models.schemas import (
    JobPublishRequest,
    JobPublishResponse,
    GrabOrderRequest,
    GrabOrderResponse,
    DispatchOrderRequest,
    DispatchOrderResponse,
    LockPaymentRequest,
    LockPaymentResponse,
    CloseJobRequest,
    CloseJobResponse,
    DepositPaymentRequest,
    FinalPaymentRequest,
    PaymentStatusResponse,
    RefundRequest,
    CancelDispatchRequest,
    ConfirmWorkerReadyRequest,
)

router = APIRouter()


# ========== 依赖注入 ==========

DbSession = Annotated[Session, Depends(get_db)]


def get_redis() -> aioredis.Redis:
    """获取 Redis 连接实例"""
    from redis import asyncio as aioredis
    return aioredis.from_url(
        "redis://localhost:6379/0",
        decode_responses=True
    )


RedisSession = Annotated[aioredis.Redis, Depends(get_redis)]


def get_prompt_guard() -> PromptGuard:
    """获取 PromptGuard 实例"""
    return PromptGuard(strict_mode=True)


def get_output_guard() -> OutputGuard:
    """获取 OutputGuard 实例"""
    return OutputGuard()


PromptGuardSession = Annotated[PromptGuard, Depends(get_prompt_guard)]
OutputGuardSession = Annotated[OutputGuard, Depends(get_output_guard)]


def get_job_service(db: DbSession, redis: RedisSession) -> JobService:
    """获取 JobService 实例"""
    return create_job_service(db, redis)


def get_payment_service(db: DbSession, redis: RedisSession) -> PaymentService:
    """获取 PaymentService 实例"""
    return create_payment_service(db, redis)


def get_dispatch_service(db: DbSession, redis: RedisSession) -> DispatchService:
    """获取 DispatchService 实例"""
    return create_dispatch_service(db, redis)


# ========== 统一安全处理 ==========

async def validate_user_input(
    redis: aioredis.Redis,
    guard: PromptGuard,
    user_id: str,
    rate_limit_type: str,
    **content_fields
):
    """
    统一验证用户输入

    Args:
        redis: Redis 实例
        guard: PromptGuard 实例
        user_id: 用户 ID
        rate_limit_type: 速率限制类型
        **content_fields: 需要验证的内容字段 (name=value)

    Returns:
        dict: 验证后的内容字段

    Raises:
        HTTPException: 当检测到危险内容时
    """
    # 速率限制
    await raise_if_rate_limited(redis, user_id, rate_limit_type)

    # 验证每个字段
    validated = {}
    for field_name, content in content_fields.items():
        if not content:
            continue

        result = guard.analyze(content)
        if result.threat_level == ThreatLevel.DANGEROUS:
            logger.warning(f"{field_name} contains dangerous patterns: {result.detected_patterns}")
            raise HTTPException(
                status_code=400,
                detail=f"{field_name}包含危险内容：{result.detected_patterns[0] if result.detected_patterns else 'unknown'}"
            )
        if result.threat_level == ThreatLevel.SUSPICIOUS:
            logger.info(f"{field_name} sanitized, detected patterns: {result.detected_patterns}")
            validated[field_name] = result.sanitized_content
        else:
            validated[field_name] = content

    return validated


# ========== Job Service 接口 ==========

@router.post("/jobs/publish", response_model=JobPublishResponse)
async def publish_job(
    request: JobPublishRequest,
    employer_id: str,
    redis: RedisSession,
    guard: PromptGuardSession,
    service: JobService = Depends(get_job_service)
):
    """发布任务

    创建新任务并初始化 Redis 状态机
    """
    # 统一验证用户输入（速率限制 + Prompt Injection 检测）
    validated = await validate_user_input(
        redis=redis,
        guard=guard,
        user_id=employer_id,
        rate_limit_type="job_create_hour",
        description=request.description,
        title=request.title
    )

    # 验证雇主是否存在
    employer = agent_dal.get_agent(service.db, employer_id)
    if not employer:
        raise HTTPException(status_code=400, detail=f"雇主 {employer_id} 不存在")

    try:
        result = await service.create_and_publish_job(
            employer_id=employer_id,
            title=validated.get("title", request.title),
            description=validated.get("description", request.description),
            required_tags=request.required_tags,
            reward_amount=request.reward_amount,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            bid_limit=request.bid_limit,
            deadline=request.deadline,
            priority=request.priority
        )
        return JobPublishResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/jobs/{job_id}/grab", response_model=GrabOrderResponse)
async def grab_order(
    job_id: str,
    request: GrabOrderRequest,
    worker_id: str,
    redis: RedisSession,
    guard: PromptGuardSession,
    service: JobService = Depends(get_job_service)
):
    """抢单

    工人抢单，创建 bid 和 job_worker 关联
    """
    # 统一验证用户输入
    validated = await validate_user_input(
        redis=redis,
        guard=guard,
        user_id=worker_id,
        rate_limit_type="bid_submit_hour",
        proposal=request.proposal
    )

    # 验证工人是否存在
    worker = agent_dal.get_agent(service.db, worker_id)
    if not worker:
        raise HTTPException(status_code=400, detail=f"工人 {worker_id} 不存在")

    quote_data = request.quote.model_dump() if request.quote else None

    result = await service.grab_order(
        job_id=job_id,
        worker_id=worker_id,
        proposal=validated.get("proposal", request.proposal),
        quote=quote_data
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return GrabOrderResponse(
        success=True,
        bid_id=result["bid_id"],
        job_id=job_id,
        message=result["message"]
    )


@router.post("/jobs/{job_id}/dispatch", response_model=DispatchOrderResponse)
async def dispatch_order(
    job_id: str,
    request: DispatchOrderRequest,
    redis: RedisSession,
    service: DispatchService = Depends(get_dispatch_service)
):
    """派单/锁单

    雇主选中最多 3 个接单方
    """
    # 速率限制
    await raise_if_rate_limited(redis, request.employer_id, "api_per_minute")

    result = await service.dispatch_order(
        job_id=job_id,
        selected_bid_ids=request.selected_bid_ids,
        employer_id=request.employer_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return DispatchOrderResponse(**result)


@router.post("/jobs/{job_id}/lock-payment", response_model=LockPaymentResponse)
async def confirm_lock_payment(
    job_id: str,
    request: LockPaymentRequest,
    redis: RedisSession,
    service: JobService = Depends(get_job_service)
):
    """确认锁单支付 (订金)

    工人支付订金后调用
    """
    # 速率限制
    await raise_if_rate_limited(redis, request.worker_id, "api_per_minute")

    result = await service.confirm_lock_payment(
        job_id=job_id,
        bid_id=request.bid_id,
        worker_id=request.worker_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return LockPaymentResponse(**result)


@router.post("/jobs/{job_id}/close", response_model=CloseJobResponse)
async def close_job(
    job_id: str,
    request: CloseJobRequest,
    redis: RedisSession,
    service: JobService = Depends(get_job_service)
):
    """关闭任务

    支持选中标的
    """
    # 速率限制
    await raise_if_rate_limited(redis, request.closer_id, "api_per_minute")

    result = await service.close_job(
        job_id=job_id,
        winner_bid_id=request.winner_bid_id,
        closer_id=request.closer_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return CloseJobResponse(**result)


# ========== Payment Service 接口 ==========

@router.post("/payments/deposit")
async def process_deposit_payment(
    request: DepositPaymentRequest,
    job_id: str,
    redis: RedisSession,
    service: PaymentService = Depends(get_payment_service)
):
    """处理订金支付

    工人支付订金
    """
    # 速率限制
    await raise_if_rate_limited(redis, request.worker_id, "api_per_minute")

    result = await service.process_deposit_payment(
        job_id=job_id,
        worker_id=request.worker_id,
        transaction_id=request.transaction_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/payments/final")
async def process_final_payment(
    request: FinalPaymentRequest,
    job_id: str,
    redis: RedisSession,
    service: PaymentService = Depends(get_payment_service)
):
    """处理尾款支付

    雇主支付尾款
    """
    # 速率限制
    await raise_if_rate_limited(redis, request.winner_bid_id, "api_per_minute")

    result = await service.process_final_payment(
        job_id=job_id,
        winner_bid_id=request.winner_bid_id,
        transaction_id=request.transaction_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/payments/{job_id}/status", response_model=PaymentStatusResponse)
async def get_payment_status(
    job_id: str,
    redis: RedisSession,
    service: PaymentService = Depends(get_payment_service)
):
    """获取任务支付状态"""
    # 速率限制
    await raise_if_rate_limited(redis, job_id, "api_per_second")

    result = await service.get_payment_status(job_id=job_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return PaymentStatusResponse(**result)


@router.post("/payments/refund")
async def process_refund(
    request: RefundRequest,
    redis: RedisSession,
    service: PaymentService = Depends(get_payment_service)
):
    """处理退款"""
    # 速率限制
    await raise_if_rate_limited(redis, request.payment_id, "api_per_minute")

    result = await service.process_refund(
        payment_id=request.payment_id,
        refund_amount=request.refund_amount,
        reason=request.reason
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


# ========== Dispatch Service 接口 ==========

@router.post("/dispatch/cancel")
async def cancel_dispatch(
    request: CancelDispatchRequest,
    job_id: str,
    redis: RedisSession,
    service: DispatchService = Depends(get_dispatch_service)
):
    """取消派单"""
    # 速率限制
    await raise_if_rate_limited(redis, request.employer_id, "api_per_minute")

    result = await service.cancel_dispatch(
        job_id=job_id,
        bid_id=request.bid_id,
        employer_id=request.employer_id,
        reason=request.reason
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/dispatch/worker-ready")
async def confirm_worker_ready(
    request: ConfirmWorkerReadyRequest,
    job_id: str,
    redis: RedisSession,
    service: DispatchService = Depends(get_dispatch_service)
):
    """确认工人已就绪 (开始工作)"""
    # 速率限制
    await raise_if_rate_limited(redis, request.worker_id, "api_per_minute")

    result = await service.confirm_worker_ready(
        job_id=job_id,
        worker_id=request.worker_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result
