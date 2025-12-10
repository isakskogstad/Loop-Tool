#!/usr/bin/env python3
"""
XBRL Backfill Script

Downloads and processes annual reports for all tracked companies.
Can also process specific companies or use locally downloaded files.

Usage:
    # Process all companies in database
    python scripts/backfill_xbrl.py

    # Process specific company
    python scripts/backfill_xbrl.py 5566599766

    # Process from local test files
    python scripts/backfill_xbrl.py --local

    # Dry run (show what would be processed)
    python scripts/backfill_xbrl.py --dry-run
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.supabase_client import get_database
from src.parsers import XBRLParser, parse_annual_report, ParseError
from src.xbrl_storage import get_xbrl_storage


def process_local_files(directory: str, dry_run: bool = False) -> dict:
    """
    Process local ZIP files from a directory.

    Args:
        directory: Path to directory with ZIP files
        dry_run: If True, only show what would be processed

    Returns:
        Processing results
    """
    storage = get_xbrl_storage()
    parser = XBRLParser()
    results = {
        "processed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }

    zip_files = list(Path(directory).glob("*.zip"))
    print(f"Found {len(zip_files)} ZIP files in {directory}")

    for zip_file in zip_files:
        print(f"\nProcessing: {zip_file.name}")

        if dry_run:
            print(f"  [DRY RUN] Would process {zip_file}")
            results["skipped"] += 1
            continue

        try:
            # Parse the file
            try:
                parse_result = parser.parse_zip_file(str(zip_file))
            except ParseError as e:
                print(f"  ERROR: Parse failed - {e}")
                results["failed"] += 1
                results["errors"].append(f"{zip_file.name}: {str(e)}")
                continue

            # Extract company info
            company_info = parse_result.company_info
            if not company_info or not company_info.orgnr:
                print(f"  ERROR: No company info found")
                results["failed"] += 1
                continue

            print(f"  Company: {company_info.name} ({company_info.orgnr})")
            print(f"  Fiscal Year: {company_info.fiscal_year_end.year if company_info.fiscal_year_end else 'N/A'}")
            print(f"  Facts: {len(parse_result.all_facts)}")

            # Store in database
            report_id = storage.store_annual_report(
                parse_result,
                document_id=zip_file.stem  # Use filename as document ID
            )

            if report_id:
                print(f"  Stored: {report_id}")
                results["processed"] += 1
            else:
                print(f"  ERROR: Failed to store")
                results["failed"] += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            results["failed"] += 1
            results["errors"].append(f"{zip_file.name}: {str(e)}")

    return results


async def process_from_api(
    orgnrs: list = None,
    years: int = 5,
    batch_size: int = 50,
    concurrency: int = 5,
    dry_run: bool = False
) -> dict:
    """
    Process companies by downloading from Bolagsverket VDM API.

    Args:
        orgnrs: Specific orgnrs to process (None = all companies)
        years: Number of years per company
        batch_size: Companies per batch
        concurrency: Concurrent requests
        dry_run: Show what would be processed

    Returns:
        Processing results
    """
    from src.annual_report_sync import get_annual_report_sync

    db = get_database()
    sync_service = get_annual_report_sync()

    # Get companies to process
    if orgnrs:
        companies = orgnrs
    else:
        result = db.client.table("companies").select("orgnr").execute()
        companies = [c["orgnr"] for c in result.data] if result.data else []

    print(f"Processing {len(companies)} companies ({years} years each)")

    if dry_run:
        print("\n[DRY RUN] Would process:")
        for i, orgnr in enumerate(companies[:20]):
            print(f"  {i+1}. {orgnr}")
        if len(companies) > 20:
            print(f"  ... and {len(companies) - 20} more")
        return {"dry_run": True, "count": len(companies)}

    # Process
    results = await sync_service.sync_batch(
        companies,
        years=years,
        concurrency=concurrency
    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Backfill XBRL data from annual reports"
    )
    parser.add_argument(
        "orgnrs",
        nargs="*",
        help="Specific organization numbers to process"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Process local files from test_annual_reports directory"
    )
    parser.add_argument(
        "--local-dir",
        type=str,
        default="test_annual_reports/documents",
        help="Directory with local ZIP files"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Number of years per company (default: 5)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Companies per batch (default: 50)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Concurrent requests (default: 5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making changes"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("XBRL Backfill Script")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    if args.local:
        # Process local files
        local_dir = project_root / args.local_dir
        if not local_dir.exists():
            print(f"ERROR: Directory not found: {local_dir}")
            sys.exit(1)

        results = process_local_files(str(local_dir), dry_run=args.dry_run)
    else:
        # Process from API
        results = asyncio.run(
            process_from_api(
                orgnrs=args.orgnrs if args.orgnrs else None,
                years=args.years,
                batch_size=args.batch_size,
                concurrency=args.concurrency,
                dry_run=args.dry_run
            )
        )

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    for key, value in results.items():
        if key != "errors":
            print(f"  {key}: {value}")

    if results.get("errors"):
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results["errors"][:10]:
            print(f"  - {error}")
        if len(results["errors"]) > 10:
            print(f"  ... and {len(results['errors']) - 10} more")

    print(f"\nCompleted: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
