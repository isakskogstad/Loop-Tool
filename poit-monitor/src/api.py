#!/usr/bin/env python3
"""
POIT Monitor API - FastAPI endpoints för bevakningar och kungörelser

Kör lokalt:
    uvicorn src.api:app --reload --port 8000
"""

import os
from datetime import datetime, date
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# ============================================================
# App Setup
# ============================================================

app = FastAPI(
    title="POIT Monitor API",
    description="API för att hantera POIT-bevakningar och kungörelser",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Dependencies
# ============================================================

def get_supabase() -> Client:
    """Dependency för Supabase-klient."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(500, "Supabase credentials missing")
    return create_client(url, key)

# ============================================================
# Models
# ============================================================

class WatchlistItem(BaseModel):
    orgnr: str
    company_name: Optional[str] = None
    alert_categories: Optional[List[str]] = None
    email_notifications: bool = True

class WatchlistResponse(BaseModel):
    id: str
    user_id: Optional[str]
    orgnr: str
    company_name: Optional[str]
    alert_categories: List[str]
    email_notifications: bool
    created_at: str

class AnnouncementResponse(BaseModel):
    id: str
    poit_id: str
    category: str
    subcategory: Optional[str]
    title: Optional[str]
    content: Optional[str]
    announcement_date: str
    source_url: Optional[str]
    extracted_orgnrs: List[str]
    created_at: str

class SyncStatsResponse(BaseModel):
    id: str
    sync_date: str
    status: str
    announcements_found: int
    announcements_new: int
    notifications_sent: int

# ============================================================
# Health Check
# ============================================================

@app.get("/")
async def root():
    return {"status": "ok", "service": "POIT Monitor API"}

@app.get("/health")
async def health(db: Client = Depends(get_supabase)):
    """Health check med databas-verifiering."""
    try:
        result = db.table("poit_sync_stats").select("id").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(503, f"Database error: {e}")

# ============================================================
# Watchlist Endpoints
# ============================================================

@app.get("/api/v1/watchlist", response_model=List[WatchlistResponse])
async def get_watchlist(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: Client = Depends(get_supabase)
):
    """Hämta bevakningslista."""
    query = db.table("user_watchlists").select("*")
    
    if user_id:
        query = query.eq("user_id", user_id)
    
    result = query.order("created_at", desc=True).execute()
    return result.data or []

@app.post("/api/v1/watchlist", response_model=WatchlistResponse)
async def add_to_watchlist(
    item: WatchlistItem,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: Client = Depends(get_supabase)
):
    """Lägg till företag i bevakning."""
    data = {
        "user_id": user_id,
        "orgnr": item.orgnr,
        "company_name": item.company_name,
        "email_notifications": item.email_notifications
    }
    
    if item.alert_categories:
        data["alert_categories"] = item.alert_categories
    
    try:
        result = db.table("user_watchlists").insert(data).execute()
        if result.data:
            return result.data[0]
        raise HTTPException(500, "Failed to create watchlist item")
    except Exception as e:
        if "duplicate" in str(e).lower():
            raise HTTPException(409, "Already watching this company")
        raise HTTPException(500, str(e))

@app.delete("/api/v1/watchlist/{orgnr}")
async def remove_from_watchlist(
    orgnr: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: Client = Depends(get_supabase)
):
    """Ta bort företag från bevakning."""
    query = db.table("user_watchlists").delete().eq("orgnr", orgnr)
    
    if user_id:
        query = query.eq("user_id", user_id)
    
    result = query.execute()
    return {"deleted": True, "orgnr": orgnr}

# ============================================================
# Announcements Endpoints
# ============================================================

@app.get("/api/v1/announcements", response_model=List[AnnouncementResponse])
async def get_announcements(
    orgnr: Optional[str] = Query(None, description="Filter by orgnr"),
    category: Optional[str] = Query(None, description="Filter by category"),
    days: int = Query(7, description="Days back to search"),
    limit: int = Query(50, description="Max results"),
    db: Client = Depends(get_supabase)
):
    """Hämta kungörelser med filter."""
    query = db.table("poit_announcements").select("*")
    
    if category:
        query = query.eq("category", category)
    
    if orgnr:
        query = query.contains("extracted_orgnrs", [orgnr])
    
    # Datum-filter
    from datetime import timedelta
    min_date = (date.today() - timedelta(days=days)).isoformat()
    query = query.gte("announcement_date", min_date)
    
    result = query.order("announcement_date", desc=True).limit(limit).execute()
    return result.data or []

@app.get("/api/v1/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: str,
    db: Client = Depends(get_supabase)
):
    """Hämta specifik kungörelse."""
    result = db.table("poit_announcements").select("*").eq("id", announcement_id).execute()
    
    if not result.data:
        raise HTTPException(404, "Announcement not found")
    
    return result.data[0]

# ============================================================
# Stats Endpoints
# ============================================================

@app.get("/api/v1/stats", response_model=List[SyncStatsResponse])
async def get_sync_stats(
    days: int = Query(7, description="Days of history"),
    db: Client = Depends(get_supabase)
):
    """Hämta sync-statistik."""
    from datetime import timedelta
    min_date = (date.today() - timedelta(days=days)).isoformat()
    
    result = db.table("poit_sync_stats").select(
        "id, sync_date, status, announcements_found, announcements_new, notifications_sent"
    ).gte("sync_date", min_date).order("sync_date", desc=True).execute()
    
    return result.data or []

@app.get("/api/v1/stats/summary")
async def get_stats_summary(
    db: Client = Depends(get_supabase)
):
    """Hämta sammanfattande statistik."""
    # Antal bevakningar
    watchlist = db.table("user_watchlists").select("id", count="exact").execute()
    
    # Antal kungörelser (senaste 30 dagar)
    from datetime import timedelta
    min_date = (date.today() - timedelta(days=30)).isoformat()
    announcements = db.table("poit_announcements").select(
        "id", count="exact"
    ).gte("announcement_date", min_date).execute()
    
    # Senaste sync
    last_sync = db.table("poit_sync_stats").select("*").order(
        "sync_started_at", desc=True
    ).limit(1).execute()
    
    return {
        "total_watchlist": watchlist.count or 0,
        "announcements_30d": announcements.count or 0,
        "last_sync": last_sync.data[0] if last_sync.data else None
    }

# ============================================================
# Companies Lookup (from loop_table)
# ============================================================

@app.get("/api/v1/companies/search")
async def search_companies(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, description="Max results"),
    db: Client = Depends(get_supabase)
):
    """Sök företag i loop_table för bevakning."""
    # Sök på namn eller orgnr
    result = db.table("loop_table").select(
        "orgnr, company_name"
    ).or_(
        f"company_name.ilike.%{q}%,orgnr.ilike.%{q}%"
    ).limit(limit).execute()
    
    return result.data or []

# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
