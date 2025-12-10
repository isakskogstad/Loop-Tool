"""
XBRL Taxonomy Mapping for Swedish Annual Reports (iXBRL)
=========================================================
Maps XBRL fact names to database columns and provides extraction utilities.

Based on analysis of 28 annual reports from 9 companies (2018-2024).
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum


class FieldAvailability(Enum):
    """How consistently a field appears across documents."""
    CORE = "core"           # 100% - Always present
    COMMON = "common"       # >80% - Usually present
    EXTENDED = "extended"   # 50-80% - Often present
    OPTIONAL = "optional"   # <50% - Sometimes present


@dataclass
class XBRLMapping:
    """Mapping from XBRL field to database column."""
    xbrl_name: str
    db_column: str
    db_table: str
    description_sv: str
    description_en: str
    availability: FieldAvailability
    unit: str = "SEK"       # Default unit
    is_calculated: bool = False


# =============================================================================
# CORE FIELDS - Present in ALL documents (100%)
# =============================================================================

CORE_FINANCIAL_MAPPINGS = [
    # Income Statement
    XBRLMapping(
        xbrl_name="se-gen-base:Nettoomsattning",
        db_column="revenue",
        db_table="financials",
        description_sv="Nettoomsättning",
        description_en="Net Revenue",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Rorelseresultat",
        db_column="operating_profit",
        db_table="financials",
        description_sv="Rörelseresultat",
        description_en="Operating Profit",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:ResultatEfterFinansiellaPoster",
        db_column="profit_after_financial",
        db_table="financials",
        description_sv="Resultat efter finansiella poster",
        description_en="Profit After Financial Items",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:ResultatForeSkatt",
        db_column="profit_before_tax",
        db_table="financials",
        description_sv="Resultat före skatt",
        description_en="Profit Before Tax",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:AretsResultat",
        db_column="net_profit",
        db_table="financials",
        description_sv="Årets resultat",
        description_en="Net Profit",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Rorelsekostnader",
        db_column="operating_costs",
        db_table="financials",
        description_sv="Rörelsekostnader",
        description_en="Operating Costs",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:OvrigaExternaKostnader",
        db_column="other_external_costs",
        db_table="financials",
        description_sv="Övriga externa kostnader",
        description_en="Other External Costs",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Personalkostnader",
        db_column="personnel_costs",
        db_table="financials",
        description_sv="Personalkostnader",
        description_en="Personnel Costs",
        availability=FieldAvailability.CORE,
    ),

    # Balance Sheet - Assets
    XBRLMapping(
        xbrl_name="se-gen-base:Tillgangar",
        db_column="total_assets",
        db_table="financials",
        description_sv="Tillgångar",
        description_en="Total Assets",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Omsattningstillgangar",
        db_column="current_assets",
        db_table="financials",
        description_sv="Omsättningstillgångar",
        description_en="Current Assets",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:KortfristigaFordringar",
        db_column="receivables",
        db_table="financials",
        description_sv="Kortfristiga fordringar",
        description_en="Short-term Receivables",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:KassaBankExklRedovisningsmedel",
        db_column="cash",
        db_table="financials",
        description_sv="Kassa och bank",
        description_en="Cash and Bank",
        availability=FieldAvailability.CORE,
    ),

    # Balance Sheet - Equity
    XBRLMapping(
        xbrl_name="se-gen-base:EgetKapital",
        db_column="equity",
        db_table="financials",
        description_sv="Eget kapital",
        description_en="Equity",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:BundetEgetKapital",
        db_column="restricted_equity",
        db_table="financials",
        description_sv="Bundet eget kapital",
        description_en="Restricted Equity",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:FrittEgetKapital",
        db_column="unrestricted_equity",
        db_table="financials",
        description_sv="Fritt eget kapital",
        description_en="Unrestricted Equity",
        availability=FieldAvailability.CORE,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Aktiekapital",
        db_column="share_capital",
        db_table="financials",
        description_sv="Aktiekapital",
        description_en="Share Capital",
        availability=FieldAvailability.CORE,
    ),

    # Balance Sheet - Liabilities
    XBRLMapping(
        xbrl_name="se-gen-base:KortfristigaSkulder",
        db_column="current_liabilities",
        db_table="financials",
        description_sv="Kortfristiga skulder",
        description_en="Current Liabilities",
        availability=FieldAvailability.CORE,
    ),

    # Key Ratios
    XBRLMapping(
        xbrl_name="se-gen-base:Soliditet",
        db_column="equity_ratio",
        db_table="financials",
        description_sv="Soliditet",
        description_en="Equity Ratio",
        availability=FieldAvailability.CORE,
        unit="percent",
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:MedelantaletAnstallda",
        db_column="num_employees",
        db_table="financials",
        description_sv="Medelantalet anställda",
        description_en="Average Employees",
        availability=FieldAvailability.CORE,
        unit="count",
    ),
]

# Company identification (always present)
CORE_COMPANY_MAPPINGS = [
    XBRLMapping(
        xbrl_name="se-cd-base:ForetagetsNamn",
        db_column="name",
        db_table="companies",
        description_sv="Företagets namn",
        description_en="Company Name",
        availability=FieldAvailability.CORE,
        unit="text",
    ),
    XBRLMapping(
        xbrl_name="se-cd-base:Organisationsnummer",
        db_column="orgnr",
        db_table="companies",
        description_sv="Organisationsnummer",
        description_en="Organization Number",
        availability=FieldAvailability.CORE,
        unit="text",
    ),
    XBRLMapping(
        xbrl_name="se-cd-base:RakenskapsarForstaDag",
        db_column="fiscal_year_start",
        db_table="annual_reports",
        description_sv="Räkenskapsårets första dag",
        description_en="Fiscal Year Start",
        availability=FieldAvailability.CORE,
        unit="date",
    ),
    XBRLMapping(
        xbrl_name="se-cd-base:RakenskapsarSistaDag",
        db_column="fiscal_year_end",
        db_table="annual_reports",
        description_sv="Räkenskapsårets sista dag",
        description_en="Fiscal Year End",
        availability=FieldAvailability.CORE,
        unit="date",
    ),
]


# =============================================================================
# COMMON FIELDS - Present in >80% of documents
# =============================================================================

COMMON_FINANCIAL_MAPPINGS = [
    # Detailed Assets
    XBRLMapping(
        xbrl_name="se-gen-base:Anlaggningstillgangar",
        db_column="fixed_assets",
        db_table="financials",
        description_sv="Anläggningstillgångar",
        description_en="Fixed Assets",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:MateriellaAnlaggningstillgangar",
        db_column="tangible_assets",
        db_table="financials",
        description_sv="Materiella anläggningstillgångar",
        description_en="Tangible Fixed Assets",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:FinansiellaAnlaggningstillgangar",
        db_column="financial_assets",
        db_table="financials",
        description_sv="Finansiella anläggningstillgångar",
        description_en="Financial Fixed Assets",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:InventarierVerktygInstallationer",
        db_column="equipment",
        db_table="financials",
        description_sv="Inventarier, verktyg och installationer",
        description_en="Equipment",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Kundfordringar",
        db_column="accounts_receivable",
        db_table="financials",
        description_sv="Kundfordringar",
        description_en="Accounts Receivable",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:ForutbetaldaKostnaderUpplupnaIntakter",
        db_column="prepaid_expenses",
        db_table="financials",
        description_sv="Förutbetalda kostnader och upplupna intäkter",
        description_en="Prepaid Expenses",
        availability=FieldAvailability.COMMON,
    ),

    # Detailed Liabilities
    XBRLMapping(
        xbrl_name="se-gen-base:LangfristigaSkulder",
        db_column="long_term_liabilities",
        db_table="financials",
        description_sv="Långfristiga skulder",
        description_en="Long-term Liabilities",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Leverantorsskulder",
        db_column="accounts_payable",
        db_table="financials",
        description_sv="Leverantörsskulder",
        description_en="Accounts Payable",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:UpplupnaKostnaderForutbetaldaIntakter",
        db_column="accrued_expenses",
        db_table="financials",
        description_sv="Upplupna kostnader och förutbetalda intäkter",
        description_en="Accrued Expenses",
        availability=FieldAvailability.COMMON,
    ),

    # Financial Items
    XBRLMapping(
        xbrl_name="se-gen-base:FinansiellaPoster",
        db_column="financial_items_net",
        db_table="financials",
        description_sv="Finansiella poster",
        description_en="Financial Items Net",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:RantekostnaderLiknandeResultatposter",
        db_column="interest_costs",
        db_table="financials",
        description_sv="Räntekostnader och liknande resultatposter",
        description_en="Interest Costs",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:OvrigaRorelseintakter",
        db_column="other_income",
        db_table="financials",
        description_sv="Övriga rörelseintäkter",
        description_en="Other Operating Income",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:AvskrivningarNedskrivningarMateriellaImmateriellaAnlaggningstillgangar",
        db_column="depreciation",
        db_table="financials",
        description_sv="Avskrivningar",
        description_en="Depreciation",
        availability=FieldAvailability.COMMON,
    ),

    # Equity Details
    XBRLMapping(
        xbrl_name="se-gen-base:BalanseratResultat",
        db_column="retained_earnings",
        db_table="financials",
        description_sv="Balanserat resultat",
        description_en="Retained Earnings",
        availability=FieldAvailability.COMMON,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Overkursfond",
        db_column="share_premium",
        db_table="financials",
        description_sv="Överkursfond",
        description_en="Share Premium",
        availability=FieldAvailability.EXTENDED,
    ),
]


# =============================================================================
# EXTENDED FIELDS - Present in 50-80% of documents
# =============================================================================

EXTENDED_FINANCIAL_MAPPINGS = [
    # Intangible Assets
    XBRLMapping(
        xbrl_name="se-gen-base:ImmateriellaAnlaggningstillgangar",
        db_column="intangible_assets",
        db_table="financials",
        description_sv="Immateriella anläggningstillgångar",
        description_en="Intangible Assets",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:BalanseradeUtgifterUtvecklingsarbetenLiknandeArbeten",
        db_column="capitalized_rd",
        db_table="financials",
        description_sv="Balanserade utgifter för utvecklingsarbete",
        description_en="Capitalized R&D",
        availability=FieldAvailability.EXTENDED,
    ),

    # Cost Details
    XBRLMapping(
        xbrl_name="se-gen-base:RavarorFornodenheterKostnader",
        db_column="raw_materials",
        db_table="financials",
        description_sv="Råvaror och förnödenheter",
        description_en="Raw Materials Costs",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:HandelsvarorKostnader",
        db_column="goods",
        db_table="financials",
        description_sv="Handelsvaror",
        description_en="Goods Costs",
        availability=FieldAvailability.EXTENDED,
    ),

    # Tax
    XBRLMapping(
        xbrl_name="se-gen-base:SkattAretsResultat",
        db_column="income_tax",
        db_table="financials",
        description_sv="Skatt på årets resultat",
        description_en="Income Tax",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Skatteskulder",
        db_column="tax_liabilities",
        db_table="financials",
        description_sv="Skatteskulder",
        description_en="Tax Liabilities",
        availability=FieldAvailability.EXTENDED,
    ),

    # Reserves
    XBRLMapping(
        xbrl_name="se-gen-base:ObeskattadeReserver",
        db_column="untaxed_reserves",
        db_table="financials",
        description_sv="Obeskattade reserver",
        description_en="Untaxed Reserves",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:Periodiseringsfonder",
        db_column="tax_allocation_reserves",
        db_table="financials",
        description_sv="Periodiseringsfonder",
        description_en="Tax Allocation Reserves",
        availability=FieldAvailability.EXTENDED,
    ),

    # Key Ratios (extended)
    XBRLMapping(
        xbrl_name="se-gen-base:Kassalikviditet",
        db_column="quick_ratio",
        db_table="financials",
        description_sv="Kassalikviditet",
        description_en="Quick Ratio",
        availability=FieldAvailability.EXTENDED,
        unit="percent",
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:AvkastningEgetKapital",
        db_column="return_on_equity",
        db_table="financials",
        description_sv="Avkastning på eget kapital",
        description_en="Return on Equity",
        availability=FieldAvailability.EXTENDED,
        unit="percent",
    ),

    # Employee Details
    XBRLMapping(
        xbrl_name="se-gen-base:MedelantaletAnstalldaMan",
        db_column="employees_male",
        db_table="financials",
        description_sv="Medelantal anställda män",
        description_en="Average Male Employees",
        availability=FieldAvailability.EXTENDED,
        unit="count",
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:MedelantaletAnstalldaKvinnor",
        db_column="employees_female",
        db_table="financials",
        description_sv="Medelantal anställda kvinnor",
        description_en="Average Female Employees",
        availability=FieldAvailability.EXTENDED,
        unit="count",
    ),

    # Salary Details
    XBRLMapping(
        xbrl_name="se-gen-base:LonerAndraErsattningar",
        db_column="total_salaries",
        db_table="financials",
        description_sv="Löner och andra ersättningar",
        description_en="Total Salaries",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:LonerAndraErsattningarStyrelseledamoterVerkstallandeDirektorMotsvarandeBefattningshavare",
        db_column="salaries_board_ceo",
        db_table="financials",
        description_sv="Löner till styrelse och VD",
        description_en="Salaries Board and CEO",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:LonerAndraErsattningarOvrigaAnstallda",
        db_column="salaries_other",
        db_table="financials",
        description_sv="Löner till övriga anställda",
        description_en="Salaries Other Employees",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:SocialaKostnaderInklPensionskostnader",
        db_column="social_costs",
        db_table="financials",
        description_sv="Sociala kostnader inkl pensionskostnader",
        description_en="Social Costs incl Pension",
        availability=FieldAvailability.EXTENDED,
    ),

    # Group Company Details
    XBRLMapping(
        xbrl_name="se-gen-base:FordringarKoncernforetagKortfristiga",
        db_column="receivables_group_short",
        db_table="financials",
        description_sv="Fordringar på koncernföretag",
        description_en="Receivables Group Companies",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:SkulderKoncernforetagKortfristiga",
        db_column="liabilities_group_short",
        db_table="financials",
        description_sv="Skulder till koncernföretag",
        description_en="Liabilities Group Companies",
        availability=FieldAvailability.EXTENDED,
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:AndelarKoncernforetag",
        db_column="shares_group_companies",
        db_table="financials",
        description_sv="Andelar i koncernföretag",
        description_en="Shares in Group Companies",
        availability=FieldAvailability.EXTENDED,
    ),
]


# =============================================================================
# OPTIONAL FIELDS - Present in <50% of documents (but valuable)
# =============================================================================

OPTIONAL_AUDIT_MAPPINGS = [
    XBRLMapping(
        xbrl_name="se-ar-base:RevisionAvslutandeDatum",
        db_column="audit_date",
        db_table="annual_reports",
        description_sv="Datum revision avslutad",
        description_en="Audit Completion Date",
        availability=FieldAvailability.OPTIONAL,
        unit="date",
    ),
    XBRLMapping(
        xbrl_name="se-cd-base:ValtRevisionsbolagsnamn",
        db_column="audit_firm",
        db_table="annual_reports",
        description_sv="Revisionsbolagets namn",
        description_en="Audit Firm Name",
        availability=FieldAvailability.OPTIONAL,
        unit="text",
    ),
]

OPTIONAL_BOARD_MAPPINGS = [
    XBRLMapping(
        xbrl_name="se-gen-base:FordelningStyrelseledamoterAndelKvinnor",
        db_column="board_female_percent",
        db_table="annual_reports",
        description_sv="Andel kvinnor i styrelsen",
        description_en="Board Female Percentage",
        availability=FieldAvailability.OPTIONAL,
        unit="percent",
    ),
    XBRLMapping(
        xbrl_name="se-gen-base:FordelningStyrelseledamoterAndelMan",
        db_column="board_male_percent",
        db_table="annual_reports",
        description_sv="Andel män i styrelsen",
        description_en="Board Male Percentage",
        availability=FieldAvailability.OPTIONAL,
        unit="percent",
    ),
]


# =============================================================================
# COMBINED MAPPINGS
# =============================================================================

ALL_MAPPINGS = (
    CORE_FINANCIAL_MAPPINGS +
    CORE_COMPANY_MAPPINGS +
    COMMON_FINANCIAL_MAPPINGS +
    EXTENDED_FINANCIAL_MAPPINGS +
    OPTIONAL_AUDIT_MAPPINGS +
    OPTIONAL_BOARD_MAPPINGS
)

# Create lookup dictionaries
XBRL_TO_DB = {m.xbrl_name: m for m in ALL_MAPPINGS}
DB_TO_XBRL = {(m.db_table, m.db_column): m for m in ALL_MAPPINGS}


def get_mapping(xbrl_name: str) -> Optional[XBRLMapping]:
    """Get database mapping for an XBRL field name."""
    return XBRL_TO_DB.get(xbrl_name)


def get_core_fields() -> list[str]:
    """Get list of XBRL field names that are always present."""
    return [m.xbrl_name for m in ALL_MAPPINGS if m.availability == FieldAvailability.CORE]


def get_all_financial_fields() -> list[str]:
    """Get all XBRL field names related to financial data."""
    return [m.xbrl_name for m in ALL_MAPPINGS if m.db_table == "financials"]


def get_fields_by_availability(availability: FieldAvailability) -> list[str]:
    """Get XBRL field names by availability level."""
    return [m.xbrl_name for m in ALL_MAPPINGS if m.availability == availability]
