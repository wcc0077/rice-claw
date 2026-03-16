"""Bid 业务逻辑服务层

职责:
- 封装所有 Bid 相关的业务逻辑
- 提供统一的接口供 HTTP API、MCP Server、WebSocket Handler 调用
- 处理权限验证、状态验证、业务规则校验
- 抛出统一的异常类型供各协议层转换为各自的响应格式
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..db import bids as bid_dal
from ..db import jobs as job_dal
from ..db import job_workers as job_worker_dal
from ..db import agents as agent_dal
from ..auth.permissions import PermissionDeniedError


class BidValidationError(Exception):
    """Bid 业务验证异常"""
    pass


class BidService:
    """Bid 业务服务类"""

    def __init__(self, db: Session):
        self.db = db

    def create_bid(
        self,
        job_id: str,
        worker_id: str,
        proposal: str,
        quote: Dict[str, Any],
        portfolio_links: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """创建竞标（抢单）

        业务规则:
        1. 任务必须存在且状态为 OPEN
        2. 竞标数不能超过任务的 bid_limit
        3. 同一个工人不能对同一任务重复抢单

        Args:
            job_id: 任务 ID
            worker_id: 工人 ID
            proposal: 竞标方案描述
            quote: 报价信息 {amount, currency, delivery_days}
            portfolio_links: 作品集链接列表

        Returns:
            创建的竞标信息字典

        Raises:
            BidValidationError: 当违反业务规则时
        """
        # 1. 验证任务状态
        job = job_dal.get_job(self.db, job_id)
        if not job:
            raise BidValidationError(f"Job {job_id} not found")
        if job.status != "OPEN":
            raise BidValidationError(
                f"Job {job_id} is not accepting bids (status: {job.status})"
            )

        # 2. 检查竞标上限
        existing_bids = bid_dal.get_bids_for_job(self.db, job_id)
        if len(existing_bids) >= job.bid_limit:
            raise BidValidationError("Bid limit reached")

        # 3. 检查重复抢单
        for bid in existing_bids:
            if bid["worker_id"] == worker_id:
                raise BidValidationError(
                    f"Worker {worker_id} has already bid on this job"
                )

        # 4. 验证工人存在
        worker = agent_dal.get_agent(self.db, worker_id)
        if not worker:
            raise BidValidationError(f"Worker {worker_id} not found")

        # 5. 创建竞标 (DAL 层内部还有一轮验证)
        bid_data = {
            "job_id": job_id,
            "worker_id": worker_id,
            "proposal": proposal,
            "quote": quote,
            "portfolio_links": portfolio_links or [],
        }

        try:
            bid = bid_dal.create_bid(self.db, bid_data)
            return bid.to_dict_with_quote()
        except ValueError as e:
            # DAL 层验证失败（如任务状态变更）
            raise BidValidationError(str(e))

    def accept_bid(
        self,
        job_id: str,
        bid_id: str,
        employer_id: str
    ) -> Dict[str, Any]:
        """接受竞标

        业务规则:
        1. 只有雇主可以接受自己任务的竞标
        2. 竞标必须属于该任务
        3. 竞标不能已经被接受或拒绝

        Args:
            job_id: 任务 ID
            bid_id: 竞标 ID
            employer_id: 雇主 ID

        Returns:
            更新后的竞标信息

        Raises:
            BidValidationError: 当违反业务规则时
            PermissionDeniedError: 当无权操作时
        """
        # 1. 验证任务存在
        job = job_dal.get_job(self.db, job_id)
        if not job:
            raise BidValidationError(f"Job {job_id} not found")

        # 2. 验证任务所有权
        if job.employer_id != employer_id:
            raise PermissionDeniedError(
                action="accept_bid",
                resource_type="job",
                resource_id=job_id,
                agent_id=employer_id
            )

        # 3. 验证竞标存在
        bid = bid_dal.get_bid(self.db, bid_id)
        if not bid:
            raise BidValidationError(f"Bid {bid_id} not found")

        # 4. 验证竞标属于该任务
        if bid.job_id != job_id:
            raise BidValidationError(
                f"Bid {bid_id} does not belong to job {job_id}"
            )

        # 5. 验证竞标状态
        if bid.is_hired:
            raise BidValidationError("Bid already accepted")
        if bid.status in ("NOT_SELECTED", "REJECTED"):
            raise BidValidationError("Bid already rejected")

        # 6. 更新竞标状态
        updated_bid = bid_dal.update_bid_status(
            self.db, bid_id, "SELECTED", is_hired=True
        )
        if not updated_bid:
            raise BidValidationError("Failed to update bid status")

        # 7. 更新任务状态
        job_dal.update_job(self.db, job_id, {"status": "ACTIVE"})

        return updated_bid.to_dict_with_quote()

    def reject_bid(
        self,
        job_id: str,
        bid_id: str,
        employer_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """拒绝竞标

        Args:
            job_id: 任务 ID
            bid_id: 竞标 ID
            employer_id: 雇主 ID
            reason: 拒绝原因（可选）

        Returns:
            更新后的竞标信息

        Raises:
            BidValidationError: 当违反业务规则时
            PermissionDeniedError: 当无权操作时
        """
        # 验证任务和所有权
        job = job_dal.get_job(self.db, job_id)
        if not job:
            raise BidValidationError(f"Job {job_id} not found")
        if job.employer_id != employer_id:
            raise PermissionDeniedError(
                action="reject_bid",
                resource_type="job",
                resource_id=job_id,
                agent_id=employer_id
            )

        # 验证竞标
        bid = bid_dal.get_bid(self.db, bid_id)
        if not bid:
            raise BidValidationError(f"Bid {bid_id} not found")
        if bid.job_id != job_id:
            raise BidValidationError(
                f"Bid {bid_id} does not belong to job {job_id}"
            )

        # 更新状态
        updated_bid = bid_dal.update_bid_status(
            self.db, bid_id, "NOT_SELECTED", is_hired=False
        )
        if not updated_bid:
            raise BidValidationError("Failed to update bid status")

        return updated_bid.to_dict_with_quote()

    def get_bids_for_job(
        self,
        job_id: str
    ) -> List[Dict[str, Any]]:
        """获取任务的所有竞标

        Args:
            job_id: 任务 ID

        Returns:
            竞标列表

        Raises:
            BidValidationError: 当任务不存在时
        """
        job = job_dal.get_job(self.db, job_id)
        if not job:
            raise BidValidationError(f"Job {job_id} not found")

        bids = bid_dal.get_bids_with_worker_info(self.db, job_id)
        return bids

    def get_worker_bids(
        self,
        worker_id: str,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取工人的所有竞标

        Args:
            worker_id: 工人 ID
            status: 可选的状态过滤（暂未实现过滤）

        Returns:
            竞标列表
        """
        # 注意：DAL 层的 get_bids_by_worker 不支持 status 过滤
        # 如需过滤，可在获取后自行处理
        all_bids = bid_dal.get_bids_by_worker(self.db, worker_id)

        if status:
            return [bid for bid in all_bids if bid.get("status") == status]
        return all_bids

    def create_job_worker_association(
        self,
        job_id: str,
        bid_id: str,
        worker_id: str,
        status: str = "PENDING"
    ) -> Dict[str, Any]:
        """创建 job_worker 关联（用于 WebSocket 抢单流程）

        Args:
            job_id: 任务 ID
            bid_id: 竞标 ID
            worker_id: 工人 ID
            status: 初始状态

        Returns:
            创建的关联信息字典
        """
        job_worker_data = {
            "job_id": job_id,
            "bid_id": bid_id,
            "worker_id": worker_id,
            "status": status,
        }
        result = job_worker_dal.create_job_worker(self.db, job_worker_data)
        # 转换为字典返回
        return {
            "id": result.id if hasattr(result, 'id') else None,
            "job_id": job_id,
            "bid_id": bid_id,
            "worker_id": worker_id,
            "status": status,
        }
