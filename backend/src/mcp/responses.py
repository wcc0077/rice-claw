"""MCP Server Error Responses.

Provides standardized error response formatting for MCP tool calls.
"""

from typing import Any, Dict, Optional
from .errors import MCPError


def format_error_response(error: Exception) -> Dict[str, Any]:
    """Format an exception as a structured MCP error response.

    Args:
        error: The exception to format

    Returns:
        Dictionary with error information suitable for MCP response
    """
    if isinstance(error, MCPError):
        return error.to_dict()
    elif isinstance(error, ValueError):
        return {
            "error_code": "VALIDATION_ERROR",
            "message": str(error),
            "message_en": f"Validation error: {str(error)}",
            "suggestion": "请检查输入参数是否正确",
        }
    elif isinstance(error, PermissionError):
        return {
            "error_code": "PERMISSION_DENIED",
            "message": str(error),
            "message_en": f"Permission denied: {str(error)}",
            "suggestion": "您没有执行此操作的权限",
        }
    else:
        return {
            "error_code": "INTERNAL_ERROR",
            "message": f"系统内部错误：{str(error)}",
            "message_en": f"Internal error: {str(error)}",
            "suggestion": "请稍后重试或联系管理员",
        }


def format_success_response(data: Any) -> Dict[str, Any]:
    """Format a successful response.

    Args:
        data: The response data

    Returns:
        Dictionary with success status and data
    """
    return {
        "success": True,
        "data": data,
    }


def format_tool_response(result: Any, error: Optional[Exception] = None) -> Dict[str, Any]:
    """Format a complete MCP tool response.

    Args:
        result: The tool execution result
        error: Optional error if execution failed

    Returns:
        Formatted response dictionary
    """
    if error:
        return {
            "success": False,
            "error": format_error_response(error),
        }
    return {
        "success": True,
        "result": result,
    }
