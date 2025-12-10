"""
POIT Watchlist API Endpoints

FastAPI router for POIT monitoring and watchlist functionality.
Include this router in the main API application.

Usage:
    from src.poit_api import poit_router
    app.include_router(poit_router, prefix="/api/v1")
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

try:
    from .supabase_client import get_database
    from .logging_config import get_source_logger
except ImportError:
    from src.supabase_client import get_database
    
    def get_source_logger(name):
        return logging.getLogger(name)

logger = get_source_logger("poit_api")


# =============================================================================
# Pydantic Models
# =============================================================================

class WatchlistEntry(BaseModel):
    """A company in the user's watchlist"""
    id: str
    user_id: str
    orgnr: str
    company_name: Optional[str] = None
    alert_categories: List[str] = ["konkurser", "bolagsverkets_registreringar", "kallelser", "skuldsaneringar"]
    email_notifications: bool = True
    created_at: str


class WatchlistAddRequest(BaseModel):
    """Request to add a company to watchlist"""
    orgnr: str = Field(..., min_length=10, max_length=12, description="Organisationsnummer (10 siffror)")
    company_name: Optional[str] = Field(None, max_length=200, description="Företagsnamn (valfritt)")
    alert_categories: Optional[List[str]] = Field(
        None,
        description="Kategorier att bevaka: konkurser, bolagsverkets_registreringar, kallelser, skuldsaneringar, familjeratt"
    )
    email_notifications: bool = Field(True, description="Skicka email-notifieringar")


class WatchlistUpdateRequest(BaseModel):
    """Request to update watchlist entry"""
    company_name: Optional[str] = None
    alert_categories: Optional[List[str]] = None
    email_notifications: Optional[bool] = None


class POITAnnouncementResponse(BaseModel):
    """A POIT announcement from the new monitoring system"""
    id: str
    poit_id: Optional[str] = None
    orgnr: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    announcement_date: str
    source_url: Optional[str] = None
    extracted_orgnrs: List[str] = []
    created_at: str


class SyncStatsResponse(BaseModel):
    """POIT sync run statistics"""
    id: str
    sync_date: str
    sync_started_at: str
    sync_completed_at: Optional[str] = None
    announcements_found: int = 0
    announcements_new: int = 0
    notifications_sent: int = 0
    status: str
    errors: Optional[List[str]] = None


# =============================================================================
# Router
# =============================================================================

poit_router = APIRouter(tags=["POIT Bevakning"])


# =============================================================================
# Helper Functions
# =============================================================================

def normalize_orgnr(orgnr: str) -> str:
    """Normalize org.nr to 10 digits without hyphen."""
    import re
    clean = re.sub(r'[-\s]', '', orgnr)
    if len(clean) == 12 and clean[:2] in ('16', '19', '20'):
        clean = clean[2:]
    return clean if len(clean) == 10 and clean.isdigit() else ""


def get_user_id_from_request(request: Request, user_id: Optional[str] = None) -> str:
    """
    Extract user ID from request.
    
    In a real implementation, this would come from:
    1. JWT token in Authorization header
    2. Session cookie
    3. API key with associated user
    
    For now, accepts explicit user_id parameter for testing.
    """
    # TODO: Implement proper auth extraction
    # For now, use the provided user_id parameter
    if user_id:
        return user_id
    
    # Try to get from header (for testing)
    return request.headers.get("X-User-ID", "")


# =============================================================================
# Watchlist Endpoints
# =============================================================================

@poit_router.get("/watchlist", response_model=List[WatchlistEntry])
async def get_watchlist(
    request: Request,
    user_id: str = Query(..., description="Användar-ID")
):
    """
    Hämta användarens bevakningslista.
    
    Returnerar alla företag som användaren bevakar med sina inställningar.
    """
    db = get_database()
    
    try:
        result = db.client.table('user_watchlists') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte hämta bevakningslistan")


