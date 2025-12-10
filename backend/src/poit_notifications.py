"""
POIT Email Notifications via Resend

Sends email alerts to users when their watched companies appear in POIT announcements.

Features:
- HTML email templates with responsive design
- Batch processing of pending notifications
- Rate limiting to respect Resend API limits
- Error handling with retry logic
- Company name lookup from loop_table

Environment:
    RESEND_API_KEY - Resend API key
    NOTIFICATION_FROM_EMAIL - Sender email (default: alerts@impactloop.se)
    NOTIFICATION_FROM_NAME - Sender name (default: Impact Loop Alerts)
    FRONTEND_URL - Frontend URL for links (default: https://impactloop.se)

Usage:
    from src.poit_notifications import send_pending_notifications
    sent_count = await send_pending_notifications()
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

try:
    from .supabase_client import get_database
    from .logging_config import get_source_logger
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.supabase_client import get_database
    
    def get_source_logger(name):
        return logging.getLogger(name)

logger = get_source_logger("poit_notifications")


# =============================================================================
# Configuration
# =============================================================================

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("NOTIFICATION_FROM_EMAIL", "alerts@impactloop.se")
FROM_NAME = os.environ.get("NOTIFICATION_FROM_NAME", "Impact Loop Alerts")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://impactloop.se")

# Rate limiting
MAX_EMAILS_PER_BATCH = 50
DELAY_BETWEEN_EMAILS = 0.2  # seconds


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class NotificationData:
    """Data needed to send a notification"""
    notification_id: str
    user_id: str
    user_email: str
    orgnr: str
    company_name: str
    announcement_id: str
    category: str
    title: str
    content: str
    announcement_date: str
    source_url: Optional[str]


# =============================================================================
# Email Templates
# =============================================================================

def get_email_html(data: NotificationData) -> str:
    """Generate HTML email content."""
    
    # Category display names
    category_names = {
        "konkurser": "Konkurs",
        "konkursbeslut": "Konkursbeslut",
        "bolagsverkets_registreringar": "Bolagsverkets registrering",
        "aktiebolagsregistret": "Aktiebolagsregistret",
        "kallelser": "Kallelse",
        "kallelse_pa_borgenarer": "Kallelse på borgenärer",
        "skuldsaneringar": "Skuldsanering",
        "familjeratt": "Familjerätt"
    }
    
    # Category colors
    category_colors = {
        "konkurser": "#dc2626",  # Red
        "konkursbeslut": "#dc2626",
        "bolagsverkets_registreringar": "#2563eb",  # Blue
        "aktiebolagsregistret": "#2563eb",
        "kallelser": "#d97706",  # Orange
        "skuldsaneringar": "#7c3aed",  # Purple
        "familjeratt": "#059669"  # Green
    }
    
    category_key = data.category.lower().replace(" ", "_").replace("å", "a").replace("ä", "a").replace("ö", "o")
    category_display = category_names.get(category_key, data.category)
    category_color = category_colors.get(category_key, "#6b7280")
    
    # Truncate content if too long
    content_preview = data.content[:500] + "..." if len(data.content) > 500 else data.content
    
    # Format orgnr
    orgnr_formatted = f"{data.orgnr[:6]}-{data.orgnr[6:]}" if len(data.orgnr) == 10 else data.orgnr
    
    html = f"""
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>POIT Alert: {data.company_name}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" style="width: 100%; max-width: 600px; border-collapse: collapse;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); padding: 30px; border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">
                                🔔 Ny kungörelse upptäckt
                            </h1>
                            <p style="margin: 10px 0 0 0; color: #cbd5e1; font-size: 14px;">
                                Ett av dina bevakade företag har en ny publicering i Post- och Inrikes Tidningar
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 30px;">
                            <!-- Company Info -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                                <tr>
                                    <td style="padding: 20px; background-color: #f8fafc; border-radius: 8px; border-left: 4px solid #1e3a5f;">
                                        <h2 style="margin: 0 0 8px 0; color: #1e293b; font-size: 20px; font-weight: 600;">
                                            {data.company_name}
                                        </h2>
                                        <p style="margin: 0; color: #64748b; font-size: 14px;">
                                            Org.nr: {orgnr_formatted}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Category Badge -->
                            <p style="margin: 0 0 20px 0;">
                                <span style="display: inline-block; padding: 6px 14px; background-color: {category_color}; color: #ffffff; font-size: 13px; font-weight: 500; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px;">
                                    {category_display}
                                </span>
                                <span style="margin-left: 10px; color: #64748b; font-size: 13px;">
                                    {data.announcement_date}
                                </span>
                            </p>
                            
                            <!-- Announcement Title -->
                            <h3 style="margin: 0 0 15px 0; color: #1e293b; font-size: 16px; font-weight: 600; line-height: 1.4;">
                                {data.title}
                            </h3>
                            
                            <!-- Content Preview -->
                            <div style="padding: 20px; background-color: #f8fafc; border-radius: 8px; margin-bottom: 25px;">
                                <p style="margin: 0; color: #475569; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">
{content_preview}
                                </p>
                            </div>
                            
                            <!-- Action Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center">
                                        <a href="{data.source_url or 'https://poit.bolagsverket.se/poit-app/'}" 
                                           style="display: inline-block; padding: 14px 28px; background-color: #1e3a5f; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; border-radius: 8px;">
                                            Visa fullständig kungörelse →
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 25px 30px; border-radius: 0 0 12px 12px; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 13px; text-align: center;">
                                Du får detta mail för att du bevakar {data.company_name} via Impact Loop.
                            </p>
                            <p style="margin: 0; color: #94a3b8; font-size: 12px; text-align: center;">
                                <a href="{FRONTEND_URL}/settings/watchlist" style="color: #64748b; text-decoration: underline;">
                                    Hantera dina bevakningar
                                </a>
                                &nbsp;•&nbsp;
                                <a href="{FRONTEND_URL}" style="color: #64748b; text-decoration: underline;">
                                    Impact Loop
                                </a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


