# POIT Scrapers Package
"""
Scrapers för olika datakällor.

- poit_scraper: undetected-chromedriver scraper för POIT (rekommenderad)
- poit_playwright: Playwright-baserad scraper (backup)
"""

# Primär scraper - undetected-chromedriver (bypasses CAPTCHA)
from .poit_scraper import (
    POITScraper,
    POITAnnouncement,
    POITDailyStats,
    ScrapeResult,
    extract_orgnrs,
    get_todays_poit_stats,
    scrape_category
)

__all__ = [
    "POITScraper",
    "POITAnnouncement",
    "POITDailyStats",
    "ScrapeResult",
    "extract_orgnrs",
    "get_todays_poit_stats",
    "scrape_category"
]
