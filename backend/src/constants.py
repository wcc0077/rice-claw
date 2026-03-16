"""Shared constants for the Shrimp Market API."""

# =============================================================================
# Order/Bid Status Constants
# =============================================================================

# Current status values (use these for new code)
class OrderStatus:
    """Order status constants."""
    BIDDING = "BIDDING"          # 竞标中
    SELECTED = "SELECTED"        # 中标
    NOT_SELECTED = "NOT_SELECTED"  # 未中标
    IN_PROGRESS = "IN_PROGRESS"  # 实施中
    COMPLETED = "COMPLETED"      # 实施完成
    DELIVERED = "DELIVERED"      # 已交付
    CANCELLED = "CANCELLED"      # 已取消

    # Legacy status aliases (for backward compatibility)
    PENDING = "PENDING"          # Maps to BIDDING
    ACCEPTED = "ACCEPTED"        # Maps to SELECTED
    REJECTED = "REJECTED"        # Maps to NOT_SELECTED


# All valid status values (including legacy for validation)
VALID_ORDER_STATUSES = [
    # New statuses
    OrderStatus.BIDDING,
    OrderStatus.SELECTED,
    OrderStatus.NOT_SELECTED,
    OrderStatus.IN_PROGRESS,
    OrderStatus.COMPLETED,
    OrderStatus.DELIVERED,
    OrderStatus.CANCELLED,
    # Legacy statuses (backward compatibility)
    OrderStatus.PENDING,
    OrderStatus.ACCEPTED,
    OrderStatus.REJECTED,
]

# Human-readable labels for statuses
ORDER_STATUS_LABELS = {
    OrderStatus.BIDDING: "竞标中",
    OrderStatus.SELECTED: "中标",
    OrderStatus.NOT_SELECTED: "未中标",
    OrderStatus.IN_PROGRESS: "实施中",
    OrderStatus.COMPLETED: "实施完成",
    OrderStatus.DELIVERED: "已交付",
    OrderStatus.CANCELLED: "已取消",
    # Legacy status labels
    OrderStatus.PENDING: "竞标中",
    OrderStatus.ACCEPTED: "中标",
    OrderStatus.REJECTED: "未中标",
}

# Mapping from legacy status to new status
STATUS_NORMALIZE = {
    OrderStatus.PENDING: OrderStatus.BIDDING,
    OrderStatus.ACCEPTED: OrderStatus.SELECTED,
    OrderStatus.REJECTED: OrderStatus.NOT_SELECTED,
}

# Valid status transitions for workers
ORDER_STATUS_TRANSITIONS = {
    OrderStatus.SELECTED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
    OrderStatus.IN_PROGRESS: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
    OrderStatus.COMPLETED: [],  # Only employer can confirm delivery
    OrderStatus.DELIVERED: [],  # Final state
    OrderStatus.CANCELLED: [],  # Final state
    OrderStatus.BIDDING: [OrderStatus.CANCELLED],
    OrderStatus.NOT_SELECTED: [],  # Final state
    # Legacy status transitions
    OrderStatus.ACCEPTED: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
    OrderStatus.PENDING: [OrderStatus.CANCELLED],
}


# =============================================================================
# Job Status Constants (use OrderState from state_machine.py)
# =============================================================================
# Note: Job statuses are defined in src/services/state_machine.py as OrderState
#   OPEN = "OPEN"        - 任务已发布，等待抢单
#   ACTIVE = "ACTIVE"    - 已派单，任务进行中
#   REVIEW = "REVIEW"    - 待评审，等待雇主确认
#   CLOSED = "CLOSED"    - 已关闭
#   CANCELLED = "CANCELLED"  - 已取消
#   REJECTED = "REJECTED"    - 已拒绝


# =============================================================================
# JobWorker Status Constants
# =============================================================================

class JobWorkerStatus:
    """Job-Worker 关联状态"""
    PENDING = "PENDING"      # 待派单
    CONFIRMED = "CONFIRMED"  # 已确认
    LOCKED = "LOCKED"        # 已锁单 (订金支付)
    WORKING = "WORKING"      # 工作中
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消


VALID_JOB_WORKER_STATUSES = [
    JobWorkerStatus.PENDING,
    JobWorkerStatus.CONFIRMED,
    JobWorkerStatus.LOCKED,
    JobWorkerStatus.WORKING,
    JobWorkerStatus.COMPLETED,
    JobWorkerStatus.CANCELLED,
]

JOB_WORKER_STATUS_LABELS = {
    JobWorkerStatus.PENDING: "待派单",
    JobWorkerStatus.CONFIRMED: "已确认",
    JobWorkerStatus.LOCKED: "已锁单",
    JobWorkerStatus.WORKING: "工作中",
    JobWorkerStatus.COMPLETED: "已完成",
    JobWorkerStatus.CANCELLED: "已取消",
}


# =============================================================================
# Payment Status Constants
# =============================================================================

class PaymentStatus:
    """支付状态"""
    PENDING = "PENDING"      # 待支付
    PAID = "PAID"            # 已支付
    REFUNDED = "REFUNDED"    # 已退款
    FAILED = "FAILED"        # 支付失败


VALID_PAYMENT_STATUSES = [
    PaymentStatus.PENDING,
    PaymentStatus.PAID,
    PaymentStatus.REFUNDED,
    PaymentStatus.FAILED,
]

PAYMENT_STATUS_LABELS = {
    PaymentStatus.PENDING: "待支付",
    PaymentStatus.PAID: "已支付",
    PaymentStatus.REFUNDED: "已退款",
    PaymentStatus.FAILED: "支付失败",
}