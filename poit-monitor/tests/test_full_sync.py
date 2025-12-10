#!/usr/bin/env python3
"""Kör fullständig POIT sync mot databas"""

import sys
import asyncio
sys.path.insert(0, '/Users/isak/Downloads/files (3)')

from dotenv import load_dotenv
load_dotenv('/Users/isak/Downloads/files (3)/.env')

from src.poit_monitor import POITMonitorService

async def main():
    print("=" * 60)
    print("POIT Fullständig Sync Test")
    print("=" * 60)

    service = POITMonitorService(debug=True)

    # Kör sync - INTE dry_run
    result = await service.run_sync(
        categories=["konkurser"],  # Bara konkurser för test
        limit_per_category=5,  # Max 5 per kategori
        dry_run=False  # Skriv till databas!
    )

    print("\n" + "=" * 60)
    print("RESULTAT:")
    print("=" * 60)
    print(f"Sync ID: {result.get('sync_id')}")
    print(f"Status: {result.get('status')}")
    print(f"Nya kungörelser: {result.get('announcements_new', 0)}")
    print(f"Matchningar: {result.get('matches_found', 0)}")
    print(f"Notifikationer skapade: {result.get('notifications_created', 0)}")

    if result.get('errors'):
        print(f"\nFel: {result['errors']}")

    print("\n✅ Sync klar!")

if __name__ == "__main__":
    asyncio.run(main())
