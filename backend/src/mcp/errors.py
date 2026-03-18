"""MCP Server Error Handling Module.

Provides structured, semantically meaningful error responses for AI agents.
All errors include:
- error_code: Machine-readable code for programmatic handling
- message: Human-readable message (Chinese)
- message_en: English message for reference
- suggestion: Actionable suggestion for the agent
"""

from typing import Optional, Dict, Any


# =============================================================================
# Base Error Classes
# =============================================================================

class MCPError(Exception):
    """Base error class for MCP Server."""

    error_code: str = "UNKNOWN_ERROR"
    message: str = "Unknown error occurred"
    message_en: str = "Unknown error occurred"
    suggestion: str = "Please check the request and try again"

    def __init__(self, message: Optional[str] = None,
                 suggestion: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        if message:
            self.message = message
        if suggestion:
            self.suggestion = suggestion
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "message_en": self.message_en,
            "suggestion": self.suggestion,
            "details": self.details,
        }


class AuthenticationError(MCPError):
    """Authentication failed."""
    error_code = "AUTHENTICATION_FAILED"
    message_en = "Authentication failed. Please check your API key."
    suggestion = "请检查 Authorization Header 中的 API Key 是否正确，或联系管理员重新生成密钥"


class PermissionDeniedError(MCPError):
    """Permission denied."""
    error_code = "PERMISSION_DENIED"
    message_en = "You do not have permission to perform this action."
    suggestion = "请确认您是否有执行此操作的权限，或联系任务所有者"

    def __init__(self, action: Optional[str] = None,
                 resource_type: Optional[str] = None,
                 resource_id: Optional[str] = None,
                 agent_id: Optional[str] = None,
                 message: Optional[str] = None,
                 suggestion: Optional[str] = None):
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.agent_id = agent_id

        if message:
            self.message = message
        elif action and resource_type:
            self.message = f"您无权{action}此{resource_type}"

        super().__init__(message=self.message, suggestion=suggestion)


class NotFoundError(MCPError):
    """Resource not found."""
    error_code = "RESOURCE_NOT_FOUND"
    message_en = "The requested resource was not found."
    suggestion = "请检查资源 ID 是否正确，或确认资源是否已被删除"

    def __init__(self, resource_type: str, resource_id: str,
                 message: Optional[str] = None,
                 suggestion: Optional[str] = None):
        self.resource_type = resource_type
        self.resource_id = resource_id

        if message:
            self.message = message
        else:
            self.message = f"{resource_type}「{resource_id}」不存在"

        super().__init__(message=self.message, suggestion=suggestion)


class AgentNotFoundError(NotFoundError):
    """Agent not found."""
    error_code = "AGENT_NOT_FOUND"

    def __init__(self, agent_id: str, message: Optional[str] = None):
        super().__init__(
            resource_type="Agent",
            resource_id=agent_id,
            message=message or f"Agent「{agent_id}」不存在",
            suggestion="请检查 Agent ID 是否正确，或确认 Agent 是否已被删除"
        )


class ValidationError(MCPError):
    """Validation failed."""
    error_code = "VALIDATION_ERROR"
    message_en = "Request validation failed."
    suggestion = "请检查请求参数是否符合要求"


# =============================================================================
# Job-related Errors
# =============================================================================

class JobNotFoundError(NotFoundError):
    """Job not found."""
    error_code = "JOB_NOT_FOUND"

    def __init__(self, job_id: str, message: Optional[str] = None):
        super().__init__(
            resource_type="任务",
            resource_id=job_id,
            message=message or f"任务「{job_id}」不存在",
            suggestion="请检查任务 ID 是否正确，或确认任务是否已被删除"
        )


class JobCreateError(ValidationError):
    """Failed to create job."""
    error_code = "JOB_CREATE_FAILED"
    message_en = "Failed to create job."
    suggestion = "请检查任务信息是否完整，或联系管理员"


class JobSingleTaskConstraintError(ValidationError):
    """Single-task constraint violation for employer."""
    error_code = "SINGLE_TASK_CONSTRAINT"
    message_en = "Employer already has an active job."
    suggestion = "请等待当前任务完成（CLOSED/REJECTED 状态）后再发布新任务"

    def __init__(self, active_job_title: str, active_job_status: str,
                 message: Optional[str] = None,
                 suggestion: Optional[str] = None):
        self.active_job_title = active_job_title
        self.active_job_status = active_job_status

        if message:
            self.message = message
        else:
            self.message = f"您已有一个进行中的任务「{active_job_title}」(状态：{active_job_status})"

        super().__init__(message=self.message, suggestion=suggestion or self.suggestion)


class JobStatusTransitionError(ValidationError):
    """Invalid job status transition."""
    error_code = "INVALID_STATUS_TRANSITION"
    message_en = "Invalid job status transition."
    suggestion = "请检查任务当前状态是否允许此操作"

    def __init__(self, current_status: str, target_status: str,
                 message: Optional[str] = None):
        self.current_status = current_status
        self.target_status = target_status

        if message:
            self.message = message
        else:
            self.message = f"无法将任务从 {current_status} 变更为 {target_status}"

        super().__init__(message=self.message)


class JobDeleteError(ValidationError):
    """Failed to delete job."""
    error_code = "JOB_DELETE_FAILED"
    message_en = "Failed to delete job."
    suggestion = "请检查任务状态是否允许删除（仅 OPEN/CLOSED/REJECTED 状态可删除）"

    def __init__(self, job_id: str, current_status: str,
                 message: Optional[str] = None):
        self.job_id = job_id
        self.current_status = current_status

        if message:
            self.message = message
        else:
            self.message = f"无法删除任务「{job_id}」：当前状态为 {current_status}"

        super().__init__(message=self.message)


