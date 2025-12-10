#!/usr/bin/env python3
"""Test av orgnr-extraktion från kungörelser"""

import sys
import time
sys.path.insert(0, '/Users/isak/Downloads/files (3)')

from src.scrapers.poit_scraper import POITScraper, extract_orgnrs

print("=" * 60)
print("Test: Orgnr-extraktion från kungörelser")
print("=" * 60)

with POITScraper(headless=False, debug=True) as scraper:
    print("\n📋 Scrapar konkurser...")
    result = scraper.scrape_category("konkurser", limit=50)

    if result.success:
        print(f"✅ Hittade {result.total_found} kungörelser")

        all_orgnrs = set()
        for ann in result.announcements:
            if ann.extracted_orgnrs:
                for orgnr in ann.extracted_orgnrs:
                    all_orgnrs.add(orgnr)

        print(f"\n📊 Totalt {len(all_orgnrs)} unika orgnr extraherade:")
        for orgnr in sorted(all_orgnrs)[:10]:
            print(f"   {orgnr}")

        # Visa innehåll för första kungörelser
        print(f"\n📄 Första 3 kungörelsers innehåll:")
        for i, ann in enumerate(result.announcements[:3]):
            print(f"\n--- Kungörelse {i+1} ---")
            print(f"Titel: {ann.title}")
            print(f"Orgnr: {ann.extracted_orgnrs}")
            print(f"Content (100 tecken): {(ann.content or '')[:100]}...")

        # Om inga orgnr, visa raw text för att se vad som finns
        if not all_orgnrs:
            print("\n⚠️ Inga orgnr hittade!")
            print("Visar rådata från första 3 kungörelser:")
            for ann in result.announcements[:3]:
                print(f"\nRaw content:\n{ann.content}")
                print("-" * 40)
    else:
        print(f"❌ Fel: {result.error}")

print("\n✅ Test klart!")
