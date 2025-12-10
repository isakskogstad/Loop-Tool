"""
Scrapers for Swedish company data sources

All scrapers support both sync and async HTTP:
- Sync: scraper.scrape_company(orgnr)
- Async: await scraper.scrape_company_async(orgnr)

Data sources:
- Bolagsverket VDM: Official company registry (OAuth2 API)
- Bolagsverket POIT: Post- och Inrikes Tidningar (browser-based scraper)
- Allabolag: Financial data, board members, corporate structure (scraping)
"""

from .base import BaseScraper
from .allabolag import AllabolagScraper, scrape_allabolag
from .bolagsverket_vdm import BolagsverketVDMClient, get_bolagsverket_vdm_client
from .bolagsverket_poit import (
    BolagsverketPOITClient,
    get_bolagsverket_poit_client,
    get_poit_daily_stats,
    get_todays_bankruptcies,
    get_poit_daily_stats_async,
    get_todays_bankruptcies_async,
    CategoryStats,
    Announcement,
    DailyStats
)

__all__ = [
    # Base
    'BaseScraper',
    
    # Allabolag
    'AllabolagScraper',
    'scrape_allabolag',
    
    # Bolagsverket VDM (OAuth2 API)
    'BolagsverketVDMClient',
    'get_bolagsverket_vdm_client',
    
    # Bolagsverket POIT (Browser scraper)
    'BolagsverketPOITClient',
    'get_bolagsverket_poit_client',
    'get_poit_daily_stats',
    'get_todays_bankruptcies',
    'get_poit_daily_stats_async',
    'get_todays_bankruptcies_async',
    'CategoryStats',
    'Announcement',
    'DailyStats'
]
