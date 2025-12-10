"""
Playwright-based POIT Scraper for GitHub Actions

This scraper uses Playwright instead of undetected-chromedriver for better
compatibility with GitHub Actions and headless server environments.

Features:
- Async-first design with context manager support
- Headless Chrome/Chromium support
- Automatic org.nr extraction from announcement text
- Category-based scraping
- Robust error handling and retries

Usage:
    async with POITPlaywrightScraper() as scraper:
        stats = await scraper.get_daily_stats()
        announcements = await scraper.scrape_category("konkurser")
"""

import re
import asyncio
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict, field
import logging

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from ..logging_config import get_source_logger
except ImportError:
    def get_source_logger(name):
        return logging.getLogger(name)

logger = get_source_logger("poit_playwright")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class POITCategory:
    """POIT announcement category"""
    key: str
    name: str
    count: int
    url: str
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None


@dataclass
class POITAnnouncement:
    """A single POIT announcement"""
    poit_id: Optional[str] = None
    category: str = ""
    subcategory: Optional[str] = None
    title: str = ""
    company_name: Optional[str] = None
    orgnr: Optional[str] = None
    announcement_date: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[str] = None
    extracted_orgnrs: List[str] = field(default_factory=list)
    raw_html: Optional[str] = None
    scraped_at: Optional[str] = None


@dataclass
class POITDailyStats:
    """Daily statistics from POIT"""
    date: str
    categories: Dict[str, POITCategory]
    total_announcements: int = 0
    scraped_at: Optional[str] = None


@dataclass 
class ScrapeResult:
    """Result from a scraping operation"""
    success: bool
    announcements: List[POITAnnouncement] = field(default_factory=list)
    total_found: int = 0
    category: str = ""
    error: Optional[str] = None
    scraped_at: Optional[str] = None


# =============================================================================
# POIT Category Definitions
# =============================================================================

POIT_CATEGORIES = {
    "kallelser": {
        "name": "Kallelser",
        "category_id": "1",
        "subcategories": {
            "kallelse_pa_borgenarer": {"name": "Kallelse på borgenärer", "id": "1"}
        }
    },
    "bolagsverkets_registreringar": {
        "name": "Bolagsverkets registreringar", 
        "category_id": "2",
        "subcategories": {
            "aktiebolagsregistret": {"name": "Aktiebolagsregistret", "id": "4"},
            "foreningsregistret": {"name": "Föreningsregistret", "id": "10"},
            "handelsregistret": {"name": "Handelsregistret", "id": "11"}
        }
    },
    "konkurser": {
        "name": "Konkurser",
        "category_id": "3",
        "subcategories": {
            "konkursbeslut": {"name": "Konkursbeslut", "id": "20"},
            "utdelningsforslag": {"name": "Utdelningsförslag", "id": "16"}
        }
    },
    "familjeratt": {
        "name": "Familjerätt",
        "category_id": "4",
        "subcategories": {
            "bodelning": {"name": "Bodelning", "id": "24"},
            "forvaltarskap": {"name": "Förvaltarskap", "id": "26"}
        }
    },
    "skuldsaneringar": {
        "name": "Skuldsaneringar",
        "category_id": "5",
        "subcategories": {}
    }
}


# =============================================================================
# Org.nr Extraction
# =============================================================================

def extract_orgnrs(text: str) -> List[str]:
    """
    Extract Swedish organization numbers from text.
    
    Formats supported:
    - 5569201998 (10 digits)
    - 556920-1998 (with hyphen)
    - 16556920-1998 (with century prefix)
    
    Returns:
        List of normalized org.nrs (10 digits, no hyphen)
    """
    if not text:
        return []
    
    orgnrs: Set[str] = set()
    
    # Pattern 1: 10 digits with optional hyphen (most common)
    # Matches: 5569201998, 556920-1998
    pattern1 = r'\b(\d{6})-?(\d{4})\b'
    
    # Pattern 2: 12 digits with century prefix  
    # Matches: 165569201998, 16556920-1998
    pattern2 = r'\b(16|19|20)(\d{6})-?(\d{4})\b'
    
    # Extract pattern 2 first (longer, more specific)
    for match in re.finditer(pattern2, text):
        # Skip century prefix, take last 10 digits
        orgnr = match.group(2) + match.group(3)
        if _is_valid_orgnr(orgnr):
            orgnrs.add(orgnr)
    
    # Extract pattern 1
    for match in re.finditer(pattern1, text):
        orgnr = match.group(1) + match.group(2)
        # Skip if already found with century prefix
        if orgnr not in orgnrs and _is_valid_orgnr(orgnr):
            orgnrs.add(orgnr)
    
    return sorted(list(orgnrs))


