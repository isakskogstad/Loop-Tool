"""
Base Scraper Class

Provides common functionality for all scrapers:
- Async HTTP client support (httpx)
- Sync HTTP client support (requests)
- Rate limiting
- Structured logging
"""

import time
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

# HTTP clients
import requests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Logging
try:
    from ..logging_config import get_source_logger
except ImportError:
    import logging

    class MockLogger:
        def __init__(self, name):
            self._logger = logging.getLogger(name)

        def info(self, msg, **kwargs):
            self._logger.info(msg)

        def warning(self, msg, **kwargs):
            self._logger.warning(msg)

        def error(self, msg, **kwargs):
            self._logger.error(msg)

        def debug(self, msg, **kwargs):
            self._logger.debug(msg)

    def get_source_logger(name):
        return MockLogger(name)

# Config
try:
    from config import Config
except ImportError:
    class Config:
        USER_AGENT = "Mozilla/5.0 (compatible)"
        REQUEST_TIMEOUT = 15
        CONNECT_TIMEOUT = 5


class BaseScraper(ABC):
    """
    Base class for all scrapers.

    Provides:
    - Rate limiting per domain
    - Both sync (requests) and async (httpx) HTTP support
    - Structured logging
    - Common error handling

    Subclasses should implement:
    - scrape_company(orgnr) -> Dict
    - scrape_company_async(orgnr) -> Dict (optional, falls back to sync)
    """

    def __init__(
        self,
        source_name: str,
        delay: float = 1.0,
        base_url: str = ""
    ):
        """
        Initialize base scraper.

        Args:
            source_name: Name for logging (e.g., 'allabolag', 'bolagsverket')
            delay: Minimum delay between requests in seconds
            base_url: Base URL for this source
        """
        self.source_name = source_name
        self.delay = delay
        self.base_url = base_url
        self.logger = get_source_logger(source_name)

        # Rate limiting
        self._last_request = 0
        self._lock = asyncio.Lock() if HTTPX_AVAILABLE else None

        # Sync HTTP client (requests)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7',
        })

        # Async HTTP client (httpx) - initialized lazily
        self._async_client: Optional["httpx.AsyncClient"] = None

    async def _get_async_client(self) -> "httpx.AsyncClient":
        """Get or create async HTTP client."""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx not installed. Install with: pip install httpx")

        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=Config.REQUEST_TIMEOUT,
                    connect=Config.CONNECT_TIMEOUT
                ),
                headers={
                    'User-Agent': Config.USER_AGENT,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7',
                },
                follow_redirects=True
            )
        return self._async_client

    async def close(self):
        """Close async client when done."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    # =========================================================================
    # RATE LIMITING
    # =========================================================================

    def _rate_limit_sync(self):
        """Apply rate limiting (sync version)."""
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            wait_time = self.delay - elapsed
            self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        self._last_request = time.time()

    async def _rate_limit_async(self):
        """Apply rate limiting (async version)."""
        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            elapsed = time.time() - self._last_request
            if elapsed < self.delay:
                wait_time = self.delay - elapsed
                self.logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            self._last_request = time.time()

    # =========================================================================
    # SYNC HTTP METHODS
    # =========================================================================

    def _fetch_page(self, url: str, **kwargs) -> Optional[str]:
        """
        Fetch page content with rate limiting (sync).

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get

        Returns:
            HTML content or None on error
        """
        self._rate_limit_sync()
        start_time = time.perf_counter()

        try:
            response = self.session.get(
                url,
                timeout=kwargs.pop('timeout', Config.REQUEST_TIMEOUT),
                **kwargs
            )
            response.raise_for_status()

            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.debug(
                f"Fetched {url}",
                action="fetch",
                status_code=response.status_code,
                duration_ms=duration_ms
            )

            return response.text

        except requests.RequestException as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.warning(
                f"Error fetching {url}: {e}",
                action="fetch_error",
                error=str(e),
                duration_ms=duration_ms
            )
            return None

    def _fetch_json(self, url: str, **kwargs) -> Optional[Dict]:
        """
        Fetch JSON content with rate limiting (sync).

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get

        Returns:
            Parsed JSON or None on error
        """
        self._rate_limit_sync()
        start_time = time.perf_counter()

        try:
            response = self.session.get(
                url,
                timeout=kwargs.pop('timeout', Config.REQUEST_TIMEOUT),
                **kwargs
            )
            response.raise_for_status()

            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.debug(
                f"Fetched JSON {url}",
                action="fetch_json",
                status_code=response.status_code,
                duration_ms=duration_ms
            )

            return response.json()

        except (requests.RequestException, ValueError) as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.warning(
                f"Error fetching JSON {url}: {e}",
                action="fetch_json_error",
                error=str(e),
                duration_ms=duration_ms
            )
            return None

    # =========================================================================
    # ASYNC HTTP METHODS
    # =========================================================================

    async def _fetch_page_async(self, url: str, **kwargs) -> Optional[str]:
        """
        Fetch page content with rate limiting (async).

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for httpx

        Returns:
            HTML content or None on error
        """
        await self._rate_limit_async()
        start_time = time.perf_counter()

        try:
            client = await self._get_async_client()
            response = await client.get(url, **kwargs)
            response.raise_for_status()

            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.debug(
                f"Async fetched {url}",
                action="async_fetch",
                status_code=response.status_code,
                duration_ms=duration_ms
            )

            return response.text

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.warning(
                f"Async error fetching {url}: {e}",
                action="async_fetch_error",
                error=str(e),
                duration_ms=duration_ms
            )
            return None

    async def _fetch_json_async(self, url: str, **kwargs) -> Optional[Dict]:
        """
        Fetch JSON content with rate limiting (async).

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for httpx

        Returns:
            Parsed JSON or None on error
        """
        await self._rate_limit_async()
        start_time = time.perf_counter()

        try:
            client = await self._get_async_client()
            response = await client.get(url, **kwargs)
            response.raise_for_status()

            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.debug(
                f"Async fetched JSON {url}",
                action="async_fetch_json",
                status_code=response.status_code,
                duration_ms=duration_ms
            )

            return response.json()

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.warning(
                f"Async error fetching JSON {url}: {e}",
                action="async_fetch_json_error",
                error=str(e),
                duration_ms=duration_ms
            )
            return None

    # =========================================================================
    # ABSTRACT METHODS
    # =========================================================================

    @abstractmethod
    def scrape_company(self, orgnr: str) -> Optional[Dict[str, Any]]:
        """
        Scrape company data (sync).

        Args:
            orgnr: Organization number (10 digits)

        Returns:
            Company data dict or None if not found
        """
        pass

    async def scrape_company_async(self, orgnr: str) -> Optional[Dict[str, Any]]:
        """
        Scrape company data (async).

        Default implementation runs sync version in thread pool.
        Override for native async implementation.

        Args:
            orgnr: Organization number (10 digits)

        Returns:
            Company data dict or None if not found
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scrape_company, orgnr)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for companies.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of company dicts
        """
        return []

    async def search_async(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for companies (async).

        Default implementation runs sync version in thread pool.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of company dicts
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search, query, limit)
