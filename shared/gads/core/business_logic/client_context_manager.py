"""
Client Context Manager for Isolated Multi-Tenant Operations

This module provides secure client isolation and context management for Google Ads
operations. It ensures that client data remains isolated and operations are
executed within proper security boundaries.

Key Features:
- Client context isolation
- Secure credential management
- Data access control
- Audit trail logging
- Performance monitoring per client
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import threading
from pathlib import Path

from client_config_schema import (
    ClientSpecificConfig,
    ClientStatus,
    validate_client_config
)

# Context variables for client isolation
current_client_context: ContextVar[Optional['ClientContext']] = ContextVar('current_client_context', default=None)
client_operation_stack: ContextVar[List[str]] = ContextVar('client_operation_stack', default=[])

T = TypeVar('T')
logger = logging.getLogger(__name__)


@dataclass
class ClientOperation:
    """Represents a client-specific operation with audit trail"""
    operation_id: str
    client_id: str
    operation_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, cancelled
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None

    def complete(self, success: bool = True, error: Optional[str] = None):
        """Mark operation as completed"""
        self.end_time = datetime.now()
        self.status = "completed" if success else "failed"
        self.error_message = error
        if self.start_time and self.end_time:
            self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        self.thread_id = threading.get_ident()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "operation_id": self.operation_id,
            "client_id": self.client_id,
            "operation_type": self.operation_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "thread_id": self.thread_id,
            "process_id": self.process_id
        }


@dataclass
class ClientMetrics:
    """Performance metrics for client operations"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time_ms: float = 0.0
    last_operation_time: Optional[datetime] = None
    error_rate: float = 0.0
    operation_counts: Dict[str, int] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)

    def update_metrics(self, operation: ClientOperation):
        """Update metrics based on completed operation"""
        self.total_operations += 1
        self.last_operation_time = operation.end_time or datetime.now()

        if operation.status == "completed":
            self.successful_operations += 1
        elif operation.status == "failed":
            self.failed_operations += 1

        # Update operation type counts
        op_type = operation.operation_type
        self.operation_counts[op_type] = self.operation_counts.get(op_type, 0) + 1

        # Update error rate
        if self.total_operations > 0:
            self.error_rate = self.failed_operations / self.total_operations

        # Update average response time
        if operation.duration_ms is not None:
            total_time = self.average_response_time_ms * (self.total_operations - 1)
            self.average_response_time_ms = (total_time + operation.duration_ms) / self.total_operations


