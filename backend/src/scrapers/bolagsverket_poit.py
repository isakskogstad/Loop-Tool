"""
Bolagsverket POIT (Post- och Inrikes Tidningar) Client
Browser-based scraper for Swedish company announcements

Data source: https://poit.bolagsverket.se/poit-app/

Features:
- Daily statistics (konkurser, registreringar, kallelser, etc.)
- Category-based announcement listings
- Automatic bot protection bypass using undetected-chromedriver
- Both sync and async interfaces

Note: Requires Chrome browser and undetected-chromedriver for bot bypass.
For server deployment, run sync job locally and store results in database.
"""

import os
import re
import time
import asyncio
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

try:
    from ..logging_config import get_source_logger
except ImportError:
    import logging
    def get_source_logger(name):
        return logging.getLogger(name)

logger = get_source_logger("bolagsverket_poit")


@dataclass
class CategoryStats:
    """Statistics for an announcement category"""
    name: str
    count: int
    url: str = ""
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None


@dataclass
class Announcement:
    """A single announcement/kungörelse"""
    id: Optional[str] = None
    category: str = ""
    subcategory: Optional[str] = None
    title: str = ""
    company_name: Optional[str] = None
    orgnr: Optional[str] = None
    published_date: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    raw_data: Optional[Dict] = None


@dataclass
class DailyStats:
    """Daily statistics from POIT"""
    date: str
    categories: Dict[str, CategoryStats]
    total_announcements: int = 0
    scraped_at: Optional[str] = None


