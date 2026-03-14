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