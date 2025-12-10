"""
Metrics Collection for Performance Monitoring

Collects and exposes performance metrics for the Swedish Company API.
Designed for integration with health endpoints and monitoring systems.

Features:
- Request timing statistics
- Source-specific success/failure tracking
- Cache hit/miss rates
- Rolling averages (last N requests)

Data Sources:
- Bolagsverket VDM: Official company registry
- Allabolag: Financial data, board members

Usage:
    metrics = get_metrics()

    # Record timing
    with metrics.timer("allabolag"):
        result = await fetch_allabolag(orgnr)

    # Or manually
    metrics.record_fetch("allabolag", duration_ms=150.5, success=True)
    metrics.record_cache_hit("db_company")
    metrics.record_cache_miss("db_company")

    # Get statistics
    stats = metrics.get_stats()
"""

import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Optional, Deque
from contextlib import contextmanager

try:
    from .logging_config import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


logger = get_logger("metrics")


@dataclass
class SourceMetrics:
    """Metrics for a single data source."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0.0
    recent_durations: Deque[float] = field(default_factory=lambda: deque(maxlen=100))

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def avg_duration_ms(self) -> float:
        """Average duration of all requests."""
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests

    @property
    def avg_recent_duration_ms(self) -> float:
        """Average duration of recent requests (last 100)."""
        if not self.recent_durations:
            return 0.0
        return sum(self.recent_durations) / len(self.recent_durations)

    @property
    def min_recent_duration_ms(self) -> float:
        """Minimum duration of recent requests."""
        if not self.recent_durations:
            return 0.0
        return min(self.recent_durations)

    @property
    def max_recent_duration_ms(self) -> float:
        """Maximum duration of recent requests."""
        if not self.recent_durations:
            return 0.0
        return max(self.recent_durations)


@dataclass
class CacheMetrics:
    """Metrics for cache operations."""
    hits: int = 0
    misses: int = 0

    @property
    def total(self) -> int:
        """Total cache lookups."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.hits / self.total) * 100


class Metrics:
    """
    Central metrics collection for the API.

    Thread-safe implementation for concurrent access.
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize metrics collector.

        Args:
            window_size: Number of recent requests to track for rolling averages
        """
        self.window_size = window_size
        self._sources: Dict[str, SourceMetrics] = {}
        self._caches: Dict[str, CacheMetrics] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()

        # Pre-initialize common sources (only Bolagsverket and Allabolag)
        for source in ['bolagsverket', 'allabolag', 'orchestrator']:
            self._sources[source] = SourceMetrics(
                recent_durations=deque(maxlen=window_size)
            )

        # Pre-initialize common caches
        for cache in ['db_company']:
            self._caches[cache] = CacheMetrics()

    def _get_source(self, name: str) -> SourceMetrics:
        """Get or create source metrics."""
        if name not in self._sources:
            self._sources[name] = SourceMetrics(
                recent_durations=deque(maxlen=self.window_size)
            )
        return self._sources[name]

    def _get_cache(self, name: str) -> CacheMetrics:
        """Get or create cache metrics."""
        if name not in self._caches:
            self._caches[name] = CacheMetrics()
        return self._caches[name]

    def record_fetch(
        self,
        source: str,
        duration_ms: float,
        success: bool = True
    ):
        """
        Record a fetch operation.

        Args:
            source: Source name (e.g., 'allabolag', 'bolagsverket')
            duration_ms: Request duration in milliseconds
            success: Whether request succeeded
        """
        with self._lock:
            metrics = self._get_source(source)
            metrics.total_requests += 1
            metrics.total_duration_ms += duration_ms
            metrics.recent_durations.append(duration_ms)

            if success:
                metrics.successful_requests += 1
            else:
                metrics.failed_requests += 1

    def record_cache_hit(self, cache: str):
        """Record a cache hit."""
        with self._lock:
            self._get_cache(cache).hits += 1

    def record_cache_miss(self, cache: str):
        """Record a cache miss."""
        with self._lock:
            self._get_cache(cache).misses += 1

    @contextmanager
    def timer(self, source: str):
        """
        Context manager for timing operations.

        Usage:
            with metrics.timer("allabolag"):
                result = await fetch()
        """
        start = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self.record_fetch(source, duration_ms, success)

    def get_source_stats(self, source: str) -> dict:
        """Get statistics for a specific source."""
        with self._lock:
            metrics = self._get_source(source)
            return {
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'failed_requests': metrics.failed_requests,
                'success_rate': round(metrics.success_rate, 2),
                'avg_duration_ms': round(metrics.avg_duration_ms, 2),
                'avg_recent_duration_ms': round(metrics.avg_recent_duration_ms, 2),
                'min_recent_duration_ms': round(metrics.min_recent_duration_ms, 2),
                'max_recent_duration_ms': round(metrics.max_recent_duration_ms, 2),
            }

    def get_cache_stats(self, cache: str) -> dict:
        """Get statistics for a specific cache."""
        with self._lock:
            metrics = self._get_cache(cache)
            return {
                'hits': metrics.hits,
                'misses': metrics.misses,
                'total': metrics.total,
                'hit_rate': round(metrics.hit_rate, 2),
            }

    def get_stats(self) -> dict:
        """Get all metrics statistics."""
        with self._lock:
            # Calculate totals
            total_requests = sum(m.total_requests for m in self._sources.values())
            total_success = sum(m.successful_requests for m in self._sources.values())
            total_failed = sum(m.failed_requests for m in self._sources.values())

            # Calculate overall average
            all_durations = []
            for m in self._sources.values():
                all_durations.extend(m.recent_durations)
            avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0

            return {
                'uptime_seconds': round(time.time() - self._start_time, 1),
                'summary': {
                    'total_requests': total_requests,
                    'successful_requests': total_success,
                    'failed_requests': total_failed,
                    'success_rate': round((total_success / total_requests * 100) if total_requests else 0, 2),
                    'avg_fetch_time_ms': round(avg_duration, 2),
                },
                'sources': {
                    name: {
                        'requests': m.total_requests,
                        'success_rate': round(m.success_rate, 2),
                        'avg_duration_ms': round(m.avg_recent_duration_ms, 2),
                    }
                    for name, m in self._sources.items()
                    if m.total_requests > 0
                },
                'caches': {
                    name: {
                        'hits': c.hits,
                        'misses': c.misses,
                        'hit_rate': round(c.hit_rate, 2),
                    }
                    for name, c in self._caches.items()
                    if c.total > 0
                }
            }

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            for source in self._sources.values():
                source.total_requests = 0
                source.successful_requests = 0
                source.failed_requests = 0
                source.total_duration_ms = 0.0
                source.recent_durations.clear()

            for cache in self._caches.values():
                cache.hits = 0
                cache.misses = 0

            self._start_time = time.time()

        logger.info("Metrics reset")


# Global metrics instance
_metrics: Optional[Metrics] = None


def get_metrics() -> Metrics:
    """Get or create the global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics


def reset_metrics():
    """Reset the global metrics instance."""
    global _metrics
    if _metrics is not None:
        _metrics.reset()
