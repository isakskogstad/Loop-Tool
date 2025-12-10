#!/usr/bin/env python3
"""Test av POIT scraper med undetected-chromedriver"""

import sys
sys.path.insert(0, '/Users/isak/Downloads/files (3)')

from src.scrapers.poit_scraper import POITScraper

print("=" * 60)
print("Test: POIT Scraper med undetected-chromedriver")
print("=" * 60)

with POITScraper(headless=False, debug=True) as scraper:
    print("\n📊 Hämtar statistik...")
    stats = scraper.get_daily_stats()

    if stats:
        print(f"\n✅ Lyckades! Totalt: {stats.total_count} kungörelser")
        for key, cat in list(stats.categories.items())[:5]:
            print(f"   {cat.name}: {cat.count}")

        # Spara screenshot
        scraper.screenshot("/tmp/poit_uc_test.png")
        print(f"\n📸 Screenshot: /tmp/poit_uc_test.png")
    else:
        print("\n❌ Kunde inte hämta statistik")
        scraper.screenshot("/tmp/poit_uc_fail.png")
        print(f"📸 Screenshot: /tmp/poit_uc_fail.png")

print("\n✅ Test klart!")
