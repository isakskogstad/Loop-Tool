#!/usr/bin/env python3
"""
XBRL Parser for Swedish Annual Reports (Årsredovisningar)

This module provides a robust parser for extracting financial data from
iXBRL (Inline XBRL) annual reports from Bolagsverket.

FORMAT: Annual reports are ZIP archives containing XHTML files with embedded
XBRL tags (ix:nonFraction for numeric data, ix:nonNumeric for text).

USAGE:
    from src.parsers.xbrl_parser import XBRLParser

    parser = XBRLParser()
    result = parser.parse_zip_file("/path/to/report.zip")

    # Access extracted data
    print(result.company_info)
    print(result.financials)
    print(result.all_facts)

EXTRACTION METHODOLOGY:
    1. Open ZIP archive and find XHTML file(s)
    2. Parse XHTML using BeautifulSoup/lxml
    3. Extract ix:nonFraction (numeric) and ix:nonNumeric (text) elements
    4. Parse context references for period information
    5. Map XBRL fact names to database columns using taxonomy
    6. Return structured data ready for database insertion

HANDLES VARIATIONS:
    - Different company sizes (83-425 facts per document)
    - Companies with/without audit reports
    - Single vs multi-year historical data
    - Various namespace prefixes
    - Missing optional fields gracefully

Author: Claude Code
Date: 2025-12-09
"""

import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from bs4 import BeautifulSoup

from .xbrl_taxonomy import (
    CORE_FINANCIAL_MAPPINGS,
    COMMON_FINANCIAL_MAPPINGS,
    EXTENDED_FINANCIAL_MAPPINGS,
    OPTIONAL_AUDIT_MAPPINGS,
    OPTIONAL_BOARD_MAPPINGS,
    get_mapping,
    get_all_financial_fields,
)


class ParseError(Exception):
    """Raised when parsing fails."""
    pass


class PeriodType(Enum):
    """Type of reporting period."""
    CURRENT_YEAR = "current"      # period0, balans0
    PREVIOUS_YEAR = "previous"    # period1, balans1
    TWO_YEARS_AGO = "two_years"   # period2, balans2
    THREE_YEARS_AGO = "three_years"  # period3, balans3


@dataclass
class XBRLFact:
    """A single XBRL fact extracted from the document."""
    name: str                    # Full name with namespace (e.g., se-gen-base:Nettoomsattning)
    value: Any                   # Parsed value (Decimal for numbers, str for text)
    raw_value: str               # Original string value
    context_ref: str             # Context reference (e.g., period0, balans0)
    unit_ref: Optional[str]      # Unit reference (e.g., SEK) - only for numeric
    decimals: Optional[int]      # Decimal precision - only for numeric
    scale: Optional[int]         # Scale factor - only for numeric
    period_type: Optional[PeriodType]  # Inferred period type
    is_numeric: bool             # True for ix:nonFraction, False for ix:nonNumeric


@dataclass
class CompanyInfo:
    """Company identification data."""
    name: str
    orgnr: str
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None


