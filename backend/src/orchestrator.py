"""
Data Orchestrator
Combines data from multiple sources with intelligent fallback

Features:
- Async parallel fetching for performance
- Sync methods for backward compatibility
- Structured logging
- Circuit breaker integration (pending)

Data Sources:
- Bolagsverket VDM: Official API for basic company data
- Allabolag: Scraping for financials, board, corporate structure
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import time

from .supabase_client import SupabaseDatabase, get_db
from .scrapers.bolagsverket_vdm import BolagsverketVDMClient, get_bolagsverket_vdm_client
from .scrapers.allabolag import AllabolagScraper

# Import logging
try:
    from .logging_config import get_orchestrator_logger
    logger = get_orchestrator_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.info = lambda msg, **kwargs: logging.info(msg)
    logger.error = lambda msg, **kwargs: logging.error(msg)
    logger.warning = lambda msg, **kwargs: logging.warning(msg)
    logger.debug = lambda msg, **kwargs: logging.debug(msg)

# Import circuit breaker
try:
    from .circuit_breaker import get_circuit_breaker, CircuitOpenError
except ImportError:
    get_circuit_breaker = None
    CircuitOpenError = Exception

# Import config
try:
    from config import Config
except ImportError:
    class Config:
        MAX_PARALLEL_SOURCES = 2
        BATCH_PARALLEL_WORKERS = 5
        BATCH_INTER_DELAY = 0.5
        ENABLE_ASYNC_FETCH = True


class DataOrchestrator:
    """
    Orchestrates data retrieval from multiple sources:
    1. Cache (Supabase PostgreSQL) - fastest
    2. Bolagsverket VDM - official API for basic data
    3. Allabolag - primary scraper for board/financials

    Supports both sync and async operations for maximum flexibility.
    """

    def __init__(self,
                 db: SupabaseDatabase = None,
                 bolagsverket_api_key: str = None,
                 cache_ttl_hours: int = 24):

        self.db = db or get_db()
        self.cache_ttl = cache_ttl_hours

        # Initialize clients
        self.bolagsverket = get_bolagsverket_vdm_client()
        self.allabolag = AllabolagScraper(delay=1.0)

        logger.info("DataOrchestrator initialized", action="init")

    # =========================================================================
    # SYNC API (backward compatible)
    # =========================================================================

    def get_company(self, orgnr: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get complete company data (sync version).

        For async usage, prefer get_company_async() for better performance.
        """
        # Use async implementation if enabled
        if Config.ENABLE_ASYNC_FETCH:
            try:
                return asyncio.run(self.get_company_async(orgnr, force_refresh))
            except RuntimeError:
                # Already running in async context
                pass

        # Fall back to sync implementation
        return self._get_company_sync(orgnr, force_refresh)

    def _get_company_sync(self, orgnr: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Original sync implementation for fallback."""
        orgnr = orgnr.replace('-', '')
        start_time = time.perf_counter()

        # 1. Check cache
        if not force_refresh and self.db.is_cache_fresh(orgnr, self.cache_ttl):
            cached = self.db.get_company(orgnr)
            if cached:
                cached['_meta'] = {
                    'from_cache': True,
                    'fetched_at': cached.get('updated_at')
                }
                logger.info(
                    f"Cache hit for {orgnr}",
                    orgnr=orgnr,
                    action="cache_hit",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )
                return cached

        # 2. Fetch from sources (sequential)
        result = {
            'orgnr': orgnr,
            '_meta': {
                'from_cache': False,
                'fetched_at': datetime.now().isoformat(),
                'sources': {}
            }
        }

        # 2a. Bolagsverket VDM
        bv_data = self._fetch_bolagsverket(orgnr)
        if bv_data:
            result.update(bv_data)
            result['_meta']['sources']['basic'] = 'bolagsverket'

        # 2b. Allabolag
        ab_data = self._fetch_allabolag(orgnr)
        if ab_data:
            result = self._merge_data(result, ab_data, prefer_existing=['name', 'orgnr', 'status'])
            result['_meta']['sources']['board'] = 'allabolag'
            result['_meta']['sources']['financials'] = 'allabolag'

        # 3. Validate
        if not result.get('name'):
            logger.warning(f"No data found for {orgnr}", orgnr=orgnr, action="not_found")
            return None

        # 4. Save sources before storing (store removes _meta)
        meta = result.get('_meta', {})
        sources = meta.get('sources', {})
        sources_list = list(sources.values()) if sources else ['allabolag']

        # 5. Store in cache
        self._store_in_db(result)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Fetched {orgnr} from sources",
            orgnr=orgnr,
            action="fetch_complete",
            duration_ms=duration_ms,
            sources=sources_list
        )

        return self.db.get_company(orgnr)

    # =========================================================================
    # ASYNC API (high performance)
    # =========================================================================

    async def get_company_async(self, orgnr: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get complete company data using parallel async fetching.

        Performance: ~4-6s vs ~12s for sync (when all sources are needed)

        Priority:
        1. Return cached if fresh (unless force_refresh)
        2. Parallel fetch: Bolagsverket + Allabolag
        3. Merge and cache results
        """
        orgnr = orgnr.replace('-', '')
        start_time = time.perf_counter()

        # 1. Check cache
        if not force_refresh and self.db.is_cache_fresh(orgnr, self.cache_ttl):
            cached = self.db.get_company(orgnr)
            if cached:
                cached['_meta'] = {
                    'from_cache': True,
                    'fetched_at': cached.get('updated_at')
                }
                logger.info(
                    f"Cache hit for {orgnr}",
                    orgnr=orgnr,
                    action="cache_hit",
                    duration_ms=(time.perf_counter() - start_time) * 1000
                )
                return cached

        # 2. Parallel fetch from sources
        result = {
            'orgnr': orgnr,
            '_meta': {
                'from_cache': False,
                'fetched_at': datetime.now().isoformat(),
                'sources': {},
                'async': True
            }
        }

        # Fetch both sources in parallel
        bv_task = self._fetch_bolagsverket_async(orgnr)
        ab_task = self._fetch_allabolag_async(orgnr)

        results = await asyncio.gather(bv_task, ab_task, return_exceptions=True)

        # Process results
        bv_data = results[0] if not isinstance(results[0], Exception) else None
        ab_data = results[1] if not isinstance(results[1], Exception) else None

        # Log any errors
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning(f"Async fetch error for task {i}: {r}", orgnr=orgnr, action="async_error")

        # 3. Merge results
        if bv_data:
            result.update(bv_data)
            result['_meta']['sources']['basic'] = 'bolagsverket'

        if ab_data:
            result = self._merge_data(result, ab_data, prefer_existing=['name', 'orgnr', 'status'])
            result['_meta']['sources']['board'] = 'allabolag'
            result['_meta']['sources']['financials'] = 'allabolag'

        # 4. Validate
        if not result.get('name'):
            logger.warning(f"No data found for {orgnr}", orgnr=orgnr, action="not_found")
            return None

        # 5. Save sources before storing (store removes _meta)
        sources_used = list(result.get('_meta', {}).get('sources', {}).values())

        # 6. Store in cache
        self._store_in_db(result)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Async fetched {orgnr}",
            orgnr=orgnr,
            action="async_fetch_complete",
            duration_ms=duration_ms,
            sources=sources_used
        )

        return self.db.get_company(orgnr)

    async def enrich_batch_async(
        self,
        orgnrs: List[str],
        max_workers: int = None,
        progress_callback: Callable[[int, int, str], None] = None,
        force_refresh: bool = False
    ) -> Dict[str, Optional[Dict]]:
        """
        Enrich multiple companies in parallel.

        Performance: 10 companies in ~12-16s vs ~120s sync

        Args:
            orgnrs: List of organization numbers
            max_workers: Max parallel workers (default from config)
            progress_callback: Optional callback(current, total, orgnr)
            force_refresh: Force refresh from sources (bypass cache)

        Returns:
            Dict mapping orgnr -> company data or None
        """
        max_workers = max_workers or Config.BATCH_PARALLEL_WORKERS
        semaphore = asyncio.Semaphore(max_workers)
        results = {}
        total = len(orgnrs)
        completed = 0

        async def process_one(orgnr: str) -> tuple:
            nonlocal completed
            async with semaphore:
                try:
                    data = await self.get_company_async(orgnr, force_refresh=force_refresh)
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, orgnr)
                    return (orgnr, data)
                except Exception as e:
                    logger.error(f"Batch error for {orgnr}: {e}", orgnr=orgnr, action="batch_error")
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, orgnr)
                    return (orgnr, None)

        start_time = time.perf_counter()
        logger.info(f"Starting batch enrichment of {total} companies", action="batch_start", count=total)

        # Process all in parallel (limited by semaphore)
        tasks = [process_one(orgnr) for orgnr in orgnrs]
        batch_results = await asyncio.gather(*tasks)

        for orgnr, data in batch_results:
            results[orgnr] = data

        duration_ms = (time.perf_counter() - start_time) * 1000
        success_count = sum(1 for v in results.values() if v is not None)

        logger.info(
            f"Batch enrichment complete: {success_count}/{total} successful",
            action="batch_complete",
            duration_ms=duration_ms,
            success_count=success_count,
            total_count=total
        )

        return results

    # =========================================================================
    # ASYNC FETCH METHODS (with circuit breaker protection)
    # =========================================================================

    async def _fetch_bolagsverket_async(self, orgnr: str) -> Optional[Dict]:
        """Async fetch from Bolagsverket VDM API with circuit breaker."""
        # Get circuit breaker if available
        breaker = get_circuit_breaker("bolagsverket") if get_circuit_breaker else None

        try:
            # Check if circuit is open
            if breaker and not breaker.can_execute():
                logger.warning(
                    f"Circuit open for bolagsverket, skipping fetch",
                    orgnr=orgnr,
                    action="circuit_open"
                )
                breaker.record_rejection()
                return None

            # Run sync method in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.bolagsverket.get_company,
                orgnr
            )

            # Record success
            if breaker:
                breaker.record_success()

            return result

        except Exception as e:
            # Record failure
            if breaker:
                breaker.record_failure()

            logger.warning(f"Bolagsverket async fetch error: {e}", orgnr=orgnr, action="bv_error")
            return None

    async def _fetch_allabolag_async(self, orgnr: str) -> Optional[Dict]:
        """Async fetch from Allabolag scraper with circuit breaker."""
        # Get circuit breaker if available
        breaker = get_circuit_breaker("allabolag") if get_circuit_breaker else None

        try:
            # Check if circuit is open
            if breaker and not breaker.can_execute():
                logger.warning(
                    f"Circuit open for allabolag, skipping fetch",
                    orgnr=orgnr,
                    action="circuit_open"
                )
                breaker.record_rejection()
                return None

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.allabolag.scrape_company,
                orgnr
            )

            # Record success
            if breaker:
                breaker.record_success()

            return result

        except Exception as e:
            # Record failure
            if breaker:
                breaker.record_failure()

            logger.warning(f"Allabolag async fetch error: {e}", orgnr=orgnr, action="ab_error")
            return None

    # =========================================================================
    # SYNC FETCH METHODS (original)
    # =========================================================================

    def _fetch_bolagsverket(self, orgnr: str) -> Optional[Dict]:
        """Fetch from Bolagsverket VDM API"""
        try:
            return self.bolagsverket.get_company(orgnr)
        except Exception as e:
            logger.warning(f"Bolagsverket fetch error: {e}", orgnr=orgnr, action="bv_error")
            return None

    def _fetch_allabolag(self, orgnr: str) -> Optional[Dict]:
        """Fetch from Allabolag scraper"""
        try:
            return self.allabolag.scrape_company(orgnr)
        except Exception as e:
            logger.warning(f"Allabolag fetch error: {e}", orgnr=orgnr, action="ab_error")
            return None

    # =========================================================================
    # DATA PROCESSING METHODS
    # =========================================================================

    def _merge_data(self, base: Dict, new: Dict, prefer_existing: List[str] = None) -> Dict:
        """Merge data from multiple sources"""
        prefer_existing = prefer_existing or []

        for key, value in new.items():
            if key.startswith('_'):
                continue

            if key in prefer_existing and base.get(key):
                continue

            if value is not None:
                if isinstance(value, list) and key in base and isinstance(base[key], list):
                    # Merge lists (e.g., financials, roles)
                    base[key].extend(value)
                else:
                    base[key] = value

        return base

    def _store_in_db(self, data: Dict):
        """
        Store enriched data in database with full history tracking.

        Uses store_company_complete() which:
        1. Snapshots existing data before any update (for history)
        2. Stores all data in a single atomic transaction
        3. Handles roles, financials, etc.
        """
        orgnr = data['orgnr']

        # Extract meta (not stored in main tables)
        meta = data.pop('_meta', {})

        # Extract nested data that goes to separate tables
        roles = data.pop('roles', None)
        financials = data.pop('financials', None)
        industries = data.pop('industries', None)
        trademarks = data.pop('trademarks', None)
        related_companies = data.pop('related_companies', None)
        announcements = data.pop('announcements', None)

        # Add source tracking from meta
        data['source_basic'] = meta.get('sources', {}).get('basic')
        data['source_board'] = meta.get('sources', {}).get('board')
        data['source_financials'] = meta.get('sources', {}).get('financials')

        # Use store_company_complete() with properly separated data
        try:
            self.db.store_company_complete(
                company_data=data,
                roles=roles,
                financials=financials,
                industries=industries,
                trademarks=trademarks,
                related_companies=related_companies,
                announcements=announcements
            )
            logger.info(f"Stored complete data with history for {orgnr}", orgnr=orgnr, action="db_store")
        except Exception as e:
            logger.error(f"Error storing data for {orgnr}: {e}", orgnr=orgnr, action="db_store_error")
            raise

    # =========================================================================
    # SYNC BATCH & SEARCH (backward compatible)
    # =========================================================================

    def enrich_batch(self, orgnrs: List[str],
                     progress_callback=None) -> Dict[str, Optional[Dict]]:
        """
        Enrich multiple companies (sync version).

        For better performance, use enrich_batch_async().
        """
        if Config.ENABLE_ASYNC_FETCH:
            try:
                return asyncio.run(self.enrich_batch_async(orgnrs, progress_callback=progress_callback))
            except RuntimeError:
                pass

        # Fallback to sync
        results = {}
        total = len(orgnrs)

        for i, orgnr in enumerate(orgnrs):
            try:
                results[orgnr] = self._get_company_sync(orgnr)
            except Exception as e:
                logger.error(f"Error enriching {orgnr}: {e}", orgnr=orgnr, action="enrich_error")
                results[orgnr] = None

            if progress_callback:
                progress_callback(i + 1, total, orgnr)

            # Small delay between companies
            if i < total - 1:
                time.sleep(Config.BATCH_INTER_DELAY)

        return results

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Search across sources"""
        # First check local DB
        local_results = self.db.search_companies(query=query, limit=limit)

        if len(local_results) >= limit:
            return local_results

        # Search external sources
        try:
            ab_results = self.allabolag.search(query, limit=limit)

            # Merge results
            seen_orgnrs = {r['orgnr'] for r in local_results}
            for r in ab_results:
                if r['orgnr'] not in seen_orgnrs:
                    local_results.append(r)
                    seen_orgnrs.add(r['orgnr'])
        except Exception as e:
            logger.warning(f"External search error: {e}", action="search_error")

        return local_results[:limit]

    def get_summary(self, orgnr: str) -> Optional[Dict]:
        """Get quick summary without full enrichment"""
        orgnr = orgnr.replace('-', '')

        # Try cache first
        company = self.db.get_company(orgnr)
        if company:
            return self._format_summary(company)

        # Quick fetch
        company = self.get_company(orgnr)
        if company:
            return self._format_summary(company)

        return None

    def _format_summary(self, company: Dict) -> Dict:
        """Format company data as summary"""
        # Find VD and chairman
        vd = None
        chairman = None
        for role in company.get('roles', []):
            if role.get('role_type') in ['Verkställande direktör', 'VD']:
                vd = role.get('name')
            elif role.get('role_type') in ['Styrelseordförande', 'Ordförande']:
                chairman = role.get('name')

        # Get latest financials
        latest_fin = None
        for fin in company.get('financials', []):
            if not fin.get('is_consolidated'):
                latest_fin = fin
                break

        return {
            'orgnr': company.get('orgnr'),
            'name': company.get('name'),
            'company_type': company.get('company_type'),
            'status': company.get('status'),
            'founded': company.get('foundation_year'),
            'municipality': company.get('postal_city'),
            'key_persons': {
                'ceo': vd,
                'chairman': chairman
            },
            'key_figures': {
                'revenue': company.get('revenue'),
                'profit': company.get('net_profit'),
                'employees': company.get('num_employees'),
                'equity_ratio': company.get('equity_ratio'),
                'return_on_equity': company.get('return_on_equity')
            } if latest_fin else None,
            'board_size': len([r for r in company.get('roles', []) if r.get('role_category') == 'BOARD'])
        }


# Singleton orchestrator
_orchestrator = None

def get_orchestrator(**kwargs) -> DataOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DataOrchestrator(**kwargs)
    return _orchestrator