@poit_router.post("/watchlist", response_model=WatchlistEntry)
async def add_to_watchlist(
    request: Request,
    data: WatchlistAddRequest,
    user_id: str = Query(..., description="Användar-ID")
):
    """
    Lägg till företag i bevakningslistan.
    
    Om företaget redan bevakas returneras det befintliga entryt.
    """
    db = get_database()
    
    # Normalize orgnr
    orgnr = normalize_orgnr(data.orgnr)
    if not orgnr:
        raise HTTPException(status_code=400, detail="Ogiltigt organisationsnummer")
    
    try:
        # Check if already exists
        existing = db.client.table('user_watchlists') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('orgnr', orgnr) \
            .limit(1) \
            .execute()
        
        if existing.data:
            return existing.data[0]
        
        # Try to get company name from loop_table if not provided
        company_name = data.company_name
        if not company_name:
            company_result = db.client.table('loop_table') \
                .select('company_name') \
                .eq('orgnr', orgnr) \
                .limit(1) \
                .execute()
            
            if company_result.data:
                company_name = company_result.data[0].get('company_name')
        
        # Create watchlist entry
        entry = {
            "user_id": user_id,
            "orgnr": orgnr,
            "company_name": company_name,
            "alert_categories": data.alert_categories or ["konkurser", "bolagsverkets_registreringar", "kallelser", "skuldsaneringar"],
            "email_notifications": data.email_notifications
        }
        
        result = db.client.table('user_watchlists') \
            .insert(entry) \
            .execute()
        
        if result.data:
            return result.data[0]
        
        raise HTTPException(status_code=500, detail="Kunde inte lägga till bevakning")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte lägga till bevakning")


@poit_router.put("/watchlist/{orgnr}", response_model=WatchlistEntry)
async def update_watchlist_entry(
    request: Request,
    orgnr: str,
    data: WatchlistUpdateRequest,
    user_id: str = Query(..., description="Användar-ID")
):
    """
    Uppdatera inställningar för en bevakning.
    
    Kan uppdatera:
    - company_name: Företagsnamn
    - alert_categories: Vilka kategorier att bevaka
    - email_notifications: Om email ska skickas
    """
    db = get_database()
    
    normalized_orgnr = normalize_orgnr(orgnr)
    if not normalized_orgnr:
        raise HTTPException(status_code=400, detail="Ogiltigt organisationsnummer")
    
    try:
        # Build update data
        update_data = {}
        if data.company_name is not None:
            update_data['company_name'] = data.company_name
        if data.alert_categories is not None:
            update_data['alert_categories'] = data.alert_categories
        if data.email_notifications is not None:
            update_data['email_notifications'] = data.email_notifications
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Ingen data att uppdatera")
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        result = db.client.table('user_watchlists') \
            .update(update_data) \
            .eq('user_id', user_id) \
            .eq('orgnr', normalized_orgnr) \
            .execute()
        
        if result.data:
            return result.data[0]
        
        raise HTTPException(status_code=404, detail="Bevakning hittades inte")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating watchlist: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte uppdatera bevakning")


@poit_router.delete("/watchlist/{orgnr}")
async def remove_from_watchlist(
    request: Request,
    orgnr: str,
    user_id: str = Query(..., description="Användar-ID")
):
    """
    Ta bort företag från bevakningslistan.
    """
    db = get_database()
    
    normalized_orgnr = normalize_orgnr(orgnr)
    if not normalized_orgnr:
        raise HTTPException(status_code=400, detail="Ogiltigt organisationsnummer")
    
    try:
        result = db.client.table('user_watchlists') \
            .delete() \
            .eq('user_id', user_id) \
            .eq('orgnr', normalized_orgnr) \
            .execute()
        
        return {
            "success": True,
            "message": f"Bevakning för {orgnr} borttagen"
        }
        
    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte ta bort bevakning")


# =============================================================================
# POIT Announcements Endpoints (Updated)
# =============================================================================

