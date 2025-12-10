#!/usr/bin/env python3
"""
Swedish News Client - Förbättrad version med RSS-stöd och NYT API
API-klient för att hämta och söka svenska affärs- och tech-nyheter

Stödjer:
- Svenska källor (Breakit, Realtid, Ny Teknik, m.fl.)
- New York Times API (Newswire + Article Search)
  - Löpande bevakning av tech/business-nyheter
  - Sökning efter Sverige-relaterade artiklar
  - Bevakning av svenska bolag (Klarna, Spotify, Ikea, etc.)

Datahämtning:
- RSS-flöden (primär källa - snabbare och mer pålitlig)
- Web scraping (fallback när RSS inte finns)
- NYT API (internationella nyheter med Sverige-fokus)
"""

import re
import time
import hashlib
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable, Union
from urllib.parse import urljoin, urlparse, urlencode, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup, Tag
import feedparser


# =============================================================================
# NYT API Konfiguration
# =============================================================================

# VIKTIGT: Din NYT API-nyckel måste ha rätt API:er aktiverade!
# Gå till https://developer.nytimes.com/my-apps och säkerställ att:
# - "Article Search API" är aktiverat
# - "Times Newswire API" är aktiverat

NYT_API_KEY = "c4GaD1G9jx0j0LiabhIL0mdv1yAMI6RT"

# Miljövariabel för API-nyckel (högre prioritet)
import os
NYT_API_KEY = os.environ.get('NYT_API_KEY', NYT_API_KEY)

# Svenska företag att bevaka i internationella medier
SWEDISH_COMPANIES = [
    "Klarna",
    "Spotify", 
    "Ericsson",
    "Volvo",
    "IKEA",
    "H&M",
    "Northvolt",
    "Skype",
    "Oatly",
    "Paradox Interactive",
    "King",  # Candy Crush
    "Mojang",  # Minecraft
    "SEB",
    "Handelsbanken",
    "Atlas Copco",
    "ABB",
    "Sandvik",
    "Telia",
    "Embracer Group",
]

# Svenska platser för geografisk filtrering
SWEDISH_LOCATIONS = [
    "Sweden",
    "Stockholm",
    "Gothenburg",
    "Malmo",
    "Uppsala",
]

# NYT sektioner relevanta för tech/business
NYT_TECH_SECTIONS = ["technology", "business"]
NYT_RELEVANT_DESKS = ["Business", "Technology", "Foreign"]


@dataclass
class NewsArticle:
    """En nyhetsartikel med metadata"""
    id: str
    title: str
    url: str
    source: str
    summary: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None
    source_type: str = 'scrape'  # 'rss' eller 'scrape'
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertera till dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """Konvertera till JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class SearchResult:
    """Resultat från sökning"""
    articles: List[NewsArticle]
    total_count: int
    search_time_ms: int
    sources_searched: List[str]
    errors: Optional[List[Dict[str, str]]] = None


class RateLimiter:
    """Rate limiter för att begränsa requests per domän"""
    
    def __init__(self, requests_per_second: float = 2.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request: Dict[str, float] = {}
    
    def wait(self, domain: str):
        """Vänta tills nästa request är tillåten"""
        now = time.time()
        last = self.last_request.get(domain, 0)
        elapsed = now - last
        
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        self.last_request[domain] = time.time()


class SimpleCache:
    """Enkel in-memory cache"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        entry = self.cache.get(key)
        if not entry:
            return None
        if time.time() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            return None
        return entry['data']
    
    def set(self, key: str, data: Any):
        self.cache[key] = {'data': data, 'timestamp': time.time()}
    
    def clear(self):
        self.cache.clear()


# =============================================================================
# NYT API Klient
# =============================================================================