@dataclass
class FinancialData:
    """Financial data for a specific period."""
    period_type: PeriodType
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    # Income Statement (Resultaträkning)
    revenue: Optional[Decimal] = None                    # Nettoomsättning
    operating_income: Optional[Decimal] = None           # Rörelseintäkter
    operating_costs: Optional[Decimal] = None            # Rörelsekostnader
    operating_profit: Optional[Decimal] = None           # Rörelseresultat
    profit_after_financial: Optional[Decimal] = None     # Resultat efter finansiella poster
    profit_before_tax: Optional[Decimal] = None          # Resultat före skatt
    net_profit: Optional[Decimal] = None                 # Årets resultat

    # Cost breakdown
    other_external_costs: Optional[Decimal] = None       # Övriga externa kostnader
    personnel_costs: Optional[Decimal] = None            # Personalkostnader
    raw_materials_costs: Optional[Decimal] = None        # Råvaror och förnödenheter
    goods_costs: Optional[Decimal] = None                # Handelsvaror
    depreciation: Optional[Decimal] = None               # Avskrivningar

    # Balance Sheet (Balansräkning) - Assets
    total_assets: Optional[Decimal] = None               # Tillgångar
    fixed_assets: Optional[Decimal] = None               # Anläggningstillgångar
    intangible_assets: Optional[Decimal] = None          # Immateriella anläggningstillgångar
    tangible_assets: Optional[Decimal] = None            # Materiella anläggningstillgångar
    financial_assets: Optional[Decimal] = None           # Finansiella anläggningstillgångar
    current_assets: Optional[Decimal] = None             # Omsättningstillgångar
    receivables: Optional[Decimal] = None                # Kortfristiga fordringar
    cash: Optional[Decimal] = None                       # Kassa och bank

    # Balance Sheet - Equity & Liabilities
    equity: Optional[Decimal] = None                     # Eget kapital
    share_capital: Optional[Decimal] = None              # Aktiekapital
    restricted_equity: Optional[Decimal] = None          # Bundet eget kapital
    unrestricted_equity: Optional[Decimal] = None        # Fritt eget kapital
    retained_earnings: Optional[Decimal] = None          # Balanserat resultat
    current_liabilities: Optional[Decimal] = None        # Kortfristiga skulder
    long_term_liabilities: Optional[Decimal] = None      # Långfristiga skulder
    accounts_payable: Optional[Decimal] = None           # Leverantörsskulder

    # Key Ratios (Nyckeltal)
    equity_ratio: Optional[Decimal] = None               # Soliditet
    quick_ratio: Optional[Decimal] = None                # Kassalikviditet
    return_on_equity: Optional[Decimal] = None           # Avkastning eget kapital
    num_employees: Optional[int] = None                  # Medelantal anställda

    # Additional fields dict for extended data
    extra: dict = field(default_factory=dict)


@dataclass
class AuditInfo:
    """Audit report information."""
    auditor_first_name: Optional[str] = None
    auditor_last_name: Optional[str] = None
    audit_firm: Optional[str] = None
    audit_completion_date: Optional[date] = None
    audit_opinion: Optional[str] = None


@dataclass
class BoardInfo:
    """Board composition information."""
    members: list = field(default_factory=list)  # List of dicts with name, role
    percent_women: Optional[Decimal] = None
    percent_men: Optional[Decimal] = None


@dataclass
class ParseResult:
    """Complete result from parsing an annual report."""
    company_info: CompanyInfo
    financials: dict[PeriodType, FinancialData]  # Keyed by period type
    audit_info: Optional[AuditInfo] = None
    board_info: Optional[BoardInfo] = None
    all_facts: list[XBRLFact] = field(default_factory=list)
    contexts: dict = field(default_factory=dict)
    namespaces: set = field(default_factory=set)
    source_file: Optional[str] = None
    parse_timestamp: datetime = field(default_factory=datetime.now)

    @property
    def current_year(self) -> Optional[FinancialData]:
        """Get current year financials."""
        return self.financials.get(PeriodType.CURRENT_YEAR)

    @property
    def previous_year(self) -> Optional[FinancialData]:
        """Get previous year financials."""
        return self.financials.get(PeriodType.PREVIOUS_YEAR)


