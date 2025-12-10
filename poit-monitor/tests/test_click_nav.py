#!/usr/bin/env python3
"""Test av klickbaserad navigation i POIT"""

import sys
import time
sys.path.insert(0, '/Users/isak/Downloads/files (3)')

from src.scrapers.poit_scraper import POITScraper

print("=" * 60)
print("Test: Klicka på Konkurser-länk")
print("=" * 60)

with POITScraper(headless=False, debug=True) as scraper:
    print("\n📊 Hämtar stats...")
    stats = scraper.get_daily_stats()

    if stats:
        print(f"✅ Totalt: {stats.total_count}")

        # Testa scrape_category som nu använder klick
        print("\n🔗 Testar scrape_category('konkurser')...")
        result = scraper.scrape_category("konkurser", limit=20)

        print(f"\n📊 Resultat:")
        print(f"   Success: {result.success}")
        print(f"   Total found: {result.total_found}")
        if result.error:
            print(f"   Error: {result.error}")

        if result.announcements:
            print(f"\n📋 Första 3 kungörelser:")
            for ann in result.announcements[:3]:
                print(f"   - {ann.title or 'Ingen titel'}")
                if ann.extracted_orgnrs:
                    print(f"     Orgnr: {', '.join(ann.extracted_orgnrs)}")

        scraper.screenshot("/tmp/click_nav_result.png")
        print(f"\n📸 Screenshot: /tmp/click_nav_result.png")
    else:
        print("❌ Kunde inte hämta statistik")

print("\n✅ Test klart!")
