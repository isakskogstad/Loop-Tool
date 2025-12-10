"""
Retry Logic with Exponential Backoff

Provides robust retry mechanisms for handling transient failures.
Supports both sync and async operations with configurable backoff.

Features:
- Exponential backoff with optional jitter
- Configurable retry conditions
- Integration with circuit breakers
- Structured logging of retry attempts

Usage:
    # Decorator
    @retry_async(max_retries=3, base_delay=1.0)
    async def fetch_data():
        ...

    # Function wrapper
    result = await retry_with_backoff(
        fetch_data,
        max_retries=3,
        base_delay=1.0
    )
"""

import time
import random
import asyncio
from functools import wraps
from typing import Callable, TypeVar, Any, Optional, Type, Tuple, Union

try:
    from .logging_config import get_source_logger
except ImportError:
    import logging
    class _FallbackLogger:
        """Fallback logger that handles kwargs."""
        def __init__(self, name):
            self._logger = logging.getLogger(name)
        def debug(self, msg, **kwargs):
            self._logger.debug(msg)
        def info(self, msg, **kwargs):
            self._logger.info(msg)
        def warning(self, msg, **kwargs):
            self._logger.warning(msg)
        def error(self, msg, **kwargs):
            self._logger.error(msg)
    def get_source_logger(name):
        return _FallbackLogger(name)

try:
    from config import Config
except ImportError:
    class Config:
        MAX_RETRIES = 3
        RETRY_BACKOFF_BASE = 1.5


logger = get_source_logger("retry")

T = TypeVar('T')


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Exception = None, attempts: int = 0):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempts = attempts


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate backoff delay for a retry attempt.

    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Initial delay in seconds
        exponential_base: Multiplier for exponential growth
        max_delay: Maximum delay cap
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds
    """
    # Exponential: base_delay * (exponential_base ^ attempt)
    delay = base_delay * (exponential_base ** attempt)

    # Cap at max_delay
    delay = min(delay, max_delay)

    # Add jitter (0-50% of delay) to prevent thundering herd
    if jitter:
        jitter_amount = delay * random.uniform(0, 0.5)
        delay += jitter_amount

    return delay


def is_retryable_exception(
    exception: Exception,
    retryable_exceptions: Tuple[Type[Exception], ...] = None
) -> bool:
    """
    Check if an exception should trigger a retry.

    Args:
        exception: The caught exception
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        True if should retry, False otherwise
    """
    if retryable_exceptions is None:
        # Default: retry on common transient errors
        retryable_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
        )

    # Also check for httpx/requests exceptions if available
    try:
        import httpx
        retryable_exceptions = retryable_exceptions + (
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadError,
        )
    except ImportError:
        pass

    try:
        import requests
        retryable_exceptions = retryable_exceptions + (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        )
    except ImportError:
        pass

    return isinstance(exception, retryable_exceptions)


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    max_retries: int = None,
    base_delay: float = 1.0,
    exponential_base: float = None,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = None,
    on_retry: Callable[[int, Exception, float], None] = None,
    **kwargs
) -> T:
    """
    Execute async function with retry and exponential backoff.

    Args:
        func: Async function to execute
        *args: Arguments to pass to func
        max_retries: Maximum retry attempts (default from Config)
        base_delay: Initial delay in seconds
        exponential_base: Multiplier for exponential growth (default from Config)
        max_delay: Maximum delay cap
        jitter: Whether to add random jitter
        retryable_exceptions: Exception types to retry on
        on_retry: Callback(attempt, exception, delay) called before retry
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from func

    Raises:
        RetryError: If all retries exhausted
    """
    max_retries = max_retries if max_retries is not None else Config.MAX_RETRIES
    exponential_base = exponential_base if exponential_base is not None else Config.RETRY_BACKOFF_BASE

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

        except Exception as e:
            last_exception = e

            # Check if we should retry this exception
            if not is_retryable_exception(e, retryable_exceptions):
                logger.warning(
                    f"Non-retryable exception: {type(e).__name__}",
                    exception_type=type(e).__name__,
                    message=str(e)
                )
                raise

            # Check if we have retries left
            if attempt >= max_retries:
                logger.error(
                    f"All {max_retries + 1} attempts exhausted",
                    attempts=max_retries + 1,
                    last_error=str(e)
                )
                raise RetryError(
                    f"All {max_retries + 1} retry attempts exhausted",
                    last_exception=e,
                    attempts=max_retries + 1
                )

            # Calculate backoff delay
            delay = calculate_backoff(
                attempt=attempt,
                base_delay=base_delay,
                exponential_base=exponential_base,
                max_delay=max_delay,
                jitter=jitter
            )

            logger.info(
                f"Retry attempt {attempt + 1}/{max_retries + 1} after {delay:.2f}s",
                attempt=attempt + 1,
                max_attempts=max_retries + 1,
                delay=delay,
                error=str(e)
            )

            # Call retry callback if provided
            if on_retry:
                on_retry(attempt, e, delay)

            # Wait before retry
            await asyncio.sleep(delay)


def retry_sync(
    func: Callable[..., T],
    *args,
    max_retries: int = None,
    base_delay: float = 1.0,
    exponential_base: float = None,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = None,
    on_retry: Callable[[int, Exception, float], None] = None,
    **kwargs
) -> T:
    """
    Execute sync function with retry and exponential backoff.

    Args:
        func: Sync function to execute
        *args: Arguments to pass to func
        max_retries: Maximum retry attempts (default from Config)
        base_delay: Initial delay in seconds
        exponential_base: Multiplier for exponential growth (default from Config)
        max_delay: Maximum delay cap
        jitter: Whether to add random jitter
        retryable_exceptions: Exception types to retry on
        on_retry: Callback(attempt, exception, delay) called before retry
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from func

    Raises:
        RetryError: If all retries exhausted
    """
    max_retries = max_retries if max_retries is not None else Config.MAX_RETRIES
    exponential_base = exponential_base if exponential_base is not None else Config.RETRY_BACKOFF_BASE

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            last_exception = e

            if not is_retryable_exception(e, retryable_exceptions):
                raise

            if attempt >= max_retries:
                raise RetryError(
                    f"All {max_retries + 1} retry attempts exhausted",
                    last_exception=e,
                    attempts=max_retries + 1
                )

            delay = calculate_backoff(
                attempt=attempt,
                base_delay=base_delay,
                exponential_base=exponential_base,
                max_delay=max_delay,
                jitter=jitter
            )

            logger.info(
                f"Retry attempt {attempt + 1}/{max_retries + 1} after {delay:.2f}s",
                attempt=attempt + 1,
                max_attempts=max_retries + 1,
                delay=delay,
                error=str(e)
            )

            if on_retry:
                on_retry(attempt, e, delay)

            time.sleep(delay)


def retry_async(
    max_retries: int = None,
    base_delay: float = 1.0,
    exponential_base: float = None,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = None
):
    """
    Decorator for async functions with retry logic.

    Usage:
        @retry_async(max_retries=3, base_delay=1.0)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                exponential_base=exponential_base,
                max_delay=max_delay,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        return wrapper
    return decorator


