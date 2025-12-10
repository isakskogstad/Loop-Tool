"""
Supabase Database Client for Loop-Auto.
Replaces SQLite database.py with Supabase PostgreSQL backend.

Data Sources:
- Bolagsverket VDM: Official company registry
- Allabolag: Financial data, board members, corporate structure
"""

import os
import re
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


def sanitize_search_input(value: str, max_length: int = 100) -> str:
    """
    Sanitize user input for ILIKE queries to prevent SQL injection.

    - Escapes SQL wildcards (%, _)
    - Escapes backslashes
    - Limits length
    - Strips dangerous characters
    """
    if not value:
        return ""

    # Truncate to max length
    value = value[:max_length]

    # Remove null bytes and other control characters
    value = re.sub(r'[\x00-\x1f\x7f]', '', value)

    # Escape SQL LIKE special characters
    # Order matters: escape backslash first
    value = value.replace('\\', '\\\\')
    value = value.replace('%', '\\%')
    value = value.replace('_', '\\_')

    return value.strip()

try:
    from supabase import create_client, Client
except ImportError:
    raise ImportError("supabase package required. Install with: pip install supabase")

try:
    from .logging_config import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)


logger = get_logger("supabase_client")


class SupabaseDatabase:
    """
    Supabase database client with interface compatible with SQLite Database class.
    """

    def __init__(self):
        """
        Initialize Supabase client using environment variables.

        Required env vars:
            SUPABASE_URL: Project URL (https://xxx.supabase.co)
            SUPABASE_KEY: Service role key (for server-side operations)
        """
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables required"
            )

        self.client: Client = create_client(url, key)
        logger.info(f"Connected to Supabase: {url}")

    # =========================================================================
    # Connection Management (compatibility layer)
    # =========================================================================

    @contextmanager
    def connection(self):
        """
        Compatibility method - Supabase handles connections automatically.
        Yields self for compatibility with existing code.
        """
        yield self

    def get_connection(self):
        """Legacy compatibility - returns self."""
        return self

    def return_connection(self, conn):
        """Legacy compatibility - no-op for Supabase."""
        pass

    def init_db(self):
        """No-op for Supabase - tables created via SQL."""
        pass

    # =========================================================================
    # Company Operations
    # =========================================================================

    def upsert_company(self, data: Dict[str, Any]) -> bool:
        """
        Insert or update a company record.

        Args:
            data: Company data dict with 'orgnr' as primary key
        """
        if not data.get('orgnr'):
            logger.warning("Cannot upsert company without orgnr")
            return False

        try:
            # Add timestamps
            now = datetime.utcnow().isoformat()
            data['updated_at'] = now
            if not data.get('created_at'):
                data['created_at'] = now

            result = self.client.table('companies').upsert(
                data,
                on_conflict='orgnr'
            ).execute()

            return True
        except Exception as e:
            logger.error(f"Failed to upsert company {data.get('orgnr')}: {e}")
            return False

    def get_company(self, orgnr: str) -> Optional[Dict[str, Any]]:
        """
        Get a company by orgnr with all related data.

        Returns dict with: company data + roles, financials, industries, etc.
        """
        try:
            # Get company
            result = self.client.table('companies').select('*').eq('orgnr', orgnr).execute()

            if not result.data:
                return None

            company = dict(result.data[0])

            # Get related data
            company['roles'] = self._get_roles(orgnr)
            company['financials'] = self._get_financials(orgnr)
            company['industries'] = self._get_industries(orgnr)
            company['trademarks'] = self._get_trademarks(orgnr)
            company['related_companies'] = self._get_related_companies(orgnr)
            company['announcements'] = self._get_announcements(orgnr)

            return company

        except Exception as e:
            logger.error(f"Failed to get company {orgnr}: {e}")
            return None

    def company_exists(self, orgnr: str) -> bool:
        """Check if a company exists in the database."""
        try:
            result = self.client.table('companies').select('orgnr').eq('orgnr', orgnr).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to check company existence {orgnr}: {e}")
            return False

    def get_company_basic(self, orgnr: str) -> Optional[Dict[str, Any]]:
        """Get basic company info without relations."""
        try:
            result = self.client.table('companies').select('*').eq('orgnr', orgnr).execute()
            return dict(result.data[0]) if result.data else None
        except Exception as e:
            logger.error(f"Failed to get basic company {orgnr}: {e}")
            return None

    # =========================================================================
    # Roles (Board Members, etc.)
    # =========================================================================

    def _get_roles(self, orgnr: str) -> List[Dict[str, Any]]:
        """Get all roles for a company."""
        try:
            result = self.client.table('roles').select('*').eq('company_orgnr', orgnr).execute()
            return [dict(r) for r in result.data]
        except Exception as e:
            logger.error(f"Failed to get roles for {orgnr}: {e}")
            return []

    def add_role(self, orgnr: str, role_data: Dict[str, Any]) -> bool:
        """Add a role (board member, etc.) to a company."""
        try:
            role_data['company_orgnr'] = orgnr
            role_data['created_at'] = datetime.utcnow().isoformat()

            self.client.table('roles').insert(role_data).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add role for {orgnr}: {e}")
            return False

    def clear_roles(self, orgnr: str) -> bool:
        """Delete all roles for a company (before re-importing)."""
        try:
            self.client.table('roles').delete().eq('company_orgnr', orgnr).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to clear roles for {orgnr}: {e}")
            return False

    def add_roles_batch(self, orgnr: str, roles: List[Dict[str, Any]]) -> bool:
        """Add multiple roles at once."""
        if not roles:
            return True

        try:
            for role in roles:
                role['company_orgnr'] = orgnr
                role['created_at'] = datetime.utcnow().isoformat()

            self.client.table('roles').insert(roles).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add roles batch for {orgnr}: {e}")
            return False

    # =========================================================================
    # Financials
    # =========================================================================

    def _get_financials(self, orgnr: str) -> List[Dict[str, Any]]:
        """Get all financial records for a company."""
        try:
            result = self.client.table('financials').select('*').eq(
                'company_orgnr', orgnr
            ).order('period_year', desc=True).execute()
            return [dict(f) for f in result.data]
        except Exception as e:
            logger.error(f"Failed to get financials for {orgnr}: {e}")
            return []

    def add_financials(self, orgnr: str, financials: Dict[str, Any]) -> bool:
        """Add financial data for a year."""
        try:
            financials['company_orgnr'] = orgnr
            financials['created_at'] = datetime.utcnow().isoformat()

            self.client.table('financials').upsert(
                financials,
                on_conflict='company_orgnr,period_year'
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add financials for {orgnr}: {e}")
            return False

    def add_financials_batch(self, orgnr: str, financials_list: List[Dict[str, Any]]) -> bool:
        """Add multiple financial periods at once."""
        if not financials_list:
            return True

        try:
            # Deduplicate by (period_year, is_consolidated) - keep latest in list
            seen = {}
            for fin in financials_list:
                fin['company_orgnr'] = orgnr
                fin['created_at'] = datetime.utcnow().isoformat()
                # Ensure is_consolidated has a value (default False)
                if 'is_consolidated' not in fin:
                    fin['is_consolidated'] = False
                # Create unique key
                key = (fin.get('period_year'), fin.get('is_consolidated', False))
                seen[key] = fin  # Later entries overwrite earlier

            deduped_list = list(seen.values())

            self.client.table('financials').upsert(
                deduped_list,
                on_conflict='company_orgnr,period_year,is_consolidated'
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add financials batch for {orgnr}: {e}")
            return False

    # =========================================================================
    # Industries (SNI Codes)
    # =========================================================================

    def _get_industries(self, orgnr: str) -> List[Dict[str, Any]]:
        """Get all industries for a company."""
        try:
            result = self.client.table('industries').select('*').eq('company_orgnr', orgnr).execute()
            return [dict(i) for i in result.data]
        except Exception as e:
            logger.error(f"Failed to get industries for {orgnr}: {e}")
            return []

    def add_industry(self, orgnr: str, industry_data: Dict[str, Any]) -> bool:
        """Add an industry (SNI code) to a company."""
        try:
            industry_data['company_orgnr'] = orgnr
            industry_data['created_at'] = datetime.utcnow().isoformat()

            self.client.table('industries').insert(industry_data).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add industry for {orgnr}: {e}")
            return False

    def clear_industries(self, orgnr: str) -> bool:
        """Delete all industries for a company."""
        try:
            self.client.table('industries').delete().eq('company_orgnr', orgnr).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to clear industries for {orgnr}: {e}")
            return False

    # =========================================================================
    # Trademarks
    # =========================================================================

    def _get_trademarks(self, orgnr: str) -> List[Dict[str, Any]]:
        """Get all trademarks for a company."""
        try:
            result = self.client.table('trademarks').select('*').eq('company_orgnr', orgnr).execute()
            return [dict(t) for t in result.data]
        except Exception as e:
            logger.error(f"Failed to get trademarks for {orgnr}: {e}")
            return []

    def add_trademark(self, orgnr: str, trademark_data: Dict[str, Any]) -> bool:
        """Add a trademark to a company."""
        try:
            # Map field names from scraper to database schema
            db_data = {
                'company_orgnr': orgnr,
                'trademark_name': trademark_data.get('name') or trademark_data.get('trademark_name'),
                'name': trademark_data.get('name'),  # Also store in new column
                'registration_number': trademark_data.get('registration_number'),
                'registration_date': trademark_data.get('registration_date'),
                'expiry_date': trademark_data.get('expiry_date'),
                'status': trademark_data.get('status'),
                'class_codes': trademark_data.get('class_codes'),
                'source': trademark_data.get('source'),
                'created_at': datetime.utcnow().isoformat()
            }
            # Remove None values
            db_data = {k: v for k, v in db_data.items() if v is not None}

            self.client.table('trademarks').insert(db_data).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add trademark for {orgnr}: {e}")
            return False

    def clear_trademarks(self, orgnr: str) -> bool:
        """Delete all trademarks for a company."""
        try:
            self.client.table('trademarks').delete().eq('company_orgnr', orgnr).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to clear trademarks for {orgnr}: {e}")
            return False

    # =========================================================================
    # Related Companies
    # =========================================================================

    def _get_related_companies(self, orgnr: str) -> List[Dict[str, Any]]:
        """Get all related companies (group structure)."""
        try:
            result = self.client.table('related_companies').select('*').eq('company_orgnr', orgnr).execute()
            return [dict(r) for r in result.data]
        except Exception as e:
            logger.error(f"Failed to get related companies for {orgnr}: {e}")
            return []

    def add_related_companies(self, orgnr: str, companies: List[Dict[str, Any]]) -> bool:
        """Add related companies (group structure) to database."""
        if not companies:
            return True
        try:
            for company in companies:
                company['company_orgnr'] = orgnr
                company['created_at'] = datetime.utcnow().isoformat()
            self.client.table('related_companies').insert(companies).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add related companies for {orgnr}: {e}")
            return False

    def clear_related_companies(self, orgnr: str) -> bool:
        """Delete all related companies for a company."""
        try:
            self.client.table('related_companies').delete().eq('company_orgnr', orgnr).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to clear related companies for {orgnr}: {e}")
            return False

    # =========================================================================
    # Announcements
    # =========================================================================

    def _get_announcements(self, orgnr: str) -> List[Dict[str, Any]]:
        """Get all announcements for a company."""
        try:
            result = self.client.table('announcements').select('*').eq('company_orgnr', orgnr).execute()
            return [dict(a) for a in result.data]
        except Exception as e:
            logger.error(f"Failed to get announcements for {orgnr}: {e}")
            return []

    def add_announcements(self, orgnr: str, announcements: List[Dict[str, Any]]) -> bool:
        """Add announcements (kungörelser) to database."""
        if not announcements:
            return True
        try:
            for ann in announcements:
                ann['company_orgnr'] = orgnr
                ann['created_at'] = datetime.utcnow().isoformat()
            self.client.table('announcements').insert(announcements).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to add announcements for {orgnr}: {e}")
            return False

    def clear_announcements(self, orgnr: str) -> bool:
        """Delete all announcements for a company."""
        try:
            self.client.table('announcements').delete().eq('company_orgnr', orgnr).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to clear announcements for {orgnr}: {e}")
            return False

    # =========================================================================
    # History Tables (Changelog)
    # =========================================================================

    def snapshot_company(self, orgnr: str) -> bool:
        """
        Create a history snapshot of current company state.
        Called before updating company data.
        """
        try:
            company = self.get_company_basic(orgnr)
            if not company:
                return False

            # Save company snapshot
            self.client.table('companies_history').insert({
                'orgnr': orgnr,
                'snapshot_date': datetime.utcnow().isoformat(),
                'data': json.dumps(company)
            }).execute()

            # Save roles snapshot
            roles = self._get_roles(orgnr)
            if roles:
                self.client.table('roles_history').insert({
                    'company_orgnr': orgnr,
                    'snapshot_date': datetime.utcnow().isoformat(),
                    'roles_json': json.dumps(roles)
                }).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to snapshot company {orgnr}: {e}")
            return False

    def get_full_history(self, orgnr: str) -> Dict[str, Any]:
        """Get full history for a company."""
        try:
            company_history = self.client.table('companies_history').select('*').eq(
                'orgnr', orgnr
            ).order('snapshot_date', desc=True).execute()

            roles_history = self.client.table('roles_history').select('*').eq(
                'company_orgnr', orgnr
            ).order('snapshot_date', desc=True).execute()

            return {
                'company_history': [dict(h) for h in company_history.data],
                'roles_history': [dict(h) for h in roles_history.data]
            }
        except Exception as e:
            logger.error(f"Failed to get full history for {orgnr}: {e}")
            return {'company_history': [], 'roles_history': []}

    def get_roles_history(self, orgnr: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get roles history for a company."""
        try:
            result = self.client.table('roles_history').select('*').eq(
                'company_orgnr', orgnr
            ).order('snapshot_date', desc=True).limit(limit).execute()
            return [dict(h) for h in result.data]
        except Exception as e:
            logger.error(f"Failed to get roles history for {orgnr}: {e}")
            return []

    # =========================================================================
    # Company Registry (Name Lookup)
    # =========================================================================

    def search_company_registry(self, name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search company registry by name.
        Uses PostgreSQL full-text search with Swedish language support.
        """
        try:
            # Sanitize input to prevent SQL injection
            safe_name = sanitize_search_input(name, max_length=100)
            if not safe_name:
                return []

            # First try prefix match (fast)
            result = self.client.table('company_registry').select(
                'orgnr, name, org_form'
            ).ilike('name', f'{safe_name}%').limit(limit).execute()

            if result.data:
                return [dict(r) for r in result.data]

            # Fallback: contains search
            result = self.client.table('company_registry').select(
                'orgnr, name, org_form'
            ).ilike('name', f'%{safe_name}%').limit(limit).execute()

            return [dict(r) for r in result.data]

        except Exception as e:
            logger.error(f"Failed to search company registry for '{name}': {e}")
            return []

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the company registry."""
        try:
            result = self.client.table('company_registry').select('orgnr', count='exact').execute()
            return {
                'total_companies': result.count,
                'source': 'supabase'
            }
        except Exception as e:
            logger.error(f"Failed to get registry stats: {e}")
            return {'total_companies': 0, 'source': 'supabase', 'error': str(e)}

    # =========================================================================
    # Cache Metadata
    # =========================================================================

    def get_cache_metadata(self, orgnr: str) -> Optional[Dict[str, Any]]:
        """Get cache metadata for a company."""
        try:
            result = self.client.table('cache_metadata').select('*').eq('orgnr', orgnr).execute()
            return dict(result.data[0]) if result.data else None
        except Exception as e:
            logger.error(f"Failed to get cache metadata for {orgnr}: {e}")
            return None

    def update_cache_metadata(self, orgnr: str, source: str = None) -> bool:
        """Update cache metadata timestamp."""
        try:
            data = {
                'orgnr': orgnr,
                'last_refresh': datetime.utcnow().isoformat()
            }
            if source:
                data['source'] = source

            self.client.table('cache_metadata').upsert(data, on_conflict='orgnr').execute()
            return True
        except Exception as e:
            logger.error(f"Failed to update cache metadata for {orgnr}: {e}")
            return False

    def is_cache_fresh(self, orgnr: str, ttl_hours: int = 24) -> bool:
        """Check if cached data is still fresh."""
        try:
            metadata = self.get_cache_metadata(orgnr)
            if not metadata or not metadata.get('last_refresh'):
                return False

            last_refresh = datetime.fromisoformat(metadata['last_refresh'].replace('Z', '+00:00'))
            age_hours = (datetime.utcnow() - last_refresh.replace(tzinfo=None)).total_seconds() / 3600
            return age_hours < ttl_hours
        except Exception as e:
            logger.error(f"Failed to check cache freshness for {orgnr}: {e}")
            return False

    # =========================================================================
    # Search Companies (cached)
    # =========================================================================

    def search_companies(
        self,
        query: str = None,
        municipality: str = None,
        min_revenue: int = None,
        max_revenue: int = None,
        min_employees: int = None,
        status: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search cached companies with filters."""
        try:
            q = self.client.table('companies').select(
                'orgnr, name, company_type, status, postal_city, revenue, num_employees'
            )

            if query:
                # Sanitize to prevent SQL injection
                safe_query = sanitize_search_input(query, max_length=100)
                if safe_query:
                    q = q.or_(f'name.ilike.%{safe_query}%,orgnr.ilike.%{safe_query}%')

            if municipality:
                # Sanitize municipality input
                safe_municipality = sanitize_search_input(municipality, max_length=50)
                if safe_municipality:
                    q = q.ilike('postal_city', f'%{safe_municipality}%')

            if min_revenue:
                q = q.gte('revenue', min_revenue)

            if max_revenue:
                q = q.lte('revenue', max_revenue)

            if min_employees:
                q = q.gte('num_employees', min_employees)

            if status:
                # Status is typically a fixed value, but sanitize anyway
                safe_status = sanitize_search_input(status, max_length=20)
                if safe_status:
                    q = q.eq('status', safe_status)

            result = q.limit(limit).execute()
            return [dict(r) for r in result.data]

        except Exception as e:
            logger.error(f"Failed to search companies: {e}")
            return []

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            companies = self.client.table('companies').select('orgnr', count='exact').execute()
            return {
                'companies': companies.count or 0,
                'database_type': 'supabase'
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'companies': 0, 'database_type': 'supabase', 'error': str(e)}

    # =========================================================================
    # Complete Storage (Atomic)
    # =========================================================================

    def store_company_complete(
        self,
        company_data: Dict[str, Any],
        roles: List[Dict[str, Any]] = None,
        financials: List[Dict[str, Any]] = None,
        industries: List[Dict[str, Any]] = None,
        trademarks: List[Dict[str, Any]] = None,
        related_companies: List[Dict[str, Any]] = None,
        announcements: List[Dict[str, Any]] = None,
        snapshot_first: bool = True
    ) -> bool:
        """
        Store complete company data atomically.

        Args:
            company_data: Main company record
            roles: Board members, executives, etc.
            financials: Historical financial data
            industries: SNI codes
            trademarks: Registered trademarks
            related_companies: Group structure (parent/subsidiaries)
            announcements: Kungörelser from Bolagsverket
            snapshot_first: Create history snapshot before updating
        """
        orgnr = company_data.get('orgnr')
        if not orgnr:
            logger.error("Cannot store company without orgnr")
            return False

        try:
            # Create snapshot if company exists
            if snapshot_first and self.company_exists(orgnr):
                self.snapshot_company(orgnr)

            # Update main company record
            self.upsert_company(company_data)

            # Clear and re-add related data
            if roles is not None:
                self.clear_roles(orgnr)
                self.add_roles_batch(orgnr, roles)

            if financials is not None:
                self.add_financials_batch(orgnr, financials)

            if industries is not None:
                self.clear_industries(orgnr)
                for i in industries:
                    self.add_industry(orgnr, i)

            if trademarks is not None:
                self.clear_trademarks(orgnr)
                for t in trademarks:
                    self.add_trademark(orgnr, t)

            if related_companies is not None:
                self.clear_related_companies(orgnr)
                self.add_related_companies(orgnr, related_companies)

            if announcements is not None:
                self.clear_announcements(orgnr)
                self.add_announcements(orgnr, announcements)

            # Update cache metadata
            self.update_cache_metadata(orgnr)

            logger.info(f"Stored complete data for {orgnr}")
            return True

        except Exception as e:
            logger.error(f"Failed to store complete data for {orgnr}: {e}")
            return False


# Alias for compatibility
def get_db() -> SupabaseDatabase:
    """Alias for get_database()."""
    return get_database()


# Create singleton instance
_db_instance: Optional[SupabaseDatabase] = None


def get_database() -> SupabaseDatabase:
    """Get singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDatabase()
    return _db_instance


# Alias for compatibility
Database = SupabaseDatabase
