#!/usr/bin/env python3
"""
Test Bolagsverket med undetected-chromedriver
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_bolagsverket():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║   Bolagsverket - undetected-chromedriver Test                 ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")

    print("🚀 Startar undetected Chrome...")
    
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--headless')  # Kommentera bort för debug
    
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    try:
        print("📄 Navigerar till poit.bolagsverket.se...")
        driver.get("https://poit.bolagsverket.se")
        
        # Vänta på sidan
        time.sleep(5)
        
        # Kolla om CAPTCHA finns
        page_source = driver.page_source
        
        if "What code is in the image" in page_source:
            print("⚠️  CAPTCHA detekterad!")
            driver.save_screenshot("/tmp/uc_captcha.png")
            print("📸 Screenshot: /tmp/uc_captcha.png")
        else:
            print("✅ Ingen CAPTCHA! Bot-protection passerad!")
            driver.save_screenshot("/tmp/uc_success.png")
            print("📸 Screenshot: /tmp/uc_success.png")
        
        print(f"\n📍 URL: {driver.current_url}")
        print(f"📝 Titel: {driver.title}")
        
        # Visa lite av HTML:en
        print(f"\n📄 HTML-längd: {len(page_source)} tecken")
        
        # Kolla efter sökformulär eller innehåll
        if "kungörelse" in page_source.lower() or "bolagsverket" in page_source.lower():
            print("✅ Verkar vara inne på rätt sida!")
        
        # Vänta lite så vi kan inspektera
        print("\n⏳ Väntar 10 sekunder för inspektion...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Fel: {e}")
        driver.save_screenshot("/tmp/uc_error.png")
        
    finally:
        driver.quit()
        print("\n✅ Browser stängd")

if __name__ == "__main__":
    test_bolagsverket()