# =============================================================================
# Bid-related Errors
# =============================================================================

class BidNotFoundError(NotFoundError):
    """Bid not found."""
    error_code = "BID_NOT_FOUND"

    def __init__(self, bid_id: str, message: Optional[str] = None):
        super().__init__(
            resource_type="竞标",
            resource_id=bid_id,
            message=message or f"竞标「{bid_id}」不存在",
            suggestion="请检查竞标 ID 是否正确"
        )


class BidCreateError(ValidationError):
    """Failed to create bid."""
    error_code = "BID_CREATE_FAILED"
    message_en = "Failed to create bid."
    suggestion = "请检查竞标信息是否完整"


class BidSingleTaskConstraintError(ValidationError):
    """Single-task constraint violation for worker."""
    error_code = "SINGLE_TASK_CONSTRAINT"
    message_en = "Worker already has an active bid."
    suggestion = "请等待当前竞标结束后再竞标新任务"

    def __init__(self, active_job_title: str, active_bid_status: str,
                 message: Optional[str] = None,
                 suggestion: Optional[str] = None):
        self.active_job_title = active_job_title
        self.active_bid_status = active_bid_status

        if message:
            self.message = message
        else:
            status_label = "等待雇主选择" if active_bid_status in ("BIDDING", "PENDING") else "已中标，正在执行"
            self.message = f"您已有一个进行中的竞标「{active_job_title}」(状态：{status_label})"

        super().__init__(message=self.message, suggestion=suggestion or self.suggestion)


class BidLimitReachedError(ValidationError):
    """Bid limit reached for a job."""
    error_code = "BID_LIMIT_REACHED"
    message_en = "Bid limit reached for this job."
    suggestion = "该任务已满员，请等待其他竞标被拒绝或选择其他任务"

    def __init__(self, job_id: str, bid_limit: int,
                 message: Optional[str] = None):
        self.job_id = job_id
        self.bid_limit = bid_limit

        if message:
            self.message = message
        else:
            self.message = f"任务「{job_id}」已达最大竞标数 ({bid_limit})"

        super().__init__(message=self.message)


class BidAlreadyProcessedError(ValidationError):
    """Bid already processed (accepted/rejected)."""
    error_code = "BID_ALREADY_PROCESSED"
    message_en = "This bid has already been processed."
    suggestion = "该竞标已被处理，无法重复操作"

    def __init__(self, bid_id: str, current_status: str,
                 message: Optional[str] = None):
        self.bid_id = bid_id
        self.current_status = current_status

        if message:
            self.message = message
        else:
            self.message = f"竞标「{bid_id}」已被处理，当前状态：{current_status}"

        super().__init__(message=self.message)


class BidNotInBiddingStatusError(ValidationError):
    """Bid not in BIDDING status, cannot be modified."""
    error_code = "BID_NOT_IN_BIDDING_STATUS"
    message_en = "Bid is not in BIDDING status."
    suggestion = "只有 BIDDING 状态的竞标可以被修改或取消"

    def __init__(self, bid_id: str, current_status: str,
                 message: Optional[str] = None):
        self.bid_id = bid_id
        self.current_status = current_status

        if message:
            self.message = message
        else:
            self.message = f"竞标「{bid_id}」当前状态为 {current_status}，无法执行此操作"

        super().__init__(message=self.message)


# =============================================================================
# Message-related Errors
# =============================================================================

class MessageError(MCPError):
    """Message operation failed."""
    error_code = "MESSAGE_ERROR"
    message_en = "Message operation failed."


class MessageParticipantError(ValidationError):
    """Not a participant in the job, cannot send messages."""
    error_code = "NOT_JOB_PARTICIPANT"
    message_en = "You must be a participant in the job to send messages."
    suggestion = "只有任务参与者（雇主或竞标者）才能发送消息"

    def __init__(self, job_id: str, agent_id: str,
                 message: Optional[str] = None):
        self.job_id = job_id
        self.agent_id = agent_id

        if message:
            self.message = message
        else:
            self.message = f"您不是任务「{job_id}」的参与者，无法发送消息"

        super().__init__(message=self.message)


# =============================================================================
# Artifact-related Errors
# =============================================================================

class ArtifactError(MCPError):
    """Artifact operation failed."""
    error_code = "ARTIFACT_ERROR"
    message_en = "Artifact operation failed."


class ArtifactSubmissionError(ValidationError):
    """Cannot submit artifact."""
    error_code = "ARTIFACT_SUBMISSION_FAILED"
    message_en = "Cannot submit artifact for this job."
    suggestion = "请确认您是被选中的工作者，且任务状态为 ACTIVE 或 REVIEW"

    def __init__(self, job_id: str, reason: str,
                 message: Optional[str] = None):
        self.job_id = job_id
        self.reason = reason

        if message:
            self.message = message
        else:
            self.message = f"无法为任务「{job_id}」提交作品：{reason}"

        super().__init__(message=self.message)


# =============================================================================
# Error Handler Decorator
# =============================================================================

from functools import wraps


def handle_mcp_errors(func):
    """Decorator to handle MCP errors and convert to proper error responses.

    This decorator catches known error types and re-raises them as MCPError
    with proper formatting. Unknown exceptions are wrapped in MCPError.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MCPError:
            # Re-raise known MCP errors
            raise
        except ValueError as e:
            # Convert ValueError to ValidationError
            raise ValidationError(
                message=str(e),
                suggestion="请检查输入参数是否正确"
            )
        except Exception as e:
            # Wrap unknown exceptions
            raise MCPError(
                message=f"系统错误：{str(e)}",
                suggestion="请稍后重试或联系管理员"
            )

    return wrapper
