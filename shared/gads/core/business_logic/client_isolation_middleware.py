"""
Client Isolation Middleware for Secure Multi-Tenant Operations

This middleware provides comprehensive client isolation and security for Google Ads
operations. It ensures that all client interactions are properly isolated, validated,
and auditable within secure boundaries.

Key Features:
- Request/response isolation
- Client context injection
- Security validation
- Audit trail logging
- Rate limiting per client
- Error isolation
"""

import asyncio
import logging
import time
import threading
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Dict, List, Optional, Any, Callable, TypeVar, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import json
from pathlib import Path

from client_context_manager import ClientContext, get_current_client_context
from client_auth_router import get_auth_router
from google_ads_client_business_rules import validate_client_operation, ValidationResult
from client_config_schema import ClientStatus

logger = logging.getLogger(__name__)

# Type variables for generic middleware
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Middleware context
middleware_stack: ContextVar[List[str]] = ContextVar('middleware_stack', default=[])


@dataclass
class MiddlewareRequest:
    """Represents a request through the middleware"""
    client_id: str
    operation: str
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.request_id:
            import secrets
            self.request_id = f"{self.client_id}_{self.operation}_{secrets.token_hex(4)}"


@dataclass
class MiddlewareResponse:
    """Represents a response from the middleware"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: Optional[int] = None
    validation_results: List[ValidationResult] = field(default_factory=list)


@dataclass
class ClientIsolationConfig:
    """Configuration for client isolation middleware"""
    enable_audit_trail: bool = True
    enable_rate_limiting: bool = True
    enable_validation: bool = True
    max_concurrent_operations: int = 10
    operation_timeout_seconds: int = 300
    rate_limit_requests_per_minute: int = 60
    enable_error_isolation: bool = True
    log_sensitive_data: bool = False  # Never log credentials or PII


class ClientIsolationMiddleware:
    """
    Middleware for secure client isolation in multi-tenant operations

    This middleware provides:
    - Client context management
    - Operation validation and authorization
    - Audit trail logging
    - Rate limiting
    - Error isolation and recovery
    - Performance monitoring
    """

    def __init__(self, config: ClientIsolationConfig = None):
        self.config = config or ClientIsolationConfig()
        self.auth_router = get_auth_router()

        # Rate limiting storage (client_id -> request timestamps)
        self.rate_limit_store: Dict[str, List[datetime]] = {}
        self.rate_limit_lock = threading.RLock()

        # Concurrent operation tracking
        self.active_operations: Dict[str, int] = {}
        self.operation_semaphores: Dict[str, asyncio.Semaphore] = {}

        # Audit trail storage
        self.audit_trail: List[Dict[str, Any]] = []
        self.max_audit_entries = 10000

        logger.info("Initialized ClientIsolationMiddleware")

    @asynccontextmanager
    async def client_operation_context(self, request: MiddlewareRequest):
        """
        Context manager for client operations with full isolation

        Usage:
            async with middleware.client_operation_context(request) as response:
                # Perform operation
                response.data = await some_operation()
        """
        start_time = time.time()
        client_context = None
        operation_id = None

        try:
            # Validate and setup client context
            client_context = await self._setup_client_context(request.client_id)
            if not client_context:
                yield MiddlewareResponse(
                    success=False,
                    error=f"Client context not available for {request.client_id}"
                )
                return

            # Rate limiting check
            if not await self._check_rate_limit(request.client_id):
                yield MiddlewareResponse(
                    success=False,
                    error="Rate limit exceeded"
                )
                return

            # Validate operation
            if self.config.enable_validation:
                validation_errors = await self._validate_operation(client_context, request)
                if validation_errors:
                    yield MiddlewareResponse(
                        success=False,
                        error="Operation validation failed",
                        validation_results=validation_errors
                    )
                    return

            # Start operation tracking
            operation_id = client_context.start_operation(request.operation, request.metadata)

            # Add to middleware stack
            current_stack = middleware_stack.get()
            current_stack.append(request.request_id)
            middleware_stack.set(current_stack)

            # Create response object for the context
            response = MiddlewareResponse(success=True)

            try:
                yield response
            finally:
                # Calculate processing time
                end_time = time.time()
                processing_time = int((end_time - start_time) * 1000)
                response.processing_time_ms = processing_time

                # End operation tracking
                if operation_id:
                    client_context.end_operation(operation_id, response.success,
                                               response.error)

                # Remove from middleware stack
                current_stack = middleware_stack.get()
                if request.request_id in current_stack:
                    current_stack.remove(request.request_id)
                    middleware_stack.set(current_stack)

                # Audit logging
                if self.config.enable_audit_trail:
                    await self._log_audit_entry(request, response)

        except Exception as e:
            logger.error(f"Middleware error for client {request.client_id}: {e}")

            # Ensure proper cleanup on error
            if operation_id and client_context:
                client_context.end_operation(operation_id, success=False, str(e))

            yield MiddlewareResponse(
                success=False,
                error=f"Middleware error: {str(e)}"
            )

    async def _setup_client_context(self, client_id: str) -> Optional[ClientContext]:
        """Setup and validate client context"""
        from client_context_manager import get_context_manager
        context_manager = get_context_manager()

        # Get or load client context
        context = context_manager.get_client_context(client_id)
        if not context:
            context = context_manager.load_or_create_context(client_id)

        if not context:
            logger.error(f"Failed to setup context for client {client_id}")
            return None

        # Validate client status
        if context.config.status != ClientStatus.ACTIVE:
            logger.warning(f"Operation attempted for inactive client {client_id} (status: {context.config.status.value})")
            return None

        return context

    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limits"""
        if not self.config.enable_rate_limiting:
            return True

        with self.rate_limit_lock:
            now = datetime.now()
            cutoff_time = now - timedelta(minutes=1)

            # Get or create client request history
            if client_id not in self.rate_limit_store:
                self.rate_limit_store[client_id] = []

            client_requests = self.rate_limit_store[client_id]

            # Remove old requests
            client_requests[:] = [req_time for req_time in client_requests if req_time > cutoff_time]

            # Check rate limit
            if len(client_requests) >= self.config.rate_limit_requests_per_minute:
                logger.warning(f"Rate limit exceeded for client {client_id}")
                return False

            # Add current request
            client_requests.append(now)
            return True

    async def _validate_operation(self, client_context: ClientContext,
                                request: MiddlewareRequest) -> List[ValidationResult]:
        """Validate operation against client rules and permissions"""
        errors = []

        # Check operation permissions
        if not client_context.validate_access(request.operation):
            errors.append(ValidationResult(
                is_valid=False,
                severity="error",
                message=f"Operation '{request.operation}' not permitted for client",
                rule_name="operation_permission"
            ))
            return errors

        # Validate business rules
        is_valid, validation_results = validate_client_operation(
            client_context.config,
            request.operation,
            request.parameters
        )

        # Filter to only errors
        error_results = [r for r in validation_results if not r.is_valid and r.severity.name in ["ERROR", "CRITICAL"]]
        errors.extend(error_results)

        return errors

    async def _log_audit_entry(self, request: MiddlewareRequest, response: MiddlewareResponse):
        """Log operation to audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request.request_id,
            "client_id": request.client_id,
            "operation": request.operation,
            "parameters": self._sanitize_parameters(request.parameters),
            "success": response.success,
            "error": response.error,
            "processing_time_ms": response.processing_time_ms,
            "validation_warnings": len([r for r in response.validation_results if r.severity.name == "WARNING"]),
            "validation_errors": len([r for r in response.validation_results if not r.is_valid]),
            "thread_id": threading.get_ident(),
            "middleware_stack_depth": len(middleware_stack.get())
        }

        self.audit_trail.append(audit_entry)

        # Maintain audit trail size limit
        if len(self.audit_trail) > self.max_audit_entries:
            self.audit_trail.pop(0)

        logger.debug(f"Audit logged: {request.request_id} - {request.operation}")

    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from parameters for logging"""
        if not self.config.log_sensitive_data:
            # List of parameter keys that contain sensitive data
            sensitive_keys = [
                'password', 'token', 'key', 'secret', 'credential',
                'api_key', 'auth_token', 'refresh_token', 'access_token'
            ]

            sanitized = {}
            for key, value in parameters.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "***REDACTED***"
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_parameters(value)
                elif isinstance(value, list):
                    sanitized[key] = [self._sanitize_parameters({"item": item})["item"] if isinstance(item, dict) else item for item in value]
                else:
                    sanitized[key] = value
            return sanitized

        return parameters

    def get_audit_trail(self, client_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail entries, optionally filtered by client"""
        if client_id:
            filtered_trail = [entry for entry in self.audit_trail if entry["client_id"] == client_id]
        else:
            filtered_trail = self.audit_trail

        return filtered_trail[-limit:] if limit > 0 else filtered_trail

    def get_client_metrics(self, client_id: str) -> Dict[str, Any]:
        """Get middleware metrics for a specific client"""
        client_audit_entries = [entry for entry in self.audit_trail if entry["client_id"] == client_id]

        if not client_audit_entries:
            return {"error": "No audit data found for client"}

        total_operations = len(client_audit_entries)
        successful_operations = len([e for e in client_audit_entries if e["success"]])
        failed_operations = total_operations - successful_operations

        avg_processing_time = sum(e["processing_time_ms"] for e in client_audit_entries if e["processing_time_ms"]) / total_operations

        operation_counts = {}
        for entry in client_audit_entries:
            op = entry["operation"]
            operation_counts[op] = operation_counts.get(op, 0) + 1

        # Rate limiting info
        rate_limit_violations = len([e for e in client_audit_entries if e.get("error") == "Rate limit exceeded"])

        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
            "average_processing_time_ms": avg_processing_time,
            "operation_counts": operation_counts,
            "rate_limit_violations": rate_limit_violations,
            "audit_entries_count": len(client_audit_entries)
        }

    async def execute_client_operation(self, client_id: str, operation: str,
                                     operation_func: Callable[..., Awaitable[T]],
                                     *args, **kwargs) -> MiddlewareResponse:
        """
        Execute a client operation with full middleware protection

        Args:
            client_id: Client identifier
            operation: Operation name/type
            operation_func: Async function to execute
            *args, **kwargs: Arguments for the operation function

        Returns:
            MiddlewareResponse with operation result
        """
        request = MiddlewareRequest(
            client_id=client_id,
            operation=operation,
            parameters={"args": args, "kwargs": kwargs}
        )

        async with self.client_operation_context(request) as response:
            if not response.success:
                return response

            try:
                # Execute the operation
                result = await operation_func(*args, **kwargs)
                response.data = result
                response.success = True

            except Exception as e:
                logger.error(f"Operation execution failed for client {client_id}: {e}")
                response.success = False
                response.error = str(e)

        return response


def client_operation(operation_name: str) -> Callable[[F], F]:
    """
    Decorator for client operations that automatically applies middleware

    Usage:
        @client_operation("get_campaign_performance")
        async def get_campaign_performance(client_id: str, campaign_id: str) -> Dict:
            # Operation implementation
            return {"performance": "data"}
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(client_id: str, *args, **kwargs):
            # Get middleware instance (could be from dependency injection)
            middleware = get_middleware_instance()

            # Extract operation parameters
            operation_params = {
                "client_id": client_id,
                "operation": operation_name,
                "func_name": func.__name__,
                "args": args,
                "kwargs": kwargs
            }

            # Execute with middleware
            response = await middleware.execute_client_operation(
                client_id,
                operation_name,
                func,
                client_id,
                *args,
                **kwargs
            )

            # Handle response
            if not response.success:
                raise Exception(f"Operation failed: {response.error}")

            return response.data

        return wrapper
    return decorator


# Global middleware instance
_middleware_instance: Optional[ClientIsolationMiddleware] = None

def get_middleware_instance() -> ClientIsolationMiddleware:
    """Get global middleware instance"""
    global _middleware_instance
    if _middleware_instance is None:
        _middleware_instance = ClientIsolationMiddleware()
    return _middleware_instance

def set_middleware_config(config: ClientIsolationConfig):
    """Configure the global middleware instance"""
    global _middleware_instance
    _middleware_instance = ClientIsolationMiddleware(config)


# Export for easy importing
__all__ = [
    'ClientIsolationMiddleware',
    'ClientIsolationConfig',
    'MiddlewareRequest',
    'MiddlewareResponse',
    'client_operation',
    'get_middleware_instance',
    'set_middleware_config'
]
