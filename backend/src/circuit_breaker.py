"""
Circuit Breaker Pattern Implementation

Provides fault tolerance by preventing repeated calls to failing services.
When failures exceed a threshold, the circuit "opens" and rejects requests
until a recovery timeout passes.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests are rejected immediately
- HALF_OPEN: Testing if service has recovered

Usage:
    breaker = CircuitBreaker("allabolag", failure_threshold=5)

    async with breaker:
        result = await fetch_data()

    # Or manual:
    if breaker.can_execute():
        try:
            result = await fetch_data()
            breaker.record_success()
        except Exception as e:
            breaker.record_failure()
            raise
"""

import time
import asyncio
from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

try:
    from .logging_config import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

try:
    from config import Config
except ImportError:
    class Config:
        CIRCUIT_FAILURE_THRESHOLD = 5
        CIRCUIT_RECOVERY_TIMEOUT = 60


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Attributes:
        name: Identifier for this circuit (e.g., 'allabolag')
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before testing recovery
        success_threshold: Successes needed in half-open to close circuit
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for logging and monitoring
            failure_threshold: Failures before opening (default from Config)
            recovery_timeout: Seconds before retry (default from Config)
            success_threshold: Successes to close from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold or Config.CIRCUIT_FAILURE_THRESHOLD
        self.recovery_timeout = recovery_timeout or Config.CIRCUIT_RECOVERY_TIMEOUT
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_state_change = time.time()
        self._lock = asyncio.Lock()

        self.logger = get_logger(f"circuit.{name}")

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitStats:
        """Circuit statistics."""
        return self._stats

    @property
    def is_closed(self) -> bool:
        """True if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """True if circuit is open (rejecting requests)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """True if circuit is testing recovery."""
        return self._state == CircuitState.HALF_OPEN

    def can_execute(self) -> bool:
        """
        Check if request can proceed.

        Returns:
            True if request should proceed, False if circuit is open
        """
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            elapsed = time.time() - self._last_state_change
            if elapsed >= self.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                return True
            return False

        # HALF_OPEN - allow limited requests
        return True

    def record_success(self):
        """Record a successful request."""
        self._stats.total_requests += 1
        self._stats.successful_requests += 1
        self._stats.last_success_time = time.time()
        self._stats.consecutive_successes += 1
        self._stats.consecutive_failures = 0

        if self._state == CircuitState.HALF_OPEN:
            if self._stats.consecutive_successes >= self.success_threshold:
                self._transition_to(CircuitState.CLOSED)

    def record_failure(self):
        """Record a failed request."""
        self._stats.total_requests += 1
        self._stats.failed_requests += 1
        self._stats.last_failure_time = time.time()
        self._stats.consecutive_failures += 1
        self._stats.consecutive_successes = 0

        if self._state == CircuitState.CLOSED:
            if self._stats.consecutive_failures >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)

        elif self._state == CircuitState.HALF_OPEN:
            # Single failure in half-open returns to open
            self._transition_to(CircuitState.OPEN)

    def record_rejection(self):
        """Record a rejected request (circuit open)."""
        self._stats.total_requests += 1
        self._stats.rejected_requests += 1

    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.time()

        # Reset counters on state change
        if new_state == CircuitState.CLOSED:
            self._stats.consecutive_failures = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._stats.consecutive_successes = 0

        self.logger.info(
            f"Circuit '{self.name}' transitioned: {old_state.value} -> {new_state.value}",
            circuit=self.name,
            old_state=old_state.value,
            new_state=new_state.value
        )

    def reset(self):
        """Reset circuit to closed state and clear stats."""
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._last_state_change = time.time()

        self.logger.info(f"Circuit '{self.name}' manually reset")

    def get_status(self) -> dict:
        """Get circuit status for monitoring."""
        return {
            'name': self.name,
            'state': self._state.value,
            'stats': {
                'total_requests': self._stats.total_requests,
                'successful': self._stats.successful_requests,
                'failed': self._stats.failed_requests,
                'rejected': self._stats.rejected_requests,
                'consecutive_failures': self._stats.consecutive_failures,
                'consecutive_successes': self._stats.consecutive_successes
            },
            'thresholds': {
                'failure_threshold': self.failure_threshold,
                'recovery_timeout': self.recovery_timeout,
                'success_threshold': self.success_threshold
            },
            'time_in_state': time.time() - self._last_state_change
        }

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        async with self._lock:
            if not self.can_execute():
                self.record_rejection()
                raise CircuitOpenError(f"Circuit '{self.name}' is open")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
        return False  # Don't suppress exceptions

    def __enter__(self):
        """Sync context manager entry."""
        if not self.can_execute():
            self.record_rejection()
            raise CircuitOpenError(f"Circuit '{self.name}' is open")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        if exc_type is None:
            self.record_success()
        else:
            self.record_failure()
        return False


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is rejected."""
    pass


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Usage:
        registry = CircuitBreakerRegistry()
        breaker = registry.get_or_create('allabolag')
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = None,
        recovery_timeout: int = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
        return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)

    def get_all_status(self) -> dict:
        """Get status of all circuit breakers."""
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()


# Global registry instance
_registry = CircuitBreakerRegistry()


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker from the global registry."""
    return _registry.get_or_create(name, **kwargs)


def get_all_circuit_status() -> dict:
    """Get status of all circuit breakers."""
    return _registry.get_all_status()