@poit_router.get("/poit/monitored-announcements", response_model=Dict[str, Any])
async def get_monitored_announcements(
    request: Request,
    category: Optional[str] = Query(None, description="Filtrera på kategori"),
    orgnr: Optional[str] = Query(None, description="Filtrera på org.nr"),
    days: int = Query(7, ge=1, le=30, description="Antal dagar bakåt"),
    limit: int = Query(50, ge=1, le=200, description="Max antal resultat")
):
    """
    Hämta kungörelser från POIT-övervakningssystemet.
    
    Denna endpoint använder det nya övervakningssystemet som:
    - Kör 2-3 gånger per dag
    - Extraherar org.nr automatiskt
    - Stödjer bevakningslistor
    
    **Kategorier:**
    - konkurser
    - bolagsverkets_registreringar  
    - kallelser
    - skuldsaneringar
    - familjeratt
    """
    db = get_database()
    
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = db.client.table('poit_announcements') \
            .select('*') \
            .gte('announcement_date', start_date)
        
        if category:
            query = query.ilike('category', f'%{category}%')
        
        if orgnr:
            normalized = normalize_orgnr(orgnr)
            if normalized:
                # Search in both orgnr field and extracted_orgnrs array
                query = query.or_(f"orgnr.eq.{normalized},extracted_orgnrs.cs.{{{normalized}}}")
        
        query = query.order('announcement_date', desc=True).limit(limit)
        
        result = query.execute()
        
        return {
            "antal": len(result.data) if result.data else 0,
            "filter": {
                "kategori": category,
                "orgnr": orgnr,
                "period_dagar": days
            },
            "kungorelser": result.data or [],
            "kalla": "POIT Monitor System"
        }
        
    except Exception as e:
        logger.error(f"Error getting announcements: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte hämta kungörelser")


@poit_router.get("/poit/user-announcements", response_model=Dict[str, Any])
async def get_user_watchlist_announcements(
    request: Request,
    user_id: str = Query(..., description="Användar-ID"),
    days: int = Query(7, ge=1, le=30, description="Antal dagar bakåt"),
    limit: int = Query(50, ge=1, le=200, description="Max antal resultat")
):
    """
    Hämta kungörelser för företag i användarens bevakningslista.
    
    Returnerar endast kungörelser för företag som användaren bevakar,
    filtrerade enligt användarens kategoripreferenser.
    """
    db = get_database()
    
    try:
        # Get user's watchlist
        watchlist = db.client.table('user_watchlists') \
            .select('orgnr, company_name, alert_categories') \
            .eq('user_id', user_id) \
            .execute()
        
        if not watchlist.data:
            return {
                "antal": 0,
                "meddelande": "Ingen bevakningslista hittad",
                "kungorelser": []
            }
        
        # Get all watched orgnrs
        watched_orgnrs = [entry['orgnr'] for entry in watchlist.data]
        orgnr_to_categories = {
            entry['orgnr']: entry.get('alert_categories', [])
            for entry in watchlist.data
        }
        orgnr_to_name = {
            entry['orgnr']: entry.get('company_name')
            for entry in watchlist.data
        }
        
        # Query announcements
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        announcements = []
        
        for orgnr in watched_orgnrs:
            result = db.client.table('poit_announcements') \
                .select('*') \
                .gte('announcement_date', start_date) \
                .or_(f"orgnr.eq.{orgnr},extracted_orgnrs.cs.{{{orgnr}}}") \
                .order('announcement_date', desc=True) \
                .limit(20) \
                .execute()
            
            if result.data:
                # Filter by user's category preferences
                categories = orgnr_to_categories.get(orgnr, [])
                
                for ann in result.data:
                    # Check category filter
                    ann_category = (ann.get('category') or '').lower()
                    category_key = ann_category.replace(' ', '_').replace('å', 'a').replace('ä', 'a').replace('ö', 'o')
                    
                    if not categories or category_key in categories or ann_category in categories:
                        ann['matched_orgnr'] = orgnr
                        ann['matched_company_name'] = orgnr_to_name.get(orgnr)
                        announcements.append(ann)
        
        # Sort by date and limit
        announcements.sort(key=lambda x: x.get('announcement_date', ''), reverse=True)
        announcements = announcements[:limit]
        
        return {
            "antal": len(announcements),
            "bevakade_foretag": len(watched_orgnrs),
            "period_dagar": days,
            "kungorelser": announcements
        }
        
    except Exception as e:
        logger.error(f"Error getting user announcements: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte hämta kungörelser")


