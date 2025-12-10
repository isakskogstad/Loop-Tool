#!/usr/bin/env python3
"""
POIT Notification Service - Email via Resend

Skickar email-notifikationer för matchade POIT-kungörelser.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any

import resend
from supabase import create_client, Client


class POITNotificationService:
    """Hanterar email-notifikationer för POIT-kungörelser."""
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        resend_api_key: Optional[str] = None,
        from_email: str = "POIT Monitor <noreply@impactloop.se>",
        debug: bool = False
    ):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.resend_api_key = resend_api_key or os.environ.get("RESEND_API_KEY")
        self.from_email = from_email
        self.debug = debug
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY required")
        
        if not self.resend_api_key:
            raise ValueError("RESEND_API_KEY required")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        resend.api_key = self.resend_api_key
    
    def _log(self, msg: str):
        if self.debug:
            print(f"[Notifications] {msg}")
    
    async def send_pending_notifications(self, limit: int = 100) -> int:
        """
        Skickar alla pending notifikationer.
        
        Args:
            limit: Max antal att skicka per körning
        
        Returns:
            Antal skickade notifikationer
        """
        # Hämta pending notifikationer med joins
        result = self.supabase.table("poit_notifications").select(
            "*, poit_announcements(*), user_watchlists!inner(company_name, user_id)"
        ).eq("status", "pending").limit(limit).execute()
        
        sent_count = 0
        
        for notification in result.data or []:
            try:
                sent = await self._send_single_notification(notification)
                if sent:
                    sent_count += 1
            except Exception as e:
                self._log(f"Fel vid utskick: {e}")
                # Markera som failed
                self.supabase.table("poit_notifications").update({
                    "status": "failed",
                    "error_message": str(e)
                }).eq("id", notification["id"]).execute()
        
        return sent_count
    
    async def _send_single_notification(self, notification: Dict) -> bool:
        """Skickar en enskild notifikation."""
        announcement = notification.get("poit_announcements", {})
        watchlist = notification.get("user_watchlists", {})
        
        # Hämta användare för email (om user_id finns)
        user_id = watchlist.get("user_id") or notification.get("user_id")
        email = None
        
        if user_id:
            # Hämta email från auth.users
            try:
                user_result = self.supabase.auth.admin.get_user_by_id(user_id)
                if user_result and user_result.user:
                    email = user_result.user.email
            except Exception:
                pass
        
        if not email:
            self._log(f"Ingen email för notifikation {notification['id']}, hoppar över")
            # Markera som skipped
            self.supabase.table("poit_notifications").update({
                "status": "skipped",
                "error_message": "No email address"
            }).eq("id", notification["id"]).execute()
            return False
        
        # Bygg email
        company_name = watchlist.get("company_name") or notification.get("orgnr")
        category = announcement.get("category", "kungörelse").replace("_", " ").title()
        title = announcement.get("title", "")
        content = announcement.get("content", "")[:500]  # Trunkera
        source_url = announcement.get("source_url", "")
        
        subject = f"🔔 POIT Alert: {company_name} - {category}"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a365d;">POIT Kungörelse</h2>
            
            <div style="background: #f7fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">{company_name}</h3>
                <p><strong>Kategori:</strong> {category}</p>
                <p><strong>Ärendenummer:</strong> {title}</p>
                <p><strong>Organisationsnummer:</strong> {notification.get('orgnr')}</p>
                <p><strong>Datum:</strong> {announcement.get('announcement_date', 'Okänt')}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <h4>Kungörelsetext</h4>
                <p style="background: #edf2f7; padding: 15px; border-radius: 4px;">{content}...</p>
            </div>
            
            {f'<p><a href="{source_url}" style="color: #3182ce;">Visa fullständig kungörelse →</a></p>' if source_url else ''}
            
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
            
            <p style="color: #718096; font-size: 12px;">
                Detta är en automatisk notifikation från POIT Monitor.<br>
                Du bevakar detta företag via din watchlist.
            </p>
        </div>
        """
        
        # Skicka via Resend
        try:
            response = resend.Emails.send({
                "from": self.from_email,
                "to": [email],
                "subject": subject,
                "html": html_body
            })
            
            self._log(f"Email skickat till {email}: {response}")
            
            # Markera som skickad
            self.supabase.table("poit_notifications").update({
                "status": "sent",
                "email_sent_at": datetime.now().isoformat()
            }).eq("id", notification["id"]).execute()
            
            return True
            
        except Exception as e:
            self._log(f"Resend fel: {e}")
            raise


# ============================================================
# Convenience-funktioner
# ============================================================

async def send_pending_notifications(limit: int = 100) -> int:
    """Skickar pending notifikationer."""
    service = POITNotificationService(debug=True)
    return await service.send_pending_notifications(limit)


async def send_test_notification(email: str, orgnr: str = "559252-0182") -> bool:
    """Skickar ett test-email."""
    service = POITNotificationService(debug=True)
    
    # Skapa fake notification data
    notification = {
        "id": "test-notification",
        "orgnr": orgnr,
        "poit_announcements": {
            "category": "konkurser",
            "title": "K000000/25",
            "content": "Detta är ett test-meddelande för att verifiera att POIT Monitor fungerar korrekt.",
            "announcement_date": datetime.now().strftime("%Y-%m-%d"),
            "source_url": "https://poit.bolagsverket.se"
        },
        "user_watchlists": {
            "company_name": "Test Company AB"
        }
    }
    
    # Bygg email direkt
    subject = "🧪 POIT Monitor - Test"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1a365d;">✅ POIT Monitor Fungerar!</h2>
        <p>Detta är ett test-email som bekräftar att notifikationssystemet fungerar.</p>
        <p>Organisationsnummer: {orgnr}</p>
        <p>Tid: {datetime.now().isoformat()}</p>
    </div>
    """
    
    resend.api_key = service.resend_api_key
    response = resend.Emails.send({
        "from": service.from_email,
        "to": [email],
        "subject": subject,
        "html": html_body
    })
    
    print(f"Test-email skickat: {response}")
    return True


if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        if len(sys.argv) < 3:
            print("Användning: python poit_notifications.py test <email>")
            sys.exit(1)
        
        email = sys.argv[2]
        asyncio.run(send_test_notification(email))
    else:
        count = asyncio.run(send_pending_notifications())
        print(f"Skickade {count} notifikationer")
