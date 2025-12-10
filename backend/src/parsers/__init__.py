"""
XBRL Parsers for Swedish Annual Reports

This package provides tools for parsing iXBRL annual reports
from Bolagsverket (Swedish Companies Registration Office).

Main components:
- XBRLParser: Main parser class for extracting structured data
- xbrl_taxonomy: Field mappings between XBRL and database columns
"""

from .xbrl_parser import (
    XBRLParser,
    ParseResult,
    ParseError,
    XBRLFact,
    CompanyInfo,
    FinancialData,
    AuditInfo,
    BoardInfo,
    PeriodType,
    parse_annual_report,
    extract_financials_for_db,
)

from .xbrl_taxonomy import (
    XBRLMapping,
    FieldAvailability,
    get_mapping,
    get_core_fields,
    get_all_financial_fields,
    CORE_FINANCIAL_MAPPINGS,
    COMMON_FINANCIAL_MAPPINGS,
    EXTENDED_FINANCIAL_MAPPINGS,
    OPTIONAL_AUDIT_MAPPINGS,
    OPTIONAL_BOARD_MAPPINGS,
)

__all__ = [
    # Parser
    "XBRLParser",
    "ParseResult",
    "ParseError",
    "XBRLFact",
    "CompanyInfo",
    "FinancialData",
    "AuditInfo",
    "BoardInfo",
    "PeriodType",
    "parse_annual_report",
    "extract_financials_for_db",
    # Taxonomy
    "XBRLMapping",
    "FieldAvailability",
    "get_mapping",
    "get_core_fields",
    "get_all_financial_fields",
    "CORE_FINANCIAL_MAPPINGS",
    "COMMON_FINANCIAL_MAPPINGS",
    "EXTENDED_FINANCIAL_MAPPINGS",
    "OPTIONAL_AUDIT_MAPPINGS",
    "OPTIONAL_BOARD_MAPPINGS",
]
