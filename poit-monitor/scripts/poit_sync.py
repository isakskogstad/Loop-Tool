#!/usr/bin/env python3
"""
POIT Sync CLI - Huvudscript för schemalagd körning

Användning:
    python scripts/poit_sync.py [--dry-run] [--debug] [--categories konkurser,kallelser]
    
Environment variables:
    SUPABASE_URL - Supabase project URL
    SUPABASE_KEY - Supabase service role key
    RESEND_API_KEY - Resend API key för email
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime

# Lägg till project root i path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.poit_monitor import POITMonitorService


def main():
    parser = argparse.ArgumentParser(
        description="POIT Monitor - Scrapa kungörelser och skicka notifikationer"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Kör utan att skriva till databas"
    )
    parser.add_argument(
        "--no-notify",
        action="store_true", 
        help="Skicka inga email-notifikationer"
    )
    parser.add_argument(
        "--categories",
        type=str,
        help="Kommaseparerad lista med kategorier (default: alla)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max kungörelser per kategori (default: 100)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Parse kategorier
    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]
    
    print("=" * 60)
    print(f"POIT Monitor Sync - {datetime.now().isoformat()}")
    print("=" * 60)
    print(f"Kategorier: {categories or 'alla'}")
    print(f"Dry run: {args.dry_run}")
    print(f"Notifikationer: {not args.no_notify}")
    print(f"Debug: {args.debug}")
    print("=" * 60)
    
    # Verifiera environment
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        print(f"❌ Saknade environment variables: {missing}")
        sys.exit(1)
    
    if not args.no_notify and not os.environ.get("RESEND_API_KEY"):
        print("⚠️  RESEND_API_KEY saknas - email-notifikationer inaktiverade")
    
    # Kör sync
    try:
        service = POITMonitorService(debug=args.debug)
        result = asyncio.run(service.run_sync(
            categories=categories,
            limit_per_category=args.limit,
            send_notifications=not args.no_notify,
            dry_run=args.dry_run
        ))
        
        # Exit code baserat på status
        if result["status"] == "completed":
            print(f"\n✅ Sync klar!")
            print(f"   Nya kungörelser: {result['announcements_new']}")
            print(f"   Matchningar: {result['matches_found']}")
            print(f"   Email skickade: {result['notifications_sent']}")
            sys.exit(0)
        else:
            print(f"\n❌ Sync misslyckades: {result['errors']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Kritiskt fel: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
