#!/usr/bin/env python3
"""
POIT API Endpoints - FastAPI Router för POIT-bevakning

Endpoints:
- GET/POST/PUT/DELETE /watchlist - Hantera bevakningar
- GET /poit/announcements - Hämta kungörelser
- GET /poit/sync-stats - Sync-statistik
- GET /poit/notifications - Notifikationshistorik

Integreras med befintlig FastAPI-app via:
    from src.poit_api import poit_router
    app.include_router(poit_router, prefix="/api/v1")
"""

import os
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from supabase import create_client, Client


# ============================================================
# Pydantic Models
# ============================================================

class WatchlistItem(BaseModel):
    """En bevakad företag"""
    id: Optional[str] = None
    user_id: str
    orgnr: str
    company_name: Optional[str] = None
    alert_categories: List[str] = Field(
        default=["konkurser", "bolagsverkets_registreringar", "kallelser", "skuldsaneringar"]
    )
    email_notifications: bool = True
    created_at: Optional[str] = None


class WatchlistCreate(BaseModel):
    """Request för att lägga till bevakning"""
    orgnr: str
    company_name: Optional[str] = None
    alert_categories: Optional[List[str]] = None
    email_notifications: bool = True


class WatchlistUpdate(BaseModel):
    """Request för att uppdatera bevakning"""
    company_name: Optional[str] = None
    alert_categories: Optional[List[str]] = None
    email_notifications: Optional[bool] = None


class Announcement(BaseModel):
    """En POIT-kungörelse"""
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
    created_at: Optional[str] = None


class SyncStats(BaseModel):
    """Sync-statistik"""
    id: str
    sync_date: str
    sync_started_at: str
    sync_completed_at: Optional[str] = None
    announcements_found: int = 0
    announcements_new: int = 0
    notifications_sent: int = 0
    status: str
    errors: Optional[List[str]] = None


class NotificationRecord(BaseModel):
    """En notifikation"""
    id: str
    user_id: str
    announcement_id: str
    orgnr: str
    status: str
    email_sent_at: Optional[str] = None
    created_at: Optional[str] = None


class APIResponse(BaseModel):
    """Standard API-response"""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


# ============================================================
# Router
# ============================================================

poit_router = APIRouter(tags=["POIT Bevakning"])


