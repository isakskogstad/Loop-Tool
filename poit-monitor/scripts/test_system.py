#!/usr/bin/env python3
"""
Systemtest - Verifierar att POIT Monitor är korrekt konfigurerat
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def test_environment():
    """Test 1: Environment variables"""
    print("\n📋 Test 1: Environment variables")
    
    required = ["SUPABASE_URL", "SUPABASE_KEY", "RESEND_API_KEY"]
    missing = []
    
    for var in required:
        value = os.environ.get(var)
        if value:
            print(f"  ✅ {var}: {value[:30]}...")
        else:
            print(f"  ❌ {var}: MISSING")
            missing.append(var)
    
    return len(missing) == 0

def test_database():
    """Test 2: Database connection"""
    print("\n📋 Test 2: Database connection")
    
    try:
        from supabase import create_client
        client = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_KEY")
        )
        
        # Test queries
        watchlist = client.table("user_watchlists").select("id", count="exact").execute()
        announcements = client.table("poit_announcements").select("id", count="exact").execute()
        notifications = client.table("poit_notifications").select("id", count="exact").execute()
        
        print(f"  ✅ Connected to Supabase")
        print(f"  📊 Watchlist entries: {watchlist.count}")
        print(f"  📊 Announcements: {announcements.count}")
        print(f"  📊 Notifications: {notifications.count}")
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_resend():
    """Test 3: Resend API"""
    print("\n📋 Test 3: Resend API")
    
    try:
        import resend
        resend.api_key = os.environ.get("RESEND_API_KEY")
        
        # Test med Resend's test-address
        response = resend.Emails.send({
            "from": "POIT Monitor <onboarding@resend.dev>",
            "to": ["delivered@resend.dev"],
            "subject": "Test",
            "html": "<p>Test</p>"
        })
        
        print(f"  ✅ Resend API working (ID: {response['id'][:20]}...)")
        return True
        
    except Exception as e:
        print(f"  ❌ Resend error: {e}")
        return False

def test_scraper():
    """Test 4: Scraper (requires Chrome)"""
    print("\n📋 Test 4: Scraper availability")
    
    try:
        from src.scrapers.poit_scraper import POITScraper
        print(f"  ✅ POITScraper importable")
        print(f"  ℹ️  Full scraper test skipped (requires Chrome)")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def main():
    print("=" * 60)
    print("POIT Monitor - Systemtest")
    print("=" * 60)
    
    results = {
        "Environment": test_environment(),
        "Database": test_database(),
        "Resend": test_resend(),
        "Scraper": test_scraper()
    }
    
    print("\n" + "=" * 60)
    print("RESULTAT:")
    print("=" * 60)
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Alla tester passerade! Systemet är redo.")
    else:
        print("\n⚠️  Vissa tester misslyckades. Kontrollera konfigurationen.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
