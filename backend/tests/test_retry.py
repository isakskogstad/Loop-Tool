"""
Tests for Retry logic implementation
"""

import pytest
import asyncio
from src.retry import (
    calculate_backoff,
    retry_with_backoff,
    retry_sync,
    retry_async,
    retry,
    RetryPolicy,
    RetryError,
    is_retryable_exception
)


class TestCalculateBackoff:
    """Tests for backoff calculation."""

    def test_base_delay(self):
        """First attempt should use base delay."""
        delay = calculate_backoff(0, base_delay=1.0, jitter=False)
        assert delay == 1.0

    def test_exponential_growth(self):
        """Delay should grow exponentially."""
        delay_0 = calculate_backoff(0, base_delay=1.0, exponential_base=2.0, jitter=False)
        delay_1 = calculate_backoff(1, base_delay=1.0, exponential_base=2.0, jitter=False)
        delay_2 = calculate_backoff(2, base_delay=1.0, exponential_base=2.0, jitter=False)

        assert delay_0 == 1.0
        assert delay_1 == 2.0
        assert delay_2 == 4.0

    def test_max_delay_cap(self):
        """Delay should not exceed max_delay."""
        delay = calculate_backoff(10, base_delay=1.0, exponential_base=2.0, max_delay=60.0, jitter=False)
        assert delay == 60.0

    def test_jitter_adds_randomness(self):
        """Jitter should add random variation."""
        delays = [calculate_backoff(0, base_delay=1.0, jitter=True) for _ in range(10)]

        # With jitter, not all delays should be identical
        assert len(set(delays)) > 1

    def test_jitter_bounds(self):
        """Jitter should be within expected bounds (0-50% of base)."""
        for _ in range(100):
            delay = calculate_backoff(0, base_delay=1.0, jitter=True)
            # Base is 1.0, jitter adds 0-50%, so range is 1.0-1.5
            assert 1.0 <= delay <= 1.5


class TestRetryableException:
    """Tests for exception retryability checking."""

    def test_connection_error_is_retryable(self):
        """ConnectionError should be retryable."""
        assert is_retryable_exception(ConnectionError("test"))

    def test_timeout_error_is_retryable(self):
        """TimeoutError should be retryable."""
        assert is_retryable_exception(TimeoutError("test"))

    def test_value_error_not_retryable(self):
        """ValueError should not be retryable by default."""
        assert not is_retryable_exception(ValueError("test"))

    def test_custom_retryable_exceptions(self):
        """Should use custom exception list when provided."""
        assert is_retryable_exception(
            ValueError("test"),
            retryable_exceptions=(ValueError,)
        )


class TestRetrySync:
    """Tests for synchronous retry."""

    def test_successful_first_attempt(self):
        """Should return on first successful attempt."""
        call_count = 0

        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry_sync(success_func, max_retries=3)

        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self):
        """Should retry on retryable exception."""
        call_count = 0

        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = retry_sync(failing_then_success, max_retries=3, base_delay=0.01)

        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        """Should raise RetryError after exhausting retries."""
        def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            retry_sync(always_fails, max_retries=2, base_delay=0.01)

        assert exc_info.value.attempts == 3  # Initial + 2 retries

    def test_does_not_retry_non_retryable(self):
        """Should not retry non-retryable exceptions."""
        call_count = 0

        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            retry_sync(raises_value_error, max_retries=3, base_delay=0.01)

        assert call_count == 1


class TestRetryAsync:
    """Tests for asynchronous retry."""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Should return on first successful attempt."""
        call_count = 0

        async def async_success():
            nonlocal call_count
            call_count += 1
            return "async success"

        result = await retry_with_backoff(async_success, max_retries=3)

        assert result == "async success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        """Should retry on retryable exception."""
        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "recovered"

        result = await retry_with_backoff(failing_then_success, max_retries=3, base_delay=0.01)

        assert result == "recovered"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Should raise RetryError after exhausting retries."""
        async def always_fails():
            raise TimeoutError("Always times out")

        with pytest.raises(RetryError) as exc_info:
            await retry_with_backoff(always_fails, max_retries=2, base_delay=0.01)

        assert exc_info.value.attempts == 3


class TestRetryDecorator:
    """Tests for retry decorator."""

    def test_sync_decorator(self):
        """Should work as sync decorator."""
        call_count = 0

        @retry(max_retries=2, base_delay=0.01)
        def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError()
            return "decorated result"

        result = decorated_func()

        assert result == "decorated result"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_decorator(self):
        """Should work as async decorator."""
        call_count = 0

        @retry_async(max_retries=2, base_delay=0.01)
        async def decorated_async():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError()
            return "async decorated result"

        result = await decorated_async()

        assert result == "async decorated result"
        assert call_count == 2


class TestRetryPolicy:
    """Tests for RetryPolicy class."""

    def test_execute_sync(self):
        """Should execute sync function with policy."""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            return "policy result"

        result = policy.execute_sync(func)

        assert result == "policy result"

    @pytest.mark.asyncio
    async def test_execute_async(self):
        """Should execute async function with policy."""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)

        async def async_func():
            return "async policy result"

        result = await policy.execute_async(async_func)

        assert result == "async policy result"

    def test_sync_decorator_from_policy(self):
        """Should create sync decorator from policy."""
        policy = RetryPolicy(max_retries=2, base_delay=0.01)

        @policy.sync_decorator
        def decorated():
            return "via decorator"

        result = decorated()

        assert result == "via decorator"