def retry(
    max_retries: int = None,
    base_delay: float = 1.0,
    exponential_base: float = None,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = None
):
    """
    Decorator for sync functions with retry logic.

    Usage:
        @retry(max_retries=3, base_delay=1.0)
        def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return retry_sync(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                exponential_base=exponential_base,
                max_delay=max_delay,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        return wrapper
    return decorator


class RetryPolicy:
    """
    Configurable retry policy for reuse across multiple operations.

    Usage:
        policy = RetryPolicy(max_retries=3, base_delay=1.0)

        # Apply to function
        result = await policy.execute_async(fetch_data, url)

        # Or as decorator
        @policy.async_decorator
        async def fetch():
            ...
    """

    def __init__(
        self,
        max_retries: int = None,
        base_delay: float = 1.0,
        exponential_base: float = None,
        max_delay: float = 60.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = None
    ):
        self.max_retries = max_retries if max_retries is not None else Config.MAX_RETRIES
        self.base_delay = base_delay
        self.exponential_base = exponential_base if exponential_base is not None else Config.RETRY_BACKOFF_BASE
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    async def execute_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with this retry policy (async)."""
        return await retry_with_backoff(
            func,
            *args,
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            exponential_base=self.exponential_base,
            max_delay=self.max_delay,
            jitter=self.jitter,
            retryable_exceptions=self.retryable_exceptions,
            **kwargs
        )

    def execute_sync(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with this retry policy (sync)."""
        return retry_sync(
            func,
            *args,
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            exponential_base=self.exponential_base,
            max_delay=self.max_delay,
            jitter=self.jitter,
            retryable_exceptions=self.retryable_exceptions,
            **kwargs
        )

    def async_decorator(self, func: Callable[..., T]) -> Callable[..., T]:
        """Create decorator with this policy (async)."""
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await self.execute_async(func, *args, **kwargs)
        return wrapper

    def sync_decorator(self, func: Callable[..., T]) -> Callable[..., T]:
        """Create decorator with this policy (sync)."""
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return self.execute_sync(func, *args, **kwargs)
        return wrapper


# Default policy instance
default_policy = RetryPolicy()