class ClientContext:
    """
    Isolated client context for secure multi-tenant operations

    This class provides:
    - Client-specific configuration access
    - Secure credential management
    - Operation audit trails
    - Performance monitoring
    - Data isolation boundaries
    """

    def __init__(self, config: ClientSpecificConfig):
        self.config = config
        self.client_id = config.client_id
        self.client_name = config.client_name

        # Operation tracking
        self.current_operations: Dict[str, ClientOperation] = {}
        self.operation_history: List[ClientOperation] = []
        self.max_history_size = 1000

        # Performance metrics
        self.metrics = ClientMetrics()

        # Security context
        self.session_id = self._generate_session_id()
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()

        # Thread safety
        self._lock = threading.RLock()

        # Caching
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}

        logger.info(f"Initialized client context for {self.client_name} ({self.client_id})")

    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        import secrets
        return f"{self.client_id}_{secrets.token_hex(8)}_{int(time.time())}"

    def validate_access(self, operation: str, user_id: Optional[str] = None) -> bool:
        """
        Validate if operation is allowed for this client

        Args:
            operation: Operation type being requested
            user_id: User requesting the operation (optional)

        Returns:
            True if operation is allowed
        """
        # Check client status
        if self.config.status != ClientStatus.ACTIVE:
            logger.warning(f"Operation {operation} denied for inactive client {self.client_name}")
            return False

        # Check if operation is allowed for client's industry/service level
        allowed_operations = self._get_allowed_operations()
        if operation not in allowed_operations:
            logger.warning(f"Operation {operation} not allowed for client {self.client_name}")
            return False

        # Additional business rule validation could be added here
        return True

    def _get_allowed_operations(self) -> List[str]:
        """Get list of operations allowed for this client"""
        # Base operations available to all active clients
        base_operations = [
            "get_account_performance",
            "get_campaign_performance",
            "list_campaigns",
            "get_client_info",
            "generate_report"
        ]

        # Add industry-specific operations
        if self.config.industry.value == "healthcare":
            base_operations.extend([
                "validate_healthcare_compliance",
                "anonymize_health_data"
            ])
        elif self.config.industry.value == "finance":
            base_operations.extend([
                "validate_financial_compliance",
                "encrypt_sensitive_data"
            ])

        # Add service level operations
        if self.config.optimization.automation_enabled:
            base_operations.extend([
                "optimize_campaigns",
                "auto_adjust_bids",
                "reallocate_budget"
            ])

        return base_operations

    def start_operation(self, operation_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking a client operation

        Args:
            operation_type: Type of operation being performed
            metadata: Additional operation metadata

        Returns:
            Operation ID for tracking
        """
        with self._lock:
            operation_id = f"{self.client_id}_{operation_type}_{int(time.time() * 1000)}"

            operation = ClientOperation(
                operation_id=operation_id,
                client_id=self.client_id,
                operation_type=operation_type,
                start_time=datetime.now(),
                metadata=metadata or {},
                thread_id=threading.get_ident()
            )

            self.current_operations[operation_id] = operation
            self.last_accessed = datetime.now()

            # Add to operation stack for context tracking
            current_stack = client_operation_stack.get()
            current_stack.append(operation_id)
            client_operation_stack.set(current_stack)

            logger.debug(f"Started operation {operation_id} for client {self.client_name}")
            return operation_id

    def end_operation(self, operation_id: str, success: bool = True,
                     error: Optional[str] = None):
        """
        End tracking of a client operation

        Args:
            operation_id: Operation ID from start_operation
            success: Whether operation completed successfully
            error: Error message if operation failed
        """
        with self._lock:
            if operation_id in self.current_operations:
                operation = self.current_operations[operation_id]
                operation.complete(success, error)

                # Remove from current operations and add to history
                del self.current_operations[operation_id]
                self.operation_history.append(operation)

                # Update metrics
                self.metrics.update_metrics(operation)

                # Maintain history size limit
                if len(self.operation_history) > self.max_history_size:
                    self.operation_history.pop(0)

                # Remove from operation stack
                current_stack = client_operation_stack.get()
                if operation_id in current_stack:
                    current_stack.remove(operation_id)
                    client_operation_stack.set(current_stack)

                logger.debug(f"Ended operation {operation_id} for client {self.client_name}: {operation.status}")

    def get_secure_credentials(self, service: str) -> Optional[Dict[str, Any]]:
        """
        Get client-specific credentials for a service

        Args:
            service: Service name (google_ads, airtable, etc.)

        Returns:
            Credentials dictionary or None if not available
        """
        # This would integrate with a secure credential store
        # For now, return None to indicate external credential management
        logger.debug(f"Requesting credentials for service {service} for client {self.client_name}")
        return None

    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from client-specific cache"""
        with self._lock:
            if key in self._cache:
                if key in self._cache_ttl:
                    if datetime.now() > self._cache_ttl[key]:
                        # Cache expired
                        del self._cache[key]
                        del self._cache_ttl[key]
                        return None
                return self._cache[key]
            return None

    def cache_set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in client-specific cache with TTL"""
        with self._lock:
            self._cache[key] = value
            self._cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def cache_clear(self, pattern: Optional[str] = None):
        """Clear cache entries (optionally matching pattern)"""
        with self._lock:
            if pattern:
                keys_to_remove = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self._cache[key]
                    if key in self._cache_ttl:
                        del self._cache_ttl[key]
            else:
                self._cache.clear()
                self._cache_ttl.clear()

    def get_audit_trail(self, limit: int = 100) -> List[ClientOperation]:
        """Get recent operation audit trail"""
        with self._lock:
            return self.operation_history[-limit:] if limit > 0 else self.operation_history.copy()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        with self._lock:
            return {
                "total_operations": self.metrics.total_operations,
                "successful_operations": self.metrics.successful_operations,
                "failed_operations": self.metrics.failed_operations,
                "average_response_time_ms": self.metrics.average_response_time_ms,
                "error_rate": self.metrics.error_rate,
                "operation_counts": self.metrics.operation_counts.copy(),
                "last_operation_time": self.metrics.last_operation_time.isoformat() if self.metrics.last_operation_time else None,
                "active_operations": len(self.current_operations)
            }

    def is_operation_allowed(self, operation_type: str) -> bool:
        """Check if operation type is allowed for this client"""
        return operation_type in self._get_allowed_operations()

    def validate_business_rules(self, operation_data: Dict[str, Any]) -> List[str]:
        """
        Validate operation data against client's business rules

        Args:
            operation_data: Data for the operation to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Budget validation
        if 'budget' in operation_data:
            budget = operation_data['budget']
            campaign_type = operation_data.get('campaign_type', 'default')
            max_budget = self.config.business_rules.budget_limits.get(campaign_type)
            if max_budget and budget > max_budget:
                errors.append(f"Budget ${budget} exceeds maximum allowed ${max_budget} for {campaign_type}")

        # Bid validation
        if 'bid' in operation_data:
            bid = operation_data['bid']
            min_bid = self.config.business_rules.bid_limits.get('min_bid')
            max_bid = self.config.business_rules.bid_limits.get('max_bid')
            if min_bid and bid < min_bid:
                errors.append(f"Bid ${bid} below minimum allowed ${min_bid}")
            if max_bid and bid > max_bid:
                errors.append(f"Bid ${bid} above maximum allowed ${max_bid}")

        # Keyword restrictions
        if 'keywords' in operation_data:
            restricted_keywords = set(self.config.business_rules.keyword_restrictions)
            operation_keywords = set(operation_data['keywords'])
            forbidden_keywords = operation_keywords.intersection(restricted_keywords)
            if forbidden_keywords:
                errors.append(f"Keywords not allowed: {', '.join(forbidden_keywords)}")

        return errors


class ClientContextManager:
    """
    Manager for client contexts with secure isolation

    This class manages multiple client contexts and provides:
    - Context creation and lifecycle management
    - Secure context switching
    - Resource cleanup
    - Performance monitoring across clients
    """

    def __init__(self, config_storage_path: Optional[Path] = None):
        self.contexts: Dict[str, ClientContext] = {}
        self.config_storage_path = config_storage_path or Path("./client_configs")
        self.config_storage_path.mkdir(exist_ok=True)

        # Global metrics
        self.global_metrics = ClientMetrics()
        self._lock = threading.RLock()

        logger.info("Initialized ClientContextManager")

    def load_client_config(self, client_id: str) -> Optional[ClientSpecificConfig]:
        """Load client configuration from storage"""
        config_file = self.config_storage_path / f"{client_id}.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                config = ClientSpecificConfig.from_dict(data)

                # Validate configuration
                validation_errors = config.validate_configuration()
                if validation_errors:
                    logger.error(f"Invalid configuration for client {client_id}: {validation_errors}")
                    return None

                return config
            except Exception as e:
                logger.error(f"Failed to load config for client {client_id}: {e}")
                return None
        return None

    def save_client_config(self, config: ClientSpecificConfig) -> bool:
        """Save client configuration to storage"""
        config_file = self.config_storage_path / f"{config.client_id}.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config for client {config.client_id}: {e}")
            return False

    def create_client_context(self, config: ClientSpecificConfig) -> ClientContext:
        """Create a new client context"""
        with self._lock:
            if config.client_id in self.contexts:
                logger.warning(f"Context already exists for client {config.client_name}, replacing")

            context = ClientContext(config)
            self.contexts[config.client_id] = context

            # Save configuration
            self.save_client_config(config)

            logger.info(f"Created context for client {config.client_name} ({config.client_id})")
            return context

    def get_client_context(self, client_id: str) -> Optional[ClientContext]:
        """Get existing client context"""
        with self._lock:
            context = self.contexts.get(client_id)
            if context:
                context.last_accessed = datetime.now()
            return context

    def load_or_create_context(self, client_id: str) -> Optional[ClientContext]:
        """Load client config and create context if it doesn't exist"""
        # Try to load from storage first
        config = self.load_client_config(client_id)
        if config:
            return self.create_client_context(config)
        return None

    def remove_client_context(self, client_id: str) -> bool:
        """Remove client context (cleanup)"""
        with self._lock:
            if client_id in self.contexts:
                context = self.contexts[client_id]
                logger.info(f"Removing context for client {context.client_name} ({client_id})")

                # Save final state if needed
                # Cleanup resources
                context.cache_clear()

                del self.contexts[client_id]
                return True
            return False

    def list_active_clients(self) -> List[Dict[str, Any]]:
        """List all active client contexts"""
        with self._lock:
            return [
                {
                    "client_id": ctx.client_id,
                    "client_name": ctx.client_name,
                    "status": ctx.config.status.value,
                    "last_accessed": ctx.last_accessed.isoformat(),
                    "active_operations": len(ctx.current_operations),
                    "total_operations": ctx.metrics.total_operations
                }
                for ctx in self.contexts.values()
            ]

    def get_global_metrics(self) -> Dict[str, Any]:
        """Get global performance metrics across all clients"""
        with self._lock:
            total_clients = len(self.contexts)
            total_operations = sum(ctx.metrics.total_operations for ctx in self.contexts.values())
            total_successful = sum(ctx.metrics.successful_operations for ctx in self.contexts.values())
            total_failed = sum(ctx.metrics.failed_operations for ctx in self.contexts.values())

            return {
                "total_clients": total_clients,
                "total_operations": total_operations,
                "total_successful_operations": total_successful,
                "total_failed_operations": total_failed,
                "overall_success_rate": total_successful / total_operations if total_operations > 0 else 0,
                "active_client_operations": sum(len(ctx.current_operations) for ctx in self.contexts.values())
            }

    @asynccontextmanager
    async def client_context(self, client_id: str):
        """
        Async context manager for client operations

        Usage:
            async with context_manager.client_context(client_id) as ctx:
                # Perform client operations within context
                result = await some_operation()
        """
        context = self.get_client_context(client_id)
        if not context:
            raise ValueError(f"No context found for client {client_id}")

        # Set context variable
        token = current_client_context.set(context)

        try:
            yield context
        finally:
            # Restore previous context
            current_client_context.reset(token)

    def validate_operation_for_client(self, client_id: str, operation_type: str,
                                    operation_data: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Validate that an operation is allowed for a specific client

        Args:
            client_id: Client identifier
            operation_type: Type of operation
            operation_data: Operation data for validation

        Returns:
            List of validation error messages (empty if valid)
        """
        context = self.get_client_context(client_id)
        if not context:
            return [f"No context found for client {client_id}"]

        errors = []

        # Check operation permissions
        if not context.validate_access(operation_type):
            errors.append(f"Operation {operation_type} not allowed for client {client_id}")

        # Validate business rules
        if operation_data:
            business_errors = context.validate_business_rules(operation_data)
            errors.extend(business_errors)

        return errors


# Global context manager instance
_context_manager = None

def get_context_manager() -> ClientContextManager:
    """Get global context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ClientContextManager()
    return _context_manager

def get_current_client_context() -> Optional[ClientContext]:
    """Get current client context from context variable"""
    return current_client_context.get()

# Export for easy importing
__all__ = [
    'ClientContext',
    'ClientContextManager',
    'ClientOperation',
    'ClientMetrics',
    'get_context_manager',
    'get_current_client_context'
]
