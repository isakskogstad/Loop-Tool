#!/usr/bin/env python3
"""
POIT Playwright Scraper - Async browser automation för GitHub Actions

Scrapar Post- och Inrikes Tidningar (POIT) från Bolagsverket.
Designad för headless körning i GitHub Actions med Playwright.

Kräver: pip install playwright
         playwright install chromium
"""

import asyncio
import re
import hashlib
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    raise


@dataclass
class POITAnnouncement:
    """En kungörelse från POIT"""
    poit_id: Optional[str] = None
    category: str = ""
    subcategory: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    announcement_date: str = ""  # ISO format
    source_url: Optional[str] = None
    extracted_orgnrs: List[str] = field(default_factory=list)
    raw_html: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CategoryStats:
    """Statistik för en POIT-kategori"""
    name: str
    count: int
    url: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class POITDailyStats:
    """Dagens statistik från POIT"""
    timestamp: str
    categories: Dict[str, CategoryStats] = field(default_factory=dict)
    total_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "total_count": self.total_count
        }


@dataclass
class ScrapeResult:
    """Resultat från en scrape-operation"""
    success: bool
    category: str
    announcements: List[POITAnnouncement] = field(default_factory=list)
    total_found: int = 0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "category": self.category,
            "announcements": [a.to_dict() for a in self.announcements],
            "total_found": self.total_found,
            "error": self.error
        }


# Regex för svenska organisationsnummer
ORGNR_PATTERNS = [
    r'\b(\d{6}[-–]\d{4})\b',           # 556920-1998
    r'\b(\d{10})\b',                     # 5569201998
    r'\b(16\d{10})\b',                   # 165569201998 (med sekelsiffra)
]


def extract_orgnrs(text: str) -> List[str]:
    """
    Extraherar svenska organisationsnummer från text.
    
    Stödjer format:
    - 556920-1998 (med bindestreck)
    - 5569201998 (utan bindestreck)
    - 165569201998 (med sekelsiffra)
    
    Returns:
        Lista med unika orgnr normaliserade till format NNNNNN-NNNN
    """
    if not text:
        return []
    
    found = set()
    
    for pattern in ORGNR_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            # Normalisera till 10-siffrig form utan bindestreck
            clean = match.replace('-', '').replace('–', '')
            
            # Ta bort sekelsiffra om 12 siffror
            if len(clean) == 12 and clean.startswith('16'):
                clean = clean[2:]
            
            # Validera längd
            if len(clean) == 10:
                # Formatera med bindestreck
                normalized = f"{clean[:6]}-{clean[6:]}"
                
                # Enkel validering: första siffran ska vara 1-9
                if clean[0] in '123456789':
                    found.add(normalized)
    
    return sorted(list(found))


def generate_content_hash(category: str, title: str, content: str, date_str: str) -> str:
    """Genererar SHA256-hash för deduplicering"""
    combined = f"{category}|{title or ''}|{content or ''}|{date_str}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:32]


