"""
Annual Report Sync Service

Downloads and processes annual reports from Bolagsverket's VDM API.
Uses the BolagsverketVDMClient with OAuth2 authentication.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from .scrapers.bolagsverket_vdm import BolagsverketVDMClient, get_bolagsverket_vdm_client
from .parsers import XBRLParser, ParseError
from .xbrl_storage import XBRLStorage, get_xbrl_storage
from .supabase_client import get_database

logger = logging.getLogger(__name__)


class AnnualReportSyncService:
    """Service for syncing annual reports from Bolagsverket."""

    # Rate limiting constants for Bolagsverket VDM API
    # IMPORTANT: Bolagsverket has strict rate limits - keep these conservative!
    VDM_REQUEST_DELAY = 5.0  # Seconds between each VDM API call (increased from 3)
    VDM_BATCH_SIZE = 10  # Companies per batch (conservative)
    VDM_CONCURRENCY = 1  # MUST be 1 - sequential processing to avoid 429 errors
    VDM_MAX_CONCURRENCY = 1  # Hard limit - do not allow override above this

    def __init__(
        self,
        vdm_client: Optional[BolagsverketVDMClient] = None,
        storage: Optional[XBRLStorage] = None
    ):
        self.vdm = vdm_client or get_bolagsverket_vdm_client()
        self.storage = storage or get_xbrl_storage()
        self.parser = XBRLParser()
        self.db = get_database()

    async def sync_company(
        self,
        orgnr: str,
        years: Optional[int] = 5,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Sync annual reports for a single company.

        Args:
            orgnr: Organization number
            years: Number of years to sync (default 5)
            force: Re-download even if already processed

        Returns:
            Dict with sync results
        """
        results = {
            "orgnr": orgnr,
            "reports_found": 0,
            "reports_processed": 0,
            "reports_failed": 0,
            "errors": [],
        }

        try:
            # Get available documents from VDM API (uses OAuth2)
            documents = await self.vdm.get_document_list_async(orgnr)

            if not documents:
                logger.info(f"No annual reports found for {orgnr}")
                return results

            # Filter by years if specified
            if years:
                current_year = datetime.now().year
                min_year = current_year - years
                documents = [
                    doc for doc in documents
                    if self._extract_fiscal_year(doc) and self._extract_fiscal_year(doc) >= min_year
                ]

            results["reports_found"] = len(documents)

            for doc in documents:
                # VDM API uses 'dokumentId' (Swedish spelling)
                doc_id = doc.get("dokumentId") or doc.get("documentId") or doc.get("id")
                fiscal_year = self._extract_fiscal_year(doc)

                if not fiscal_year:
                    logger.warning(f"Could not determine fiscal year for doc {doc_id}")
                    continue

                # Check if already processed
                if not force:
                    existing = self.storage.get_annual_report(orgnr, fiscal_year)
                    if existing and existing.get("processing_status") == "processed":
                        logger.debug(f"Skipping already processed {orgnr}/{fiscal_year}")
                        continue

                # Download and process
                try:
                    zip_content = await self.vdm.download_document_async(doc_id)

                    if not zip_content:
                        results["errors"].append(f"Failed to download {doc_id}")
                        results["reports_failed"] += 1
                        continue

                    # Parse the document
                    try:
                        parse_result = self.parser.parse_zip_bytes(zip_content)
                    except ParseError as e:
                        results["errors"].append(
                            f"Parse failed for {orgnr}/{fiscal_year}: {str(e)}"
                        )
                        results["reports_failed"] += 1
                        continue

                    # Verify we got company info
                    if not parse_result.company_info or not parse_result.company_info.orgnr:
                        results["errors"].append(
                            f"No company info extracted for {orgnr}/{fiscal_year}"
                        )
                        results["reports_failed"] += 1
                        continue

                    # Store in database
                    report_id = self.storage.store_annual_report(
                        parse_result,
                        document_id=doc_id
                    )

                    if report_id:
                        results["reports_processed"] += 1
                        logger.info(f"Processed {orgnr}/{fiscal_year}")
                    else:
                        results["reports_failed"] += 1
                        results["errors"].append(f"Storage failed for {orgnr}/{fiscal_year}")

                except Exception as e:
                    results["errors"].append(f"Error processing {doc_id}: {str(e)}")
                    results["reports_failed"] += 1
                    logger.error(f"Error processing annual report {doc_id}: {e}")

        except Exception as e:
            results["errors"].append(f"Sync error: {str(e)}")
            logger.error(f"Error syncing company {orgnr}: {e}")

        return results

    async def sync_batch(
        self,
        orgnrs: List[str],
        years: int = 3,
        concurrency: int = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Sync annual reports for multiple companies.

        Args:
            orgnrs: List of organization numbers
            years: Number of years per company
            concurrency: Max concurrent requests (CAPPED to VDM_MAX_CONCURRENCY=1)
            force: Re-process even if already done

        Returns:
            Aggregated results
        """
        # Use class constant if not specified, and ENFORCE max limit
        if concurrency is None:
            concurrency = self.VDM_CONCURRENCY
        else:
            # Cap concurrency to avoid 429 errors - Bolagsverket has strict limits
            if concurrency > self.VDM_MAX_CONCURRENCY:
                logger.warning(
                    f"Requested concurrency={concurrency} exceeds max={self.VDM_MAX_CONCURRENCY}. "
                    f"Using {self.VDM_MAX_CONCURRENCY} to avoid 429 rate limiting."
                )
                concurrency = self.VDM_MAX_CONCURRENCY

        results = {
            "total_companies": len(orgnrs),
            "companies_processed": 0,
            "total_reports_found": 0,
            "total_reports_processed": 0,
            "total_reports_failed": 0,
            "errors": [],
        }

        semaphore = asyncio.Semaphore(concurrency)

        async def process_with_semaphore(orgnr: str):
            async with semaphore:
                # Add delay between VDM API calls to avoid 429 rate limiting
                await asyncio.sleep(self.VDM_REQUEST_DELAY)
                return await self.sync_company(orgnr, years=years, force=force)

        # Process in parallel with semaphore
        tasks = [process_with_semaphore(orgnr) for orgnr in orgnrs]
        company_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in company_results:
            if isinstance(result, Exception):
                results["errors"].append(str(result))
                continue

            results["companies_processed"] += 1
            results["total_reports_found"] += result.get("reports_found", 0)
            results["total_reports_processed"] += result.get("reports_processed", 0)
            results["total_reports_failed"] += result.get("reports_failed", 0)
            results["errors"].extend(result.get("errors", []))

        return results

    async def sync_all_tracked_companies(
        self,
        years: int = 3,
        batch_size: int = None,
        concurrency: int = None
    ) -> Dict[str, Any]:
        """
        Sync annual reports for all companies in the database.

        Args:
            years: Number of years per company
            batch_size: Companies per batch (defaults to VDM_BATCH_SIZE)
            concurrency: Concurrent requests per batch (defaults to VDM_CONCURRENCY)

        Returns:
            Aggregated results
        """
        # Use class constants if not specified
        if batch_size is None:
            batch_size = self.VDM_BATCH_SIZE
        if concurrency is None:
            concurrency = self.VDM_CONCURRENCY

        # Get all tracked company orgnrs
        all_companies = self.db.client.table("companies").select("orgnr").execute()
        orgnrs = [c["orgnr"] for c in all_companies.data] if all_companies.data else []

        logger.info(f"Starting sync for {len(orgnrs)} companies (batch_size={batch_size}, concurrency={concurrency})")

        total_results = {
            "total_companies": len(orgnrs),
            "companies_processed": 0,
            "total_reports_found": 0,
            "total_reports_processed": 0,
            "total_reports_failed": 0,
            "batches_completed": 0,
            "errors": [],
        }

        # Process in batches
        for i in range(0, len(orgnrs), batch_size):
            batch = orgnrs[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(orgnrs) + batch_size - 1) // batch_size

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} companies)")

            batch_results = await self.sync_batch(
                batch,
                years=years,
                concurrency=concurrency
            )

            total_results["companies_processed"] += batch_results["companies_processed"]
            total_results["total_reports_found"] += batch_results["total_reports_found"]
            total_results["total_reports_processed"] += batch_results["total_reports_processed"]
            total_results["total_reports_failed"] += batch_results["total_reports_failed"]
            total_results["batches_completed"] += 1

            # Limit error accumulation
            if len(total_results["errors"]) < 100:
                total_results["errors"].extend(batch_results["errors"][:10])

            # Brief pause between batches to respect rate limits
            await asyncio.sleep(1)

        return total_results

    def _extract_fiscal_year(self, doc: Dict[str, Any]) -> Optional[int]:
        """Extract fiscal year from document metadata."""
        import re

        # Try VDM API specific fields first (Swedish)
        # VDM returns: rapporteringsperiodTom (reporting period end date)
        for field in ["rapporteringsperiodTom", "rapporteringsperiodFrom", "rakenskapsarSlut", "rakenskapsarStart"]:
            if field in doc and doc[field]:
                try:
                    val = doc[field]
                    # Handle YYYY-MM-DD format
                    if isinstance(val, str) and len(val) >= 4:
                        return int(val[:4])
                    elif isinstance(val, int):
                        return val
                except (ValueError, TypeError):
                    pass

        # Try English field names
        for field in ["fiscalYear", "fiscal_year", "year"]:
            if field in doc and doc[field]:
                try:
                    val = doc[field]
                    if isinstance(val, str) and len(val) >= 4:
                        return int(val[:4])
                    elif isinstance(val, int):
                        return val
                except (ValueError, TypeError):
                    pass

        # Try date fields (Swedish and English)
        for date_field in ["slutdatum", "periodEnd", "period_end", "endDate", "end_date"]:
            if date_field in doc and doc[date_field]:
                try:
                    date_str = str(doc[date_field])
                    if len(date_str) >= 4:
                        return int(date_str[:4])
                except (ValueError, TypeError):
                    pass

        # Try document name/title (Swedish and English)
        for name_field in ["dokumentnamn", "name", "title"]:
            if name_field in doc and doc[name_field]:
                match = re.search(r"20\d{2}", str(doc[name_field]))
                if match:
                    return int(match.group())

        # Try dokumentId which may contain year
        if "dokumentId" in doc:
            match = re.search(r"20\d{2}", str(doc["dokumentId"]))
            if match:
                return int(match.group())

        return None


def get_annual_report_sync() -> AnnualReportSyncService:
    """
    Get sync service instance.

    Note: Creates a new instance each time to ensure fresh credentials
    are picked up (important when env vars are added after server start).
    """
    return AnnualReportSyncService()


# CLI entry point
async def main():
    """CLI entry point for manual sync."""
    import sys

    sync = get_annual_report_sync()

    if len(sys.argv) > 1:
        # Sync specific company
        orgnr = sys.argv[1]
        years = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        print(f"Syncing annual reports for {orgnr} ({years} years)")
        result = await sync.sync_company(orgnr, years=years)
        print(f"Result: {result}")
    else:
        # Sync all tracked companies
        print("Syncing annual reports for all tracked companies...")
        result = await sync.sync_all_tracked_companies()
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