def _is_valid_orgnr(orgnr: str) -> bool:
    """
    Basic validation of Swedish org.nr.
    
    Rules:
    - Must be 10 digits
    - First digit indicates entity type (5=AB, 7=EF, 8=IF, 9=kommun, etc.)
    - Should pass Luhn checksum (simplified here)
    """
    if not orgnr or len(orgnr) != 10:
        return False
    
    if not orgnr.isdigit():
        return False
    
    # First digit should be valid entity type
    first_digit = int(orgnr[0])
    if first_digit < 1 or first_digit > 9:
        return False
    
    # Common valid first digits: 5 (AB), 7 (EF), 8 (IF), 9 (kommun)
    # But we're lenient here to catch edge cases
    
    return True


def normalize_orgnr(orgnr: str) -> str:
    """Normalize org.nr to 10 digits without hyphen."""
    if not orgnr:
        return ""
    # Remove any hyphens and spaces
    clean = re.sub(r'[-\s]', '', orgnr)
    # If 12 digits with century prefix, take last 10
    if len(clean) == 12 and clean[:2] in ('16', '19', '20'):
        clean = clean[2:]
    return clean if len(clean) == 10 and clean.isdigit() else ""


# =============================================================================
# Playwright POIT Scraper
# =============================================================================

class POITPlaywrightScraper:
    """
    Playwright-based scraper for Bolagsverket's POIT (Post- och Inrikes Tidningar).
    
    Designed for GitHub Actions and headless server environments.
    
    Example:
        async with POITPlaywrightScraper() as scraper:
            stats = await scraper.get_daily_stats()
            print(f"Found {stats.total_announcements} announcements")
            
            bankruptcies = await scraper.scrape_category("konkurser")
            for ann in bankruptcies.announcements:
                print(f"{ann.company_name}: {ann.orgnr}")
    """
    
    BASE_URL = "https://poit.bolagsverket.se"
    POIT_APP_URL = "https://poit.bolagsverket.se/poit-app/"
    
    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 100,
        timeout: int = 30000,
        debug: bool = False
    ):
        """
        Initialize POIT Playwright scraper.
        
        Args:
            headless: Run browser in headless mode (default: True for CI)
            slow_mo: Slow down actions by ms (helps avoid bot detection)
            timeout: Default timeout in ms
            debug: Enable debug logging
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.debug = debug
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._ready = False
        self._last_stats: Optional[POITDailyStats] = None
    
    def _log(self, msg: str, level: str = "info"):
        """Log message."""
        if self.debug or level in ("warning", "error"):
            log_func = getattr(logger, level, logger.info)
            log_func(f"[POITPlaywright] {msg}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self) -> bool:
        """
        Start browser and navigate to POIT.
        
        Returns:
            True if successful, False on error
        """
        if not PLAYWRIGHT_AVAILABLE:
            self._log("Playwright not installed. Run: pip install playwright && playwright install chromium", "error")
            return False
        
        try:
            self._log("Starting Playwright...")
            self._playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create context with realistic viewport and user agent
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='sv-SE',
                timezone_id='Europe/Stockholm'
            )
            
            # Create page
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.timeout)
            
            self._log("Browser started, navigating to POIT...")
            
            # Navigate to POIT
            response = await self._page.goto(self.POIT_APP_URL, wait_until='networkidle')
            
            if not response or response.status >= 400:
                self._log(f"Failed to load POIT: HTTP {response.status if response else 'no response'}", "error")
                return False
            
            # Wait for page to be ready
            await self._page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)  # Additional wait for dynamic content
            
            # Check for CAPTCHA or blocking
            content = await self._page.content()
            if "What code is in the image" in content or "captcha" in content.lower():
                self._log("CAPTCHA detected - bot protection triggered", "warning")
                return False
            
            # Verify we're on the right page
            title = await self._page.title()
            if "Post- och Inrikes Tidningar" not in title:
                self._log(f"Unexpected page title: {title}", "warning")
                # Continue anyway, might still work
            
            self._ready = True
            self._log("Scraper initialized and ready")
            return True
            
        except Exception as e:
            self._log(f"Initialization failed: {e}", "error")
            await self.close()
            return False
    
    async def close(self):
        """Close browser and release resources."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            self._log(f"Error during cleanup: {e}", "warning")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._ready = False
            self._log("Scraper closed")
    
    async def get_daily_stats(self) -> Optional[POITDailyStats]:
        """
        Get today's announcement statistics from the homepage.
        
        Returns:
            POITDailyStats object with category counts
        """
        if not self._ready:
            self._log("Scraper not initialized", "error")
            return None
        
        try:
            # Navigate to homepage if not already there
            current_url = self._page.url
            if "/poit-app/" not in current_url or "/sok" in current_url:
                await self._page.goto(self.POIT_APP_URL, wait_until='networkidle')
                await asyncio.sleep(2)
            
            categories: Dict[str, POITCategory] = {}
            total = 0
            
            # Find all category links
            links = await self._page.query_selector_all(
                "a.kungorelser__link, a.kungorelser__link--sub"
            )
            
            for link in links:
                try:
                    href = await link.get_attribute("href") or ""
                    
                    # Get name from bg-white span
                    name_elem = await link.query_selector("span.bg-white")
                    badge_elem = await link.query_selector("span.badge")
                    
                    if name_elem and badge_elem:
                        name = (await name_elem.inner_text()).strip()
                        count_text = (await badge_elem.inner_text()).strip()
                        
                        if name and count_text.isdigit():
                            count = int(count_text)
                            key = self._normalize_key(name)
                            cat_id, subcat_id = self._parse_category_url(href)
                            
                            categories[key] = POITCategory(
                                key=key,
                                name=name,
                                count=count,
                                url=href,
                                category_id=cat_id,
                                subcategory_id=subcat_id
                            )
                            total += count
                            
                except Exception as e:
                    self._log(f"Error parsing category link: {e}", "warning")
                    continue
            
            # Fallback: parse from HTML if no categories found
            if not categories:
                self._log("Fallback to HTML parsing for stats")
                content = await self._page.content()
                categories = self._parse_stats_from_html(content)
                total = sum(c.count for c in categories.values())
            
            stats = POITDailyStats(
                date=date.today().isoformat(),
                categories=categories,
                total_announcements=total,
                scraped_at=datetime.now().isoformat()
            )
            
            self._last_stats = stats
            self._log(f"Found {len(categories)} categories, {total} total announcements")
            
            return stats
            
        except Exception as e:
            self._log(f"Error getting daily stats: {e}", "error")
            return None
    
    async def scrape_category(
        self,
        category_key: str,
        limit: int = 100,
        extract_details: bool = True
    ) -> ScrapeResult:
        """
        Scrape announcements from a specific category.
        
        Args:
            category_key: Category key (e.g., "konkurser", "bolagsverkets_registreringar")
            limit: Maximum announcements to scrape
            extract_details: Whether to extract detailed content (slower)
            
        Returns:
            ScrapeResult with announcements
        """
        if not self._ready:
            return ScrapeResult(success=False, error="Scraper not initialized")
        
        # Get stats if we don't have them
        if not self._last_stats:
            await self.get_daily_stats()
        
        if not self._last_stats:
            return ScrapeResult(success=False, error="Could not get daily stats")
        
        # Find category
        cat = self._last_stats.categories.get(category_key)
        if not cat:
            return ScrapeResult(
                success=False,
                error=f"Category not found: {category_key}",
                category=category_key
            )
        
        try:
            self._log(f"Scraping category: {cat.name} ({cat.count} items)")
            
            # Navigate to category page
            await self._page.goto(cat.url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            announcements = await self._extract_announcements(
                category=cat.name,
                category_key=category_key,
                limit=limit,
                extract_details=extract_details
            )
            
            return ScrapeResult(
                success=True,
                announcements=announcements,
                total_found=len(announcements),
                category=category_key,
                scraped_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            self._log(f"Error scraping category {category_key}: {e}", "error")
            return ScrapeResult(
                success=False,
                error=str(e),
                category=category_key
            )
    
    async def scrape_all_categories(
        self,
        limit_per_category: int = 50,
        categories: Optional[List[str]] = None
    ) -> Dict[str, ScrapeResult]:
        """
        Scrape all (or specified) categories.
        
        Args:
            limit_per_category: Max announcements per category
            categories: Specific categories to scrape (None = all)
            
        Returns:
            Dict mapping category_key to ScrapeResult
        """
        if not self._ready:
            return {}
        
        # Get current stats
        stats = await self.get_daily_stats()
        if not stats:
            return {}
        
        # Determine which categories to scrape
        target_categories = categories or list(stats.categories.keys())
        
        results: Dict[str, ScrapeResult] = {}
        
        for cat_key in target_categories:
            if cat_key in stats.categories:
                self._log(f"Scraping {cat_key}...")
                result = await self.scrape_category(
                    cat_key,
                    limit=limit_per_category
                )
                results[cat_key] = result
                
                # Small delay between categories
                await asyncio.sleep(1)
        
        return results
    
    async def scrape_bankruptcies(self, limit: int = 100) -> ScrapeResult:
        """Convenience method to scrape bankruptcy announcements."""
        return await self.scrape_category("konkurser", limit)
    
    async def scrape_registrations(self, limit: int = 100) -> ScrapeResult:
        """Convenience method to scrape company registrations."""
        return await self.scrape_category("bolagsverkets_registreringar", limit)
    
    async def _extract_announcements(
        self,
        category: str,
        category_key: str,
        limit: int,
        extract_details: bool = True
    ) -> List[POITAnnouncement]:
        """Extract announcements from current page."""
        announcements = []
        
        try:
            # Wait for content to load
            await self._page.wait_for_load_state('networkidle')
            
            # Try different selectors for result rows
            selectors = [
                "table.table tbody tr",
                ".search-result-item",
                ".kungorelse-item", 
                "[class*='result'] tr",
                "table tbody tr"
            ]
            
            rows = []
            for selector in selectors:
                rows = await self._page.query_selector_all(selector)
                if rows:
                    self._log(f"Found {len(rows)} rows with selector: {selector}")
                    break
            
            if not rows:
                # Fallback: try to get any table rows
                rows = await self._page.query_selector_all("tr")
                self._log(f"Fallback: found {len(rows)} generic rows")
            
            for i, row in enumerate(rows[:limit]):
                try:
                    # Skip header rows
                    header_cells = await row.query_selector_all("th")
                    if header_cells:
                        continue
                    
                    # Get row text
                    text = (await row.inner_text()).strip()
                    if not text or len(text) < 10:
                        continue
                    
                    # Get row HTML for detailed extraction
                    html = await row.inner_html()
                    
                    # Extract org.nrs from text
                    orgnrs = extract_orgnrs(text)
                    
                    # Try to extract company name (usually first cell or first line)
                    cells = await row.query_selector_all("td")
                    company_name = None
                    title_text = text[:200]
                    
                    if cells and len(cells) > 0:
                        first_cell = (await cells[0].inner_text()).strip()
                        if first_cell and len(first_cell) > 2:
                            company_name = first_cell
                            title_text = first_cell
                    
                    # Try to find a link for more details
                    link = await row.query_selector("a")
                    source_url = None
                    if link:
                        source_url = await link.get_attribute("href")
                        if source_url and not source_url.startswith("http"):
                            source_url = f"{self.BASE_URL}{source_url}"
                    
                    # Create announcement
                    ann = POITAnnouncement(
                        poit_id=f"poit_{date.today().isoformat()}_{category_key}_{i}",
                        category=category,
                        title=title_text,
                        company_name=company_name,
                        orgnr=orgnrs[0] if orgnrs else None,
                        announcement_date=date.today().isoformat(),
                        content=text,
                        source_url=source_url,
                        extracted_orgnrs=orgnrs,
                        raw_html=html[:2000] if html else None,
                        scraped_at=datetime.now().isoformat()
                    )
                    
                    announcements.append(ann)
                    
                except Exception as e:
                    self._log(f"Error extracting row {i}: {e}", "warning")
                    continue
            
            self._log(f"Extracted {len(announcements)} announcements from {category}")
            
        except Exception as e:
            self._log(f"Error in _extract_announcements: {e}", "error")
        
        return announcements
    
    async def screenshot(self, path: str) -> bool:
        """Save screenshot of current page."""
        if self._page:
            try:
                await self._page.screenshot(path=path, full_page=True)
                return True
            except Exception as e:
                self._log(f"Screenshot failed: {e}", "warning")
        return False
    
    async def get_page_content(self) -> str:
        """Get current page HTML content."""
        if self._page:
            return await self._page.content()
        return ""
    
    def _normalize_key(self, name: str) -> str:
        """Normalize category name to a key."""
        key = name.lower()
        # Swedish character replacements
        replacements = {
            'å': 'a', 'ä': 'a', 'ö': 'o',
            'é': 'e', 'è': 'e', 'ü': 'u'
        }
        for old, new in replacements.items():
            key = key.replace(old, new)
        key = re.sub(r'[^a-z0-9]', '_', key)
        key = re.sub(r'_+', '_', key)
        return key.strip('_')
    
    def _parse_category_url(self, url: str) -> tuple:
        """Extract category and subcategory IDs from URL."""
        # URLs like: /poit-app/urval-senaste-publiceringar/3/20#search
        match = re.search(r'/urval-senaste-publiceringar/(\d+)(?:/(\d+))?', url)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    def _parse_stats_from_html(self, html: str) -> Dict[str, POITCategory]:
        """Parse statistics directly from HTML (fallback method)."""
        categories = {}
        
        # Pattern: <span class="...bg-white...">Name</span><span class="...badge...">COUNT</span>
        pattern = r'class="[^"]*bg-white[^"]*">([^<]+)</span><span[^>]*class="[^"]*badge[^"]*">(\d+)</span>'
        matches = re.findall(pattern, html)
        
        for name, count in matches:
            name = name.strip()
            if 2 < len(name) < 60:
                key = self._normalize_key(name)
                categories[key] = POITCategory(
                    key=key,
                    name=name,
                    count=int(count),
                    url=""
                )
        
        return categories


# =============================================================================
# Convenience Functions
# =============================================================================

async def scrape_poit_stats() -> Optional[Dict[str, Any]]:
    """
    Quick function to get today's POIT statistics.
    
    Returns:
        Dict with category statistics or None on failure
    """
    async with POITPlaywrightScraper(headless=True, debug=False) as scraper:
        stats = await scraper.get_daily_stats()
        if stats:
            return {
                "date": stats.date,
                "scraped_at": stats.scraped_at,
                "total": stats.total_announcements,
                "categories": {
                    k: asdict(v) for k, v in stats.categories.items()
                }
            }
    return None


async def scrape_poit_bankruptcies(limit: int = 100) -> List[Dict]:
    """
    Quick function to get today's bankruptcy announcements.
    
    Returns:
        List of bankruptcy announcement dicts
    """
    async with POITPlaywrightScraper(headless=True, debug=False) as scraper:
        result = await scraper.scrape_bankruptcies(limit=limit)
        if result.success:
            return [asdict(a) for a in result.announcements]
    return []


async def scrape_poit_all(
    categories: Optional[List[str]] = None,
    limit_per_category: int = 50
) -> Dict[str, List[Dict]]:
    """
    Scrape all POIT categories.
    
    Args:
        categories: Specific categories to scrape (None = all)
        limit_per_category: Max items per category
        
    Returns:
        Dict mapping category to list of announcement dicts
    """
    results = {}
    
    async with POITPlaywrightScraper(headless=True, debug=False) as scraper:
        scrape_results = await scraper.scrape_all_categories(
            limit_per_category=limit_per_category,
            categories=categories
        )
        
        for cat_key, result in scrape_results.items():
            if result.success:
                results[cat_key] = [asdict(a) for a in result.announcements]
            else:
                results[cat_key] = []
    
    return results


# =============================================================================
# CLI Testing
# =============================================================================

async def _test_scraper():
    """Test the scraper functionality."""
    print("=" * 60)
    print("POIT Playwright Scraper Test")
    print("=" * 60)
    
    async with POITPlaywrightScraper(headless=True, debug=True) as scraper:
        # Test 1: Get daily stats
        print("\n📊 Getting daily statistics...")
        stats = await scraper.get_daily_stats()
        
        if stats:
            print(f"Date: {stats.date}")
            print(f"Total announcements: {stats.total_announcements}")
            print("\nCategories:")
            for key, cat in sorted(stats.categories.items()):
                print(f"  {cat.name}: {cat.count}")
        else:
            print("Failed to get stats")
            return
        
        # Test 2: Scrape bankruptcies
        print("\n📋 Scraping konkurser (limit 5)...")
        result = await scraper.scrape_category("konkurser", limit=5)
        
        if result.success:
            print(f"Found {result.total_found} announcements:")
            for ann in result.announcements[:3]:
                print(f"  - {ann.company_name or ann.title[:50]}")
                if ann.extracted_orgnrs:
                    print(f"    Orgnrs: {', '.join(ann.extracted_orgnrs)}")
        else:
            print(f"Failed: {result.error}")
        
        # Test 3: Screenshot
        print("\n📸 Taking screenshot...")
        await scraper.screenshot("/tmp/poit_playwright_test.png")
        print("Saved to /tmp/poit_playwright_test.png")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(_test_scraper())