class POITPlaywrightScraper:
    """
    Async Playwright-baserad scraper för POIT.
    
    Exempel:
        async with POITPlaywrightScraper() as scraper:
            stats = await scraper.get_daily_stats()
            results = await scraper.scrape_category("konkurser", limit=50)
    """
    
    BASE_URL = "https://poit.bolagsverket.se"
    APP_URL = f"{BASE_URL}/poit-app/"
    
    # Kategori-mappning till URL-segment
    CATEGORIES = {
        "kallelser": "1",
        "bolagsverkets_registreringar": "2",
        "konkurser": "3",
        "familjeratt": "4",
        "skuldsaneringar": "5",
    }
    
    # Subkategorier
    SUBCATEGORIES = {
        "kallelse_pa_borgenarer": "1/1",
        "aktiebolagsregistret": "2/4",
        "foreningsregistret": "2/10",
        "handelsregistret": "2/11",
        "konkursbeslut": "3/20",
        "utdelningsforslag": "3/16",
        "bodelning": "4/24",
        "forvaltarskap": "4/26",
    }
    
    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
    
    def _log(self, msg: str):
        if self.debug:
            print(f"[POITScraper] {msg}")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self) -> bool:
        """Startar Playwright och navigerar till POIT."""
        try:
            self._playwright = await async_playwright().start()
            
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self._page = await context.new_page()
            
            # Navigera till POIT
            self._log("Navigerar till POIT...")
            await self._page.goto(self.APP_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)
            
            # Kolla om CAPTCHA
            content = await self._page.content()
            if "What code is in the image" in content:
                self._log("❌ CAPTCHA detekterad")
                return False
            
            self._log("✅ Initierad")
            return True
            
        except Exception as e:
            self._log(f"❌ Initialiseringsfel: {e}")
            return False
    
    async def close(self):
        """Stänger browser och frigör resurser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._log("Stängd")
    
    async def get_daily_stats(self) -> Optional[POITDailyStats]:
        """
        Hämtar dagens statistik från POIT-startsidan.
        
        Returns:
            POITDailyStats med antal per kategori
        """
        if not self._page:
            return None
        
        try:
            # Se till att vi är på startsidan
            if "/poit-app/" not in self._page.url:
                await self._page.goto(self.APP_URL, wait_until='networkidle')
                await asyncio.sleep(2)
            
            stats = POITDailyStats(timestamp=datetime.now().isoformat())
            
            # Hitta alla kategori-länkar med badge
            links = await self._page.query_selector_all("a.kungorelser__link, a.kungorelser__link--sub")
            
            for link in links:
                try:
                    href = await link.get_attribute("href") or ""
                    
                    # Hitta namn och antal
                    name_el = await link.query_selector("span.bg-white")
                    badge_el = await link.query_selector("span.badge")
                    
                    if name_el and badge_el:
                        name = (await name_el.text_content() or "").strip()
                        count_text = (await badge_el.text_content() or "").strip()
                        
                        if name and count_text.isdigit():
                            key = self._normalize_key(name)
                            count = int(count_text)
                            
                            stats.categories[key] = CategoryStats(
                                name=name,
                                count=count,
                                url=href
                            )
                            stats.total_count += count
                            
                except Exception:
                    continue
            
            # Fallback: parsa HTML
            if not stats.categories:
                html = await self._page.content()
                stats = await self._parse_stats_from_html(html)
            
            self._log(f"Hämtade {len(stats.categories)} kategorier, totalt {stats.total_count}")
            return stats
            
        except Exception as e:
            self._log(f"Fel vid hämtning av statistik: {e}")
            return None
    
    def _normalize_key(self, name: str) -> str:
        """Normaliserar kategorinamn till nyckel."""
        key = name.lower()
        # Ersätt svenska tecken
        key = key.replace('å', 'a').replace('ä', 'a').replace('ö', 'o')
        key = re.sub(r'[^a-z0-9]', '_', key)
        key = re.sub(r'_+', '_', key)
        return key.strip('_')
    
    async def _parse_stats_from_html(self, html: str) -> POITDailyStats:
        """Parsar statistik från HTML som fallback."""
        stats = POITDailyStats(timestamp=datetime.now().isoformat())
        
        pattern = r'class="[^"]*bg-white[^"]*">([^<]+)</span><span[^>]*class="[^"]*badge[^"]*">(\d+)</span>'
        matches = re.findall(pattern, html)
        
        for name, count in matches:
            name = name.strip()
            if 2 < len(name) < 60:
                key = self._normalize_key(name)
                count_int = int(count)
                stats.categories[key] = CategoryStats(name=name, count=count_int, url="")
                stats.total_count += count_int
        
        return stats
    
    async def scrape_category(
        self, 
        category_key: str, 
        limit: int = 100,
        include_content: bool = True
    ) -> ScrapeResult:
        """
        Scrapar kungörelser från en specifik kategori.
        
        Args:
            category_key: Kategori-nyckel (t.ex. "konkurser", "bolagsverkets_registreringar")
            limit: Max antal att hämta
            include_content: Om detaljerat innehåll ska hämtas
        
        Returns:
            ScrapeResult med hittade kungörelser
        """
        if not self._page:
            return ScrapeResult(success=False, category=category_key, error="Not initialized")
        
        # Bygg URL
        category_id = self.CATEGORIES.get(category_key) or self.SUBCATEGORIES.get(category_key)
        if not category_id:
            return ScrapeResult(
                success=False, 
                category=category_key, 
                error=f"Unknown category: {category_key}"
            )
        
        url = f"{self.APP_URL}urval-senaste-publiceringar/{category_id}#search"
        
        try:
            self._log(f"Scrapar {category_key}: {url}")
            await self._page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            announcements = []
            today = date.today().isoformat()
            
            # Försök hitta resultat i olika format
            # Format 1: Tabell med resultat
            rows = await self._page.query_selector_all("table tbody tr, .search-result-item, .result-row")
            
            for i, row in enumerate(rows[:limit]):
                try:
                    ann = await self._parse_announcement_row(row, category_key, today)
                    if ann:
                        announcements.append(ann)
                except Exception as e:
                    self._log(f"Fel vid parsing av rad {i}: {e}")
                    continue
            
            # Om inga resultat i tabell, försök andra selektorer
            if not announcements:
                # Försök med generisk parsing
                announcements = await self._scrape_generic_results(category_key, today, limit)
            
            return ScrapeResult(
                success=True,
                category=category_key,
                announcements=announcements,
                total_found=len(announcements)
            )
            
        except PlaywrightTimeout:
            return ScrapeResult(
                success=False,
                category=category_key,
                error="Timeout vid navigering"
            )
        except Exception as e:
            return ScrapeResult(
                success=False,
                category=category_key,
                error=str(e)
            )
    
    async def _parse_announcement_row(
        self, 
        row, 
        category: str, 
        date_str: str
    ) -> Optional[POITAnnouncement]:
        """Parsar en rad till POITAnnouncement."""
        try:
            text = await row.text_content()
            if not text or len(text.strip()) < 10:
                return None
            
            text = text.strip()
            html = await row.inner_html()
            
            # Extrahera orgnr
            orgnrs = extract_orgnrs(text)
            
            # Försök extrahera titel (första raden eller fetstil)
            title_el = await row.query_selector("strong, b, .title, td:first-child")
            title = None
            if title_el:
                title = (await title_el.text_content() or "").strip()
            
            # Generera ID baserat på innehåll
            poit_id = generate_content_hash(category, title or "", text, date_str)
            
            return POITAnnouncement(
                poit_id=poit_id,
                category=category,
                title=title,
                content=text[:2000] if len(text) > 2000 else text,
                announcement_date=date_str,
                source_url=self._page.url,
                extracted_orgnrs=orgnrs,
                raw_html=html[:1000] if len(html) > 1000 else html
            )
            
        except Exception:
            return None
    
    async def _scrape_generic_results(
        self, 
        category: str, 
        date_str: str, 
        limit: int
    ) -> List[POITAnnouncement]:
        """Generisk scraping när specifika selektorer inte fungerar."""
        announcements = []
        
        try:
            # Hämta allt text-innehåll från main content
            content_area = await self._page.query_selector("main, .content, #content, .search-results")
            if not content_area:
                content_area = await self._page.query_selector("body")
            
            if content_area:
                full_text = await content_area.text_content()
                
                # Dela upp på organisationsnummer för att hitta separata poster
                orgnrs = extract_orgnrs(full_text or "")
                
                if orgnrs:
                    # Skapa en announcement per unikt orgnr
                    for orgnr in orgnrs[:limit]:
                        poit_id = generate_content_hash(category, orgnr, "", date_str)
                        announcements.append(POITAnnouncement(
                            poit_id=poit_id,
                            category=category,
                            title=f"Kungörelse för {orgnr}",
                            content=None,
                            announcement_date=date_str,
                            source_url=self._page.url,
                            extracted_orgnrs=[orgnr]
                        ))
        
        except Exception as e:
            self._log(f"Generisk scraping fel: {e}")
        
        return announcements
    
    async def scrape_all_categories(
        self,
        categories: Optional[List[str]] = None,
        limit_per_category: int = 100
    ) -> Dict[str, ScrapeResult]:
        """
        Scrapar alla (eller angivna) kategorier.
        
        Args:
            categories: Lista med kategorier att scrapa (None = alla)
            limit_per_category: Max antal per kategori
        
        Returns:
            Dict med kategori -> ScrapeResult
        """
        if categories is None:
            categories = list(self.CATEGORIES.keys())
        
        results = {}
        
        for cat in categories:
            self._log(f"Scrapar kategori: {cat}")
            result = await self.scrape_category(cat, limit=limit_per_category)
            results[cat] = result
            
            # Paus mellan kategorier för att undvika rate limiting
            await asyncio.sleep(2)
        
        return results
    
    async def screenshot(self, path: str) -> bool:
        """Tar en screenshot av nuvarande sida."""
        if self._page:
            await self._page.screenshot(path=path, full_page=True)
            return True
        return False


# ============================================================
# Convenience-funktioner
# ============================================================

async def get_todays_poit_stats() -> Optional[Dict]:
    """
    Snabbfunktion för att hämta dagens POIT-statistik.
    
    Returns:
        Dict med statistik eller None vid fel
    """
    async with POITPlaywrightScraper(headless=True) as scraper:
        stats = await scraper.get_daily_stats()
        return stats.to_dict() if stats else None


async def scrape_category(category: str, limit: int = 50) -> List[Dict]:
    """
    Snabbfunktion för att scrapa en kategori.
    
    Args:
        category: Kategori att scrapa
        limit: Max antal
    
    Returns:
        Lista med kungörelser som dict
    """
    async with POITPlaywrightScraper(headless=True) as scraper:
        result = await scraper.scrape_category(category, limit=limit)
        return [a.to_dict() for a in result.announcements]


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("POIT Playwright Scraper - Test")
        print("=" * 60)
        
        async with POITPlaywrightScraper(headless=True, debug=True) as scraper:
            # Hämta statistik
            print("\n📊 Hämtar dagens statistik...")
            stats = await scraper.get_daily_stats()
            
            if stats:
                print(f"\nTotalt: {stats.total_count} kungörelser")
                for key, cat in stats.categories.items():
                    print(f"  {cat.name}: {cat.count}")
            
            # Testa scraping av konkurser
            print("\n📋 Scrapar konkurser...")
            result = await scraper.scrape_category("konkurser", limit=10)
            
            if result.success:
                print(f"Hittade {result.total_found} kungörelser")
                for ann in result.announcements[:3]:
                    print(f"  - {ann.title or 'Ingen titel'}")
                    if ann.extracted_orgnrs:
                        print(f"    Orgnr: {', '.join(ann.extracted_orgnrs)}")
            else:
                print(f"Fel: {result.error}")
            
            # Screenshot
            await scraper.screenshot("/tmp/poit_test.png")
            print("\n📸 Screenshot: /tmp/poit_test.png")
        
        print("\n✅ Klar!")
    
    asyncio.run(main())