def get_email_text(data: NotificationData) -> str:
    """Generate plain text email content."""
    
    orgnr_formatted = f"{data.orgnr[:6]}-{data.orgnr[6:]}" if len(data.orgnr) == 10 else data.orgnr
    content_preview = data.content[:500] + "..." if len(data.content) > 500 else data.content
    
    return f"""
🔔 NY KUNGÖRELSE UPPTÄCKT

Ett av dina bevakade företag har en ny publicering i Post- och Inrikes Tidningar.

────────────────────────────────

FÖRETAG: {data.company_name}
ORG.NR: {orgnr_formatted}
KATEGORI: {data.category}
DATUM: {data.announcement_date}

────────────────────────────────

{data.title}

{content_preview}

────────────────────────────────

Läs fullständig kungörelse:
{data.source_url or 'https://poit.bolagsverket.se/poit-app/'}

────────────────────────────────

Du får detta mail för att du bevakar {data.company_name} via Impact Loop.
Hantera dina bevakningar: {FRONTEND_URL}/settings/watchlist

Impact Loop - {FRONTEND_URL}
"""


# =============================================================================
# Notification Service
# =============================================================================

class POITNotificationService:
    """
    Service for sending POIT email notifications via Resend.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize notification service.
        
        Args:
            api_key: Resend API key (defaults to RESEND_API_KEY env var)
        """
        self.api_key = api_key or RESEND_API_KEY
        self.db = get_database()
        
        if RESEND_AVAILABLE and self.api_key:
            resend.api_key = self.api_key
    
    @property
    def is_configured(self) -> bool:
        """Check if Resend is configured."""
        return RESEND_AVAILABLE and bool(self.api_key)
    
    async def send_pending_notifications(
        self,
        limit: int = MAX_EMAILS_PER_BATCH
    ) -> int:
        """
        Send all pending notifications.
        
        Args:
            limit: Maximum notifications to send in this batch
            
        Returns:
            Number of emails successfully sent
        """
        if not self.is_configured:
            logger.warning("Resend not configured, skipping notifications")
            return 0
        
        # Get pending notifications
        pending = self._get_pending_notifications(limit)
        
        if not pending:
            logger.info("No pending notifications")
            return 0
        
        logger.info(f"Processing {len(pending)} pending notifications")
        
        sent = 0
        
        for notification in pending:
            try:
                # Prepare notification data
                data = await self._prepare_notification_data(notification)
                
                if not data:
                    # Mark as skipped if we couldn't prepare data
                    self._update_notification_status(
                        notification['id'],
                        status="skipped",
                        error="Could not prepare notification data"
                    )
                    continue
                
                # Send email
                success = await self._send_email(data)
                
                if success:
                    self._update_notification_status(
                        notification['id'],
                        status="sent"
                    )
                    sent += 1
                else:
                    self._update_notification_status(
                        notification['id'],
                        status="failed",
                        error="Email send failed"
                    )
                
                # Rate limiting
                await asyncio.sleep(DELAY_BETWEEN_EMAILS)
                
            except Exception as e:
                logger.error(f"Error processing notification {notification['id']}: {e}")
                self._update_notification_status(
                    notification['id'],
                    status="failed",
                    error=str(e)
                )
        
        logger.info(f"Sent {sent}/{len(pending)} notifications")
        return sent
    
    async def send_test_notification(
        self,
        email: str,
        orgnr: str = "5569201998",
        company_name: str = "Test Company AB"
    ) -> bool:
        """
        Send a test notification email.
        
        Args:
            email: Recipient email
            orgnr: Test org.nr
            company_name: Test company name
            
        Returns:
            True if sent successfully
        """
        if not self.is_configured:
            logger.error("Resend not configured")
            return False
        
        data = NotificationData(
            notification_id="test",
            user_id="test",
            user_email=email,
            orgnr=orgnr,
            company_name=company_name,
            announcement_id="test",
            category="konkurser",
            title="Testmeddelande - Konkursbeslut",
            content="Detta är ett testmeddelande för att verifiera att POIT-notifieringar fungerar korrekt.\n\nIngen åtgärd krävs.",
            announcement_date=datetime.now().strftime("%Y-%m-%d"),
            source_url="https://poit.bolagsverket.se/poit-app/"
        )
        
        return await self._send_email(data)
    
    def _get_pending_notifications(self, limit: int) -> List[Dict]:
        """Get pending notifications from database."""
        try:
            result = self.db.client.table('poit_notifications') \
                .select('*') \
                .eq('status', 'pending') \
                .order('created_at') \
                .limit(limit) \
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting pending notifications: {e}")
            return []
    
    async def _prepare_notification_data(
        self,
        notification: Dict
    ) -> Optional[NotificationData]:
        """Prepare data needed to send a notification."""
        try:
            # Get user email from auth.users
            user_email = self._get_user_email(notification['user_id'])
            if not user_email:
                logger.warning(f"No email found for user {notification['user_id']}")
                return None
            
            # Get announcement details
            ann_result = self.db.client.table('poit_announcements') \
                .select('*') \
                .eq('id', notification['announcement_id']) \
                .single() \
                .execute()
            
            if not ann_result.data:
                logger.warning(f"Announcement not found: {notification['announcement_id']}")
                return None
            
            ann = ann_result.data
            
            # Get company name from loop_table or watchlist
            company_name = self._get_company_name(notification['orgnr'])
            
            return NotificationData(
                notification_id=notification['id'],
                user_id=notification['user_id'],
                user_email=user_email,
                orgnr=notification['orgnr'],
                company_name=company_name or f"Org.nr {notification['orgnr']}",
                announcement_id=notification['announcement_id'],
                category=ann.get('category', ''),
                title=ann.get('title', '')[:200],
                content=ann.get('content', ''),
                announcement_date=ann.get('announcement_date', ''),
                source_url=ann.get('source_url')
            )
            
        except Exception as e:
            logger.error(f"Error preparing notification data: {e}")
            return None
    
    def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email from Supabase auth.users."""
        try:
            # Query auth.users table
            result = self.db.client.rpc(
                'get_user_email',
                {'user_id': user_id}
            ).execute()
            
            if result.data:
                return result.data
            
            # Fallback: try direct query (requires service role)
            # This may not work depending on RLS policies
            result = self.db.client.table('users') \
                .select('email') \
                .eq('id', user_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data.get('email')
                
        except Exception as e:
            logger.warning(f"Error getting user email: {e}")
        
        return None
    
    def _get_company_name(self, orgnr: str) -> Optional[str]:
        """Get company name from loop_table or watchlist."""
        try:
            # Try loop_table first (our main company database)
            result = self.db.client.table('loop_table') \
                .select('company_name') \
                .eq('orgnr', orgnr) \
                .limit(1) \
                .execute()
            
            if result.data and result.data[0].get('company_name'):
                return result.data[0]['company_name']
            
            # Try user_watchlists as fallback
            result = self.db.client.table('user_watchlists') \
                .select('company_name') \
                .eq('orgnr', orgnr) \
                .not_.is_('company_name', 'null') \
                .limit(1) \
                .execute()
            
            if result.data and result.data[0].get('company_name'):
                return result.data[0]['company_name']
                
        except Exception as e:
            logger.warning(f"Error getting company name: {e}")
        
        return None
    
    async def _send_email(self, data: NotificationData) -> bool:
        """Send email via Resend."""
        try:
            params = {
                "from": f"{FROM_NAME} <{FROM_EMAIL}>",
                "to": [data.user_email],
                "subject": f"🔔 {data.company_name} - Ny {data.category}",
                "html": get_email_html(data),
                "text": get_email_text(data)
            }
            
            response = resend.Emails.send(params)
            
            if response.get('id'):
                logger.info(f"Email sent: {response['id']} to {data.user_email}")
                return True
            else:
                logger.warning(f"Email send failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _update_notification_status(
        self,
        notification_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """Update notification status in database."""
        try:
            data = {
                "status": status,
                "email_sent_at": datetime.now().isoformat() if status == "sent" else None
            }
            
            self.db.client.table('poit_notifications') \
                .update(data) \
                .eq('id', notification_id) \
                .execute()
                
        except Exception as e:
            logger.warning(f"Error updating notification status: {e}")


# =============================================================================
# Convenience Functions
# =============================================================================

async def send_pending_notifications(limit: int = MAX_EMAILS_PER_BATCH) -> int:
    """
    Send all pending POIT notifications.
    
    Args:
        limit: Maximum notifications to process
        
    Returns:
        Number of emails sent
    """
    service = POITNotificationService()
    return await service.send_pending_notifications(limit)


async def send_test_email(email: str) -> bool:
    """
    Send a test notification email.
    
    Args:
        email: Recipient email address
        
    Returns:
        True if sent successfully
    """
    service = POITNotificationService()
    return await service.send_test_notification(email)


def get_notification_service() -> POITNotificationService:
    """Factory function to create notification service."""
    return POITNotificationService()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="POIT Email Notifications")
    parser.add_argument("--send", action="store_true", help="Send pending notifications")
    parser.add_argument("--test", type=str, help="Send test email to address")
    parser.add_argument("--limit", type=int, default=50, help="Max emails to send")
    parser.add_argument("--check", action="store_true", help="Check configuration")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        service = POITNotificationService()
        
        if args.check:
            print("\nConfiguration Check:")
            print(f"  Resend available: {RESEND_AVAILABLE}")
            print(f"  API key configured: {bool(RESEND_API_KEY)}")
            print(f"  From email: {FROM_EMAIL}")
            print(f"  From name: {FROM_NAME}")
            print(f"  Frontend URL: {FRONTEND_URL}")
            print(f"  Service configured: {service.is_configured}")
            return
        
        if args.test:
            print(f"\nSending test email to {args.test}...")
            success = await service.send_test_notification(args.test)
            print(f"Result: {'✅ Sent' if success else '❌ Failed'}")
            return
        
        if args.send:
            print(f"\nSending pending notifications (limit: {args.limit})...")
            sent = await service.send_pending_notifications(limit=args.limit)
            print(f"\nSent {sent} emails")
            return
        
        parser.print_help()
    
    asyncio.run(main())