def get_supabase() -> Client:
    """Dependency för Supabase-klient."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase configuration missing")
    
    return create_client(url, key)


# ============================================================
# Watchlist Endpoints
# ============================================================

@poit_router.get("/watchlist", response_model=List[WatchlistItem])
async def get_watchlist(
    user_id: str = Query(..., description="User ID"),
    supabase: Client = Depends(get_supabase)
):
    """
    Hämta användarens bevakningslista.
    
    Returns:
        Lista med bevakade företag
    """
    try:
        result = supabase.table("user_watchlists").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()
        
        return result.data or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@poit_router.post("/watchlist", response_model=WatchlistItem)
async def add_to_watchlist(
    item: WatchlistCreate,
    user_id: str = Query(..., description="User ID"),
    supabase: Client = Depends(get_supabase)
):
    """
    Lägg till ett företag i bevakningslistan.
    
    - Validerar orgnr-format
    - Hämtar företagsnamn från loop_table om ej angivet
    """
    # Validera orgnr
    orgnr = item.orgnr.replace("-", "").replace(" ", "")
    if len(orgnr) != 10 or not orgnr.isdigit():
        raise HTTPException(status_code=400, detail="Ogiltigt organisationsnummer")
    
    # Formatera med bindestreck
    formatted_orgnr = f"{orgnr[:6]}-{orgnr[6:]}"
    
    # Hämta företagsnamn om ej angivet
    company_name = item.company_name
    if not company_name:
        try:
            name_result = supabase.table("loop_table").select(
                "name"
            ).eq("orgnr", formatted_orgnr).limit(1).execute()
            
            if name_result.data:
                company_name = name_result.data[0].get("name")
        except:
            pass
    
    # Skapa bevakning
    try:
        record = {
            "user_id": user_id,
            "orgnr": formatted_orgnr,
            "company_name": company_name,
            "alert_categories": item.alert_categories or [
                "konkurser", "bolagsverkets_registreringar", 
                "kallelser", "skuldsaneringar"
            ],
            "email_notifications": item.email_notifications
        }
        
        result = supabase.table("user_watchlists").insert(record).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=500, detail="Kunde inte skapa bevakning")
            
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(
                status_code=409, 
                detail="Företaget finns redan i din bevakningslista"
            )
        raise HTTPException(status_code=500, detail=str(e))


@poit_router.put("/watchlist/{orgnr}", response_model=WatchlistItem)
async def update_watchlist_item(
    orgnr: str,
    update: WatchlistUpdate,
    user_id: str = Query(..., description="User ID"),
    supabase: Client = Depends(get_supabase)
):
    """
    Uppdatera inställningar för en bevakning.
    """
    # Formatera orgnr
    clean_orgnr = orgnr.replace("-", "")
    formatted_orgnr = f"{clean_orgnr[:6]}-{clean_orgnr[6:]}"
    
    # Bygg update-data
    update_data = {}
    if update.company_name is not None:
        update_data["company_name"] = update.company_name
    if update.alert_categories is not None:
        update_data["alert_categories"] = update.alert_categories
    if update.email_notifications is not None:
        update_data["email_notifications"] = update.email_notifications
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Ingen data att uppdatera")
    
    try:
        result = supabase.table("user_watchlists").update(
            update_data
        ).eq("user_id", user_id).eq("orgnr", formatted_orgnr).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=404, detail="Bevakning hittades inte")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@poit_router.delete("/watchlist/{orgnr}", response_model=APIResponse)
async def remove_from_watchlist(
    orgnr: str,
    user_id: str = Query(..., description="User ID"),
    supabase: Client = Depends(get_supabase)
):
    """
    Ta bort ett företag från bevakningslistan.
    """
    clean_orgnr = orgnr.replace("-", "")
    formatted_orgnr = f"{clean_orgnr[:6]}-{clean_orgnr[6:]}"
    
    try:
        result = supabase.table("user_watchlists").delete().eq(
            "user_id", user_id
        ).eq("orgnr", formatted_orgnr).execute()
        
        return APIResponse(
            success=True,
            message=f"Bevakning för {formatted_orgnr} borttagen"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# POIT Announcement Endpoints
# ============================================================

@poit_router.get("/poit/announcements", response_model=List[Announcement])
async def get_announcements(
    orgnr: Optional[str] = Query(None, description="Filtrera på orgnr"),
    category: Optional[str] = Query(None, description="Filtrera på kategori"),
    days: int = Query(7, description="Antal dagar bakåt", ge=1, le=90),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    supabase: Client = Depends(get_supabase)
):
    """
    Hämta POIT-kungörelser med filter.
    
    - Kan filtrera på orgnr (söker i extracted_orgnrs)
    - Kan filtrera på kategori
    - Begränsar till senaste X dagar
    """
    try:
        since_date = (date.today() - timedelta(days=days)).isoformat()
        
        query = supabase.table("poit_announcements").select("*").gte(
            "announcement_date", since_date
        )
        
        if category:
            query = query.eq("category", category)
        
        if orgnr:
            # Formatera orgnr
            clean_orgnr = orgnr.replace("-", "")
            formatted_orgnr = f"{clean_orgnr[:6]}-{clean_orgnr[6:]}"
            query = query.contains("extracted_orgnrs", [formatted_orgnr])
        
        result = query.order(
            "announcement_date", desc=True
        ).range(offset, offset + limit - 1).execute()
        
        return result.data or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@poit_router.get("/poit/user-announcements", response_model=List[Announcement])
async def get_user_announcements(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(50, ge=1, le=200),
    supabase: Client = Depends(get_supabase)
):
    """
    Hämta kungörelser för användarens bevakade företag.
    
    Matchar automatiskt mot användarens watchlist.
    """
    try:
        # Hämta användarens bevakade orgnr
        watchlist = supabase.table("user_watchlists").select(
            "orgnr"
        ).eq("user_id", user_id).execute()
        
        if not watchlist.data:
            return []
        
        watched_orgnrs = [w["orgnr"] for w in watchlist.data]
        
        # Hämta kungörelser som matchar
        since_date = (date.today() - timedelta(days=days)).isoformat()
        
        result = supabase.table("poit_announcements").select("*").gte(
            "announcement_date", since_date
        ).overlaps("extracted_orgnrs", watched_orgnrs).order(
            "announcement_date", desc=True
        ).limit(limit).execute()
        
        return result.data or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@poit_router.get("/companies/{orgnr}/poit-history", response_model=List[Announcement])
async def get_company_poit_history(
    orgnr: str,
    days: int = Query(365, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    supabase: Client = Depends(get_supabase)
):
    """
    Hämta POIT-historik för ett specifikt företag.
    """
    clean_orgnr = orgnr.replace("-", "")
    formatted_orgnr = f"{clean_orgnr[:6]}-{clean_orgnr[6:]}"
    
    try:
        since_date = (date.today() - timedelta(days=days)).isoformat()
        
        result = supabase.table("poit_announcements").select("*").contains(
            "extracted_orgnrs", [formatted_orgnr]
        ).gte("announcement_date", since_date).order(
            "announcement_date", desc=True
        ).limit(limit).execute()
        
        return result.data or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Sync & Notification Endpoints
# ============================================================

@poit_router.get("/poit/sync-stats", response_model=List[SyncStats])
async def get_sync_stats(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    supabase: Client = Depends(get_supabase)
):
    """
    Hämta sync-statistik.
    """
    try:
        since_date = (date.today() - timedelta(days=days)).isoformat()
        
        result = supabase.table("poit_sync_stats").select("*").gte(
            "sync_date", since_date
        ).order("sync_started_at", desc=True).limit(limit).execute()
        
        return result.data or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@poit_router.get("/poit/notifications", response_model=List[NotificationRecord])
async def get_user_notifications(
    user_id: str = Query(..., description="User ID"),
    status: Optional[str] = Query(None, description="Filtrera på status"),
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(50, ge=1, le=200),
    supabase: Client = Depends(get_supabase)
):
    """
    Hämta notifikationshistorik för en användare.
    """
    try:
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = supabase.table("poit_notifications").select("*").eq(
            "user_id", user_id
        ).gte("created_at", since_date)
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return result.data or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Health & Info
# ============================================================

@poit_router.get("/poit/categories")
async def get_poit_categories():
    """
    Returnerar tillgängliga POIT-kategorier.
    """
    return {
        "categories": [
            {"key": "konkurser", "name": "Konkurser", "description": "Konkursbeslut och utdelningsförslag"},
            {"key": "bolagsverkets_registreringar", "name": "Bolagsverkets registreringar", "description": "Aktiebolag, föreningar, handelsbolag"},
            {"key": "kallelser", "name": "Kallelser", "description": "Kallelse på borgenärer"},
            {"key": "skuldsaneringar", "name": "Skuldsaneringar", "description": "Skuldsaneringsärenden"},
            {"key": "familjeratt", "name": "Familjerätt", "description": "Bodelning, förvaltarskap"}
        ]
    }


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="POIT API Test")
    app.include_router(poit_router, prefix="/api/v1")
    
    print("Startar test-server på http://localhost:8001")
    print("API docs: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
