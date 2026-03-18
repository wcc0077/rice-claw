"""MCP Server Module for Shrimp Market.

This module provides MCP tools with structured error handling for AI agents.
"""

from .errors import (
    # Base errors
    MCPError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ValidationError,
    # Agent errors
    AgentNotFoundError,
    # Job errors
    JobNotFoundError,
    JobCreateError,
    JobSingleTaskConstraintError,
    JobStatusTransitionError,
    JobDeleteError,
    # Bid errors
    BidNotFoundError,
    BidCreateError,
    BidSingleTaskConstraintError,
    BidLimitReachedError,
    BidAlreadyProcessedError,
    BidNotInBiddingStatusError,
    # Message errors
    MessageError,
    MessageParticipantError,
    # Artifact errors
    ArtifactError,
    ArtifactSubmissionError,
    # Utils
    handle_mcp_errors,
)

from .responses import (
    format_error_response,
    format_success_response,
    format_tool_response,
)

__all__ = [
    # Error classes
    "MCPError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ValidationError",
    "AgentNotFoundError",
    "JobNotFoundError",
    "JobCreateError",
    "JobSingleTaskConstraintError",
    "JobStatusTransitionError",
    "JobDeleteError",
    "BidNotFoundError",
    "BidCreateError",
    "BidSingleTaskConstraintError",
    "BidLimitReachedError",
    "BidAlreadyProcessedError",
    "BidNotInBiddingStatusError",
    "MessageError",
    "MessageParticipantError",
    "ArtifactError",
    "ArtifactSubmissionError",
    # Utils
    "handle_mcp_errors",
    # Response formatters
    "format_error_response",
    "format_success_response",
    "format_tool_response",
]
