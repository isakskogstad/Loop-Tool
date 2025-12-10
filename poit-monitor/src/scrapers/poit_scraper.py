#!/usr/bin/env python3
"""
POIT Scraper med undetected-chromedriver

Scrapar Post- och Inrikes Tidningar (POIT) från Bolagsverket.
Använder undetected-chromedriver för att passera bot-protection.

Kräver: pip install undetected-chromedriver selenium
"""

import re
import hashlib
import time
from datetime import datetime, date
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Dependencies missing. Run: pip install undetected-chromedriver selenium")
    raise


@dataclass
class POITAnnouncement:
    """En kungörelse från POIT"""
    poit_id: Optional[str] = None
    category: str = ""
    subcategory: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    announcement_date: str = ""
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
    r'\b(\d{6}[-–]\d{4})\b',
    r'\b(\d{10})\b',
    r'\b(16\d{10})\b',
]


def extract_orgnrs(text: str) -> List[str]:
    """
    Extraherar svenska organisationsnummer från text.

    Returns:
        Lista med unika orgnr normaliserade till format NNNNNN-NNNN
    """
    if not text:
        return []

    found = set()

    for pattern in ORGNR_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            clean = match.replace('-', '').replace('–', '')

            if len(clean) == 12 and clean.startswith('16'):
                clean = clean[2:]

            if len(clean) == 10 and clean[0] in '123456789':
                normalized = f"{clean[:6]}-{clean[6:]}"
                found.add(normalized)

    return sorted(list(found))


def generate_content_hash(category: str, title: str, content: str, date_str: str) -> str:
    """Genererar SHA256-hash för deduplicering"""
    combined = f"{category}|{title or ''}|{content or ''}|{date_str}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:32]


