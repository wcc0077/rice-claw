# Backend services

from .state_machine import (
    OrderStateMachine,
    OrderState,
    StateTransitionError,
    create_order_state_machine,
    transition_order,
)
from .message_service import (
    MessageService,
    create_message_service,
)
from .pubsub_subscriber import (
    RedisPubSubSubscriber,
    create_pubsub_subscriber,
    init_pubsub_subscriber,
    shutdown_pubsub_subscriber,
)
from .job_service import (
    JobService,           # 同步版本 - 供 HTTP API 和 MCP 使用
    AsyncJobService,      # 异步版本 - 供 WebSocket 使用
    create_job_service,   # 创建异步版本
    create_sync_job_service,  # 创建同步版本
)
from .payment_service import (
    PaymentService,
    create_payment_service,
)
from .dispatch_service import (
    DispatchService,
    create_dispatch_service,
)
from .bid_service import (
    BidService,
    BidValidationError,
)
from .job_service import (
    JobValidationError,
)

__all__ = [
    "OrderStateMachine",
    "OrderState",
    "StateTransitionError",
    "create_order_state_machine",
    "transition_order",
    "MessageService",
    "create_message_service",
    "RedisPubSubSubscriber",
    "create_pubsub_subscriber",
    "init_pubsub_subscriber",
    "shutdown_pubsub_subscriber",
    "JobService",           # 同步版本
    "AsyncJobService",      # 异步版本
    "create_job_service",   # 创建异步版本
    "create_sync_job_service",  # 创建同步版本
    "PaymentService",
    "create_payment_service",
    "DispatchService",
    "create_dispatch_service",
    "BidService",
    "BidValidationError",
    "JobValidationError",
]