@dataclass
class NYTArticle:
    """Artikel från New York Times API"""
    id: str
    title: str
    url: str
    source: str = "nytimes"
    summary: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    author: Optional[str] = None
    word_count: Optional[int] = None
    keywords: Optional[List[str]] = None
    desk: Optional[str] = None
    material_type: Optional[str] = None
    source_type: str = 'nyt_api'
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertera till dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """Konvertera till JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def to_news_article(self) -> 'NewsArticle':
        """Konvertera till generisk NewsArticle"""
        return NewsArticle(
            id=self.id,
            title=self.title,
            url=self.url,
            source=f"nyt:{self.section or 'general'}",
            summary=self.summary,
            image_url=self.image_url,
            published_at=self.published_at,
            category=self.section,
            author=self.author,
            source_type='nyt_api'
        )


class NYTClient:
    """
    Klient för New York Times API
    
    Stödjer:
    - Times Newswire (realtidsflöde av nya artiklar)
    - Article Search (sök i arkivet)
    
    Exempel:
        >>> nyt = NYTClient()
        >>> 
        >>> # Hämta senaste tech-nyheter
        >>> tech = nyt.get_newswire(section='technology', limit=20)
        >>> 
        >>> # Sök efter artiklar om svenska företag
        >>> klarna = nyt.search_articles(query='Klarna', days_back=365)
        >>> 
        >>> # Hämta Sverige-relaterade nyheter
        >>> sweden = nyt.get_sweden_news(limit=50)
    """
    
    BASE_URL = "https://api.nytimes.com"
    NEWSWIRE_PATH = "/svc/news/v3/content"
    SEARCH_PATH = "/svc/search/v2/articlesearch.json"
    
    # Tillgängliga sektioner
    SECTIONS = [
        'all', 'arts', 'automobiles', 'books', 'business', 'fashion', 
        'food', 'health', 'home', 'insider', 'magazine', 'movies',
        'nyregion', 'obituaries', 'opinion', 'politics', 'realestate',
        'science', 'sports', 'sundayreview', 'technology', 'theater',
        't-magazine', 'travel', 'upshot', 'us', 'world'
    ]
    
    def __init__(
        self,
        api_key: str = NYT_API_KEY,
        timeout: int = 15,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
        rate_limit: float = 5.0  # NYT har rate limit på 5 req/min för gratis
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self.cache = SimpleCache(cache_ttl)
        self.rate_limiter = RateLimiter(rate_limit / 60)  # Konvertera till per sekund
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
        })
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Gör en request till NYT API"""
        self.rate_limiter.wait('api.nytimes.com')
        
        params['api-key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            # Hantera specifika HTTP-fel
            if response.status_code == 403:
                raise Exception(
                    f"403 Forbidden - Din API-nyckel har inte tillgång till detta API.\n"
                    f"   Gå till https://developer.nytimes.com/my-apps och aktivera:\n"
                    f"   - Article Search API\n"
                    f"   - Times Newswire API\n"
                    f"   Du kan också sätta miljövariabeln NYT_API_KEY med en giltig nyckel."
                )
            elif response.status_code == 401:
                raise Exception(
                    f"401 Unauthorized - Ogiltig API-nyckel.\n"
                    f"   Kontrollera att NYT_API_KEY är korrekt."
                )
            elif response.status_code == 429:
                raise Exception(
                    f"429 Too Many Requests - Rate limit överskriden.\n"
                    f"   NYT tillåter ca 5 anrop/minut. Vänta en stund."
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def _parse_newswire_article(self, item: Dict) -> NYTArticle:
        """Parsa en artikel från Newswire API"""
        # Hämta bild-URL
        image_url = None
        if item.get('multimedia'):
            for media in item['multimedia']:
                if media.get('url'):
                    image_url = media['url']
                    break
        
        # Hämta keywords
        keywords = []
        for field in ['des_facet', 'per_facet', 'geo_facet']:
            if item.get(field):
                if isinstance(item[field], list):
                    keywords.extend(item[field])
                else:
                    keywords.append(item[field])
        
        return NYTArticle(
            id=item.get('uri', ''),
            title=item.get('title', '') or item.get('headline', ''),
            url=item.get('url', ''),
            summary=item.get('abstract', ''),
            image_url=image_url,
            published_at=item.get('published_date', ''),
            section=item.get('section', ''),
            subsection=item.get('subsection', ''),
            author=item.get('byline', ''),
            keywords=keywords if keywords else None,
            material_type=item.get('material_type_facet', ''),
        )
    
    def _parse_search_article(self, doc: Dict) -> NYTArticle:
        """Parsa en artikel från Article Search API"""
        # Hämta headline
        headline = doc.get('headline', {})
        title = headline.get('main', '') or headline.get('print_headline', '')
        
        # Hämta bild-URL
        image_url = None
        if doc.get('multimedia'):
            for media in doc['multimedia']:
                default = media.get('default', {})
                if default.get('url'):
                    image_url = f"https://static01.nyt.com/{default['url']}"
                    break
        
        # Hämta keywords
        keywords = []
        for kw in doc.get('keywords', []):
            if kw.get('value'):
                keywords.append(kw['value'])
        
        # Hämta författare
        byline = doc.get('byline', {})
        author = byline.get('original', '') if isinstance(byline, dict) else ''
        
        return NYTArticle(
            id=doc.get('uri', ''),
            title=title,
            url=doc.get('web_url', ''),
            summary=doc.get('snippet', ''),
            image_url=image_url,
            published_at=doc.get('pub_date', ''),
            section=doc.get('section_name', ''),
            author=author,
            word_count=doc.get('word_count'),
            keywords=keywords if keywords else None,
            desk=doc.get('desk', ''),
            material_type=doc.get('type_of_material', ''),
        )
    
    def get_newswire(
        self,
        source: str = 'all',
        section: str = 'all',
        limit: int = 20,
        offset: int = 0
    ) -> List[NYTArticle]:
        """
        Hämta senaste nyheter från Times Newswire
        
        Args:
            source: 'all', 'nyt', eller 'inyt'
            section: Sektion (t.ex. 'technology', 'business', 'world')
            limit: Max antal artiklar (20-500, steg om 20)
            offset: Startposition
        
        Returns:
            Lista med NYTArticle-objekt
        """
        cache_key = f'nyt_newswire_{source}_{section}_{limit}_{offset}'
        
        if self.cache_enabled:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        url = f"{self.BASE_URL}{self.NEWSWIRE_PATH}/{source}/{section}.json"
        
        # Justera limit till multipel av 20
        limit = max(20, min(500, (limit // 20) * 20))
        
        params = {
            'limit': limit,
            'offset': offset
        }
        
        try:
            data = self._make_request(url, params)
            articles = [
                self._parse_newswire_article(item) 
                for item in data.get('results', [])
            ]
            
            if self.cache_enabled:
                self.cache.set(cache_key, articles)
            
            return articles
        except Exception as e:
            raise Exception(f"NYT Newswire request failed: {e}")
    
    def search_articles(
        self,
        query: Optional[str] = None,
        filter_query: Optional[str] = None,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort: str = 'newest',
        page: int = 0,
        days_back: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Sök artiklar i NYT:s arkiv
        
        Args:
            query: Sökord (söker i body, headline, byline)
            filter_query: Lucene filter (t.ex. 'timesTag.location:Sweden')
            begin_date: Startdatum (YYYYMMDD)
            end_date: Slutdatum (YYYYMMDD)
            sort: 'best', 'newest', 'oldest', 'relevance'
            page: Sidnummer (0-100)
            days_back: Alternativ - sök X dagar bakåt
        
        Returns:
            Dict med 'articles', 'total_hits', 'page'
        """
        # Hantera days_back
        if days_back and not begin_date:
            end_dt = datetime.now()
            begin_dt = end_dt - timedelta(days=days_back)
            begin_date = begin_dt.strftime('%Y%m%d')
            end_date = end_dt.strftime('%Y%m%d')
        
        cache_key = f'nyt_search_{query}_{filter_query}_{begin_date}_{end_date}_{sort}_{page}'
        
        if self.cache_enabled:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        url = f"{self.BASE_URL}{self.SEARCH_PATH}"
        
        params = {'sort': sort, 'page': page}
        if query:
            params['q'] = query
        if filter_query:
            params['fq'] = filter_query
        if begin_date:
            params['begin_date'] = begin_date
        if end_date:
            params['end_date'] = end_date
        
        try:
            data = self._make_request(url, params)
            response = data.get('response', {})
            
            articles = [
                self._parse_search_article(doc)
                for doc in response.get('docs', [])
            ]
            
            meta = response.get('meta', {})
            result = {
                'articles': articles,
                'total_hits': meta.get('hits', 0),
                'page': page,
                'offset': meta.get('offset', 0),
            }
            
            if self.cache_enabled:
                self.cache.set(cache_key, result)
            
            return result
        except Exception as e:
            raise Exception(f"NYT Article Search failed: {e}")
    
    def get_tech_news(self, limit: int = 20) -> List[NYTArticle]:
        """Hämta senaste tech-nyheter"""
        return self.get_newswire(section='technology', limit=limit)
    
    def get_business_news(self, limit: int = 20) -> List[NYTArticle]:
        """Hämta senaste affärsnyheter"""
        return self.get_newswire(section='business', limit=limit)
    
    def get_world_news(self, limit: int = 20) -> List[NYTArticle]:
        """Hämta senaste världsnyheter"""
        return self.get_newswire(section='world', limit=limit)
    
    def search_sweden(
        self,
        query: Optional[str] = None,
        days_back: int = 30,
        page: int = 0
    ) -> Dict[str, Any]:
        """
        Sök efter Sverige-relaterade artiklar
        
        Args:
            query: Extra sökord (optional)
            days_back: Antal dagar bakåt att söka
            page: Sidnummer
        """
        locations = ' OR '.join([f'"{loc}"' for loc in SWEDISH_LOCATIONS])
        filter_query = f'timesTag.location:({locations})'
        
        return self.search_articles(
            query=query,
            filter_query=filter_query,
            days_back=days_back,
            page=page
        )
    
    def search_swedish_company(
        self,
        company: str,
        days_back: int = 365,
        page: int = 0
    ) -> Dict[str, Any]:
        """
        Sök efter artiklar om ett svenskt företag
        
        Args:
            company: Företagsnamn (t.ex. 'Klarna', 'Spotify')
            days_back: Antal dagar bakåt att söka
            page: Sidnummer
        """
        return self.search_articles(
            query=f'"{company}"',
            days_back=days_back,
            sort='newest',
            page=page
        )
    
    def search_swedish_companies(
        self,
        companies: Optional[List[str]] = None,
        days_back: int = 30,
        limit_per_company: int = 5
    ) -> Dict[str, List[NYTArticle]]:
        """
        Sök efter artiklar om flera svenska företag
        
        Args:
            companies: Lista med företagsnamn (default: SWEDISH_COMPANIES)
            days_back: Antal dagar bakåt
            limit_per_company: Max artiklar per företag
        
        Returns:
            Dict med företagsnamn -> lista av artiklar
        """
        companies = companies or SWEDISH_COMPANIES
        results = {}
        
        for company in companies:
            try:
                search_result = self.search_swedish_company(
                    company, 
                    days_back=days_back
                )
                if search_result['articles']:
                    results[company] = search_result['articles'][:limit_per_company]
            except Exception:
                continue
        
        return results
    
    def get_sections(self) -> List[Dict[str, str]]:
        """Lista tillgängliga NYT-sektioner"""
        url = f"{self.BASE_URL}{self.NEWSWIRE_PATH}/section-list.json"
        
        try:
            data = self._make_request(url, {})
            return data.get('results', [])
        except Exception as e:
            raise Exception(f"Failed to fetch sections: {e}")
    
    def check_health(self) -> Dict[str, Any]:
        """Kontrollera NYT API status"""
        results = {
            'newswire': {'available': False},
            'search': {'available': False},
        }
        
        # Testa Newswire
        start = time.time()
        try:
            articles = self.get_newswire(section='technology', limit=20)
            results['newswire'] = {
                'available': len(articles) > 0,
                'article_count': len(articles),
                'response_time_ms': int((time.time() - start) * 1000),
            }
        except Exception as e:
            results['newswire'] = {
                'available': False,
                'error': str(e),
                'response_time_ms': int((time.time() - start) * 1000),
            }
        
        # Testa Search
        start = time.time()
        try:
            search = self.search_articles(query='technology', days_back=7)
            results['search'] = {
                'available': search['total_hits'] > 0,
                'total_hits': search['total_hits'],
                'response_time_ms': int((time.time() - start) * 1000),
            }
        except Exception as e:
            results['search'] = {
                'available': False,
                'error': str(e),
                'response_time_ms': int((time.time() - start) * 1000),
            }
        
        results['available'] = (
            results['newswire'].get('available', False) or 
            results['search'].get('available', False)
        )
        
        return results


class SwedishNewsClient:
    """
    Klient för att hämta svenska affärs- och tech-nyheter
    
    Exempel:
        >>> client = SwedishNewsClient()
        >>> 
        >>> # Hämta senaste från Breakit
        >>> news = client.get_latest('breakit', limit=10)
        >>> 
        >>> # Sök efter ett företag
        >>> results = client.search('Klarna')
        >>> 
        >>> # Hämta startup-nyheter
        >>> startups = client.get_startup_news()
    """
    
    # Kända nyhetskällor med deras URL:er och RSS-flöden
    SOURCES = {
        'breakit': {
            'name': 'Breakit',
            'base_url': 'https://www.breakit.se',
            'paths': ['/', '/senaste-nyheterna'],
            'type': 'tech',
            'rss_feeds': [
                'https://www.breakit.se/feed/artiklar',
            ]
        },
        'di': {
            'name': 'Dagens Industri',
            'base_url': 'https://www.di.se',
            'paths': ['/'],
            'type': 'business',
            'rss_feeds': []  # DI blockerar RSS-åtkomst
        },
        'di-digital': {
            'name': 'DI Digital',
            'base_url': 'https://www.di.se',
            'paths': ['/digital'],
            'type': 'tech',
            'rss_feeds': []  # DI blockerar RSS-åtkomst
        },
        'realtid': {
            'name': 'Realtid',
            'base_url': 'https://www.realtid.se',
            'paths': ['/nyheter/', '/tag/startup-bolag/'],
            'type': 'finance',
            'rss_feeds': [
                'https://www.realtid.se/feed/',
            ]
        },
        'nyteknik': {
            'name': 'Ny Teknik',
            'base_url': 'https://www.nyteknik.se',
            'paths': ['/', '/amnen/startup'],
            'type': 'tech',
            'rss_feeds': []  # Ny Teknik har stängt av sina RSS-flöden
        },
        'svd': {
            'name': 'Svenska Dagbladet',
            'base_url': 'https://www.svd.se',
            'paths': ['/naringsliv'],
            'type': 'business',
            'rss_feeds': []  # SvD blockerar RSS-åtkomst
        },
        'sydsvenskan': {
            'name': 'Sydsvenskan',
            'base_url': 'https://www.sydsvenskan.se',
            'paths': ['/naringsliv'],
            'type': 'business',
            'rss_feeds': []  # Sydsvenskan blockerar RSS-åtkomst
        },
        'borskollen': {
            'name': 'Börskollen',
            'base_url': 'https://www.borskollen.se',
            'paths': ['/nyheter/'],
            'type': 'finance',
            'rss_feeds': []  # Ingen tillgänglig RSS
        },
        # Internationella källor
        'techcrunch': {
            'name': 'TechCrunch Startups',
            'base_url': 'https://techcrunch.com',
            'paths': ['/category/startups/'],
            'type': 'tech',
            'language': 'en',
            'rss_feeds': [
                'https://techcrunch.com/startups/feed/',
                'https://techcrunch.com/category/startups/feed/',
            ],
            'relevance_keywords': [
                # Impact & Sustainability
                'impact', 'sustainability', 'sustainable', 'climate tech', 'cleantech',
                'green tech', 'carbon', 'net zero', 'esg', 'renewable', 'circular economy',
                'sdg', 'social impact', 'impact investing', 'green bond',
                # Specifika sektorer
                'electric vehicle', 'ev', 'solar', 'wind energy', 'battery',
                'food tech', 'agtech', 'vertical farming', 'alternative protein',
                'recycling', 'waste management', 'water tech',
                # Business basics
                'startup', 'founder', 'funding', 'venture', 'seed', 'series',
                'entrepreneur', 'vc', 'investment', 'raise', 'valuation',
                'ai', 'saas', 'fintech', 'b2b', 'scale', 'growth'
            ]
        },
        'wired': {
            'name': 'Wired Technology',
            'base_url': 'https://www.wired.com',
            'paths': ['/'],
            'type': 'tech',
            'language': 'en',
            'rss_feeds': [
                'https://www.wired.com/feed/rss',
            ],
            'relevance_keywords': [
                # Impact & Climate
                'climate change', 'sustainability', 'clean energy', 'carbon capture',
                'renewable energy', 'electric vehicle', 'green tech', 'climate tech',
                # Innovation & Tech
                'artificial intelligence', 'machine learning', 'innovation', 'breakthrough',
                'quantum computing', 'biotech', 'nanotech',
                # Social Impact
                'social impact', 'digital divide', 'accessibility', 'healthcare tech',
                'education tech', 'smart city', 'urban planning',
                # Business
                'startup', 'tech company', 'venture capital', 'funding'
            ]
        },
        'bbc-tech': {
            'name': 'BBC Technology',
            'base_url': 'https://www.bbc.com',
            'paths': ['/news/technology'],
            'type': 'tech',
            'language': 'en',
            'rss_feeds': [
                'http://feeds.bbci.co.uk/news/technology/rss.xml',
            ],
            'relevance_keywords': [
                # Climate & Environment
                'climate', 'environment', 'sustainable', 'green', 'renewable',
                'carbon', 'emission', 'pollution', 'conservation',
                # Innovation
                'innovation', 'breakthrough', 'technology', 'digital',
                'ai', 'artificial intelligence', 'automation',
                # Impact
                'impact', 'society', 'ethics', 'accessibility', 'healthcare',
                'education', 'equality', 'inclusion'
            ]
        },
        'bbc-business': {
            'name': 'BBC Business',
            'base_url': 'https://www.bbc.com',
            'paths': ['/news/business'],
            'type': 'business',
            'language': 'en',
            'rss_feeds': [
                'http://feeds.bbci.co.uk/news/business/rss.xml',
            ],
            'relevance_keywords': [
                # Impact Business
                'impact investing', 'esg', 'sustainable finance', 'green bond',
                'social enterprise', 'b corp', 'circular economy', 'ethical',
                # Climate Finance
                'climate finance', 'carbon market', 'renewable', 'clean energy',
                'net zero', 'carbon neutral', 'emission trading',
                # General Business
                'startup', 'entrepreneur', 'funding', 'venture capital',
                'investment', 'ipo', 'merger', 'acquisition', 'growth'
            ]
        },
    }
    
    # Fördefinierade källgrupper
    STARTUP_SOURCES = ['breakit', 'realtid', 'nyteknik', 'di-digital', 'techcrunch']
    BUSINESS_SOURCES = ['di', 'svd', 'sydsvenskan', 'realtid', 'borskollen', 'bbc-business']
    TECH_SOURCES = ['breakit', 'nyteknik', 'di-digital', 'techcrunch', 'wired', 'bbc-tech']
    FINANCE_SOURCES = ['realtid', 'borskollen', 'di', 'bbc-business']
    INTERNATIONAL_SOURCES = ['techcrunch', 'wired', 'bbc-tech', 'bbc-business']
    
    def __init__(
        self,
        timeout: int = 15,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
        rate_limit: float = 2.0,
        user_agent: Optional[str] = None
    ):
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self.cache = SimpleCache(cache_ttl)
        self.rate_limiter = RateLimiter(rate_limit)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        })
    
    def _fetch_html(self, url: str) -> str:
        """Hämta HTML från en URL med rate limiting"""
        domain = urlparse(url).netloc
        self.rate_limiter.wait(domain)
        
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text
    
    def _fetch_rss(self, feed_url: str) -> feedparser.FeedParserDict:
        """Hämta och parsa ett RSS-flöde"""
        domain = urlparse(feed_url).netloc
        self.rate_limiter.wait(domain)
        
        # feedparser kan hantera URL:er direkt men vi vill ha rate limiting
        response = self.session.get(feed_url, timeout=self.timeout)
        response.raise_for_status()
        return feedparser.parse(response.content)
    
    def _parse_rss_date(self, entry: Dict) -> Optional[str]:
        """Extrahera och formatera publiceringsdatum från RSS-entry"""
        # Försök olika datumfält
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in date_fields:
            if field in entry and entry[field]:
                try:
                    dt = datetime(*entry[field][:6])
                    return dt.isoformat()
                except:
                    pass
        
        # Fallback: försök parsa strängar
        for field in ['published', 'updated', 'created']:
            if field in entry and entry[field]:
                try:
                    dt = parsedate_to_datetime(entry[field])
                    return dt.isoformat()
                except:
                    pass
        
        return None
    
    def _extract_rss_image(self, entry: Dict) -> Optional[str]:
        """Extrahera bild-URL från RSS-entry"""
        # Kolla media:content
        if 'media_content' in entry:
            for media in entry.media_content:
                if 'url' in media and media.get('medium') in ('image', None):
                    return media['url']
        
        # Kolla media:thumbnail
        if 'media_thumbnail' in entry:
            for thumb in entry.media_thumbnail:
                if 'url' in thumb:
                    return thumb['url']
        
        # Kolla enclosures
        if 'enclosures' in entry:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href') or enclosure.get('url')
        
        # Försök hitta bild i content/description
        content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
        description = entry.get('description', '') or entry.get('summary', '')
        
        for html in [content, description]:
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    return img['src']
        
        return None
    
    def _clean_html_content(self, html: Optional[str]) -> str:
        """Ta bort HTML-taggar och rensa text"""
        if not html:
            return ''
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ')
        return self._clean_text(text)

    def _calculate_keyword_relevance(self, text: str, keywords: List[str]) -> int:
        """
        Beräkna relevans-score baserat på keywords

        Args:
            text: Text att analysera (titel + sammanfattning)
            keywords: Lista med relevanta keywords

        Returns:
            Score (0-100)
        """
        if not text or not keywords:
            return 100  # No filtering if no keywords defined

        text_lower = text.lower()
        score = 0
        matches = 0

        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                matches += 1
                # Längre keywords ger högre score
                score += len(keyword.split()) * 10

                # Bonus om keyword är i början av texten
                if text_lower.startswith(keyword_lower):
                    score += 20

        # Ge bonus för många träffar
        if matches > 0:
            score += matches * 5

        return min(score, 100)

    def _check_relevance(self, article: NewsArticle, source: str, min_score: int = 20) -> bool:
        """
        Kontrollera om en artikel är relevant för källan

        Args:
            article: Artikel att kontrollera
            source: Källans ID
            min_score: Minimum relevance score (default: 20)

        Returns:
            True om artikel är relevant
        """
        config = self.SOURCES.get(source, {})
        keywords = config.get('relevance_keywords', [])

        # Om inga keywords definierade, acceptera allt
        if not keywords:
            return True

        # Kombinera titel och sammanfattning för analys
        text = article.title
        if article.summary:
            text += ' ' + article.summary

        score = self._calculate_keyword_relevance(text, keywords)
        return score >= min_score

    def _parse_rss_entry(self, entry: Dict, source: str) -> Optional[NewsArticle]:
        """Konvertera en RSS-entry till NewsArticle"""
        try:
            # Titel är obligatorisk
            title = self._clean_text(entry.get('title', ''))
            if not title or len(title) < 5:
                return None
            
            # URL är obligatorisk
            url = entry.get('link', '') or entry.get('id', '')
            if not url:
                return None
            
            # Extrahera sammanfattning
            summary = None
            if 'summary' in entry:
                summary = self._clean_html_content(entry['summary'])
            elif 'description' in entry:
                summary = self._clean_html_content(entry['description'])
            
            # Begränsa längd på sammanfattning
            if summary and len(summary) > 300:
                summary = summary[:297] + '...'
            
            # Extrahera författare
            author = None
            if 'author' in entry:
                author = entry['author']
            elif 'authors' in entry and entry['authors']:
                author = entry['authors'][0].get('name', '')
            
            # Extrahera kategori
            category = None
            if 'tags' in entry and entry['tags']:
                category = entry['tags'][0].get('term', '')
            
            return NewsArticle(
                id=self._create_id(url),
                title=title,
                url=url,
                source=source,
                summary=summary,
                image_url=self._extract_rss_image(entry),
                published_at=self._parse_rss_date(entry),
                category=category,
                author=author,
                source_type='rss'
            )
        except Exception as e:
            return None
    
    def _fetch_from_rss(self, source: str, limit: int = 50, filter_relevance: bool = True) -> List[NewsArticle]:
        """
        Hämta artiklar från RSS-flöden för en källa

        Args:
            source: Källans ID
            limit: Max antal artiklar
            filter_relevance: Filtrera på relevance keywords (default: True)

        Returns:
            Lista med NewsArticle
        """
        config = self.SOURCES.get(source)
        if not config or 'rss_feeds' not in config:
            return []

        articles = []
        seen_urls = set()
        filtered_count = 0

        for feed_url in config['rss_feeds']:
            try:
                feed = self._fetch_rss(feed_url)

                if feed.bozo and not feed.entries:
                    # Parse error och inga entries - försök nästa feed
                    continue

                for entry in feed.entries:
                    article = self._parse_rss_entry(entry, source)
                    if not article or article.url in seen_urls:
                        continue

                    # Relevance filtering för internationella källor
                    if filter_relevance and not self._check_relevance(article, source, min_score=15):
                        filtered_count += 1
                        continue

                    seen_urls.add(article.url)
                    articles.append(article)

                    if len(articles) >= limit:
                        return articles

            except Exception as e:
                # Log men fortsätt med nästa feed
                continue

        # Debug info om filtrering
        if filtered_count > 0:
            print(f"  📊 Filtered {filtered_count} irrelevant articles from {source}")

        return articles
    
    def _create_id(self, url: str) -> str:
        """Skapa unik artikel-ID från URL"""
        return hashlib.md5(url.encode()).hexdigest()[:16]
    
    def _clean_text(self, text: Optional[str]) -> str:
        """Rensa whitespace och normalisera text"""
        if not text:
            return ''
        return re.sub(r'\s+', ' ', text).strip()
    
    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """Konvertera relativ URL till absolut"""
        if not url:
            return ''
        if url.startswith(('http://', 'https://')):
            return url
        if url.startswith('//'):
            return 'https:' + url
        return urljoin(base_url, url)
    
    def _is_valid_article_url(self, url: str, source: str) -> bool:
        """Kontrollera om URL ser ut som en giltig artikellänk"""
        try:
            parsed = urlparse(url)
            
            # Exkludera vanliga icke-artikel-sidor
            exclude_patterns = [
                r'^/?$',                    # Startsida
                r'/tag/', r'/category/',    # Kategorisidor
                r'/author/', r'/writer/',   # Författarsidor
                r'/page/\d+',               # Paginering
                r'/(login|signin|subscribe|premium)',  # Login/prenumeration
                r'\.(pdf|jpg|png|gif|css|js)$',       # Filer
                r'/search',                 # Söksidor
                r'/nyhetsbrev',             # Nyhetsbrev
            ]
            
            for pattern in exclude_patterns:
                if re.search(pattern, parsed.path, re.IGNORECASE):
                    return False
            
            # Källspecifika regler
            if source == 'breakit':
                return '/artikel/' in parsed.path
            elif source in ('di', 'di-digital'):
                return bool(re.search(r'/\d+/', parsed.path))  # DI har artikel-ID i URL
            elif source == 'realtid':
                # Realtid har /kategori/artikel-slug struktur
                return len(parsed.path.strip('/').split('/')) >= 2
            elif source == 'nyteknik':
                return bool(re.search(r'/\d+', parsed.path))
            elif source == 'svd':
                return '/naringsliv/' in parsed.path and len(parsed.path.strip('/').split('/')) > 1
            elif source == 'sydsvenskan':
                return '/naringsliv/' in parsed.path
            
            # Default: kräv minst ett URL-segment
            return len(parsed.path.strip('/').split('/')) >= 1
        except:
            return False
    
    def _extract_articles_generic(
        self,
        soup: BeautifulSoup,
        base_url: str,
        source: str
    ) -> List[NewsArticle]:
        """Generisk artikelextraktion som fungerar för de flesta sajter"""
        articles = []
        seen_urls = set()
        
        # Hitta alla länkar
        for link in soup.find_all('a', href=True):
            try:
                href = link.get('href', '')
                url = self._make_absolute_url(href, base_url)
                
                # Skippa dubbletter och ogiltiga länkar
                if url in seen_urls:
                    continue
                if not self._is_valid_article_url(url, source):
                    continue
                
                seen_urls.add(url)
                
                # Försök hitta titel
                title = None
                
                # Kolla om länken själv har text
                link_text = self._clean_text(link.get_text())
                if link_text and 10 <= len(link_text) <= 200:
                    title = link_text
                
                # Kolla inuti länken efter heading
                if not title:
                    heading = link.find(['h1', 'h2', 'h3', 'h4'])
                    if heading:
                        title = self._clean_text(heading.get_text())
                
                # Kolla föräldrar
                if not title:
                    parent = link.parent
                    for _ in range(3):  # Max 3 nivåer upp
                        if parent:
                            heading = parent.find(['h1', 'h2', 'h3', 'h4'])
                            if heading:
                                title = self._clean_text(heading.get_text())
                                break
                            parent = parent.parent
                
                if not title or len(title) < 10:
                    continue
                
                # Försök hitta bild
                image_url = None
                img = link.find('img')
                if not img:
                    # Kolla föräldrar
                    parent = link.parent
                    for _ in range(3):
                        if parent:
                            img = parent.find('img')
                            if img:
                                break
                            parent = parent.parent
                
                if img:
                    image_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if image_url:
                        image_url = self._make_absolute_url(image_url, base_url)
                
                # Försök hitta sammanfattning
                summary = None
                parent = link.parent
                for _ in range(3):
                    if parent:
                        p = parent.find('p')
                        if p and p != link:
                            text = self._clean_text(p.get_text())
                            if text and len(text) > 20 and text != title:
                                summary = text[:300] + '...' if len(text) > 300 else text
                                break
                        parent = parent.parent
                
                articles.append(NewsArticle(
                    id=self._create_id(url),
                    title=title,
                    url=url,
                    source=source,
                    summary=summary,
                    image_url=image_url,
                ))
                
            except Exception:
                continue
        
        return articles
    
    def _extract_breakit(self, soup: BeautifulSoup) -> List[NewsArticle]:
        """Specifik extraktion för Breakit"""
        # Samla all data per URL först
        url_data: Dict[str, Dict[str, Any]] = {}
        base_url = 'https://www.breakit.se'
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/artikel/' not in href:
                continue
            
            url = self._make_absolute_url(href, base_url)
            
            # Skapa entry om det inte finns
            if url not in url_data:
                url_data[url] = {'title': None, 'image_url': None}
            
            # Försök hitta titel
            heading = link.find(['h1', 'h2', 'h3'])
            if heading:
                text = self._clean_text(heading.get_text())
                if text and len(text) >= 10:
                    url_data[url]['title'] = text
            elif not url_data[url]['title']:
                text = self._clean_text(link.get_text())
                if text and len(text) >= 10:
                    url_data[url]['title'] = text
            
            # Försök hitta bild
            img = link.find('img')
            if img:
                img_url = img.get('src') or img.get('data-src')
                if img_url and 'cdn.breakit.se' in img_url:
                    url_data[url]['image_url'] = self._make_absolute_url(img_url, base_url)
        
        # Konvertera till artiklar
        articles = []
        for url, data in url_data.items():
            if data['title']:
                articles.append(NewsArticle(
                    id=self._create_id(url),
                    title=data['title'],
                    url=url,
                    source='breakit',
                    image_url=data['image_url'],
                ))
        
        return articles
    
    def _extract_realtid(self, soup: BeautifulSoup) -> List[NewsArticle]:
        """Specifik extraktion för Realtid"""
        articles = []
        seen_urls = set()
        base_url = 'https://www.realtid.se'
        
        # Realtid har artiklar i anchor-element med bilder
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Måste vara intern länk med minst 2 segment
            if not href.startswith('/') and 'realtid.se' not in href:
                continue
            
            url = self._make_absolute_url(href, base_url)
            
            if url in seen_urls:
                continue
            
            if not self._is_valid_article_url(url, 'realtid'):
                continue
            
            seen_urls.add(url)
            
            # Hitta titel
            title = None
            heading = link.find(['h1', 'h2', 'h3'])
            if heading:
                title = self._clean_text(heading.get_text())
            else:
                title = self._clean_text(link.get_text())
            
            if not title or len(title) < 10:
                continue
            
            # Hitta bild
            image_url = None
            img = link.find('img')
            if img:
                image_url = img.get('src')
                if image_url:
                    image_url = self._make_absolute_url(image_url, base_url)
            
            # Hitta sammanfattning
            summary = None
            p = link.find('p')
            if p:
                summary = self._clean_text(p.get_text())
                if summary and len(summary) > 300:
                    summary = summary[:300] + '...'
            
            articles.append(NewsArticle(
                id=self._create_id(url),
                title=title,
                url=url,
                source='realtid',
                summary=summary,
                image_url=image_url,
            ))
        
        return articles
    
    def get_latest(
        self,
        source: str,
        limit: int = 20,
        prefer_rss: bool = True
    ) -> List[NewsArticle]:
        """
        Hämta senaste nyheterna från en källa
        
        Args:
            source: Nyhetskällan ('breakit', 'di', 'realtid', etc.)
            limit: Max antal artiklar
            prefer_rss: Försök RSS först (default: True)
        
        Returns:
            Lista med NewsArticle-objekt
        """
        if source not in self.SOURCES:
            raise ValueError(f"Unknown source: {source}. Available: {list(self.SOURCES.keys())}")
        
        cache_key = f'latest_{source}_{"rss" if prefer_rss else "scrape"}'
        
        if self.cache_enabled:
            cached = self.cache.get(cache_key)
            if cached:
                return cached[:limit]
        
        config = self.SOURCES[source]
        all_articles = []
        
        # Försök RSS först om tillgängligt och önskat
        if prefer_rss and config.get('rss_feeds'):
            try:
                rss_articles = self._fetch_from_rss(source, limit * 2)
                if rss_articles:
                    all_articles = rss_articles
            except Exception as e:
                pass  # Fallback till scraping
        
        # Om inga RSS-artiklar, använd web scraping
        if not all_articles:
            for path in config['paths']:
                try:
                    url = config['base_url'] + path
                    html = self._fetch_html(url)
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Använd källspecifik extraktion om tillgänglig
                    if source == 'breakit':
                        articles = self._extract_breakit(soup)
                    elif source == 'realtid':
                        articles = self._extract_realtid(soup)
                    else:
                        articles = self._extract_articles_generic(soup, config['base_url'], source)
                    
                    all_articles.extend(articles)
                    
                except Exception as e:
                    continue
        
        # Deduplicera
        seen = set()
        unique = []
        for article in all_articles:
            if article.url not in seen:
                seen.add(article.url)
                unique.append(article)
        
        if self.cache_enabled:
            self.cache.set(cache_key, unique)
        
        return unique[:limit]
    
    def get_latest_rss(self, source: str, limit: int = 20) -> List[NewsArticle]:
        """Hämta senaste nyheterna endast från RSS (ingen scraping fallback)"""
        if source not in self.SOURCES:
            raise ValueError(f"Unknown source: {source}. Available: {list(self.SOURCES.keys())}")
        
        config = self.SOURCES[source]
        if not config.get('rss_feeds'):
            raise ValueError(f"Source '{source}' has no RSS feeds configured")
        
        return self._fetch_from_rss(source, limit)
    
    def get_rss_feeds(self, source: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Lista tillgängliga RSS-flöden
        
        Args:
            source: Specifik källa (None för alla)
        
        Returns:
            Dict med källa -> lista av RSS-URL:er
        """
        if source:
            if source not in self.SOURCES:
                raise ValueError(f"Unknown source: {source}")
            config = self.SOURCES[source]
            return {source: config.get('rss_feeds', [])}
        
        return {
            key: config.get('rss_feeds', [])
            for key, config in self.SOURCES.items()
            if config.get('rss_feeds')
        }
    
    def get_from_sources(
        self,
        sources: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[NewsArticle]:
        """
        Hämta nyheter från flera källor
        
        Args:
            sources: Lista med källor (default: alla)
            limit: Max antal artiklar totalt
        """
        if sources is None:
            sources = list(self.SOURCES.keys())
        
        all_articles = []
        per_source = max(1, limit // len(sources))
        
        for source in sources:
            try:
                articles = self.get_latest(source, per_source)
                all_articles.extend(articles)
            except Exception as e:
                print(f"Warning: Skipping {source}: {e}")
                continue
        
        return all_articles[:limit]
    
    def get_startup_news(self, limit: int = 30) -> List[NewsArticle]:
        """Hämta startup/tech-nyheter"""
        return self.get_from_sources(self.STARTUP_SOURCES, limit)
    
    def get_business_news(self, limit: int = 30) -> List[NewsArticle]:
        """Hämta affärsnyheter"""
        return self.get_from_sources(self.BUSINESS_SOURCES, limit)
    
    def search(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        limit: int = 20,
        sort_by: str = 'relevance'
    ) -> SearchResult:
        """
        Sök efter nyheter med ett sökord
        
        Args:
            query: Sökord (t.ex. företagsnamn, ämne)
            sources: Begränsa till specifika källor
            limit: Max antal resultat
            sort_by: 'relevance' eller 'date'
        
        Returns:
            SearchResult med matchande artiklar
        """
        start_time = time.time()
        sources = sources or self.STARTUP_SOURCES
        errors = []
        
        all_articles = []
        for source in sources:
            try:
                articles = self.get_latest(source, 50)
                all_articles.extend(articles)
            except Exception as e:
                errors.append({'source': source, 'error': str(e)})
        
        # Filtrera på sökord
        query_lower = query.lower()
        words = [w for w in query_lower.split() if len(w) >= 2]
        
        matching = [
            a for a in all_articles
            if all(
                word in (a.title + ' ' + (a.summary or '')).lower()
                for word in words
            )
        ]
        
        # Sortera
        if sort_by == 'relevance':
            def relevance_score(article: NewsArticle) -> int:
                text = (article.title + ' ' + (article.summary or '')).lower()
                score = 0
                if query_lower in text:
                    score += 100
                for word in words:
                    if word in text:
                        score += 10
                        if article.title.lower().startswith(word):
                            score += 20
                return score
            
            matching.sort(key=relevance_score, reverse=True)
        
        return SearchResult(
            articles=matching[:limit],
            total_count=len(matching),
            search_time_ms=int((time.time() - start_time) * 1000),
            sources_searched=sources,
            errors=errors if errors else None,
        )
    
    def search_company(self, company_name: str, limit: int = 20) -> SearchResult:
        """Sök efter nyheter om ett specifikt företag"""
        return self.search(
            query=company_name,
            sources=self.STARTUP_SOURCES + self.BUSINESS_SOURCES,
            limit=limit,
        )
    
    def get_available_sources(self) -> Dict[str, Dict[str, Any]]:
        """Lista alla tillgängliga nyhetskällor"""
        return self.SOURCES.copy()
    
    def check_health(self, source: str) -> Dict[str, Any]:
        """Kontrollera om en källa är tillgänglig (testar både RSS och scraping)"""
        result = {
            'source': source,
            'rss': {'available': False, 'article_count': 0},
            'scrape': {'available': False, 'article_count': 0},
        }
        
        config = self.SOURCES.get(source, {})
        
        # Testa RSS
        if config.get('rss_feeds'):
            start = time.time()
            try:
                articles = self._fetch_from_rss(source, 5)
                result['rss'] = {
                    'available': len(articles) > 0,
                    'article_count': len(articles),
                    'response_time_ms': int((time.time() - start) * 1000),
                    'feeds': config.get('rss_feeds', [])
                }
            except Exception as e:
                result['rss'] = {
                    'available': False,
                    'error': str(e),
                    'response_time_ms': int((time.time() - start) * 1000),
                }
        
        # Testa scraping
        start = time.time()
        try:
            articles = self.get_latest(source, 5, prefer_rss=False)
            result['scrape'] = {
                'available': len(articles) > 0,
                'article_count': len(articles),
                'response_time_ms': int((time.time() - start) * 1000),
            }
        except Exception as e:
            result['scrape'] = {
                'available': False,
                'error': str(e),
                'response_time_ms': int((time.time() - start) * 1000),
            }
        
        # Overall status
        result['available'] = result['rss'].get('available', False) or result['scrape'].get('available', False)
        
        return result
    
    def check_rss_health(self, source: Optional[str] = None) -> Dict[str, Any]:
        """Kontrollera status för RSS-flöden"""
        sources_to_check = [source] if source else list(self.SOURCES.keys())
        results = {}
        
        for src in sources_to_check:
            config = self.SOURCES.get(src, {})
            feeds = config.get('rss_feeds', [])
            
            if not feeds:
                results[src] = {'has_rss': False}
                continue
            
            feed_results = []
            for feed_url in feeds:
                start = time.time()
                try:
                    feed = self._fetch_rss(feed_url)
                    feed_results.append({
                        'url': feed_url,
                        'available': True,
                        'entry_count': len(feed.entries),
                        'title': feed.feed.get('title', ''),
                        'response_time_ms': int((time.time() - start) * 1000),
                    })
                except Exception as e:
                    feed_results.append({
                        'url': feed_url,
                        'available': False,
                        'error': str(e),
                        'response_time_ms': int((time.time() - start) * 1000),
                    })
            
            results[src] = {
                'has_rss': True,
                'feeds': feed_results,
                'any_available': any(f['available'] for f in feed_results)
            }
        
        return results
    
    def clear_cache(self):
        """Rensa cachen"""
        self.cache.clear()


# CLI-verktyg
def main():
    """Kommandoradsverktyg för Swedish News Client"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Hämta och sök svenska affärs- och tech-nyheter (med RSS-stöd)'
    )
    subparsers = parser.add_subparsers(dest='command', help='Kommando')
    
    # latest kommando
    latest_parser = subparsers.add_parser('latest', help='Hämta senaste nyheterna')
    latest_parser.add_argument('source', help='Nyhetskälla (breakit, di, realtid, etc.)')
    latest_parser.add_argument('-n', '--limit', type=int, default=10, help='Max antal artiklar')
    latest_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    latest_parser.add_argument('--rss-only', action='store_true', help='Använd endast RSS (ingen scraping fallback)')
    latest_parser.add_argument('--no-rss', action='store_true', help='Använd endast scraping (ingen RSS)')
    
    # search kommando
    search_parser = subparsers.add_parser('search', help='Sök efter nyheter')
    search_parser.add_argument('query', help='Sökord')
    search_parser.add_argument('-s', '--sources', nargs='+', help='Källor att söka i')
    search_parser.add_argument('-n', '--limit', type=int, default=10, help='Max antal resultat')
    search_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # sources kommando
    sources_parser = subparsers.add_parser('sources', help='Lista tillgängliga källor')
    
    # health kommando
    health_parser = subparsers.add_parser('health', help='Kontrollera källornas status')
    health_parser.add_argument('-v', '--verbose', action='store_true', help='Visa detaljerad status')
    
    # rss kommando - lista RSS-flöden
    rss_parser = subparsers.add_parser('rss', help='Lista tillgängliga RSS-flöden')
    rss_parser.add_argument('source', nargs='?', help='Specifik källa (valfritt)')
    
    # rss-health kommando - testa RSS-flöden
    rss_health_parser = subparsers.add_parser('rss-health', help='Testa RSS-flödens status')
    rss_health_parser.add_argument('source', nargs='?', help='Specifik källa (valfritt)')
    
    args = parser.parse_args()
    
    client = SwedishNewsClient()
    
    if args.command == 'latest':
        try:
            if args.rss_only:
                articles = client.get_latest_rss(args.source, args.limit)
                source_type = "RSS"
            elif args.no_rss:
                articles = client.get_latest(args.source, args.limit, prefer_rss=False)
                source_type = "scraping"
            else:
                articles = client.get_latest(args.source, args.limit)
                source_type = "RSS+scraping"
            
            if args.json:
                print(json.dumps([a.to_dict() for a in articles], ensure_ascii=False, indent=2))
            else:
                print(f"\n📰 Senaste från {args.source.upper()} ({len(articles)} artiklar via {source_type})\n")
                for i, a in enumerate(articles, 1):
                    rss_tag = " [RSS]" if a.source_type == 'rss' else ""
                    print(f"{i}. {a.title}{rss_tag}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at}")
                    if a.summary:
                        print(f"   {a.summary[:80]}...")
                    print()
        except ValueError as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'search':
        results = client.search(args.query, args.sources, args.limit)
        if args.json:
            print(json.dumps({
                'query': args.query,
                'total_count': results.total_count,
                'search_time_ms': results.search_time_ms,
                'articles': [a.to_dict() for a in results.articles]
            }, ensure_ascii=False, indent=2))
        else:
            print(f"\n🔍 Sökning: '{args.query}' ({results.total_count} träffar, {results.search_time_ms}ms)\n")
            for i, a in enumerate(results.articles, 1):
                rss_tag = " [RSS]" if a.source_type == 'rss' else ""
                print(f"{i}. [{a.source}] {a.title}{rss_tag}")
                print(f"   🔗 {a.url}")
                print()
    
    elif args.command == 'sources':
        sources = client.get_available_sources()
        print("\n📚 Tillgängliga nyhetskällor:\n")
        for key, info in sources.items():
            rss_icon = "📡" if info.get('rss_feeds') else "  "
            print(f"  {rss_icon} {key:15} - {info['name']} ({info['type']})")
            print(f"                     {info['base_url']}")
        print("\n  📡 = RSS-stöd tillgängligt\n")
    
    elif args.command == 'health':
        print("\n🏥 Kontrollerar källornas status...\n")
        for source in client.get_available_sources():
            health = client.check_health(source)
            status = "✅" if health.get('available') else "❌"
            
            rss_status = ""
            if health['rss'].get('available'):
                rss_status = f"RSS: ✅ ({health['rss'].get('article_count', 0)} artiklar)"
            elif 'rss_feeds' in client.SOURCES.get(source, {}):
                rss_status = "RSS: ❌"
            
            scrape_status = ""
            if health['scrape'].get('available'):
                scrape_status = f"Scrape: ✅ ({health['scrape'].get('article_count', 0)} artiklar)"
            else:
                scrape_status = "Scrape: ❌"
            
            print(f"  {source:15} {status}")
            if args.verbose or not health.get('available'):
                if rss_status:
                    print(f"                    {rss_status}")
                print(f"                    {scrape_status}")
        print()
    
    elif args.command == 'rss':
        feeds = client.get_rss_feeds(args.source if args.source else None)
        print("\n📡 Tillgängliga RSS-flöden:\n")
        for source, urls in feeds.items():
            print(f"  {source}:")
            for url in urls:
                print(f"    • {url}")
        print()
    
    elif args.command == 'rss-health':
        print("\n📡 Testar RSS-flödens status...\n")
        results = client.check_rss_health(args.source if args.source else None)
        for source, info in results.items():
            if not info.get('has_rss'):
                print(f"  {source:15} - Inget RSS-stöd")
                continue
            
            status = "✅" if info.get('any_available') else "❌"
            print(f"  {source:15} {status}")
            for feed in info.get('feeds', []):
                feed_status = "✅" if feed['available'] else "❌"
                entry_count = f"({feed.get('entry_count', 0)} artiklar)" if feed['available'] else f"(Error: {feed.get('error', 'Unknown')})"
                print(f"    {feed_status} {feed['url']}")
                print(f"       {entry_count} - {feed.get('response_time_ms', '?')}ms")
        print()
    
    else:
        parser.print_help()


def main_with_nyt():
    """Utökat kommandoradsverktyg med NYT-stöd"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Hämta och sök nyheter från svenska källor och New York Times'
    )
    subparsers = parser.add_subparsers(dest='command', help='Kommando')
    
    # =====================================================================
    # SVENSKA KÄLLOR
    # =====================================================================
    
    # latest kommando
    latest_parser = subparsers.add_parser('latest', help='Hämta senaste nyheterna (svenska källor)')
    latest_parser.add_argument('source', help='Nyhetskälla (breakit, di, realtid, etc.)')
    latest_parser.add_argument('-n', '--limit', type=int, default=10, help='Max antal artiklar')
    latest_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    latest_parser.add_argument('--rss-only', action='store_true', help='Använd endast RSS')
    latest_parser.add_argument('--no-rss', action='store_true', help='Använd endast scraping')
    
    # search kommando
    search_parser = subparsers.add_parser('search', help='Sök efter nyheter (svenska källor)')
    search_parser.add_argument('query', help='Sökord')
    search_parser.add_argument('-s', '--sources', nargs='+', help='Källor att söka i')
    search_parser.add_argument('-n', '--limit', type=int, default=10, help='Max antal resultat')
    search_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # sources kommando
    sources_parser = subparsers.add_parser('sources', help='Lista tillgängliga källor')
    
    # health kommando
    health_parser = subparsers.add_parser('health', help='Kontrollera källornas status')
    health_parser.add_argument('-v', '--verbose', action='store_true', help='Visa detaljerad status')
    health_parser.add_argument('--nyt', action='store_true', help='Inkludera NYT API status')
    
    # rss kommando
    rss_parser = subparsers.add_parser('rss', help='Lista tillgängliga RSS-flöden')
    rss_parser.add_argument('source', nargs='?', help='Specifik källa (valfritt)')
    
    # rss-health kommando
    rss_health_parser = subparsers.add_parser('rss-health', help='Testa RSS-flödens status')
    rss_health_parser.add_argument('source', nargs='?', help='Specifik källa (valfritt)')
    
    # =====================================================================
    # NYT KOMMANDON
    # =====================================================================
    
    # nyt kommando - hämta senaste NYT-nyheter
    nyt_parser = subparsers.add_parser('nyt', help='Hämta senaste NYT-nyheter (Newswire)')
    nyt_parser.add_argument('section', nargs='?', default='all', 
                           help='Sektion (technology, business, world, all)')
    nyt_parser.add_argument('-n', '--limit', type=int, default=20, help='Max antal artiklar')
    nyt_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # nyt-tech kommando
    nyt_tech_parser = subparsers.add_parser('nyt-tech', help='Senaste tech-nyheter från NYT')
    nyt_tech_parser.add_argument('-n', '--limit', type=int, default=20, help='Max antal artiklar')
    nyt_tech_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # nyt-business kommando
    nyt_biz_parser = subparsers.add_parser('nyt-business', help='Senaste affärsnyheter från NYT')
    nyt_biz_parser.add_argument('-n', '--limit', type=int, default=20, help='Max antal artiklar')
    nyt_biz_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # nyt-search kommando - sök i NYT arkiv
    nyt_search_parser = subparsers.add_parser('nyt-search', help='Sök i NYT:s arkiv')
    nyt_search_parser.add_argument('query', help='Sökord')
    nyt_search_parser.add_argument('-d', '--days', type=int, default=30, 
                                   help='Antal dagar bakåt (default: 30)')
    nyt_search_parser.add_argument('-p', '--page', type=int, default=0, help='Sidnummer')
    nyt_search_parser.add_argument('--sort', choices=['newest', 'oldest', 'relevance', 'best'],
                                   default='newest', help='Sortering')
    nyt_search_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # nyt-sweden kommando - Sverige-relaterade artiklar
    nyt_sweden_parser = subparsers.add_parser('nyt-sweden', help='NYT-artiklar om Sverige')
    nyt_sweden_parser.add_argument('query', nargs='?', help='Extra sökord (valfritt)')
    nyt_sweden_parser.add_argument('-d', '--days', type=int, default=365, 
                                   help='Antal dagar bakåt (default: 365)')
    nyt_sweden_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # nyt-company kommando - sök efter svenskt företag
    nyt_company_parser = subparsers.add_parser('nyt-company', 
                                               help='NYT-artiklar om ett svenskt företag')
    nyt_company_parser.add_argument('company', help='Företagsnamn (t.ex. Klarna, Spotify)')
    nyt_company_parser.add_argument('-d', '--days', type=int, default=365, 
                                    help='Antal dagar bakåt (default: 365)')
    nyt_company_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # nyt-companies kommando - sök efter alla bevakade svenska företag
    nyt_companies_parser = subparsers.add_parser('nyt-companies', 
                                                  help='NYT-artiklar om svenska företag')
    nyt_companies_parser.add_argument('-d', '--days', type=int, default=30, 
                                      help='Antal dagar bakåt (default: 30)')
    nyt_companies_parser.add_argument('-n', '--limit', type=int, default=5, 
                                      help='Max artiklar per företag')
    nyt_companies_parser.add_argument('-j', '--json', action='store_true', help='Utdata som JSON')
    
    # nyt-sections kommando - lista NYT-sektioner
    nyt_sections_parser = subparsers.add_parser('nyt-sections', help='Lista NYT-sektioner')
    
    # nyt-health kommando - testa NYT API
    nyt_health_parser = subparsers.add_parser('nyt-health', help='Testa NYT API-status')
    
    args = parser.parse_args()
    
    # Initiera klienter
    swedish_client = SwedishNewsClient()
    nyt_client = NYTClient()
    
    # =====================================================================
    # HANTERA KOMMANDON
    # =====================================================================
    
    if args.command == 'latest':
        try:
            if args.rss_only:
                articles = swedish_client.get_latest_rss(args.source, args.limit)
                source_type = "RSS"
            elif args.no_rss:
                articles = swedish_client.get_latest(args.source, args.limit, prefer_rss=False)
                source_type = "scraping"
            else:
                articles = swedish_client.get_latest(args.source, args.limit)
                source_type = "RSS+scraping"
            
            if args.json:
                print(json.dumps([a.to_dict() for a in articles], ensure_ascii=False, indent=2))
            else:
                print(f"\n📰 Senaste från {args.source.upper()} ({len(articles)} artiklar via {source_type})\n")
                for i, a in enumerate(articles, 1):
                    rss_tag = " [RSS]" if a.source_type == 'rss' else ""
                    print(f"{i}. {a.title}{rss_tag}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at}")
                    if a.summary:
                        print(f"   {a.summary[:80]}...")
                    print()
        except ValueError as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'search':
        results = swedish_client.search(args.query, args.sources, args.limit)
        if args.json:
            print(json.dumps({
                'query': args.query,
                'total_count': results.total_count,
                'search_time_ms': results.search_time_ms,
                'articles': [a.to_dict() for a in results.articles]
            }, ensure_ascii=False, indent=2))
        else:
            print(f"\n🔍 Sökning: '{args.query}' ({results.total_count} träffar, {results.search_time_ms}ms)\n")
            for i, a in enumerate(results.articles, 1):
                rss_tag = " [RSS]" if a.source_type == 'rss' else ""
                print(f"{i}. [{a.source}] {a.title}{rss_tag}")
                print(f"   🔗 {a.url}")
                print()
    
    elif args.command == 'sources':
        sources = swedish_client.get_available_sources()
        print("\n📚 Tillgängliga svenska nyhetskällor:\n")
        for key, info in sources.items():
            rss_icon = "📡" if info.get('rss_feeds') else "  "
            print(f"  {rss_icon} {key:15} - {info['name']} ({info['type']})")
            print(f"                     {info['base_url']}")
        print("\n  📡 = RSS-stöd tillgängligt")
        print("\n🗽 NYT-kommandon: nyt, nyt-tech, nyt-business, nyt-search, nyt-sweden, nyt-company\n")
    
    elif args.command == 'health':
        print("\n🏥 Kontrollerar källornas status...\n")
        for source in swedish_client.get_available_sources():
            health = swedish_client.check_health(source)
            status = "✅" if health.get('available') else "❌"
            
            rss_status = ""
            if health['rss'].get('available'):
                rss_status = f"RSS: ✅ ({health['rss'].get('article_count', 0)} artiklar)"
            elif 'rss_feeds' in swedish_client.SOURCES.get(source, {}):
                rss_status = "RSS: ❌"
            
            scrape_status = ""
            if health['scrape'].get('available'):
                scrape_status = f"Scrape: ✅ ({health['scrape'].get('article_count', 0)} artiklar)"
            else:
                scrape_status = "Scrape: ❌"
            
            print(f"  {source:15} {status}")
            if args.verbose or not health.get('available'):
                if rss_status:
                    print(f"                    {rss_status}")
                print(f"                    {scrape_status}")
        
        if args.nyt:
            print("\n🗽 NYT API Status:")
            nyt_health = nyt_client.check_health()
            nw_status = "✅" if nyt_health['newswire'].get('available') else "❌"
            search_status = "✅" if nyt_health['search'].get('available') else "❌"
            print(f"  Newswire  {nw_status} ({nyt_health['newswire'].get('article_count', 0)} artiklar, {nyt_health['newswire'].get('response_time_ms', '?')}ms)")
            print(f"  Search    {search_status} ({nyt_health['search'].get('total_hits', 0)} träffar, {nyt_health['search'].get('response_time_ms', '?')}ms)")
        print()
    
    elif args.command == 'rss':
        feeds = swedish_client.get_rss_feeds(args.source if args.source else None)
        print("\n📡 Tillgängliga RSS-flöden:\n")
        for source, urls in feeds.items():
            print(f"  {source}:")
            for url in urls:
                print(f"    • {url}")
        print()
    
    elif args.command == 'rss-health':
        print("\n📡 Testar RSS-flödens status...\n")
        results = swedish_client.check_rss_health(args.source if args.source else None)
        for source, info in results.items():
            if not info.get('has_rss'):
                print(f"  {source:15} - Inget RSS-stöd")
                continue
            
            status = "✅" if info.get('any_available') else "❌"
            print(f"  {source:15} {status}")
            for feed in info.get('feeds', []):
                feed_status = "✅" if feed['available'] else "❌"
                entry_count = f"({feed.get('entry_count', 0)} artiklar)" if feed['available'] else f"(Error: {feed.get('error', 'Unknown')})"
                print(f"    {feed_status} {feed['url']}")
                print(f"       {entry_count} - {feed.get('response_time_ms', '?')}ms")
        print()
    
    # =====================================================================
    # NYT KOMMANDON
    # =====================================================================
    
    elif args.command == 'nyt':
        try:
            articles = nyt_client.get_newswire(section=args.section, limit=args.limit)
            if args.json:
                print(json.dumps([a.to_dict() for a in articles], ensure_ascii=False, indent=2))
            else:
                section_name = args.section.upper() if args.section != 'all' else 'ALLA SEKTIONER'
                print(f"\n🗽 NYT Newswire - {section_name} ({len(articles)} artiklar)\n")
                for i, a in enumerate(articles, 1):
                    print(f"{i}. {a.title}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at[:10]}")
                    if a.section:
                        print(f"   📁 {a.section}", end="")
                        if a.subsection:
                            print(f" > {a.subsection}", end="")
                        print()
                    if a.summary:
                        print(f"   {a.summary[:100]}...")
                    print()
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-tech':
        try:
            articles = nyt_client.get_tech_news(limit=args.limit)
            if args.json:
                print(json.dumps([a.to_dict() for a in articles], ensure_ascii=False, indent=2))
            else:
                print(f"\n🗽 NYT Tech News ({len(articles)} artiklar)\n")
                for i, a in enumerate(articles, 1):
                    print(f"{i}. {a.title}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at[:10]}")
                    if a.summary:
                        print(f"   {a.summary[:100]}...")
                    print()
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-business':
        try:
            articles = nyt_client.get_business_news(limit=args.limit)
            if args.json:
                print(json.dumps([a.to_dict() for a in articles], ensure_ascii=False, indent=2))
            else:
                print(f"\n🗽 NYT Business News ({len(articles)} artiklar)\n")
                for i, a in enumerate(articles, 1):
                    print(f"{i}. {a.title}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at[:10]}")
                    if a.summary:
                        print(f"   {a.summary[:100]}...")
                    print()
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-search':
        try:
            result = nyt_client.search_articles(
                query=args.query,
                days_back=args.days,
                sort=args.sort,
                page=args.page
            )
            articles = result['articles']
            
            if args.json:
                print(json.dumps({
                    'query': args.query,
                    'total_hits': result['total_hits'],
                    'page': result['page'],
                    'articles': [a.to_dict() for a in articles]
                }, ensure_ascii=False, indent=2))
            else:
                print(f"\n🔍 NYT Sökning: '{args.query}' ({result['total_hits']} träffar totalt)\n")
                print(f"   Visar sida {args.page + 1}, {len(articles)} artiklar\n")
                for i, a in enumerate(articles, 1):
                    print(f"{i}. {a.title}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at[:10]}")
                    if a.desk:
                        print(f"   📁 {a.desk}")
                    if a.summary:
                        print(f"   {a.summary[:100]}...")
                    print()
                
                if result['total_hits'] > (args.page + 1) * 10:
                    print(f"   💡 Fler resultat finns. Använd --page {args.page + 1} för nästa sida.")
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-sweden':
        try:
            result = nyt_client.search_sweden(query=args.query, days_back=args.days)
            articles = result['articles']
            
            if args.json:
                print(json.dumps({
                    'query': args.query or 'Sweden',
                    'total_hits': result['total_hits'],
                    'articles': [a.to_dict() for a in articles]
                }, ensure_ascii=False, indent=2))
            else:
                query_text = f" + '{args.query}'" if args.query else ""
                print(f"\n🇸🇪 NYT om Sverige{query_text} ({result['total_hits']} träffar, senaste {args.days} dagar)\n")
                for i, a in enumerate(articles, 1):
                    print(f"{i}. {a.title}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at[:10]}")
                    if a.keywords:
                        geo_tags = [k for k in a.keywords if any(loc in k for loc in ['Sweden', 'Stockholm', 'Europe'])]
                        if geo_tags:
                            print(f"   📍 {', '.join(geo_tags[:3])}")
                    if a.summary:
                        print(f"   {a.summary[:100]}...")
                    print()
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-company':
        try:
            result = nyt_client.search_swedish_company(args.company, days_back=args.days)
            articles = result['articles']
            
            if args.json:
                print(json.dumps({
                    'company': args.company,
                    'total_hits': result['total_hits'],
                    'articles': [a.to_dict() for a in articles]
                }, ensure_ascii=False, indent=2))
            else:
                print(f"\n🏢 NYT om {args.company} ({result['total_hits']} träffar, senaste {args.days} dagar)\n")
                if not articles:
                    print("   Inga artiklar hittades.")
                for i, a in enumerate(articles, 1):
                    print(f"{i}. {a.title}")
                    print(f"   🔗 {a.url}")
                    if a.published_at:
                        print(f"   📅 {a.published_at[:10]}")
                    if a.summary:
                        print(f"   {a.summary[:100]}...")
                    print()
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-companies':
        try:
            print(f"\n🏢 Söker efter svenska företag i NYT (senaste {args.days} dagar)...\n")
            results = nyt_client.search_swedish_companies(
                days_back=args.days,
                limit_per_company=args.limit
            )
            
            if args.json:
                output = {}
                for company, articles in results.items():
                    output[company] = [a.to_dict() for a in articles]
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                if not results:
                    print("   Inga artiklar hittades för bevakade företag.")
                    print(f"\n   Bevakade företag: {', '.join(SWEDISH_COMPANIES[:10])}...")
                else:
                    total = sum(len(articles) for articles in results.values())
                    print(f"   Hittade {total} artiklar för {len(results)} företag:\n")
                    
                    for company, articles in results.items():
                        print(f"🏢 {company} ({len(articles)} artiklar)")
                        for a in articles:
                            print(f"   • {a.title[:60]}...")
                            print(f"     {a.url}")
                            if a.published_at:
                                print(f"     📅 {a.published_at[:10]}")
                        print()
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-sections':
        try:
            sections = nyt_client.get_sections()
            print("\n📁 NYT Sektioner:\n")
            for s in sections:
                print(f"  {s.get('section', ''):20} - {s.get('display_name', '')}")
            print()
        except Exception as e:
            print(f"❌ Fel: {e}")
    
    elif args.command == 'nyt-health':
        print("\n🗽 Testar NYT API...\n")
        health = nyt_client.check_health()
        
        overall = "✅" if health['available'] else "❌"
        print(f"  Overall:   {overall}\n")
        
        nw = health['newswire']
        nw_status = "✅" if nw.get('available') else "❌"
        print(f"  Newswire:  {nw_status}")
        if nw.get('available'):
            print(f"             {nw.get('article_count', 0)} artiklar, {nw.get('response_time_ms', '?')}ms")
        else:
            print(f"             Error: {nw.get('error', 'Unknown')}")
        
        search = health['search']
        search_status = "✅" if search.get('available') else "❌"
        print(f"  Search:    {search_status}")
        if search.get('available'):
            print(f"             {search.get('total_hits', 0)} träffar, {search.get('response_time_ms', '?')}ms")
        else:
            print(f"             Error: {search.get('error', 'Unknown')}")
        print()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main_with_nyt()
