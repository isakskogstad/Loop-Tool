"""
POIT (Post- och Inrikes Tidningar) Sync Service

Syncs announcement data from Bolagsverket POIT to Supabase database.

Usage:
    # Run sync for today's stats
    python -m src.poit_sync
    
    # Or as module
    from src.poit_sync import sync_daily_stats
    await sync_daily_stats()

Note: Requires Chrome browser installed locally.
This script is designed to run on a local machine with browser access,
not on the Render server.
"""

import os
import asyncio
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dataclasses import asdict

try:
    from .scrapers.bolagsverket_poit import (
        BolagsverketPOITClient,
        get_poit_daily_stats,
        DailyStats,
        CategoryStats,
        Announcement
    )
    from .supabase_client import get_database
    from .logging_config import get_source_logger
except ImportError:
    # Running as script
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.scrapers.bolagsverket_poit import (
        BolagsverketPOITClient,
        get_poit_daily_stats,
        DailyStats,
        CategoryStats,
        Announcement
    )
    from src.supabase_client import get_database
    import logging
    def get_source_logger(name):
        return logging.getLogger(name)

logger = get_source_logger("poit_sync")


class POITSyncService:
    """
    Service for syncing POIT data to Supabase.
    
    Tables used:
    - poit_daily_stats: Daily category statistics
    - poit_announcements: Individual announcements (optional)
    """
    
    def __init__(self):
        self.db = get_database()
        self.client = None
    
    async def sync_daily_stats(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync today's POIT statistics to database.
        
        Args:
            force: Re-sync even if today's data already exists
            
        Returns:
            Dict with sync results
        """
        today = date.today().isoformat()
        
        # Check if already synced today (unless forced)
        if not force:
            existing = self._get_existing_stats(today)
            if existing:
                logger.info(f"Stats for {today} already exist, skipping (use force=True to re-sync)")
                return {
                    "status": "skipped",
                    "date": today,
                    "reason": "already_synced",
                    "existing_categories": len(existing.get("categories", {}))
                }
        
        # Initialize browser client
        logger.info("Starting POIT sync...")
        
        try:
            self.client = BolagsverketPOITClient(debug=True)
            
            if not self.client.initialize():
                return {
                    "status": "error",
                    "date": today,
                    "error": "Failed to initialize browser (CAPTCHA or connection error)"
                }
            
            # Get daily stats
            stats = self.client.get_daily_stats()
            
            if not stats:
                return {
                    "status": "error",
                    "date": today,
                    "error": "Failed to get daily stats"
                }
            
            # Store in database
            stored = self._store_daily_stats(stats)
            
            logger.info(f"Synced {len(stats.categories)} categories for {today}")
            
            return {
                "status": "success",
                "date": today,
                "categories_synced": len(stats.categories),
                "total_announcements": stats.total_announcements,
                "categories": {k: v.count for k, v in stats.categories.items()}
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                "status": "error",
                "date": today,
                "error": str(e)
            }
        finally:
            if self.client:
                self.client.close()
    
    async def sync_bankruptcies(self, limit: int = 100) -> Dict[str, Any]:
        """
        Sync today's bankruptcy announcements to database.
        
        Args:
            limit: Maximum announcements to sync
            
        Returns:
            Dict with sync results
        """
        today = date.today().isoformat()
        
        try:
            self.client = BolagsverketPOITClient(debug=True)
            
            if not self.client.initialize():
                return {
                    "status": "error",
                    "error": "Failed to initialize browser"
                }
            
            # Get bankruptcy announcements
            announcements = self.client.get_bankruptcies(limit=limit)
            
            if not announcements:
                return {
                    "status": "success",
                    "date": today,
                    "announcements_synced": 0
                }
            
            # Store in database
            stored_count = self._store_announcements(announcements, "konkurser")
            
            logger.info(f"Synced {stored_count} bankruptcy announcements for {today}")
            
            return {
                "status": "success",
                "date": today,
                "announcements_synced": stored_count
            }
            
        except Exception as e:
            logger.error(f"Bankruptcy sync failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            if self.client:
                self.client.close()
    
    def _get_existing_stats(self, date_str: str) -> Optional[Dict]:
        """Check if stats for date already exist."""
        try:
            result = self.db.client.table('poit_daily_stats') \
                .select('*') \
                .eq('date', date_str) \
                .limit(1) \
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning(f"Error checking existing stats: {e}")
            return None
    
    def _store_daily_stats(self, stats: DailyStats) -> bool:
        """Store daily stats in database."""
        try:
            # Prepare data
            data = {
                "date": stats.date,
                "scraped_at": stats.scraped_at or datetime.now().isoformat(),
                "total_announcements": stats.total_announcements,
                "categories": {
                    k: asdict(v) for k, v in stats.categories.items()
                }
            }
            
            # Upsert (insert or update)
            self.db.client.table('poit_daily_stats') \
                .upsert(data, on_conflict='date') \
                .execute()
            
            return True
        except Exception as e:
            logger.error(f"Error storing daily stats: {e}")
            return False
    
    def _store_announcements(
        self, 
        announcements: List[Announcement],
        category: str
    ) -> int:
        """Store announcements in database."""
        stored = 0
        
        for ann in announcements:
            try:
                data = {
                    "date": ann.published_date or date.today().isoformat(),
                    "category": category,
                    "subcategory": ann.subcategory,
                    "title": ann.title,
                    "company_name": ann.company_name,
                    "orgnr": ann.orgnr,
                    "content": ann.content,
                    "url": ann.url,
                    "raw_data": ann.raw_data
                }
                
                self.db.client.table('poit_announcements') \
                    .insert(data) \
                    .execute()
                
                stored += 1
            except Exception as e:
                logger.warning(f"Error storing announcement: {e}")
                continue
        
        return stored


# =============================================================================
# Convenience functions
# =============================================================================

async def sync_daily_stats(force: bool = False) -> Dict[str, Any]:
    """Quick function to sync daily stats."""
    service = POITSyncService()
    return await service.sync_daily_stats(force=force)


async def sync_bankruptcies(limit: int = 100) -> Dict[str, Any]:
    """Quick function to sync bankruptcy announcements."""
    service = POITSyncService()
    return await service.sync_bankruptcies(limit=limit)


def get_poit_sync_service() -> POITSyncService:
    """Factory function to create sync service."""
    return POITSyncService()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync POIT data to database")
    parser.add_argument("--force", action="store_true", help="Force re-sync")
    parser.add_argument("--bankruptcies", action="store_true", help="Sync bankruptcies")
    parser.add_argument("--limit", type=int, default=100, help="Max announcements")
    
    args = parser.parse_args()
    
    async def main():
        if args.bankruptcies:
            result = await sync_bankruptcies(limit=args.limit)
        else:
            result = await sync_daily_stats(force=args.force)
        
        print(f"\nSync result: {result}")
    
    asyncio.run(main())
