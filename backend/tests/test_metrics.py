"""
Tests for Metrics collection
"""

import pytest
import time
from src.metrics import Metrics, get_metrics, reset_metrics


class TestMetrics:
    """Tests for Metrics class."""

    def test_record_fetch_success(self):
        """Should record successful fetch."""
        metrics = Metrics()

        metrics.record_fetch("allabolag", 150.5, success=True)

        stats = metrics.get_source_stats("allabolag")
        assert stats['total_requests'] == 1
        assert stats['successful_requests'] == 1
        assert stats['failed_requests'] == 0

    def test_record_fetch_failure(self):
        """Should record failed fetch."""
        metrics = Metrics()

        metrics.record_fetch("allabolag", 100.0, success=False)

        stats = metrics.get_source_stats("allabolag")
        assert stats['total_requests'] == 1
        assert stats['successful_requests'] == 0
        assert stats['failed_requests'] == 1

    def test_record_cache_hit(self):
        """Should track cache hits."""
        metrics = Metrics()

        metrics.record_cache_hit("company_cache")
        metrics.record_cache_hit("company_cache")

        stats = metrics.get_cache_stats("company_cache")
        assert stats['hits'] == 2
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 100.0

    def test_record_cache_miss(self):
        """Should track cache misses."""
        metrics = Metrics()

        metrics.record_cache_miss("db_company")

        stats = metrics.get_cache_stats("db_company")
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.0

    def test_cache_hit_rate_calculation(self):
        """Should calculate correct hit rate."""
        metrics = Metrics()

        # 3 hits, 1 miss = 75% hit rate
        metrics.record_cache_hit("test_cache")
        metrics.record_cache_hit("test_cache")
        metrics.record_cache_hit("test_cache")
        metrics.record_cache_miss("test_cache")

        stats = metrics.get_cache_stats("test_cache")
        assert stats['hit_rate'] == 75.0

    def test_average_duration(self):
        """Should calculate average duration."""
        metrics = Metrics()

        metrics.record_fetch("test_source", 100.0)
        metrics.record_fetch("test_source", 200.0)
        metrics.record_fetch("test_source", 300.0)

        stats = metrics.get_source_stats("test_source")
        assert stats['avg_duration_ms'] == 200.0

    def test_timer_context_manager(self):
        """Should time operations with context manager."""
        metrics = Metrics()

        with metrics.timer("timed_source"):
            time.sleep(0.01)  # Small delay

        stats = metrics.get_source_stats("timed_source")
        assert stats['total_requests'] == 1
        assert stats['successful_requests'] == 1
        assert stats['avg_recent_duration_ms'] > 10  # At least 10ms

    def test_timer_records_failure_on_exception(self):
        """Should record failure when exception raised in timer."""
        metrics = Metrics()

        try:
            with metrics.timer("failing_source"):
                raise ValueError("Test error")
        except ValueError:
            pass

        stats = metrics.get_source_stats("failing_source")
        assert stats['failed_requests'] == 1
        assert stats['successful_requests'] == 0

    def test_get_stats_summary(self):
        """Should return comprehensive stats summary."""
        metrics = Metrics()

        # Record some activity
        metrics.record_fetch("source1", 100.0, success=True)
        metrics.record_fetch("source1", 200.0, success=True)
        metrics.record_fetch("source2", 150.0, success=False)
        metrics.record_cache_hit("cache1")
        metrics.record_cache_miss("cache1")

        stats = metrics.get_stats()

        assert 'uptime_seconds' in stats
        assert 'summary' in stats
        assert stats['summary']['total_requests'] == 3
        assert stats['summary']['successful_requests'] == 2
        assert stats['summary']['failed_requests'] == 1
        assert 'sources' in stats
        assert 'caches' in stats

    def test_reset(self):
        """Should reset all metrics."""
        metrics = Metrics()

        # Record some activity
        metrics.record_fetch("source", 100.0)
        metrics.record_cache_hit("cache")

        # Reset
        metrics.reset()

        # Verify reset
        stats = metrics.get_source_stats("source")
        assert stats['total_requests'] == 0

        cache_stats = metrics.get_cache_stats("cache")
        assert cache_stats['hits'] == 0

    def test_success_rate_calculation(self):
        """Should calculate correct success rate."""
        metrics = Metrics()

        # 8 success, 2 failure = 80% success rate
        for _ in range(8):
            metrics.record_fetch("rate_test", 100.0, success=True)
        for _ in range(2):
            metrics.record_fetch("rate_test", 100.0, success=False)

        stats = metrics.get_source_stats("rate_test")
        assert stats['success_rate'] == 80.0

    def test_multiple_sources_tracked_separately(self):
        """Should track sources independently."""
        metrics = Metrics()

        metrics.record_fetch("source_a", 100.0, success=True)
        metrics.record_fetch("source_a", 100.0, success=True)
        metrics.record_fetch("source_b", 200.0, success=False)

        stats_a = metrics.get_source_stats("source_a")
        stats_b = metrics.get_source_stats("source_b")

        assert stats_a['total_requests'] == 2
        assert stats_a['success_rate'] == 100.0

        assert stats_b['total_requests'] == 1
        assert stats_b['success_rate'] == 0.0


class TestGlobalMetrics:
    """Tests for global metrics functions."""

    def test_get_metrics_returns_singleton(self):
        """Should return same metrics instance."""
        m1 = get_metrics()
        m2 = get_metrics()

        assert m1 is m2

    def test_reset_metrics(self):
        """Should reset global metrics."""
        metrics = get_metrics()

        metrics.record_fetch("global_test", 100.0)

        reset_metrics()

        stats = metrics.get_source_stats("global_test")
        assert stats['total_requests'] == 0
