"""
Tests for Circuit Breaker implementation
"""

import pytest
import asyncio
from src.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitBreakerRegistry,
    get_circuit_breaker
)


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initial_state_is_closed(self):
        """Circuit should start in CLOSED state."""
        cb = CircuitBreaker("test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed
        assert not cb.is_open

    def test_can_execute_when_closed(self):
        """Should allow execution when circuit is closed."""
        cb = CircuitBreaker("test", failure_threshold=3)
        assert cb.can_execute()

    def test_opens_after_failure_threshold(self):
        """Circuit should open after reaching failure threshold."""
        cb = CircuitBreaker("test", failure_threshold=3)

        # Record failures
        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN
        assert cb.is_open
        assert not cb.can_execute()

    def test_records_success(self):
        """Should track successful requests."""
        cb = CircuitBreaker("test", failure_threshold=3)

        cb.record_success()
        cb.record_success()

        assert cb.stats.successful_requests == 2
        assert cb.stats.consecutive_successes == 2
        assert cb.stats.consecutive_failures == 0

    def test_records_rejection(self):
        """Should track rejected requests."""
        cb = CircuitBreaker("test", failure_threshold=1)

        # Open the circuit
        cb.record_failure()

        # Try to execute when open
        cb.record_rejection()

        assert cb.stats.rejected_requests == 1

    def test_reset(self):
        """Should reset circuit to initial state."""
        cb = CircuitBreaker("test", failure_threshold=2)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open

        # Reset
        cb.reset()

        assert cb.is_closed
        assert cb.stats.total_requests == 0
        assert cb.stats.consecutive_failures == 0

    def test_get_status(self):
        """Should return comprehensive status."""
        cb = CircuitBreaker("test", failure_threshold=3)

        cb.record_success()
        cb.record_failure()

        status = cb.get_status()

        assert status['name'] == 'test'
        assert status['state'] == 'closed'
        assert status['stats']['total_requests'] == 2
        assert status['stats']['successful'] == 1
        assert status['stats']['failed'] == 1

    def test_sync_context_manager_success(self):
        """Should work as sync context manager for successful operation."""
        cb = CircuitBreaker("test", failure_threshold=3)

        with cb:
            pass  # Successful operation

        assert cb.stats.successful_requests == 1

    def test_sync_context_manager_failure(self):
        """Should record failure when exception raised in context."""
        cb = CircuitBreaker("test", failure_threshold=3)

        try:
            with cb:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert cb.stats.failed_requests == 1

    def test_context_manager_raises_when_open(self):
        """Should raise CircuitOpenError when circuit is open."""
        cb = CircuitBreaker("test", failure_threshold=1)

        # Open the circuit
        cb.record_failure()

        with pytest.raises(CircuitOpenError):
            with cb:
                pass


class TestCircuitBreakerAsync:
    """Async tests for CircuitBreaker."""

    @pytest.mark.asyncio
    async def test_async_context_manager_success(self):
        """Should work as async context manager for successful operation."""
        cb = CircuitBreaker("test_async", failure_threshold=3)

        async with cb:
            await asyncio.sleep(0.01)  # Simulated async operation

        assert cb.stats.successful_requests == 1

    @pytest.mark.asyncio
    async def test_async_context_manager_failure(self):
        """Should record failure when exception raised in async context."""
        cb = CircuitBreaker("test_async", failure_threshold=3)

        try:
            async with cb:
                raise ValueError("Async test error")
        except ValueError:
            pass

        assert cb.stats.failed_requests == 1

    @pytest.mark.asyncio
    async def test_async_raises_when_open(self):
        """Should raise CircuitOpenError in async context when open."""
        cb = CircuitBreaker("test_async", failure_threshold=1)

        # Open the circuit
        cb.record_failure()

        with pytest.raises(CircuitOpenError):
            async with cb:
                pass


class TestCircuitBreakerRegistry:
    """Tests for CircuitBreakerRegistry."""

    def test_get_or_create_new(self):
        """Should create new circuit breaker if not exists."""
        registry = CircuitBreakerRegistry()

        cb = registry.get_or_create("new_circuit")

        assert cb is not None
        assert cb.name == "new_circuit"

    def test_get_or_create_existing(self):
        """Should return existing circuit breaker."""
        registry = CircuitBreakerRegistry()

        cb1 = registry.get_or_create("existing")
        cb2 = registry.get_or_create("existing")

        assert cb1 is cb2

    def test_get_nonexistent(self):
        """Should return None for nonexistent circuit."""
        registry = CircuitBreakerRegistry()

        cb = registry.get("nonexistent")

        assert cb is None

    def test_get_all_status(self):
        """Should return status of all circuits."""
        registry = CircuitBreakerRegistry()

        registry.get_or_create("circuit1")
        registry.get_or_create("circuit2")

        status = registry.get_all_status()

        assert "circuit1" in status
        assert "circuit2" in status

    def test_reset_all(self):
        """Should reset all circuits."""
        registry = CircuitBreakerRegistry()

        cb1 = registry.get_or_create("reset1", failure_threshold=1)
        cb2 = registry.get_or_create("reset2", failure_threshold=1)

        # Open both circuits
        cb1.record_failure()
        cb2.record_failure()

        assert cb1.is_open
        assert cb2.is_open

        # Reset all
        registry.reset_all()

        assert cb1.is_closed
        assert cb2.is_closed


class TestGlobalRegistry:
    """Tests for global circuit breaker functions."""

    def test_get_circuit_breaker(self):
        """Should get or create from global registry."""
        cb = get_circuit_breaker("global_test")

        assert cb is not None
        assert cb.name == "global_test"
