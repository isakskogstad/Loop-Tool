"""
Async HTTP Client for Loop-Auto

Features:
- Async HTTP requests with httpx
- Rate limiting per domain
- Retry with exponential backoff
- Request timeout handling
- Request/response logging
"""

import asyncio
import time
import random
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict

import httpx

# Import config
try:
    from config import Config
except ImportError:
    # Fallback defaults
    class Config:
        REQUEST_TIMEOUT = 15
        CONNECT_TIMEOUT = 5
        MAX_RETRIES = 3
        RETRY_BACKOFF_BASE = 1.5
        RETRY_BACKOFF_MAX = 30
        RETRY_JITTER = True
        RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
        USER_AGENT = "Mozilla/5.0 (compatible)"

# Import logging
try:
    from src.logging_config import get_source_logger
    logger = get_source_logger('http_client')
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """
    Per-domain rate limiting.

    Ensures minimum delay between requests to the same domain.
    """
    delays: Dict[str, float] = field(default_factory=dict)
    last_requests: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def set_delay(self, domain: str, delay: float):
        """Set minimum delay for a domain."""
        self.delays[domain] = delay

    async def acquire(self, domain: str):
        """
        Wait until it's safe to make a request to the domain.

        Args:
            domain: The domain to rate limit
        """
        async with self._lock:
            delay = self.delays.get(domain, 0)
            if delay <= 0:
                return

            elapsed = time.time() - self.last_requests[domain]
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.debug(f"Rate limiting {domain}: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

            self.last_requests[domain] = time.time()


@dataclass
class RetryPolicy:
    """
    Exponential backoff retry policy with jitter.

    Delay formula: min(base * (exp_base ** attempt) + jitter, max_delay)
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_status_codes: Set[int] = field(
        default_factory=lambda: {429, 500, 502, 503, 504}
    )

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt."""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            # Add random jitter (0-10% of delay)
            delay += random.uniform(0, delay * 0.1)

        return delay

    def should_retry(self, status_code: int, attempt: int) -> bool:
        """Check if request should be retried."""
        return (
            attempt < self.max_retries and
            status_code in self.retryable_status_codes
        )


class AsyncHTTPClient:
    """
    Async HTTP client with retry, rate limiting, and logging.

    Usage:
        async with AsyncHTTPClient() as client:
            response = await client.get("https://example.com")
            html = response.text
    """

    def __init__(
        self,
        timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
        user_agent: Optional[str] = None,
        rate_limiter: Optional[RateLimiter] = None,
        retry_policy: Optional[RetryPolicy] = None
    ):
        """
        Initialize async HTTP client.

        Args:
            timeout: Request timeout in seconds
            connect_timeout: Connection timeout in seconds
            user_agent: User agent string
            rate_limiter: Optional rate limiter instance
            retry_policy: Optional retry policy instance
        """
        self.timeout = timeout or Config.REQUEST_TIMEOUT
        self.connect_timeout = connect_timeout or Config.CONNECT_TIMEOUT
        self.user_agent = user_agent or Config.USER_AGENT

        self.rate_limiter = rate_limiter or RateLimiter()
        self.retry_policy = retry_policy or RetryPolicy(
            max_retries=Config.MAX_RETRIES,
            base_delay=Config.RETRY_BACKOFF_BASE,
            max_delay=Config.RETRY_BACKOFF_MAX,
            jitter=Config.RETRY_JITTER,
            retryable_status_codes=set(Config.RETRY_STATUS_CODES)
        )

        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                timeout=self.timeout,
                connect=self.connect_timeout
            ),
            headers={
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7',
            },
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make GET request with rate limiting and retry.

        Args:
            url: Request URL
            headers: Optional additional headers
            params: Optional query parameters
            **kwargs: Additional arguments passed to httpx

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        return await self._request("GET", url, headers=headers, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make POST request with rate limiting and retry.

        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Optional additional headers
            **kwargs: Additional arguments passed to httpx

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        return await self._request(
            "POST", url, data=data, json=json, headers=headers, **kwargs
        )

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Arguments passed to httpx

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with context manager.")

        domain = self._get_domain(url)
        attempt = 0
        last_exception = None

        while attempt <= self.retry_policy.max_retries:
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire(domain)

                # Log request
                start_time = time.perf_counter()
                logger.debug(f"{method} {url}", action="request", attempt=attempt)

                # Make request
                response = await self._client.request(method, url, **kwargs)

                # Log response
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"{method} {url} -> {response.status_code}",
                    action="response",
                    status_code=response.status_code,
                    duration_ms=duration_ms
                )

                # Check if we should retry
                if self.retry_policy.should_retry(response.status_code, attempt):
                    delay = self.retry_policy.get_delay(attempt)
                    logger.warning(
                        f"Retrying {url} after {delay:.2f}s (status {response.status_code})",
                        action="retry",
                        attempt=attempt,
                        status_code=response.status_code
                    )
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue

                # Raise for client errors (4xx except 429)
                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(
                    f"Timeout for {url}",
                    action="timeout",
                    attempt=attempt,
                    error=str(e)
                )

            except httpx.HTTPStatusError as e:
                last_exception = e
                # Already handled retryable status codes above
                if not self.retry_policy.should_retry(e.response.status_code, attempt):
                    raise

            except httpx.RequestError as e:
                last_exception = e
                logger.warning(
                    f"Request error for {url}: {e}",
                    action="error",
                    attempt=attempt,
                    error=str(e)
                )

            # Retry with backoff
            if attempt < self.retry_policy.max_retries:
                delay = self.retry_policy.get_delay(attempt)
                logger.warning(
                    f"Retrying {url} after {delay:.2f}s",
                    action="retry",
                    attempt=attempt
                )
                await asyncio.sleep(delay)

            attempt += 1

        # All retries exhausted
        logger.error(
            f"All retries exhausted for {url}",
            action="exhausted",
            attempts=attempt
        )

        if last_exception:
            raise last_exception

        raise httpx.RequestError(f"Failed after {attempt} attempts")

    async def get_text(self, url: str, **kwargs) -> Optional[str]:
        """
        Get URL content as text.

        Args:
            url: Request URL
            **kwargs: Additional arguments

        Returns:
            Response text or None on error
        """
        try:
            response = await self.get(url, **kwargs)
            return response.text
        except httpx.HTTPError as e:
            logger.error(f"Failed to get {url}: {e}", action="get_text_error", error=str(e))
            return None

    async def get_json(self, url: str, **kwargs) -> Optional[Dict]:
        """
        Get URL content as JSON.

        Args:
            url: Request URL
            **kwargs: Additional arguments

        Returns:
            Parsed JSON or None on error
        """
        try:
            response = await self.get(url, **kwargs)
            return response.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.error(f"Failed to get JSON from {url}: {e}", action="get_json_error", error=str(e))
            return None


# Pre-configured rate limiters for Swedish data sources
def get_default_rate_limiter() -> RateLimiter:
    """
    Get rate limiter with default delays for known domains.
    
    Configured domains:
    - www.allabolag.se: 1.0s (company data scraping)
    - foretagsinfo.bolagsverket.se: 0.5s (XBRL/VDM annual reports)
    - poit.bolagsverket.se: 2.0s (Post- och Inrikes Tidningar announcements)
    
    Note: POIT primarily uses browser automation due to bot protection,
    but this configuration ensures consistent rate limiting if HTTP 
    requests are attempted as a fallback.
    """
    limiter = RateLimiter()
    limiter.set_delay("www.allabolag.se", 1.0)
    limiter.set_delay("foretagsinfo.bolagsverket.se", 0.5)
    limiter.set_delay("poit.bolagsverket.se", 2.0)
    return limiter


# Convenience function for one-off requests
async def fetch_url(url: str, **kwargs) -> Optional[str]:
    """
    Fetch URL content with default settings.

    Args:
        url: URL to fetch
        **kwargs: Additional arguments

    Returns:
        Response text or None on error
    """
    async with AsyncHTTPClient(rate_limiter=get_default_rate_limiter()) as client:
        return await client.get_text(url, **kwargs)
