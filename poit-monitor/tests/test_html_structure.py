#!/usr/bin/env python3
"""Undersök HTML-struktur för att hitta orgnr"""

import sys
import time
sys.path.insert(0, '/Users/isak/Downloads/files (3)')

from src.scrapers.poit_scraper import POITScraper
from selenium.webdriver.common.by import By

print("=" * 60)
print("Undersöker HTML-struktur")
print("=" * 60)

with POITScraper(headless=False, debug=True) as scraper:
    # Navigera till konkurser
    print("\n🔗 Navigerar till konkurser...")
    scraper.get_daily_stats()

    links = scraper.driver.find_elements(By.PARTIAL_LINK_TEXT, "Konkurser")
    if links:
        links[0].click()
        time.sleep(4)

    # Hitta första raden
    rows = scraper.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    if rows:
        first_row = rows[0]
        html = first_row.get_attribute("outerHTML")

        print(f"\n📄 Första radens HTML (2000 tecken):")
        print(html[:2000])

        # Kolla om det finns en länk att klicka för mer info
        links_in_row = first_row.find_elements(By.TAG_NAME, "a")
        print(f"\n🔗 Länkar i raden: {len(links_in_row)}")
        for link in links_in_row:
            print(f"   - href: {link.get_attribute('href')}")
            print(f"     text: {link.text}")

        # Försök klicka på raden för mer info
        if links_in_row:
            print("\n🖱️ Klickar på första länken...")
            links_in_row[0].click()
            time.sleep(3)

            # Kolla nuvarande URL och innehåll
            print(f"\n📍 URL efter klick: {scraper.driver.current_url}")

            # Screenshot av detaljsida
            scraper.screenshot("/tmp/detail_page.png")
            print("📸 Screenshot: /tmp/detail_page.png")

            # Hämta sidans text och sök efter orgnr-mönster
            body = scraper.driver.find_element(By.TAG_NAME, "body")
            page_text = body.text

            # Sök efter orgnr-mönster
            import re
            orgnr_pattern = r'\b(\d{6}[-–]?\d{4})\b'
            orgnrs = re.findall(orgnr_pattern, page_text)
            print(f"\n🔢 Orgnr-mönster funna på sidan: {orgnrs[:10]}")

            print(f"\n📄 Sidans text (första 1000 tecken):")
            print(page_text[:1000])
    else:
        print("❌ Hittade inga rader")

print("\n✅ Undersökning klar!")
