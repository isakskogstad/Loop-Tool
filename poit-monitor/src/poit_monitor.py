#!/usr/bin/env python3
"""
POIT Monitor Service - Komplett övervakningsworkflow

Koordinerar:
1. Scraping av POIT via Playwright
2. Lagring av kungörelser i Supabase
3. Matchning mot bevakade företag
4. Skapande av notifikationer
5. Utskick av email via Resend

Kräver environment variables:
- SUPABASE_URL
- SUPABASE_KEY (service role key)
- RESEND_API_KEY
"""

import os
import asyncio
import hashlib
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from supabase import create_client, Client

# Lokala imports - använder undetected-chromedriver scraper
from src.scrapers.poit_scraper import (
    POITScraper,
    POITAnnouncement,
    ScrapeResult,
    extract_orgnrs
)


@dataclass
class SyncStats:
    """Statistik för en sync-körning"""
    sync_id: Optional[str] = None
    started_at: str = ""
    completed_at: Optional[str] = None
    announcements_found: int = 0
    announcements_new: int = 0
    matches_found: int = 0
    notifications_created: int = 0
    notifications_sent: int = 0
    errors: List[str] = None
    status: str = "running"
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class POITMonitorService:
    """
    Huvudservice för POIT-övervakning.
    
    Workflow:
    1. Scrapa POIT-kategorier
    2. Lagra nya kungörelser (deduplicera)
    3. Hämta alla bevakade orgnr
    4. Matcha kungörelser mot bevakningar
    5. Skapa notifikationer
    6. Skicka email
    7. Uppdatera statistik
    """
    
    DEFAULT_CATEGORIES = [
        "konkurser",
        "bolagsverkets_registreringar",
        "kallelser",
        "skuldsaneringar",
        "familjeratt"
    ]
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        resend_api_key: Optional[str] = None,
        debug: bool = False
    ):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.resend_api_key = resend_api_key or os.environ.get("RESEND_API_KEY")
        self.debug = debug
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY required")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self._stats = SyncStats(started_at=datetime.now().isoformat())
    
    def _log(self, msg: str):
        if self.debug:
            print(f"[POITMonitor] {msg}")
    
    def _generate_content_hash(self, ann: POITAnnouncement) -> str:
        """Genererar hash för deduplicering"""
        content = f"{ann.category}|{ann.title or ''}|{ann.content or ''}|{ann.announcement_date}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    async def run_sync(
        self,
        categories: Optional[List[str]] = None,
        limit_per_category: int = 100,
        send_notifications: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Kör komplett sync-workflow.
        
        Args:
            categories: Kategorier att scrapa (None = alla)
            limit_per_category: Max kungörelser per kategori
            send_notifications: Om email ska skickas
            dry_run: Om True, ingen databas-skrivning
        
        Returns:
            Dict med sync-statistik
        """
        self._log("=" * 60)
        self._log("POIT Monitor Sync - Startar")
        self._log("=" * 60)
        
        if categories is None:
            categories = self.DEFAULT_CATEGORIES
        
        # 1. Skapa sync-statistik i databasen
        if not dry_run:
            await self._create_sync_record()
        
        try:
            # 2. Scrapa POIT
            self._log("\n📡 Steg 1: Scrapar POIT...")
            scrape_results = await self._scrape_poit(categories, limit_per_category)
            
            # 3. Lagra nya kungörelser
            self._log("\n💾 Steg 2: Lagrar kungörelser...")
            new_announcements = await self._store_announcements(scrape_results, dry_run)
            
            # 4. Hämta bevakade företag
            self._log("\n👀 Steg 3: Hämtar bevakningar...")
            watchlist = await self._get_all_watchlist_orgnrs()
            
            # 5. Matcha och skapa notifikationer
            self._log("\n🔍 Steg 4: Matchar mot bevakningar...")
            notifications = await self._match_and_create_notifications(
                new_announcements, 
                watchlist,
                dry_run
            )
            
            # 6. Skicka email
            if send_notifications and not dry_run and notifications:
                self._log("\n📧 Steg 5: Skickar notifikationer...")
                sent_count = await self._send_notifications()
                self._stats.notifications_sent = sent_count
            
            self._stats.status = "completed"
            self._stats.completed_at = datetime.now().isoformat()
            
        except Exception as e:
            self._stats.errors.append(str(e))
            self._stats.status = "failed"
            self._log(f"❌ Fel: {e}")
            raise
        
        finally:
            # 7. Uppdatera sync-statistik
            if not dry_run:
                await self._update_sync_record()
        
        # Sammanfattning
        self._log("\n" + "=" * 60)
        self._log("📊 Sync-sammanfattning:")
        self._log(f"   Kungörelser hittade: {self._stats.announcements_found}")
        self._log(f"   Nya kungörelser: {self._stats.announcements_new}")
        self._log(f"   Matchningar: {self._stats.matches_found}")
        self._log(f"   Notifikationer skapade: {self._stats.notifications_created}")
        self._log(f"   Email skickade: {self._stats.notifications_sent}")
        self._log(f"   Status: {self._stats.status}")
        self._log("=" * 60)
        
        return {
            "sync_id": self._stats.sync_id,
            "status": self._stats.status,
            "announcements_found": self._stats.announcements_found,
            "announcements_new": self._stats.announcements_new,
            "matches_found": self._stats.matches_found,
            "notifications_created": self._stats.notifications_created,
            "notifications_sent": self._stats.notifications_sent,
            "errors": self._stats.errors,
            "started_at": self._stats.started_at,
            "completed_at": self._stats.completed_at
        }
    
    async def _create_sync_record(self):
        """Skapar sync-statistik i databasen."""
        try:
            result = self.supabase.table("poit_sync_stats").insert({
                "sync_date": date.today().isoformat(),
                "sync_started_at": self._stats.started_at,
                "status": "running"
            }).execute()
            
            if result.data:
                self._stats.sync_id = result.data[0]["id"]
                self._log(f"Sync ID: {self._stats.sync_id}")
        except Exception as e:
            self._log(f"Varning: Kunde inte skapa sync-record: {e}")
    
    async def _update_sync_record(self):
        """Uppdaterar sync-statistik i databasen."""
        if not self._stats.sync_id:
            return
        
        try:
            self.supabase.table("poit_sync_stats").update({
                "sync_completed_at": self._stats.completed_at,
                "announcements_found": self._stats.announcements_found,
                "announcements_new": self._stats.announcements_new,
                "notifications_sent": self._stats.notifications_sent,
                "status": self._stats.status,
                "errors": self._stats.errors if self._stats.errors else None
            }).eq("id", self._stats.sync_id).execute()
        except Exception as e:
            self._log(f"Varning: Kunde inte uppdatera sync-record: {e}")
    
    async def _scrape_poit(
        self,
        categories: List[str],
        limit: int
    ) -> Dict[str, ScrapeResult]:
        """Scrapar POIT-kategorier med undetected-chromedriver."""
        # Kör synkron scraper (UC fungerar ej asynkront)
        # OBS: headless=False krävs för att undvika CAPTCHA
        with POITScraper(headless=False, debug=self.debug) as scraper:
            results = scraper.scrape_all_categories(
                categories=categories,
                limit_per_category=limit
            )

            # Räkna totalt
            for result in results.values():
                self._stats.announcements_found += result.total_found

            return results
    
    async def _store_announcements(
        self, 
        scrape_results: Dict[str, ScrapeResult],
        dry_run: bool
    ) -> List[Dict]:
        """
        Lagrar nya kungörelser i databasen.
        Deduplicerar baserat på poit_id (content hash).
        
        Returns:
            Lista med nyligen tillagda kungörelser
        """
        new_announcements = []
        
        for category, result in scrape_results.items():
            if not result.success:
                self._stats.errors.append(f"{category}: {result.error}")
                continue
            
            for ann in result.announcements:
                # Generera poit_id om saknas
                if not ann.poit_id:
                    ann.poit_id = self._generate_content_hash(ann)
                
                if dry_run:
                    new_announcements.append(ann.to_dict())
                    self._stats.announcements_new += 1
                    continue
                
                # Försök infoga (kommer misslyckas om duplicat pga UNIQUE constraint)
                try:
                    record = {
                        "poit_id": ann.poit_id,
                        "category": ann.category,
                        "subcategory": ann.subcategory,
                        "title": ann.title,
                        "content": ann.content,
                        "announcement_date": ann.announcement_date,
                        "source_url": ann.source_url,
                        "extracted_orgnrs": ann.extracted_orgnrs
                    }
                    
                    result = self.supabase.table("poit_announcements").upsert(
                        record,
                        on_conflict="poit_id"
                    ).execute()
                    
                    if result.data:
                        new_announcements.append(result.data[0])
                        self._stats.announcements_new += 1
                        
                except Exception as e:
                    self._log(f"Fel vid lagring: {e}")
        
        self._log(f"Lagrade {self._stats.announcements_new} nya kungörelser")
        return new_announcements
    
    async def _get_all_watchlist_orgnrs(self) -> Dict[str, List[Dict]]:
        """
        Hämtar alla bevakade organisationsnummer.
        
        Returns:
            Dict: orgnr -> lista med user_watchlist records
        """
        try:
            result = self.supabase.table("user_watchlists").select(
                "id, user_id, orgnr, company_name, alert_categories, email_notifications"
            ).eq("email_notifications", True).execute()
            
            # Gruppera per orgnr
            watchlist: Dict[str, List[Dict]] = {}
            for record in result.data or []:
                orgnr = record["orgnr"]
                if orgnr not in watchlist:
                    watchlist[orgnr] = []
                watchlist[orgnr].append(record)
            
            self._log(f"Hämtade {len(watchlist)} unika orgnr med {len(result.data or [])} bevakningar")
            return watchlist
            
        except Exception as e:
            self._log(f"Fel vid hämtning av watchlist: {e}")
            return {}
    
    async def _match_and_create_notifications(
        self,
        announcements: List[Dict],
        watchlist: Dict[str, List[Dict]],
        dry_run: bool
    ) -> List[Dict]:
        """
        Matchar kungörelser mot bevakade företag och skapar notifikationer.
        
        Returns:
            Lista med skapade notifikationer
        """
        notifications = []
        
        if not watchlist:
            self._log("Inga bevakningar att matcha mot")
            return notifications
        
        watched_orgnrs: Set[str] = set(watchlist.keys())
        
        for ann in announcements:
            # Hämta extraherade orgnr från kungörelsen
            extracted = ann.get("extracted_orgnrs", [])
            
            # Hitta matchningar
            matches = set(extracted) & watched_orgnrs
            
            for orgnr in matches:
                self._stats.matches_found += 1
                
                # Skapa notifikation för varje användare som bevakar detta orgnr
                for watch_record in watchlist[orgnr]:
                    user_id = watch_record["user_id"]
                    
                    # Kolla om kategori matchar användarens filter
                    alert_categories = watch_record.get("alert_categories", [])
                    if alert_categories and ann.get("category") not in alert_categories:
                        continue
                    
                    if dry_run:
                        notifications.append({
                            "user_id": user_id,
                            "announcement_id": ann.get("id"),
                            "orgnr": orgnr,
                            "status": "pending"
                        })
                        self._stats.notifications_created += 1
                        continue
                    
                    # Skapa notifikation i databasen
                    try:
                        result = self.supabase.table("poit_notifications").insert({
                            "user_id": user_id,
                            "announcement_id": ann["id"],
                            "orgnr": orgnr,
                            "status": "pending"
                        }).execute()
                        
                        if result.data:
                            notifications.append(result.data[0])
                            self._stats.notifications_created += 1
                            
                    except Exception as e:
                        # Ignorera duplicat (unique constraint)
                        if "duplicate" not in str(e).lower():
                            self._log(f"Fel vid skapande av notifikation: {e}")
        
        self._log(f"Skapade {self._stats.notifications_created} notifikationer")
        return notifications
    
    async def _send_notifications(self) -> int:
        """
        Skickar pending notifikationer via email.
        
        Returns:
            Antal skickade email
        """
        try:
            # Importera notification service
            from src.poit_notifications import send_pending_notifications
            return await send_pending_notifications(limit=100)
        except ImportError:
            self._log("poit_notifications modul ej tillgänglig")
            return 0
        except Exception as e:
            self._log(f"Fel vid utskick: {e}")
            self._stats.errors.append(f"Email error: {e}")
            return 0


# ============================================================
# Convenience-funktioner
# ============================================================

async def run_poit_sync(
    categories: Optional[List[str]] = None,
    send_notifications: bool = True,
    dry_run: bool = False,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Convenience-funktion för att köra sync.
    
    Args:
        categories: Kategorier att scrapa
        send_notifications: Om email ska skickas
        dry_run: Testläge utan databas-skrivning
        debug: Verbose output
    
    Returns:
        Sync-statistik
    """
    service = POITMonitorService(debug=debug)
    return await service.run_sync(
        categories=categories,
        send_notifications=send_notifications,
        dry_run=dry_run
    )


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="POIT Monitor Sync Service")
    parser.add_argument("--dry-run", action="store_true", help="Kör utan att skriva till databas")
    parser.add_argument("--no-notify", action="store_true", help="Skicka inga email")
    parser.add_argument("--categories", nargs="+", help="Specifika kategorier att scrapa")
    parser.add_argument("--debug", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    result = asyncio.run(run_poit_sync(
        categories=args.categories,
        send_notifications=not args.no_notify,
        dry_run=args.dry_run,
        debug=args.debug
    ))
    
    print(f"\nResultat: {result['status']}")
    if result['errors']:
        print(f"Fel: {result['errors']}")
