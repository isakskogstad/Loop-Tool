#!/usr/bin/env python3
"""
POIT Monitor CLI - Entry point för GitHub Actions

Användning:
    python scripts/poit_monitor.py [options]

Options:
    --dry-run       Kör utan att skriva till databas eller skicka email
    --no-notify     Hoppa över email-utskick
    --categories    Lista med kategorier att scrapa
    --debug         Verbose output

Environment Variables:
    SUPABASE_URL    Supabase project URL
    SUPABASE_KEY    Supabase service role key
    RESEND_API_KEY  Resend API key för email

Exempel:
    # Full sync
    python scripts/poit_monitor.py --debug
    
    # Bara konkurser, utan email
    python scripts/poit_monitor.py --categories konkurser --no-notify
    
    # Dry run för testning
    python scripts/poit_monitor.py --dry-run --debug
"""

import os
import sys
import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Lägg till projektets rot i PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.poit_monitor import POITMonitorService


def check_environment():
    """Verifierar att nödvändiga environment variables är satta."""
    required = ["SUPABASE_URL", "SUPABASE_KEY"]
    optional = ["RESEND_API_KEY"]
    
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        print(f"❌ Saknade environment variables: {', '.join(missing)}")
        print("\nSätt dessa via:")
        for var in missing:
            print(f"  export {var}=<value>")
        return False
    
    # Varning för optional
    for var in optional:
        if not os.environ.get(var):
            print(f"⚠️  Varning: {var} ej satt - email-utskick inaktiverat")
    
    return True


async def run_sync(args):
    """Kör POIT sync."""
    print("=" * 60)
    print("POIT Monitor - Sync")
    print(f"Tid: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Visa konfiguration
    print(f"\nKonfiguration:")
    print(f"  Dry run: {args.dry_run}")
    print(f"  Skicka email: {not args.no_notify and not args.dry_run}")
    print(f"  Debug: {args.debug}")
    
    if args.categories:
        print(f"  Kategorier: {', '.join(args.categories)}")
    else:
        print(f"  Kategorier: Alla")
    
    print()
    
    try:
        # Skapa service
        service = POITMonitorService(debug=args.debug)
        
        # Kör sync
        result = await service.run_sync(
            categories=args.categories if args.categories else None,
            send_notifications=not args.no_notify,
            dry_run=args.dry_run
        )
        
        # Spara resultat till JSON
        output_path = "/tmp/poit_sync_result.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Resultat sparat till: {output_path}")
        
        # Exit code baserat på status
        if result["status"] == "completed":
            print("\n✅ Sync slutförd framgångsrikt!")
            return 0
        else:
            print(f"\n❌ Sync misslyckades: {result.get('errors', [])}")
            return 1
            
    except Exception as e:
        print(f"\n❌ Kritiskt fel: {e}")
        import traceback
        traceback.print_exc()
        return 2


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="POIT Monitor - Övervakar Post- och Inrikes Tidningar",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exempel:
  python scripts/poit_monitor.py                    # Full sync
  python scripts/poit_monitor.py --dry-run          # Test utan ändringar
  python scripts/poit_monitor.py --categories konkurser skuldsaneringar
  python scripts/poit_monitor.py --no-notify --debug
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kör utan att skriva till databas eller skicka email"
    )
    
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Hoppa över email-utskick"
    )
    
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=[
            "konkurser",
            "bolagsverkets_registreringar",
            "kallelser",
            "skuldsaneringar",
            "familjeratt"
        ],
        help="Specifika kategorier att scrapa"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Aktivera verbose output"
    )
    
    args = parser.parse_args()
    
    # Kontrollera environment
    if not args.dry_run and not check_environment():
        sys.exit(1)
    
    # Kör async
    exit_code = asyncio.run(run_sync(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
