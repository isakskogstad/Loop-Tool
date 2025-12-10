"""
XBRL Storage Client for Supabase

Handles storing and retrieving XBRL data from annual reports.
"""

from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
import logging

from .supabase_client import get_database
from .parsers import ParseResult, XBRLFact, AuditInfo, BoardInfo

logger = logging.getLogger(__name__)


class XBRLStorage:
    """Storage client for XBRL annual report data."""

    def __init__(self):
        self.db = get_database()

    # ============================================================
    # Annual Reports
    # ============================================================

    def store_annual_report(
        self,
        parse_result: ParseResult,
        document_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Store a parsed annual report and all its facts.

        Returns the annual_report_id if successful, None otherwise.
        """
        if not parse_result.company_info or not parse_result.company_info.orgnr:
            logger.error("Cannot store annual report without company orgnr")
            return None

        orgnr = parse_result.company_info.orgnr
        fiscal_year = parse_result.company_info.fiscal_year_end.year if parse_result.company_info.fiscal_year_end else None

        if not fiscal_year:
            logger.error(f"Cannot store annual report for {orgnr} without fiscal year")
            return None

        try:
            # Upsert annual report metadata
            # Note: If we got here, parsing was successful (ParseError would have been raised otherwise)
            report_data = {
                "company_orgnr": orgnr,
                "document_id": document_id,
                "fiscal_year": fiscal_year,
                "fiscal_year_start": parse_result.company_info.fiscal_year_start.isoformat() if parse_result.company_info.fiscal_year_start else None,
                "fiscal_year_end": parse_result.company_info.fiscal_year_end.isoformat() if parse_result.company_info.fiscal_year_end else None,
                "total_facts_extracted": len(parse_result.all_facts),
                "namespaces_used": list(parse_result.namespaces),
                "is_audited": parse_result.audit_info is not None,
                "processing_status": "processed",
                "source_file": parse_result.source_file,
                "parse_errors": [],  # Empty since we only store successful parses
                "parse_warnings": [],  # Warnings not tracked in current ParseResult
            }

            # Add audit info if present
            if parse_result.audit_info:
                report_data.update({
                    "auditor_first_name": parse_result.audit_info.auditor_first_name,
                    "auditor_last_name": parse_result.audit_info.auditor_last_name,
                    "audit_firm": parse_result.audit_info.audit_firm,
                    "audit_completion_date": parse_result.audit_info.audit_completion_date.isoformat() if parse_result.audit_info.audit_completion_date else None,
                    "audit_opinion": parse_result.audit_info.audit_opinion,
                })

            # Upsert the annual report
            result = self.db.client.table("annual_reports").upsert(
                report_data,
                on_conflict="company_orgnr,fiscal_year"
            ).execute()

            if not result.data:
                logger.error(f"Failed to store annual report for {orgnr}/{fiscal_year}")
                return None

            report_id = result.data[0]["id"]

            # Store XBRL facts
            self._store_xbrl_facts(report_id, orgnr, parse_result.all_facts)

            # Store audit history
            if parse_result.audit_info:
                self._store_audit_history(orgnr, fiscal_year, parse_result.audit_info)

            # Store board history
            if parse_result.board_info:
                self._store_board_history(orgnr, fiscal_year, parse_result.board_info)

            # Update financials with XBRL data
            self._update_financials_from_xbrl(orgnr, fiscal_year, parse_result, report_id)

            logger.info(f"Stored annual report {orgnr}/{fiscal_year} with {len(parse_result.all_facts)} facts")
            return report_id

        except Exception as e:
            logger.error(f"Error storing annual report for {orgnr}: {e}")
            return None

    def _store_xbrl_facts(
        self,
        report_id: str,
        orgnr: str,
        facts: List[XBRLFact]
    ) -> int:
        """Store XBRL facts for an annual report. Returns count stored."""
        if not facts:
            return 0

        # Delete existing facts for this report
        self.db.client.table("xbrl_facts").delete().eq(
            "annual_report_id", report_id
        ).execute()

        # Prepare fact records
        fact_records = []
        for fact in facts:
            # Extract namespace and local_name from fact.name (format: "namespace:local_name")
            if ":" in fact.name:
                namespace, local_name = fact.name.split(":", 1)
            else:
                namespace = ""
                local_name = fact.name

            # Determine category based on namespace
            category = self._categorize_fact(namespace)

            # Handle Decimal values for numeric fields
            value = fact.value
            value_numeric = None
            value_text = None
            value_boolean = None

            if value is not None:
                if isinstance(value, bool):
                    value_boolean = value
                elif isinstance(value, (int, float)):
                    value_numeric = float(value)
                else:
                    # Try to convert Decimal or numeric strings
                    try:
                        value_numeric = float(value)
                    except (ValueError, TypeError):
                        value_text = str(value)

            fact_records.append({
                "annual_report_id": report_id,
                "company_orgnr": orgnr,
                "xbrl_name": fact.name,
                "namespace": namespace,
                "local_name": local_name,
                "context_ref": fact.context_ref,
                "period_type": fact.period_type.value if fact.period_type else "unknown",
                "value_numeric": value_numeric,
                "value_text": value_text,
                "value_boolean": value_boolean,
                "unit_ref": fact.unit_ref,
                "decimals": fact.decimals,
                "scale": fact.scale,
                "category": category,
                "availability": self._determine_availability(fact.name),
            })

        # Insert in batches
        batch_size = 100
        stored = 0
        for i in range(0, len(fact_records), batch_size):
            batch = fact_records[i:i + batch_size]
            try:
                self.db.client.table("xbrl_facts").insert(batch).execute()
                stored += len(batch)
            except Exception as e:
                logger.error(f"Error inserting XBRL facts batch: {e}")

        return stored

    def _categorize_fact(self, namespace: str) -> str:
        """Categorize fact based on namespace."""
        categories = {
            "se-gen-base": "financial",
            "se-ar-base": "audit",
            "se-cd-base": "company",
            "se-comp-base": "compliance",
            "se-bol-base": "legal",
            "se-misc-base": "misc",
        }
        return categories.get(namespace, "other")

    def _determine_availability(self, xbrl_name: str) -> str:
        """Determine field availability category."""
        # Core fields present in ALL documents
        core_fields = {
            "se-gen-base:Nettoomsattning",
            "se-gen-base:Rorelseresultat",
            "se-gen-base:AretsResultat",
            "se-gen-base:Tillgangar",
            "se-gen-base:EgetKapital",
            "se-gen-base:KortfristigaSkulder",
            "se-gen-base:Soliditet",
            "se-cd-base:ForetagetsNamn",
            "se-cd-base:Organisationsnummer",
        }

        if xbrl_name in core_fields:
            return "core"
        elif xbrl_name.startswith("se-gen-base:"):
            return "common"
        elif xbrl_name.startswith("se-ar-base:"):
            return "optional"
        else:
            return "extended"

    def _store_audit_history(
        self,
        orgnr: str,
        fiscal_year: int,
        audit_info: AuditInfo
    ) -> bool:
        """Store audit history record."""
        try:
            self.db.client.table("audit_history").upsert({
                "company_orgnr": orgnr,
                "fiscal_year": fiscal_year,
                "auditor_first_name": audit_info.auditor_first_name,
                "auditor_last_name": audit_info.auditor_last_name,
                "audit_firm": audit_info.audit_firm,
                "audit_completion_date": audit_info.audit_completion_date.isoformat() if audit_info.audit_completion_date else None,
                "audit_opinion": audit_info.audit_opinion,
                "source": "xbrl",
            }, on_conflict="company_orgnr,fiscal_year").execute()
            return True
        except Exception as e:
            logger.error(f"Error storing audit history: {e}")
            return False

    def _store_board_history(
        self,
        orgnr: str,
        fiscal_year: int,
        board_info: List[BoardInfo]
    ) -> int:
        """Store board history records."""
        stored = 0
        for member in board_info:
            try:
                self.db.client.table("board_history").insert({
                    "company_orgnr": orgnr,
                    "fiscal_year": fiscal_year,
                    "member_first_name": member.first_name,
                    "member_last_name": member.last_name,
                    "member_role": member.role,
                    "source": "xbrl",
                }).execute()
                stored += 1
            except Exception as e:
                logger.debug(f"Error storing board member: {e}")
        return stored

    def _update_financials_from_xbrl(
        self,
        orgnr: str,
        fiscal_year: int,
        parse_result: ParseResult,
        report_id: str
    ) -> bool:
        """Update financials table with XBRL data."""
        try:
            current = parse_result.current_year
            if not current:
                return False

            # Map XBRL data to financials columns
            updates = {
                "source_annual_report_id": report_id,
            }

            # Map available fields
            field_mapping = {
                "revenue": current.revenue,
                "operating_profit": current.operating_profit,
                "net_profit": current.net_profit,
                "profit_after_financial": current.profit_after_financial,
                "total_assets": current.total_assets,
                "equity": current.equity,
                "share_capital": current.share_capital,
                "current_liabilities": current.current_liabilities,
                "num_employees": current.num_employees,
                "cash": current.cash,
                "receivables": current.receivables,
                "equity_ratio": current.equity_ratio,
                "solidity": current.equity_ratio,  # Same as equity_ratio
                "operating_costs": current.operating_costs,
                "other_external_costs": current.other_external_costs,
                # New XBRL fields
                "profit_before_tax": current.profit_before_tax,
                "restricted_equity": current.restricted_equity,
                "unrestricted_equity": current.unrestricted_equity,
                "retained_earnings": current.retained_earnings,
                "current_assets": current.current_assets,
                "fixed_assets": current.fixed_assets,
                "personnel_costs": current.personnel_costs,
            }

            for col, value in field_mapping.items():
                if value is not None:
                    # Convert Decimal to int for bigint columns (financials table uses bigint)
                    try:
                        # Round to nearest integer for financial values
                        updates[col] = int(round(float(value)))
                    except (ValueError, TypeError):
                        updates[col] = value

            if len(updates) > 1:  # More than just report_id
                # Check if record exists
                existing = self.db.client.table("financials").select("id").eq(
                    "company_orgnr", orgnr
                ).eq("period_year", fiscal_year).execute()

                if existing.data:
                    # Update existing
                    self.db.client.table("financials").update(updates).eq(
                        "company_orgnr", orgnr
                    ).eq("period_year", fiscal_year).execute()
                else:
                    # Insert new
                    updates["company_orgnr"] = orgnr
                    updates["period_year"] = fiscal_year
                    updates["source"] = "xbrl"
                    self.db.client.table("financials").insert(updates).execute()

                return True

            return False

        except Exception as e:
            logger.error(f"Error updating financials from XBRL: {e}")
            return False

    # ============================================================
    # Query Methods
    # ============================================================

    def get_annual_report(
        self,
        orgnr: str,
        fiscal_year: int
    ) -> Optional[Dict[str, Any]]:
        """Get annual report metadata."""
        result = self.db.client.table("annual_reports").select("*").eq(
            "company_orgnr", orgnr
        ).eq("fiscal_year", fiscal_year).execute()

        return result.data[0] if result.data else None

    def get_annual_reports_for_company(
        self,
        orgnr: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get all annual reports for a company."""
        result = self.db.client.table("annual_reports").select("*").eq(
            "company_orgnr", orgnr
        ).order("fiscal_year", desc=True).limit(limit).execute()

        return result.data or []

    def get_xbrl_facts(
        self,
        orgnr: str,
        fiscal_year: Optional[int] = None,
        namespace: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get XBRL facts with optional filters."""
        query = self.db.client.table("xbrl_facts").select("*").eq(
            "company_orgnr", orgnr
        )

        if fiscal_year:
            # Get report_id for fiscal year
            report = self.get_annual_report(orgnr, fiscal_year)
            if report:
                query = query.eq("annual_report_id", report["id"])

        if namespace:
            query = query.eq("namespace", namespace)

        if category:
            query = query.eq("category", category)

        result = query.limit(limit).execute()
        return result.data or []

    def get_audit_history(
        self,
        orgnr: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get audit history for a company."""
        result = self.db.client.table("audit_history").select("*").eq(
            "company_orgnr", orgnr
        ).order("fiscal_year", desc=True).limit(limit).execute()

        return result.data or []

    def get_board_history(
        self,
        orgnr: str,
        fiscal_year: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get board history for a company."""
        query = self.db.client.table("board_history").select("*").eq(
            "company_orgnr", orgnr
        )

        if fiscal_year:
            query = query.eq("fiscal_year", fiscal_year)

        result = query.order("fiscal_year", desc=True).limit(limit).execute()
        return result.data or []

    def get_companies_with_xbrl(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[str]:
        """Get list of company orgnrs that have XBRL data."""
        result = self.db.client.table("annual_reports").select(
            "company_orgnr"
        ).eq("processing_status", "processed").order(
            "company_orgnr"
        ).range(offset, offset + limit - 1).execute()

        return list(set(r["company_orgnr"] for r in result.data)) if result.data else []

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about XBRL processing."""
        # Total reports
        total = self.db.client.table("annual_reports").select(
            "id", count="exact"
        ).execute()

        # By status
        processed = self.db.client.table("annual_reports").select(
            "id", count="exact"
        ).eq("processing_status", "processed").execute()

        failed = self.db.client.table("annual_reports").select(
            "id", count="exact"
        ).eq("processing_status", "failed").execute()

        # Total facts
        facts = self.db.client.table("xbrl_facts").select(
            "id", count="exact"
        ).execute()

        # Unique companies
        companies = self.db.client.rpc(
            "count_distinct_orgnr_xbrl", {}
        ).execute() if False else None  # Placeholder for RPC

        return {
            "total_reports": total.count if total else 0,
            "processed": processed.count if processed else 0,
            "failed": failed.count if failed else 0,
            "total_facts": facts.count if facts else 0,
        }


# Singleton instance
_storage: Optional[XBRLStorage] = None


def get_xbrl_storage() -> XBRLStorage:
    """Get singleton XBRL storage instance."""
    global _storage
    if _storage is None:
        _storage = XBRLStorage()
    return _storage