class BolagsverketPOITClient:
    """
    Client for Bolagsverket's Post- och Inrikes Tidningar (POIT)
    
    POIT contains official Swedish announcements including:
    - Konkurser (bankruptcies)
    - Bolagsverkets registreringar (company registrations)
    - Kallelser (summons)
    - Skuldsaneringar (debt restructuring)
    - Familjerätt (family law)
    
    Usage:
        client = BolagsverketPOITClient()
        if client.initialize():
            stats = client.get_daily_stats()
            print(f"Today's bankruptcies: {stats.categories.get('konkurser', {}).count}")
        client.close()
    
    Note: This client uses browser automation to bypass bot protection.
    For production use, run scheduled syncs and store results in database.
    """
    
    BASE_URL = "https://poit.bolagsverket.se"
    POIT_APP_URL = "https://poit.bolagsverket.se/poit-app/"
    
    # Category mapping for URL parsing
    CATEGORY_IDS = {
        "1": "kallelser",
        "2": "bolagsverkets_registreringar",
        "3": "konkurser",
        "4": "familjeratt",
        "5": "skuldsaneringar"
    }
    
    def __init__(self, headless: bool = False, debug: bool = False):
        """
        Initialize POIT client.
        
        Args:
            headless: Run browser in headless mode (may trigger CAPTCHA)
            debug: Enable debug logging
        """
        self.headless = headless
        self.debug = debug
        self.driver = None
        self._ready = False
        self._last_stats: Optional[DailyStats] = None
        
    def _log(self, msg: str, level: str = "info"):
        """Log message."""
        if self.debug or level in ("warning", "error"):
            log_func = getattr(logger, level, logger.info)
            log_func(msg)
    
    @property
    def is_configured(self) -> bool:
        """Check if browser automation is available."""
        try:
            import undetected_chromedriver
            return True
        except ImportError:
            return False
    
    def initialize(self) -> bool:
        """
        Start browser and navigate to POIT.
        
        Returns:
            True if successful, False if CAPTCHA detected or error
        """
        if not self.is_configured:
            self._log("undetected-chromedriver not installed", "error")
            return False
            
        try:
            import undetected_chromedriver as uc
            
            self._log("Starting undetected-chromedriver...")
            
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            if self.headless:
                options.add_argument('--headless=new')
            
            self.driver = uc.Chrome(options=options, use_subprocess=True)
            self._log("Browser started")
            
            # Navigate to POIT
            self.driver.get(self.POIT_APP_URL)
            time.sleep(5)
            
            # Check for CAPTCHA
            if "What code is in the image" in self.driver.page_source:
                self._log("CAPTCHA detected - bot protection triggered", "warning")
                return False
            
            # Verify we're on the right page
            if "Post- och Inrikes Tidningar" not in self.driver.title:
                self._log(f"Unexpected page: {self.driver.title}", "warning")
                return False
            
            self._ready = True
            self._log("Client ready")
            return True
            
        except Exception as e:
            self._log(f"Initialization failed: {e}", "error")
            return False
    
    def get_daily_stats(self) -> Optional[DailyStats]:
        """
        Get today's announcement statistics from the homepage.
        
        Returns:
            DailyStats object with category counts and URLs
        """
        if not self._ready:
            self._log("Client not initialized", "error")
            return None
        
        # Ensure we're on the homepage
        if "/poit-app/" not in self.driver.current_url or "/poit-app/sok" in self.driver.current_url:
            self.driver.get(self.POIT_APP_URL)
            time.sleep(3)
        
        categories = {}
        total = 0
        
        try:
            from selenium.webdriver.common.by import By
            
            # Method 1: Find category links with CSS selectors
            # Structure: <a class="kungorelser__link">...<span class="bg-white">Name</span><span class="badge">COUNT</span>...</a>
            links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a.kungorelser__link, a.kungorelser__link--sub"
            )
            
            for link in links:
                try:
                    href = link.get_attribute("href") or ""
                    
                    # Find name and count spans
                    name_spans = link.find_elements(By.CSS_SELECTOR, "span.bg-white")
                    badge_spans = link.find_elements(By.CSS_SELECTOR, "span.badge")
                    
                    if name_spans and badge_spans:
                        name = name_spans[0].text.strip()
                        count_text = badge_spans[0].text.strip()
                        
                        if name and count_text.isdigit():
                            count = int(count_text)
                            key = self._normalize_key(name)
                            
                            # Extract category/subcategory IDs from URL
                            cat_id, subcat_id = self._parse_category_url(href)
                            
                            categories[key] = CategoryStats(
                                name=name,
                                count=count,
                                url=href,
                                category_id=cat_id,
                                subcategory_id=subcat_id
                            )
                            total += count
                            
                except Exception as e:
                    continue
            
            # Fallback: parse HTML directly if no categories found
            if not categories:
                self._log("Fallback to HTML parsing")
                categories = self._parse_stats_from_html(self.driver.page_source)
                total = sum(c.count for c in categories.values())
            
            # Create stats object
            today = date.today().isoformat()
            stats = DailyStats(
                date=today,
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
    
    def get_category_announcements(
        self, 
        category_key: str,
        limit: int = 50
    ) -> List[Announcement]:
        """
        Get announcements for a specific category.
        
        Args:
            category_key: Category key from get_daily_stats() (e.g., "konkurser")
            limit: Maximum announcements to fetch
            
        Returns:
            List of Announcement objects
        """
        if not self._ready:
            return []
        
        # Get stats if we don't have them
        if not self._last_stats:
            self.get_daily_stats()
        
        if not self._last_stats:
            return []
        
        # Find category
        cat = self._last_stats.categories.get(category_key)
        if not cat or not cat.url:
            self._log(f"Category not found: {category_key}", "warning")
            return []
        
        try:
            # Navigate to category page
            self.driver.get(cat.url)
            time.sleep(3)
            
            announcements = self._extract_announcements_from_page(
                category=cat.name,
                limit=limit
            )
            
            return announcements
            
        except Exception as e:
            self._log(f"Error getting category announcements: {e}", "error")
            return []
    
    def get_bankruptcies(self, limit: int = 50) -> List[Announcement]:
        """Convenience method to get today's bankruptcy announcements."""
        return self.get_category_announcements("konkurser", limit)
    
    def get_bankruptcy_decisions(self, limit: int = 50) -> List[Announcement]:
        """Get bankruptcy decisions (konkursbeslut)."""
        return self.get_category_announcements("konkursbeslut", limit)
    
    def get_registrations(self, limit: int = 50) -> List[Announcement]:
        """Get company registrations from Bolagsverket."""
        return self.get_category_announcements("bolagsverkets_registreringar", limit)
    
    def get_debt_restructuring(self, limit: int = 50) -> List[Announcement]:
        """Get debt restructuring announcements."""
        return self.get_category_announcements("skuldsaneringar", limit)
    
    def search(self, query: str, limit: int = 50) -> List[Announcement]:
        """
        Search for announcements.
        
        Args:
            query: Search term (company name, orgnr, etc.)
            limit: Maximum results
            
        Returns:
            List of matching announcements
        """
        if not self._ready:
            return []
        
        try:
            from selenium.webdriver.common.by import By
            
            # Navigate to search page
            self.driver.get(f"{self.BASE_URL}/poit-app/sok")
            time.sleep(2)
            
            # Find and fill search input
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "input[type='text'], input[type='search'], input.form-control"
            )
            
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(query)
                        break
                except:
                    continue
            
            # Submit search
            buttons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[type='submit'], .btn-primary"
            )
            
            for btn in buttons:
                try:
                    text = btn.text.lower()
                    if "sök" in text or btn.get_attribute("type") == "submit":
                        btn.click()
                        break
                except:
                    continue
            
            time.sleep(3)
            
            # Extract results
            return self._extract_announcements_from_page(limit=limit)
            
        except Exception as e:
            self._log(f"Search error: {e}", "error")
            return []
    
    def _normalize_key(self, name: str) -> str:
        """Normalize category name to a key."""
        key = name.lower()
        # Replace Swedish characters
        key = key.replace('å', 'a').replace('ä', 'a').replace('ö', 'o')
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
    
    def _parse_stats_from_html(self, html: str) -> Dict[str, CategoryStats]:
        """Parse statistics directly from HTML (fallback method)."""
        categories = {}
        
        # Pattern: <span class="...bg-white...">Name</span><span class="...badge...">COUNT</span>
        pattern = r'class="[^"]*bg-white[^"]*">([^<]+)</span><span[^>]*class="[^"]*badge[^"]*">(\d+)</span>'
        matches = re.findall(pattern, html)
        
        for name, count in matches:
            name = name.strip()
            if 2 < len(name) < 60:
                key = self._normalize_key(name)
                categories[key] = CategoryStats(
                    name=name,
                    count=int(count),
                    url=""
                )
        
        return categories
    
    def _extract_announcements_from_page(
        self,
        category: str = "",
        limit: int = 50
    ) -> List[Announcement]:
        """Extract announcements from current page."""
        announcements = []
        
        try:
            from selenium.webdriver.common.by import By
            
            # Look for result rows/items
            selectors = [
                "table tbody tr",
                ".search-result",
                ".result-item",
                ".kungorelse-item",
                "[class*='result']"
            ]
            
            for selector in selectors:
                rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if rows:
                    break
            
            for i, row in enumerate(rows[:limit]):
                try:
                    text = row.text.strip()
                    if not text:
                        continue
                    
                    # Try to extract structured data
                    ann = Announcement(
                        id=f"poit_{datetime.now().strftime('%Y%m%d')}_{i}",
                        category=category,
                        title=text[:200] if len(text) > 200 else text,
                        published_date=date.today().isoformat(),
                        raw_data={"text": text, "html": row.get_attribute("outerHTML")[:1000]}
                    )
                    
                    # Try to extract orgnr
                    orgnr_match = re.search(r'\b(\d{6}-?\d{4})\b', text)
                    if orgnr_match:
                        ann.orgnr = orgnr_match.group(1).replace("-", "")
                    
                    announcements.append(ann)
                    
                except Exception:
                    continue
            
        except Exception as e:
            self._log(f"Error extracting announcements: {e}", "error")
        
        return announcements
    
    def screenshot(self, path: str) -> bool:
        """Save screenshot of current page."""
        if self.driver:
            try:
                self.driver.save_screenshot(path)
                return True
            except:
                pass
        return False
    
    def get_page_source(self) -> str:
        """Get current page HTML."""
        return self.driver.page_source if self.driver else ""
    
    def close(self):
        """Close browser and release resources."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self._ready = False
            self._log("Browser closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# =============================================================================
# Convenience functions
# =============================================================================

def get_poit_daily_stats() -> Optional[Dict[str, Any]]:
    """
    Quick function to get today's POIT statistics.
    
    Returns:
        Dict with category statistics or None on failure
    """
    client = BolagsverketPOITClient()
    try:
        if client.initialize():
            stats = client.get_daily_stats()
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
    finally:
        client.close()


def get_todays_bankruptcies() -> List[Dict]:
    """
    Quick function to get today's bankruptcy announcements.
    
    Returns:
        List of bankruptcy announcement dicts
    """
    client = BolagsverketPOITClient()
    try:
        if client.initialize():
            announcements = client.get_bankruptcies(limit=100)
            return [asdict(a) for a in announcements]
        return []
    finally:
        client.close()


def get_bolagsverket_poit_client(
    headless: bool = False,
    debug: bool = False
) -> BolagsverketPOITClient:
    """Factory function to create POIT client."""
    return BolagsverketPOITClient(headless=headless, debug=debug)


# =============================================================================
# Async wrapper (runs sync code in thread pool)
# =============================================================================

async def get_poit_daily_stats_async() -> Optional[Dict[str, Any]]:
    """Async version of get_poit_daily_stats."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_poit_daily_stats)


async def get_todays_bankruptcies_async() -> List[Dict]:
    """Async version of get_todays_bankruptcies."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_todays_bankruptcies)
