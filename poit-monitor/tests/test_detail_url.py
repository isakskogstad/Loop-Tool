#!/usr/bin/env python3
"""Test av detaljsidans URL-format"""

import sys
import time
sys.path.insert(0, '/Users/isak/Downloads/files (3)')

from src.scrapers.poit_scraper import POITScraper, extract_orgnrs
from selenium.webdriver.common.by import By

print("=" * 60)
print("Test: Detaljsidans URL")
print("=" * 60)

with POITScraper(headless=False, debug=True) as scraper:
    # Navigera till konkurser
    scraper.get_daily_stats()
    links = scraper.driver.find_elements(By.PARTIAL_LINK_TEXT, "Konkurser")
    if links:
        links[0].click()
        time.sleep(4)

    # Hitta första radens länk
    rows = scraper.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    if rows:
        first_row = rows[0]
        link = first_row.find_element(By.CSS_SELECTOR, "a")
        href = link.get_attribute("href")
        print(f"\n🔗 Första länkens href: {href}")

        # Klicka på länken istället för att navigera direkt
        print("\n🖱️ Klickar på länken...")
        link.click()
        time.sleep(3)

        # Kolla resultatet
        print(f"\n📍 URL efter klick: {scraper.driver.current_url}")

        # Hämta sidans text och sök efter orgnr
        body = scraper.driver.find_element(By.TAG_NAME, "body")
        page_text = body.text

        orgnrs = extract_orgnrs(page_text)
        print(f"\n🔢 Orgnr hittade: {orgnrs}")

        # Visa relevant del av sidans text
        print(f"\n📄 Text (500 tecken):")
        print(page_text[:500])

        scraper.screenshot("/tmp/click_detail.png")
        print("\n📸 Screenshot: /tmp/click_detail.png")

        # Testa att navigera direkt till samma URL
        print(f"\n🔗 Testar direkt navigering till: {href}")
        scraper.driver.get(href)
        time.sleep(3)

        print(f"📍 URL efter direkt nav: {scraper.driver.current_url}")
        body2 = scraper.driver.find_element(By.TAG_NAME, "body")
        page_text2 = body2.text
        orgnrs2 = extract_orgnrs(page_text2)
        print(f"🔢 Orgnr via direkt nav: {orgnrs2}")

        scraper.screenshot("/tmp/direct_nav_detail.png")
        print("📸 Screenshot: /tmp/direct_nav_detail.png")

print("\n✅ Test klart!")
