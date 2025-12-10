#!/usr/bin/env python3
"""Debug: undersök varför kategorisidor inte hittar resultat"""

import sys
import time
sys.path.insert(0, '/Users/isak/Downloads/files (3)')

from src.scrapers.poit_scraper import POITScraper

print("=" * 60)
print("Debug: Undersöker konkurser-sidan")
print("=" * 60)

with POITScraper(headless=False, debug=True) as scraper:
    # Först hämta stats för att se rätt URL
    print("\n📊 Hämtar stats...")
    stats = scraper.get_daily_stats()

    if stats and "konkurser" in stats.categories:
        konkurser = stats.categories["konkurser"]
        print(f"\n✅ Konkurser: {konkurser.count} poster")
        print(f"   URL: {konkurser.url}")

        # Navigera till konkurser-sidan
        print("\n🔗 Navigerar till konkurser...")
        scraper.driver.get(konkurser.url)
        time.sleep(5)

        # Screenshot
        scraper.screenshot("/tmp/debug_konkurser.png")
        print(f"📸 Screenshot: /tmp/debug_konkurser.png")

        # Kolla URL och titel
        print(f"\n📍 Nuvarande URL: {scraper.driver.current_url}")
        print(f"📝 Titel: {scraper.driver.title}")

        # Kolla om 404
        if "404" in scraper.driver.page_source or "finns inte" in scraper.driver.page_source:
            print("⚠️ 404-sida detekterad!")

        # Försök hitta resultat
        from selenium.webdriver.common.by import By
        rows = scraper.driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .search-result-item, .result-row, .list-group-item")
        print(f"\n📋 Hittade {len(rows)} rader")

        if rows:
            for i, row in enumerate(rows[:3]):
                print(f"   Rad {i}: {row.text[:100]}...")
        else:
            # Visa sidans innehåll för debug
            body = scraper.driver.find_element(By.TAG_NAME, "body")
            print(f"\n📄 Sidans text (första 500 tecken):")
            print(body.text[:500])

    else:
        print("❌ Kunde inte hämta statistik")

print("\n✅ Debug klart!")