class POITScraper:
    """
    Scraper för POIT med undetected-chromedriver.

    Exempel:
        with POITScraper() as scraper:
            stats = scraper.get_daily_stats()
            results = scraper.scrape_category("konkurser", limit=50)
    """

    BASE_URL = "https://poit.bolagsverket.se"
    APP_URL = f"{BASE_URL}/poit-app/"

    CATEGORIES = {
        "kallelser": "1",
        "bolagsverkets_registreringar": "2",
        "konkurser": "3",
        "familjeratt": "4",
        "skuldsaneringar": "5",
    }

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

    def __init__(self, headless: bool = False, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.driver = None
        self._ready = False
        self._last_stats: Dict[str, CategoryStats] = {}

    def _log(self, msg: str):
        if self.debug:
            print(f"[POITScraper] {msg}")

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def initialize(self) -> bool:
        """Startar webbläsaren och navigerar till POIT."""
        self._log("Startar undetected-chromedriver...")

        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')

        if self.headless:
            options.add_argument('--headless=new')

        try:
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self._log("Browser startad")

            self.driver.get(self.APP_URL)
            time.sleep(5)

            if "What code is in the image" in self.driver.page_source:
                self._log("❌ CAPTCHA detekterad")
                return False

            self._ready = True
            self._log("✅ Initierad")
            return True

        except Exception as e:
            self._log(f"❌ Initialiseringsfel: {e}")
            return False

    def close(self):
        """Stänger webbläsaren."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self._ready = False
            self._log("Stängd")

    def get_daily_stats(self) -> Optional[POITDailyStats]:
        """Hämtar dagens statistik från POIT-startsidan."""
        if not self._ready:
            return None

        try:
            if "/poit-app/" not in self.driver.current_url:
                self.driver.get(self.APP_URL)
                time.sleep(3)

            stats = POITDailyStats(timestamp=datetime.now().isoformat())

            links = self.driver.find_elements(
                By.CSS_SELECTOR,
                "a.kungorelser__link, a.kungorelser__link--sub"
            )

            for link in links:
                try:
                    href = link.get_attribute("href") or ""

                    name_spans = link.find_elements(By.CSS_SELECTOR, "span.bg-white")
                    badge_spans = link.find_elements(By.CSS_SELECTOR, "span.badge")

                    if name_spans and badge_spans:
                        name = name_spans[0].text.strip()
                        count_text = badge_spans[0].text.strip()

                        if name and count_text.isdigit():
                            count = int(count_text)
                            key = self._normalize_key(name)

                            cat_stats = CategoryStats(name=name, count=count, url=href)
                            stats.categories[key] = cat_stats
                            stats.total_count += count
                            self._last_stats[key] = cat_stats
                except:
                    continue

            if not stats.categories:
                self._log("Fallback till HTML-parsing")
                html = self.driver.page_source
                stats = self._parse_stats_from_html(html)

            self._log(f"Hämtade {len(stats.categories)} kategorier, totalt {stats.total_count}")
            return stats

        except Exception as e:
            self._log(f"Fel vid hämtning av statistik: {e}")
            return None

    def _normalize_key(self, name: str) -> str:
        """Normaliserar kategorinamn till nyckel."""
        key = name.lower()
        key = key.replace('å', 'a').replace('ä', 'a').replace('ö', 'o')
        key = re.sub(r'[^a-z0-9]', '_', key)
        key = re.sub(r'_+', '_', key)
        return key.strip('_')

    def _parse_stats_from_html(self, html: str) -> POITDailyStats:
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

    def scrape_category(
        self,
        category_key: str,
        limit: int = 100,
        include_content: bool = True
    ) -> ScrapeResult:
        """
        Scrapar kungörelser från en specifik kategori.

        Args:
            category_key: Kategori-nyckel (t.ex. "konkurser")
            limit: Max antal att hämta
            include_content: Om detaljerat innehåll ska hämtas

        Returns:
            ScrapeResult med hittade kungörelser
        """
        if not self._ready:
            return ScrapeResult(success=False, category=category_key, error="Not initialized")

        try:
            # Gå till startsidan först (Angular-appen kräver klick, inte direkt URL)
            if "/poit-app/" not in self.driver.current_url or "#" in self.driver.current_url:
                self.driver.get(self.APP_URL)
                time.sleep(3)

            # Hitta kategori-länken och klicka
            self._log(f"Scrapar {category_key}: letar efter länk...")

            # Hämta stats om vi inte har dem (för att få URL)
            if not self._last_stats:
                self.get_daily_stats()

            cat = self._last_stats.get(category_key)
            clicked = False

            if cat and cat.url:
                # Försök klicka på länken via JavaScript (mer tillförlitligt)
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, f'a[href*="{cat.url.split("#")[0].split("/")[-1]}"]')
                    if links:
                        links[0].click()
                        clicked = True
                        time.sleep(4)
                except:
                    pass

            if not clicked:
                # Fallback: hitta länk baserat på text
                try:
                    # Hitta länk med kategorinamnet
                    name_map = {
                        "konkurser": "Konkurser",
                        "bolagsverkets_registreringar": "Bolagsverkets registreringar",
                        "kallelser": "Kallelser",
                        "skuldsaneringar": "Skuldsaneringar",
                        "familjeratt": "Familjerätt"
                    }
                    link_text = name_map.get(category_key, category_key)
                    links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, link_text)
                    if links:
                        links[0].click()
                        clicked = True
                        time.sleep(4)
                except Exception as e:
                    self._log(f"Kunde inte klicka på länk: {e}")

            self._log(f"Nuvarande URL: {self.driver.current_url}")

            announcements = []
            today = date.today().isoformat()

            # Vänta på att resultaten laddas
            time.sleep(2)

            # Försök hitta resultat i tabell
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table tbody tr, .search-result-item, .result-row, .list-group-item, .kungorelse-item"
            )

            self._log(f"Hittade {len(rows)} rader")

            # Samla först alla URLs och basinfo från tabellen
            row_data = []
            for row in rows[:limit]:
                try:
                    text = row.text.strip()
                    if not text or len(text) < 10:
                        continue

                    # Hitta länk till detaljsida
                    detail_url = None
                    title = None
                    try:
                        link_el = row.find_element(By.CSS_SELECTOR, "a")
                        detail_url = link_el.get_attribute("href")
                        title = link_el.text.strip()
                    except:
                        pass

                    row_data.append({
                        "text": text,
                        "title": title,
                        "detail_url": detail_url,
                        "html": row.get_attribute("outerHTML")[:500]
                    })
                except:
                    continue

            self._log(f"Samlade {len(row_data)} poster med URLs")

            # Besök varje detaljsida för att hämta orgnr
            # OBS: Angular-appen kräver klick för navigation - driver.get fungerar inte
            for i, data in enumerate(row_data):
                try:
                    orgnrs = []
                    detail_content = None

                    if data["detail_url"]:
                        # Hitta och klicka på länken med denna URL
                        try:
                            # Hitta länk via href
                            link_selector = f'a[href="{data["detail_url"].replace(self.BASE_URL, "")}"]'
                            links = self.driver.find_elements(By.CSS_SELECTOR, link_selector)

                            if not links:
                                # Fallback: hitta via title
                                links = self.driver.find_elements(By.LINK_TEXT, data["title"])

                            if links:
                                links[0].click()
                                time.sleep(2)

                                body = self.driver.find_element(By.TAG_NAME, "body")
                                detail_content = body.text
                                orgnrs = extract_orgnrs(detail_content)

                                # Gå tillbaka
                                self.driver.back()
                                time.sleep(2)

                        except Exception as nav_e:
                            self._log(f"Navigation fel: {nav_e}")

                    poit_id = generate_content_hash(category_key, data["title"] or "", data["text"], today)

                    ann = POITAnnouncement(
                        poit_id=poit_id,
                        category=category_key,
                        title=data["title"],
                        content=detail_content[:2000] if detail_content else data["text"][:2000],
                        announcement_date=today,
                        source_url=data["detail_url"] or self.driver.current_url,
                        extracted_orgnrs=orgnrs,
                        raw_html=data["html"]
                    )
                    announcements.append(ann)

                    if (i + 1) % 10 == 0:
                        self._log(f"Bearbetat {i + 1}/{len(row_data)} poster")

                except Exception as e:
                    self._log(f"Fel vid hämtning av detaljer för rad {i}: {e}")
                    continue

            # Fallback: extrahera orgnr från hela sidan
            if not announcements:
                announcements = self._scrape_generic_results(category_key, today, limit)

            return ScrapeResult(
                success=True,
                category=category_key,
                announcements=announcements,
                total_found=len(announcements)
            )

        except Exception as e:
            return ScrapeResult(
                success=False,
                category=category_key,
                error=str(e)
            )

    def _parse_announcement_row(
        self,
        row,
        category: str,
        date_str: str,
        fetch_details: bool = True
    ) -> Optional[POITAnnouncement]:
        """Parsar en rad till POITAnnouncement."""
        try:
            text = row.text
            if not text or len(text.strip()) < 10:
                return None

            text = text.strip()
            html = row.get_attribute("outerHTML") or ""

            # Försök extrahera titel (första kolumnen = kungörelse-id)
            title = None
            detail_url = None
            try:
                link_el = row.find_element(By.CSS_SELECTOR, "a")
                title = link_el.text.strip() if link_el else None
                detail_url = link_el.get_attribute("href")
            except:
                try:
                    title_el = row.find_element(By.CSS_SELECTOR, "td:first-child")
                    title = title_el.text.strip() if title_el else None
                except:
                    pass

            # Extrahera orgnr - måste hämta från detaljsidan
            orgnrs = []
            detail_content = None

            if fetch_details and detail_url:
                try:
                    # Spara nuvarande URL
                    list_url = self.driver.current_url

                    # Gå till detaljsidan
                    self.driver.get(detail_url)
                    time.sleep(2)

                    # Hämta sidans text
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    detail_content = body.text

                    # Extrahera orgnr
                    orgnrs = extract_orgnrs(detail_content)

                    # Gå tillbaka till listan
                    self.driver.get(list_url)
                    time.sleep(2)

                except Exception as e:
                    self._log(f"Kunde inte hämta detaljer: {e}")

            # Fallback: försök extrahera från radtexten
            if not orgnrs:
                orgnrs = extract_orgnrs(text)

            poit_id = generate_content_hash(category, title or "", text, date_str)

            return POITAnnouncement(
                poit_id=poit_id,
                category=category,
                title=title,
                content=detail_content[:2000] if detail_content else (text[:2000] if len(text) > 2000 else text),
                announcement_date=date_str,
                source_url=detail_url or self.driver.current_url,
                extracted_orgnrs=orgnrs,
                raw_html=html[:1000] if len(html) > 1000 else html
            )

        except Exception:
            return None

    def _scrape_generic_results(
        self,
        category: str,
        date_str: str,
        limit: int
    ) -> List[POITAnnouncement]:
        """Generisk scraping när specifika selektorer inte fungerar."""
        announcements = []

        try:
            # Hämta text från huvudinnehåll
            try:
                content_area = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "main, .content, #content, .search-results"
                )
            except:
                content_area = self.driver.find_element(By.TAG_NAME, "body")

            full_text = content_area.text
            orgnrs = extract_orgnrs(full_text or "")

            if orgnrs:
                for orgnr in orgnrs[:limit]:
                    poit_id = generate_content_hash(category, orgnr, "", date_str)
                    announcements.append(POITAnnouncement(
                        poit_id=poit_id,
                        category=category,
                        title=f"Kungörelse för {orgnr}",
                        content=None,
                        announcement_date=date_str,
                        source_url=self.driver.current_url,
                        extracted_orgnrs=[orgnr]
                    ))

        except Exception as e:
            self._log(f"Generisk scraping fel: {e}")

        return announcements

    def scrape_all_categories(
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
            result = self.scrape_category(cat, limit=limit_per_category)
            results[cat] = result
            time.sleep(2)

        return results

    def screenshot(self, path: str) -> bool:
        """Tar en screenshot av nuvarande sida."""
        if self.driver:
            self.driver.save_screenshot(path)
            return True
        return False

    def get_page_source(self) -> str:
        """Returnerar sidans HTML."""
        return self.driver.page_source if self.driver else ""

    def get_current_url(self) -> str:
        """Returnerar aktuell URL."""
        return self.driver.current_url if self.driver else ""


# ============================================================
# Convenience-funktioner
# ============================================================

def get_todays_poit_stats() -> Optional[Dict]:
    """Snabbfunktion för att hämta dagens POIT-statistik."""
    with POITScraper(headless=True) as scraper:
        stats = scraper.get_daily_stats()
        return stats.to_dict() if stats else None


def scrape_category(category: str, limit: int = 50) -> List[Dict]:
    """Snabbfunktion för att scrapa en kategori."""
    with POITScraper(headless=True) as scraper:
        result = scraper.scrape_category(category, limit=limit)
        return [a.to_dict() for a in result.announcements]


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("POIT Scraper Test (undetected-chromedriver)")
    print("=" * 60)

    with POITScraper(headless=False, debug=True) as scraper:
        # Hämta statistik
        print("\n📊 Hämtar dagens statistik...")
        stats = scraper.get_daily_stats()

        if stats:
            print(f"\nTotalt: {stats.total_count} kungörelser")
            for key, cat in stats.categories.items():
                print(f"  {cat.name}: {cat.count}")

        # Testa scraping av konkurser
        print("\n📋 Scrapar konkurser...")
        result = scraper.scrape_category("konkurser", limit=10)

        if result.success:
            print(f"Hittade {result.total_found} kungörelser")
            for ann in result.announcements[:3]:
                print(f"  - {ann.title or 'Ingen titel'}")
                if ann.extracted_orgnrs:
                    print(f"    Orgnr: {', '.join(ann.extracted_orgnrs)}")
        else:
            print(f"Fel: {result.error}")

        # Screenshot
        scraper.screenshot("/tmp/poit_scraper_test.png")
        print("\n📸 Screenshot: /tmp/poit_scraper_test.png")

    print("\n✅ Klar!")