class XBRLParser:
    """
    Parser for Swedish iXBRL annual reports.

    This parser extracts structured financial data from Bolagsverket's
    annual report format (ZIP containing XHTML with embedded XBRL).

    Example:
        parser = XBRLParser()

        # Parse from file path
        result = parser.parse_zip_file("/path/to/report.zip")

        # Parse from bytes
        result = parser.parse_zip_bytes(zip_content)

        # Access data
        print(f"Company: {result.company_info.name}")
        print(f"Revenue: {result.current_year.revenue}")
        print(f"Facts extracted: {len(result.all_facts)}")
    """

    # Security limits for ZIP processing
    MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50 MB max uncompressed size
    MAX_COMPRESSION_RATIO = 100  # Max 100:1 compression ratio (zip bomb protection)

    # Namespace prefixes used in Swedish annual reports
    NAMESPACES = {
        "se-gen-base": "General financial data",
        "se-ar-base": "Audit report data",
        "se-cd-base": "Company description",
        "se-comp-base": "Company compliance",
        "se-bol-base": "Company law compliance",
        "se-misc-base": "Miscellaneous",
    }

    # Context reference patterns
    PERIOD_PATTERNS = {
        r"period0|Period0": PeriodType.CURRENT_YEAR,
        r"period1|Period1": PeriodType.PREVIOUS_YEAR,
        r"period2|Period2": PeriodType.TWO_YEARS_AGO,
        r"period3|Period3": PeriodType.THREE_YEARS_AGO,
        r"balans0|Balans0": PeriodType.CURRENT_YEAR,
        r"balans1|Balans1": PeriodType.PREVIOUS_YEAR,
        r"balans2|Balans2": PeriodType.TWO_YEARS_AGO,
        r"balans3|Balans3": PeriodType.THREE_YEARS_AGO,
    }

    # XBRL field to FinancialData attribute mapping
    FIELD_MAPPING = {
        # Income Statement
        "se-gen-base:Nettoomsattning": "revenue",
        "se-gen-base:RorelseintakterLagerforandringarMm": "operating_income",
        "se-gen-base:Rorelsekostnader": "operating_costs",
        "se-gen-base:Rorelseresultat": "operating_profit",
        "se-gen-base:ResultatEfterFinansiellaPoster": "profit_after_financial",
        "se-gen-base:ResultatForeSkatt": "profit_before_tax",
        "se-gen-base:AretsResultat": "net_profit",
        "se-gen-base:OvrigaExternaKostnader": "other_external_costs",
        "se-gen-base:Personalkostnader": "personnel_costs",
        "se-gen-base:RavarorFornodenheterKostnader": "raw_materials_costs",
        "se-gen-base:HandelsvarorKostnader": "goods_costs",
        "se-gen-base:AvsrivningarNedskrivningarMateriellaImmateriellaAnlaggningstillgangar": "depreciation",

        # Balance Sheet - Assets
        "se-gen-base:Tillgangar": "total_assets",
        "se-gen-base:Anlaggningstillgangar": "fixed_assets",
        "se-gen-base:ImmateriellaAnlaggningstillgangar": "intangible_assets",
        "se-gen-base:MateriellaAnlaggningstillgangar": "tangible_assets",
        "se-gen-base:FinansiellaAnlaggningstillgangar": "financial_assets",
        "se-gen-base:Omsattningstillgangar": "current_assets",
        "se-gen-base:KortfristigaFordringar": "receivables",
        "se-gen-base:KassaBankExklRedovisningsmedel": "cash",

        # Balance Sheet - Equity & Liabilities
        "se-gen-base:EgetKapital": "equity",
        "se-gen-base:Aktiekapital": "share_capital",
        "se-gen-base:BundetEgetKapital": "restricted_equity",
        "se-gen-base:FrittEgetKapital": "unrestricted_equity",
        "se-gen-base:BalanseratResultat": "retained_earnings",
        "se-gen-base:KortfristigaSkulder": "current_liabilities",
        "se-gen-base:LangfristigaSkulder": "long_term_liabilities",
        "se-gen-base:Leverantorsskulder": "accounts_payable",

        # Key Ratios
        "se-gen-base:Soliditet": "equity_ratio",
        "se-gen-base:Kassalikviditet": "quick_ratio",
        "se-gen-base:AvkastningEgetKapital": "return_on_equity",
        "se-gen-base:MedelantaletAnstallda": "num_employees",
    }

    def __init__(self, strict: bool = False):
        """
        Initialize the parser.

        Args:
            strict: If True, raise exceptions on parse errors.
                   If False, log warnings and continue.
        """
        self.strict = strict
        self._errors: list[str] = []
        self._warnings: list[str] = []

    def parse_zip_file(self, file_path: str | Path) -> ParseResult:
        """
        Parse an annual report from a ZIP file path.

        Args:
            file_path: Path to the ZIP file

        Returns:
            ParseResult with extracted data

        Raises:
            ParseError: If parsing fails and strict mode is enabled
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "rb") as f:
            result = self.parse_zip_bytes(f.read())
            result.source_file = str(path)
            return result

    def parse_zip_bytes(self, content: bytes) -> ParseResult:
        """
        Parse an annual report from ZIP file bytes.

        Args:
            content: Raw bytes of the ZIP file

        Returns:
            ParseResult with extracted data
        """
        self._errors = []
        self._warnings = []

        # Find and read XHTML content from ZIP
        xhtml_content = self._extract_xhtml_from_zip(content)
        if not xhtml_content:
            raise ParseError("No XHTML file found in ZIP archive")

        # Parse XHTML
        return self._parse_xhtml(xhtml_content)

    def _is_safe_zip_entry(self, filename: str) -> bool:
        """Validate ZIP entry name is safe (no path traversal)."""
        # Reject absolute paths
        if filename.startswith('/') or filename.startswith('\\'):
            return False
        # Reject path traversal
        if '..' in filename:
            return False
        # Reject dangerous characters (Windows)
        if any(c in filename for c in [':', '*', '?', '"', '<', '>', '|']):
            return False
        return True

    def _extract_xhtml_from_zip(self, content: bytes) -> Optional[str]:
        """Extract XHTML content from ZIP archive with security checks."""
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                # Security: Check total uncompressed size (ZIP bomb protection)
                total_size = sum(info.file_size for info in zf.infolist())
                if total_size > self.MAX_ZIP_SIZE:
                    self._add_error(f"ZIP too large: {total_size} bytes (max {self.MAX_ZIP_SIZE})")
                    return None

                # Security: Check compression ratio (ZIP bomb detection)
                if len(content) > 0:
                    ratio = total_size / len(content)
                    if ratio > self.MAX_COMPRESSION_RATIO:
                        self._add_error(f"Suspicious compression ratio: {ratio:.1f} (max {self.MAX_COMPRESSION_RATIO})")
                        return None

                # Find XHTML files (with path traversal protection)
                xhtml_files = [
                    f for f in zf.namelist()
                    if self._is_safe_zip_entry(f) and
                       f.endswith(('.xhtml', '.html')) and
                       not f.startswith('__MACOSX')
                ]

                if not xhtml_files:
                    # Check for nested ZIP (with safety check)
                    nested_zips = [
                        f for f in zf.namelist()
                        if self._is_safe_zip_entry(f) and f.endswith('.zip')
                    ]
                    if nested_zips:
                        nested_content = zf.read(nested_zips[0])
                        return self._extract_xhtml_from_zip(nested_content)
                    return None

                # Read first XHTML file
                xhtml_content = zf.read(xhtml_files[0])

                # Improved encoding handling
                try:
                    return xhtml_content.decode('utf-8')
                except UnicodeDecodeError:
                    self._add_warning("UTF-8 decode failed, trying latin-1")
                    return xhtml_content.decode('latin-1')

        except zipfile.BadZipFile as e:
            self._add_error(f"Invalid ZIP file: {e}")
            return None

    def _parse_xhtml(self, content: str) -> ParseResult:
        """Parse XHTML content and extract all XBRL data."""
        # Security: Use html.parser instead of lxml to prevent XXE attacks
        # html.parser is safer for untrusted input (no external entity processing)
        soup = BeautifulSoup(content, 'html.parser')

        # Extract all facts
        all_facts = self._extract_facts(content, soup)

        # Extract contexts
        contexts = self._extract_contexts(content)

        # Extract namespaces
        namespaces = self._extract_namespaces(all_facts)

        # Build company info
        company_info = self._build_company_info(all_facts)

        # Build financial data per period
        financials = self._build_financials(all_facts)

        # Build audit info (if available)
        audit_info = self._build_audit_info(all_facts)

        # Build board info (if available)
        board_info = self._build_board_info(all_facts)

        return ParseResult(
            company_info=company_info,
            financials=financials,
            audit_info=audit_info,
            board_info=board_info,
            all_facts=all_facts,
            contexts=contexts,
            namespaces=namespaces,
        )

    def _extract_facts(self, content: str, soup: BeautifulSoup) -> list[XBRLFact]:
        """Extract all XBRL facts from the document."""
        facts = []

        # Extract numeric facts (ix:nonFraction)
        numeric_pattern = r'<ix:nonFraction\s+([^>]+)>([^<]*)</ix:nonFraction>'
        for match in re.finditer(numeric_pattern, content, re.DOTALL):
            attrs_str = match.group(1)
            raw_value = match.group(2).strip()

            fact = self._parse_numeric_fact(attrs_str, raw_value)
            if fact:
                facts.append(fact)

        # Extract text facts (ix:nonNumeric)
        text_pattern = r'<ix:nonNumeric\s+([^>]+)>(.*?)</ix:nonNumeric>'
        for match in re.finditer(text_pattern, content, re.DOTALL):
            attrs_str = match.group(1)
            raw_value = match.group(2).strip()

            # Clean HTML from text values
            raw_value = re.sub(r'<[^>]+>', ' ', raw_value)
            raw_value = re.sub(r'\s+', ' ', raw_value).strip()

            fact = self._parse_text_fact(attrs_str, raw_value)
            if fact:
                facts.append(fact)

        return facts

    def _parse_numeric_fact(self, attrs_str: str, raw_value: str) -> Optional[XBRLFact]:
        """Parse a numeric XBRL fact."""
        attrs = self._parse_attributes(attrs_str)

        name = attrs.get('name', '')
        if not name:
            return None

        context_ref = attrs.get('contextRef', '')
        unit_ref = attrs.get('unitRef')

        # Parse decimals and scale
        decimals = None
        scale = None
        if 'decimals' in attrs:
            try:
                decimals = int(attrs['decimals'])
            except ValueError:
                pass
        if 'scale' in attrs:
            try:
                scale = int(attrs['scale'])
            except ValueError:
                pass

        # Parse numeric value
        value = self._parse_numeric_value(raw_value, scale)

        # Infer period type
        period_type = self._infer_period_type(context_ref)

        return XBRLFact(
            name=name,
            value=value,
            raw_value=raw_value,
            context_ref=context_ref,
            unit_ref=unit_ref,
            decimals=decimals,
            scale=scale,
            period_type=period_type,
            is_numeric=True,
        )

    def _parse_text_fact(self, attrs_str: str, raw_value: str) -> Optional[XBRLFact]:
        """Parse a text XBRL fact."""
        attrs = self._parse_attributes(attrs_str)

        name = attrs.get('name', '')
        if not name:
            return None

        context_ref = attrs.get('contextRef', '')
        period_type = self._infer_period_type(context_ref)

        return XBRLFact(
            name=name,
            value=raw_value,
            raw_value=raw_value,
            context_ref=context_ref,
            unit_ref=None,
            decimals=None,
            scale=None,
            period_type=period_type,
            is_numeric=False,
        )

    def _parse_attributes(self, attrs_str: str) -> dict:
        """Parse HTML-style attributes string into dict."""
        attrs = {}
        pattern = r'(\w+)=["\']([^"\']*)["\']'
        for match in re.finditer(pattern, attrs_str):
            attrs[match.group(1)] = match.group(2)
        return attrs

    def _parse_numeric_value(self, raw_value: str, scale: Optional[int]) -> Optional[Decimal]:
        """Parse a numeric string into Decimal, applying scale if present."""
        if not raw_value:
            return None

        # Clean the value
        clean_value = raw_value.replace(' ', '').replace('\xa0', '')
        clean_value = clean_value.replace(',', '.')  # Swedish decimal separator

        # Handle negative values (various formats)
        is_negative = False
        if clean_value.startswith('-') or clean_value.startswith('−'):
            is_negative = True
            clean_value = clean_value[1:]
        if clean_value.startswith('(') and clean_value.endswith(')'):
            is_negative = True
            clean_value = clean_value[1:-1]

        try:
            value = Decimal(clean_value)
            if is_negative:
                value = -value

            # Apply scale (e.g., scale=3 means multiply by 1000)
            if scale:
                value = value * (Decimal(10) ** scale)

            return value
        except (InvalidOperation, ValueError, TypeError) as e:
            # Log the parsing failure for debugging (not silently ignored)
            self._add_warning(f"Failed to parse numeric value '{raw_value}': {e}")
            return None

    def _infer_period_type(self, context_ref: str) -> Optional[PeriodType]:
        """Infer the period type from context reference."""
        for pattern, period_type in self.PERIOD_PATTERNS.items():
            if re.search(pattern, context_ref, re.IGNORECASE):
                return period_type
        return None

    def _extract_contexts(self, content: str) -> dict:
        """Extract context definitions from the document."""
        contexts = {}

        # Pattern for context elements
        context_pattern = r'<xbrli:context\s+id=["\']([^"\']+)["\']>(.*?)</xbrli:context>'
        for match in re.finditer(context_pattern, content, re.DOTALL):
            context_id = match.group(1)
            context_content = match.group(2)

            # Extract period information
            period_info = {}

            # Instant date
            instant_match = re.search(r'<xbrli:instant>([^<]+)</xbrli:instant>', context_content)
            if instant_match:
                period_info['instant'] = instant_match.group(1)

            # Period start/end
            start_match = re.search(r'<xbrli:startDate>([^<]+)</xbrli:startDate>', context_content)
            end_match = re.search(r'<xbrli:endDate>([^<]+)</xbrli:endDate>', context_content)
            if start_match:
                period_info['start'] = start_match.group(1)
            if end_match:
                period_info['end'] = end_match.group(1)

            contexts[context_id] = period_info

        return contexts

    def _extract_namespaces(self, facts: list[XBRLFact]) -> set:
        """Extract unique namespaces from facts."""
        namespaces = set()
        for fact in facts:
            if ':' in fact.name:
                ns = fact.name.split(':')[0]
                namespaces.add(ns)
        return namespaces

    def _build_company_info(self, facts: list[XBRLFact]) -> CompanyInfo:
        """Build company info from facts."""
        name = ""
        orgnr = ""
        fiscal_start = None
        fiscal_end = None

        for fact in facts:
            if fact.name == "se-cd-base:ForetagetsNamn":
                name = str(fact.value)
            elif fact.name == "se-cd-base:Organisationsnummer":
                orgnr = str(fact.value).replace("-", "").replace(" ", "")
            elif fact.name == "se-cd-base:RakenskapsarForstaDag":
                fiscal_start = self._parse_date(str(fact.value))
            elif fact.name == "se-cd-base:RakenskapsarSistaDag":
                fiscal_end = self._parse_date(str(fact.value))

        return CompanyInfo(
            name=name,
            orgnr=orgnr,
            fiscal_year_start=fiscal_start,
            fiscal_year_end=fiscal_end,
        )

    def _build_financials(self, facts: list[XBRLFact]) -> dict[PeriodType, FinancialData]:
        """Build financial data per period."""
        financials = {}

        # Initialize all periods that we find
        for fact in facts:
            if fact.period_type and fact.period_type not in financials:
                financials[fact.period_type] = FinancialData(period_type=fact.period_type)

        # Map facts to financial data
        for fact in facts:
            if not fact.period_type or not fact.is_numeric:
                continue

            fin_data = financials.get(fact.period_type)
            if not fin_data:
                continue

            # Check if this fact maps to a known field
            attr_name = self.FIELD_MAPPING.get(fact.name)
            if attr_name and hasattr(fin_data, attr_name):
                setattr(fin_data, attr_name, fact.value)
            else:
                # Store in extra dict
                fin_data.extra[fact.name] = fact.value

        return financials

    def _build_audit_info(self, facts: list[XBRLFact]) -> Optional[AuditInfo]:
        """Build audit info from facts (if available)."""
        audit = AuditInfo()
        has_audit_data = False

        for fact in facts:
            if fact.name == "se-ar-base:UnderskriftRevisionsberattelseRevisorTilltalsnamn":
                audit.auditor_first_name = str(fact.value)
                has_audit_data = True
            elif fact.name == "se-ar-base:UnderskriftRevisionsberattelseRevisorEfternamn":
                audit.auditor_last_name = str(fact.value)
                has_audit_data = True
            elif fact.name == "se-cd-base:ValtRevisionsbolagsnamn":
                audit.audit_firm = str(fact.value)
                has_audit_data = True
            elif fact.name == "se-ar-base:RevisionAvslutandeDatum":
                audit.audit_completion_date = self._parse_date(str(fact.value))
                has_audit_data = True
            elif fact.name == "se-ar-base:UttalandeText":
                audit.audit_opinion = str(fact.value)
                has_audit_data = True

        return audit if has_audit_data else None

    def _build_board_info(self, facts: list[XBRLFact]) -> Optional[BoardInfo]:
        """Build board composition info from facts (if available)."""
        board = BoardInfo()
        has_board_data = False

        for fact in facts:
            if fact.name == "se-gen-base:FordelningStyrelseledamoterAndelKvinnor":
                board.percent_women = fact.value
                has_board_data = True
            elif fact.name == "se-gen-base:FordelningStyrelseledamoterAndelMan":
                board.percent_men = fact.value
                has_board_data = True

        # TODO: Extract individual board members from se-comp-base fields

        return board if has_board_data else None

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse a date string."""
        if not date_str:
            return None

        # Try common formats
        for fmt in ['%Y-%m-%d', '%Y%m%d', '%d.%m.%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        return None

    def _add_error(self, message: str):
        """Add an error message."""
        self._errors.append(message)
        if self.strict:
            raise ParseError(message)

    def _add_warning(self, message: str):
        """Add a warning message."""
        self._warnings.append(message)

    @property
    def errors(self) -> list[str]:
        """Get list of errors from last parse."""
        return self._errors.copy()

    @property
    def warnings(self) -> list[str]:
        """Get list of warnings from last parse."""
        return self._warnings.copy()


# Convenience functions

def parse_annual_report(file_path: str | Path) -> ParseResult:
    """
    Parse an annual report file.

    Convenience function that creates a parser and parses the file.

    Args:
        file_path: Path to ZIP file

    Returns:
        ParseResult with extracted data
    """
    parser = XBRLParser()
    return parser.parse_zip_file(file_path)


def extract_financials_for_db(result: ParseResult, company_id: int) -> list[dict]:
    """
    Convert ParseResult to list of dicts ready for database insertion.

    Args:
        result: ParseResult from parser
        company_id: Database company ID

    Returns:
        List of dicts with financial data per period
    """
    records = []

    for period_type, fin_data in result.financials.items():
        record = {
            "company_id": company_id,
            "period_type": period_type.value,
            "fiscal_year": None,  # Set based on period_end

            # Income Statement
            "revenue": float(fin_data.revenue) if fin_data.revenue else None,
            "operating_profit": float(fin_data.operating_profit) if fin_data.operating_profit else None,
            "profit_after_financial": float(fin_data.profit_after_financial) if fin_data.profit_after_financial else None,
            "net_profit": float(fin_data.net_profit) if fin_data.net_profit else None,
            "operating_costs": float(fin_data.operating_costs) if fin_data.operating_costs else None,

            # Balance Sheet
            "total_assets": float(fin_data.total_assets) if fin_data.total_assets else None,
            "equity": float(fin_data.equity) if fin_data.equity else None,
            "share_capital": float(fin_data.share_capital) if fin_data.share_capital else None,
            "current_liabilities": float(fin_data.current_liabilities) if fin_data.current_liabilities else None,
            "receivables": float(fin_data.receivables) if fin_data.receivables else None,
            "cash": float(fin_data.cash) if fin_data.cash else None,

            # Key Ratios
            "equity_ratio": float(fin_data.equity_ratio) if fin_data.equity_ratio else None,
            "num_employees": fin_data.num_employees,

            # Source
            "source": "bolagsverket_vdm",
        }

        # Set fiscal year from period end
        if fin_data.period_end:
            record["fiscal_year"] = fin_data.period_end.year
        elif result.company_info.fiscal_year_end:
            # Calculate based on period type
            base_year = result.company_info.fiscal_year_end.year
            if period_type == PeriodType.CURRENT_YEAR:
                record["fiscal_year"] = base_year
            elif period_type == PeriodType.PREVIOUS_YEAR:
                record["fiscal_year"] = base_year - 1
            elif period_type == PeriodType.TWO_YEARS_AGO:
                record["fiscal_year"] = base_year - 2
            elif period_type == PeriodType.THREE_YEARS_AGO:
                record["fiscal_year"] = base_year - 3

        records.append(record)

    return records


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Parsing: {file_path}")

        result = parse_annual_report(file_path)

        print(f"\n=== Company Info ===")
        print(f"Name: {result.company_info.name}")
        print(f"Org Nr: {result.company_info.orgnr}")
        print(f"Fiscal Year: {result.company_info.fiscal_year_start} - {result.company_info.fiscal_year_end}")

        print(f"\n=== Financials ===")
        for period_type, fin_data in result.financials.items():
            print(f"\n{period_type.value}:")
            print(f"  Revenue: {fin_data.revenue}")
            print(f"  Operating Profit: {fin_data.operating_profit}")
            print(f"  Net Profit: {fin_data.net_profit}")
            print(f"  Total Assets: {fin_data.total_assets}")
            print(f"  Equity: {fin_data.equity}")

        if result.audit_info:
            print(f"\n=== Audit Info ===")
            print(f"Auditor: {result.audit_info.auditor_first_name} {result.audit_info.auditor_last_name}")
            print(f"Firm: {result.audit_info.audit_firm}")

        print(f"\n=== Statistics ===")
        print(f"Total facts: {len(result.all_facts)}")
        print(f"Namespaces: {result.namespaces}")
    else:
        print("Usage: python xbrl_parser.py <path-to-zip-file>")