# =============================================================================
# Sync Stats Endpoints
# =============================================================================

@poit_router.get("/poit/sync-stats", response_model=Dict[str, Any])
async def get_sync_stats(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Antal synkningar att visa")
):
    """
    Hämta statistik för POIT-synkningar.
    
    Visar senaste synkningskörningarna med antal hämtade och nya kungörelser.
    """
    db = get_database()
    
    try:
        result = db.client.table('poit_sync_stats') \
            .select('*') \
            .order('sync_started_at', desc=True) \
            .limit(limit) \
            .execute()
        
        stats = result.data or []
        
        # Calculate summary
        total_found = sum(s.get('announcements_found', 0) for s in stats)
        total_new = sum(s.get('announcements_new', 0) for s in stats)
        total_notifications = sum(s.get('notifications_sent', 0) for s in stats)
        
        return {
            "senaste_synkningar": stats,
            "sammanfattning": {
                "antal_synkningar": len(stats),
                "totalt_hittade": total_found,
                "totalt_nya": total_new,
                "totalt_notifieringar": total_notifications
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting sync stats: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte hämta synkstatistik")


@poit_router.get("/poit/notifications", response_model=Dict[str, Any])
async def get_user_notifications(
    request: Request,
    user_id: str = Query(..., description="Användar-ID"),
    status: Optional[str] = Query(None, description="Filtrera på status: pending, sent, failed, skipped"),
    limit: int = Query(50, ge=1, le=200, description="Max antal resultat")
):
    """
    Hämta användarens POIT-notifieringar.
    
    Visar historik över skickade och väntande notifieringar.
    """
    db = get_database()
    
    try:
        query = db.client.table('poit_notifications') \
            .select('*, poit_announcements(category, title, announcement_date)') \
            .eq('user_id', user_id)
        
        if status:
            query = query.eq('status', status)
        
        query = query.order('created_at', desc=True).limit(limit)
        
        result = query.execute()
        
        return {
            "antal": len(result.data) if result.data else 0,
            "filter": {"status": status},
            "notifieringar": result.data or []
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte hämta notifieringar")


# =============================================================================
# Company POIT Search
# =============================================================================

@poit_router.get("/companies/{orgnr}/poit-history", response_model=Dict[str, Any])
async def get_company_poit_history(
    request: Request,
    orgnr: str,
    days: int = Query(365, ge=1, le=730, description="Antal dagar bakåt (max 2 år)"),
    limit: int = Query(50, ge=1, le=200, description="Max antal resultat")
):
    """
    Hämta POIT-historik för ett specifikt företag.
    
    Söker i både det primära org.nr-fältet och i extraherade org.nr
    från kungörelsetexterna.
    """
    db = get_database()
    
    normalized = normalize_orgnr(orgnr)
    if not normalized:
        raise HTTPException(status_code=400, detail="Ogiltigt organisationsnummer")
    
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        result = db.client.table('poit_announcements') \
            .select('*') \
            .gte('announcement_date', start_date) \
            .or_(f"orgnr.eq.{normalized},extracted_orgnrs.cs.{{{normalized}}}") \
            .order('announcement_date', desc=True) \
            .limit(limit) \
            .execute()
        
        # Try to get company name
        company_name = None
        company_result = db.client.table('loop_table') \
            .select('company_name') \
            .eq('orgnr', normalized) \
            .limit(1) \
            .execute()
        
        if company_result.data:
            company_name = company_result.data[0].get('company_name')
        
        return {
            "orgnr": normalized,
            "foretag": company_name,
            "antal": len(result.data) if result.data else 0,
            "period_dagar": days,
            "kungorelser": result.data or [],
            "kalla": "POIT Monitor System"
        }
        
    except Exception as e:
        logger.error(f"Error getting company POIT history: {e}")
        raise HTTPException(status_code=500, detail="Kunde inte hämta företagets POIT-historik")
