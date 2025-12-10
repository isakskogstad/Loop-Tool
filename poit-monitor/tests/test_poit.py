#!/usr/bin/env python3
"""Quick test of POIT scraper - with better waiting"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    print('🔄 Testar POIT med Playwright...')
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print('📡 Navigerar till POIT...')
        await page.goto('https://poit.bolagsverket.se/poit-app/', timeout=60000)
        
        # Vänta på att sidan laddas
        print('⏳ Väntar på innehåll...')
        await page.wait_for_load_state('networkidle', timeout=30000)
        await asyncio.sleep(3)
        
        # Ta screenshot
        await page.screenshot(path='/tmp/poit_debug.png', full_page=True)
        print('📸 Screenshot: /tmp/poit_debug.png')
        
        # Visa URL och titel
        print(f'🔗 URL: {page.url}')
        print(f'📝 Titel: {await page.title()}')
        
        # Hämta HTML för debugging
        html = await page.content()
        print(f'📄 HTML längd: {len(html)} tecken')
        
        # Kolla om vi träffade CAPTCHA
        if 'What code is in the image' in html:
            print('⚠️ CAPTCHA detekterad!')
        elif 'Välkommen till Post- och Inrikes Tidningar' in html:
            print('✅ Rätt sida laddad!')
            
            # Försök hitta kategorier med regex
            import re
            pattern = r'<span[^>]*class="[^"]*bg-white[^"]*"[^>]*>([^<]+)</span>\s*<span[^>]*class="[^"]*badge[^"]*"[^>]*>(\d+)</span>'
            matches = re.findall(pattern, html)
            
            if matches:
                print(f'\n📊 Hittade {len(matches)} kategorier:')
                for name, count in matches:
                    print(f'   {name.strip()}: {count}')
            else:
                # Alternativ pattern
                pattern2 = r'>([^<]{3,40})</span><span[^>]*badge[^>]*>(\d+)<'
                matches2 = re.findall(pattern2, html)
                if matches2:
                    print(f'\n📊 Hittade {len(matches2)} kategorier (alt):')
                    for name, count in matches2[:10]:
                        print(f'   {name.strip()}: {count}')
        else:
            print('❓ Okänd sida')
            # Spara HTML för debugging
            with open('/tmp/poit_debug.html', 'w') as f:
                f.write(html)
            print('💾 HTML sparad: /tmp/poit_debug.html')
        
        await browser.close()
        print('\n✅ Test klart!')

if __name__ == "__main__":
    asyncio.run(test())
