"""Audit logging middleware for tracking API and MCP requests."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..db.database import SessionLocal
from ..models.db_models import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit purposes."""

    # Paths to exclude from audit logging
    EXCLUDED_PATHS = {
        "/health",
        "/",
        "/favicon.ico",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    # Sensitive fields to mask in request data
    SENSITIVE_FIELDS = {"api_key", "password", "token", "secret"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log audit information."""

        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Skip static files
        if request.url.path.startswith("/static"):
            return await call_next(request)

        # Capture request info
        request_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)

        # Extract request data
        request_data = await self._extract_request_data(request)
        agent_id = request_data.get("api_key") or request_data.get("agent_id")

        # Store request info in state for access in route handlers
        request.state.request_id = request_id
        request.state.agent_id = agent_id

        # Process request
        error_message = None
        response_status = 500

        try:
            response = await call_next(request)
            response_status = response.status_code
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            # Log the request
            await self._log_request(
                request_id=request_id,
                request=request,
                request_data=request_data,
                response_status=response_status,
                error_message=error_message,
                agent_id=agent_id,
            )

        return response

    async def _extract_request_data(self, request: Request) -> dict:
        """Extract and mask sensitive data from request."""
        data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
        }

        # Try to extract body for POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body)
                        data["body"] = self._mask_sensitive_fields(body_json)
                    except json.JSONDecodeError:
                        data["body"] = "[non-JSON body]"
            except Exception:
                pass

        return data

    def _mask_sensitive_fields(self, data: dict) -> dict:
        """Recursively mask sensitive fields in a dictionary."""
        if not isinstance(data, dict):
            return data

        result = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_FIELDS:
                result[key] = "***MASKED***"
            elif isinstance(value, dict):
                result[key] = self._mask_sensitive_fields(value)
            else:
                result[key] = value

        return result

    async def _log_request(
        self,
        request_id: str,
        request: Request,
        request_data: dict,
        response_status: int,
        error_message: Optional[str],
        agent_id: Optional[str],
    ) -> None:
        """Save audit log to database."""
        db = SessionLocal()
        try:
            # Determine action type
            action = self._determine_action(request.url.path, request.method)

            # Determine resource type
            resource_type = self._determine_resource_type(request.url.path)

            # Extract resource ID from path
            resource_id = self._extract_resource_id(request.url.path)

            log_entry = AuditLog(
                log_id=f"audit_{request_id[:16]}",
                agent_id=agent_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", "")[:256],
                request_data=json.dumps(request_data),
                response_status=response_status,
                error_message=error_message,
            )

            db.add(log_entry)
            db.commit()
        except Exception as e:
            # Don't fail the request if logging fails
            print(f"Audit log error: {e}")
        finally:
            db.close()

    def _determine_action(self, path: str, method: str) -> str:
        """Determine the action type from path and method."""
        if "/mcp" in path:
            return "mcp_tool_call"
        return f"api_{method.lower()}"

    def _determine_resource_type(self, path: str) -> str:
        """Determine resource type from path."""
        if "/agents" in path:
            return "agent"
        elif "/jobs" in path:
            return "job"
        elif "/bids" in path:
            return "bid"
        elif "/messages" in path:
            return "message"
        elif "/artifacts" in path:
            return "artifact"
        elif "/orders" in path:
            return "order"
        return "unknown"

    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from path segments."""
        parts = path.strip("/").split("/")
        if len(parts) >= 3:
            # e.g., /api/v1/jobs/job_123 -> job_123
            return parts[2]
        return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, handling proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"


def log_mcp_tool_call(
    agent_id: str,
    tool_name: str,
    arguments: dict,
    response_status: int = 200,
    error_message: Optional[str] = None,
) -> None:
    """Log an MCP tool call for audit purposes.

    Args:
        agent_id: The authenticated agent's ID
        tool_name: Name of the MCP tool called
        arguments: Tool arguments (will be masked for sensitive fields)
        response_status: HTTP-style status code
        error_message: Error message if call failed
    """
    db = SessionLocal()
    try:
        # Mask sensitive fields
        masked_args = _mask_sensitive_fields(arguments)

        log_entry = AuditLog(
            log_id=f"mcp_{uuid.uuid4().hex[:16]}",
            agent_id=agent_id,
            action=f"mcp_tool_{tool_name}",
            resource_type=_infer_resource_type(tool_name),
            resource_id=arguments.get("job_id") or arguments.get("bid_id"),
            ip_address=None,  # MCP calls don't have direct IP
            user_agent="MCP Client",
            request_data=json.dumps(masked_args),
            response_status=response_status,
            error_message=error_message,
        )

        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"MCP audit log error: {e}")
    finally:
        db.close()


def _mask_sensitive_fields(data: dict) -> dict:
    """Mask sensitive fields in a dictionary."""
    sensitive = {"api_key", "password", "token", "secret"}

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if key.lower() in sensitive:
            result[key] = "***MASKED***"
        elif isinstance(value, dict):
            result[key] = _mask_sensitive_fields(value)
        else:
            result[key] = value

    return result


def _infer_resource_type(tool_name: str) -> str:
    """Infer resource type from tool name."""
    if "job" in tool_name:
        return "job"
    elif "bid" in tool_name:
        return "bid"
    elif "message" in tool_name or "msg" in tool_name:
        return "message"
    elif "artifact" in tool_name or "demo" in tool_name or "work" in tool_name:
        return "artifact"
    elif "capability" in tool_name or "agent" in tool_name:
        return "agent"
    return "unknown"