#!/usr/bin/env python3
"""
Daily Sync Script for Loop-Auto API
====================================
Full synchronization that works exactly like regular API enrichment:
- Fetches from both Bolagsverket VDM and Allabolag
- Creates history snapshots before updates
- Stores all data: roles, financials, industries, etc.

Run manually:
    python scripts/daily_sync.py

Or via GitHub Actions (daily at 05:00 UTC)
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - both console and file
LOG_FILE = "daily_sync.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode='w')  # Overwrite each run
    ]
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BOLAGSVERKET_CLIENT_ID = os.getenv("BOLAGSVERKET_CLIENT_ID")
BOLAGSVERKET_CLIENT_SECRET = os.getenv("BOLAGSVERKET_CLIENT_SECRET")

# Rate limiting: Be gentle with external sources
# Allabolag scraping needs delays to avoid blocks
REQUEST_DELAY = 2.0  # seconds between companies (both sources)
BATCH_SIZE = 10  # Process in small batches


def validate_config():
    """Validate required environment variables."""
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not BOLAGSVERKET_CLIENT_ID:
        missing.append("BOLAGSVERKET_CLIENT_ID")
    if not BOLAGSVERKET_CLIENT_SECRET:
        missing.append("BOLAGSVERKET_CLIENT_SECRET")

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    return True


async def run_xbrl_sync(companies: list) -> dict:
    """
    Sync XBRL annual reports for all companies.

    This downloads and parses iXBRL reports from Bolagsverket's VDM API.
    """
    logger.info("-" * 60)
    logger.info("XBRL ANNUAL REPORTS SYNC")
    logger.info("-" * 60)

    try:
        from src.annual_report_sync import get_annual_report_sync
    except ImportError as e:
        logger.warning(f"XBRL sync not available: {e}")
        return {"skipped": True, "reason": str(e)}

    sync_service = get_annual_report_sync()
    orgnrs = [c.get("orgnr") for c in companies if c.get("orgnr")]

    logger.info(f"Syncing XBRL reports for {len(orgnrs)} companies (3 years each)")

    try:
        # Use default class constants (VDM_CONCURRENCY=1, VDM_REQUEST_DELAY=3.0)
        # This ensures we don't hit Bolagsverket's rate limits
        results = await sync_service.sync_batch(
            orgnrs,
            years=3
            # concurrency defaults to VDM_CONCURRENCY (1) with 3-second delays
        )

        logger.info(f"XBRL sync completed:")
        logger.info(f"  Companies processed: {results.get('companies_processed', 0)}")
        logger.info(f"  Reports found: {results.get('total_reports_found', 0)}")
        logger.info(f"  Reports processed: {results.get('total_reports_processed', 0)}")
        logger.info(f"  Reports failed: {results.get('total_reports_failed', 0)}")

        if results.get("errors"):
            logger.warning(f"  XBRL errors: {len(results['errors'])}")
            for err in results["errors"][:5]:
                logger.warning(f"    - {err}")

        return results

    except Exception as e:
        logger.error(f"XBRL sync failed: {e}")
        return {"error": str(e)}


async def run_daily_sync():
    """
    Main sync function using the same orchestrator as regular API.

    This ensures:
    - History snapshots are created before updates
    - All data is stored correctly (roles, financials, industries, etc.)
    - Data merging works the same as regular enrichment
    - XBRL annual reports are synced from Bolagsverket VDM API
    """
    logger.info("=" * 60)
    logger.info("DAILY SYNC STARTED (Full Enrichment Mode)")
    logger.info(f"Time: {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)

    # Validate configuration
    if not validate_config():
        sys.exit(1)

    # Import after validation (these require env vars)
    try:
        from src.supabase_client import get_db
        from src.orchestrator import DataOrchestrator
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you're running from the project root directory")
        sys.exit(1)

    # Initialize
    db = get_db()
    orchestrator = DataOrchestrator(db=db)

    # Get all companies from database
    try:
        response = db.client.table("companies").select("orgnr, name").execute()
        companies = response.data or []
    except Exception as e:
        logger.error(f"Failed to fetch companies: {e}")
        sys.exit(1)

    total_companies = len(companies)
    logger.info(f"Found {total_companies} companies in database")
    logger.info(f"Estimated time: ~{total_companies * REQUEST_DELAY / 60:.1f} minutes")
    logger.info("-" * 60)

    # Stats
    stats = {
        "total": total_companies,
        "processed": 0,
        "updated": 0,
        "unchanged": 0,
        "errors": 0,
        "not_found": 0
    }

    start_time = time.time()

    # Process companies
    for i, company in enumerate(companies, 1):
        orgnr = company.get("orgnr")
        name = company.get("name", "Unknown")

        try:
            # Rate limiting between companies
            if i > 1:
                await asyncio.sleep(REQUEST_DELAY)

            # Progress logging
            if i % 25 == 0 or i == 1:
                elapsed = time.time() - start_time
                remaining = (total_companies - i) * REQUEST_DELAY
                logger.info(
                    f"Progress: {i}/{total_companies} ({i/total_companies*100:.1f}%) - "
                    f"Elapsed: {elapsed/60:.1f}m - Remaining: ~{remaining/60:.1f}m"
                )

            # Get current data to compare later
            current = db.get_company(orgnr)
            current_roles_count = len(current.get("roles", [])) if current else 0
            current_financials_count = len(current.get("financials", [])) if current else 0

            # Full enrichment using orchestrator (same as API)
            # force_refresh=True ensures we fetch fresh data
            result = await orchestrator.get_company_async(orgnr, force_refresh=True)

            stats["processed"] += 1

            if not result:
                logger.warning(f"  {orgnr}: Not found in any source - {name}")
                stats["not_found"] += 1
                continue

            # Check if data changed
            new_roles_count = len(result.get("roles", []))
            new_financials_count = len(result.get("financials", []))

            # Simple change detection (more comprehensive than before)
            changes = []
            if current:
                if current.get("name") != result.get("name"):
                    changes.append(f"name: {current.get('name')} -> {result.get('name')}")
                if current.get("status") != result.get("status"):
                    changes.append(f"status: {current.get('status')} -> {result.get('status')}")
                if current_roles_count != new_roles_count:
                    changes.append(f"roles: {current_roles_count} -> {new_roles_count}")
                if current_financials_count != new_financials_count:
                    changes.append(f"financials: {current_financials_count} -> {new_financials_count}")
                if current.get("address") != result.get("address"):
                    changes.append(f"address changed")

            if changes:
                stats["updated"] += 1
                logger.info(f"  {orgnr}: UPDATED - {name}")
                for change in changes:
                    logger.info(f"    {change}")
            else:
                stats["unchanged"] += 1
                # Only log every 50th unchanged company to reduce noise
                if stats["unchanged"] % 50 == 0:
                    logger.debug(f"  {orgnr}: unchanged - {name}")

        except Exception as e:
            stats["errors"] += 1
            logger.error(f"  {orgnr}: Error - {e}")

    # Final report
    elapsed_total = time.time() - start_time
    logger.info("=" * 60)
    logger.info("DAILY SYNC COMPLETED")
    logger.info(f"Duration: {elapsed_total/60:.1f} minutes ({elapsed_total:.0f} seconds)")
    logger.info(f"Total companies: {stats['total']}")
    logger.info(f"Processed: {stats['processed']}")
    logger.info(f"Updated: {stats['updated']}")
    logger.info(f"Unchanged: {stats['unchanged']}")
    logger.info(f"Not found: {stats['not_found']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 60)

    # Exit with error code if too many failures
    error_rate = stats["errors"] / max(stats["total"], 1)
    if error_rate > 0.1:  # More than 10% errors
        logger.error(f"Too many errors during sync! ({error_rate*100:.1f}%)")
        sys.exit(1)

    # ============================================================
    # XBRL Annual Reports Sync
    # ============================================================
    # Sync XBRL data from Bolagsverket VDM API after regular sync
    xbrl_results = await run_xbrl_sync(companies)

    # Log XBRL results
    if xbrl_results.get("skipped"):
        logger.info(f"XBRL sync skipped: {xbrl_results.get('reason', 'unknown')}")
    elif xbrl_results.get("error"):
        logger.error(f"XBRL sync error: {xbrl_results.get('error')}")
    else:
        logger.info("XBRL sync completed successfully")


def main():
    """Entry point."""
    try:
        asyncio.run(run_daily_sync())
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
