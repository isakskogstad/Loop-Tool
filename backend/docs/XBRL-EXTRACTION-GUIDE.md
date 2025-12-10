# XBRL Extraction Guide for Swedish Annual Reports

## Overview

This guide documents the methodology for extracting financial data from Swedish annual reports (årsredovisningar) obtained via Bolagsverket's VDM API.

## Document Format

**Format:** iXBRL (Inline XBRL)
- ZIP archive containing XHTML file(s)
- XBRL tags embedded in HTML (`ix:nonFraction`, `ix:nonNumeric`)
- No PDF - structured data ready for extraction

## Annual Report Structure (According to Bolagsverket)

### Mandatory Parts (All Companies)

| Swedish | English | XBRL Namespace | Required |
|---------|---------|----------------|----------|
| Förvaltningsberättelse | Management Report | `se-gen-base`, text fields | ✅ All |
| Resultaträkning | Income Statement | `se-gen-base` | ✅ All |
| Balansräkning | Balance Sheet | `se-gen-base` | ✅ All |
| Noter | Notes | `se-gen-base`, various | ✅ All |
| Underskrifter | Signatures | `se-comp-base` | ✅ All |

### Optional Attachments (Larger Companies)

| Swedish | English | Trigger | XBRL Namespace |
|---------|---------|---------|----------------|
| Revisionsberättelse | Audit Report | Has auditor | `se-ar-base` |
| Kassaflödesanalys | Cash Flow | Larger company | `se-gen-base:Kassaflode*` |
| Koncernredovisning | Group Accounts | Parent company | Group fields |
| Hållbarhetsrapport | Sustainability | Larger company | Separate report |

### Company Size Definitions

**Larger company** = meets 2+ criteria in BOTH last 2 years:
- >50 employees on average (`se-gen-base:MedelantaletAnstallda`)
- >40 MSEK balance sheet (`se-gen-base:Tillgangar`)
- >80 MSEK net revenue (`se-gen-base:Nettoomsattning`)

This explains the variation in document complexity:
- Small companies: 80-150 XBRL facts
- Large companies: 300-425 XBRL facts

---

## XBRL Namespaces

| Namespace | Purpose | Fact Count |
|-----------|---------|------------|
| `se-gen-base` | General financial data | ~309 unique fields |
| `se-ar-base` | Audit report data | ~22 fields |
| `se-cd-base` | Company description | ~15 fields |
| `se-comp-base` | Company compliance/signatures | ~9 fields |
| `se-bol-base` | Company law compliance | ~9 fields |
| `se-misc-base` | Miscellaneous | ~4 fields |

---

## Extraction Methodology

### Step 1: Parse ZIP Archive

```python
import zipfile
import io

def extract_xhtml(zip_content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
        xhtml_files = [f for f in zf.namelist() if f.endswith('.xhtml')]
        return zf.read(xhtml_files[0]).decode('utf-8')
```

### Step 2: Extract XBRL Facts

Two types of facts:
- **Numeric** (`ix:nonFraction`): Financial values with units and decimals
- **Text** (`ix:nonNumeric`): Company info, descriptions, dates

```python
import re

# Numeric facts
numeric_pattern = r'<ix:nonFraction\s+([^>]+)>([^<]*)</ix:nonFraction>'
for match in re.finditer(numeric_pattern, content):
    attrs = match.group(1)  # name, contextRef, unitRef, decimals, scale
    value = match.group(2)  # raw numeric value

# Text facts
text_pattern = r'<ix:nonNumeric\s+([^>]+)>(.*?)</ix:nonNumeric>'
for match in re.finditer(text_pattern, content, re.DOTALL):
    attrs = match.group(1)
    value = match.group(2)  # may contain HTML
```

### Step 3: Parse Context References

Context references indicate which period the data belongs to:

| Pattern | Meaning | Example Fields |
|---------|---------|----------------|
| `period0` | Current fiscal year | Revenue, operating profit |
| `period1` | Previous year | Comparison data |
| `period2` | 2 years ago | Historical |
| `balans0` | Current balance date | Assets, liabilities |
| `balans1` | Previous balance date | Comparison |

### Step 4: Map to Database

Use the taxonomy mapping in `src/parsers/xbrl_taxonomy.py`:

```python
from src.parsers import get_mapping

# Get database column for XBRL field
mapping = get_mapping("se-gen-base:Nettoomsattning")
# Returns: XBRLMapping(db_column="revenue", db_table="financials", ...)
```

---

## Core Fields (100% Available)

These 31 fields are present in ALL annual reports:

### Income Statement
| XBRL Name | Swedish | English | DB Column |
|-----------|---------|---------|-----------|
| `se-gen-base:Nettoomsattning` | Nettoomsättning | Revenue | `revenue` |
| `se-gen-base:Rorelseresultat` | Rörelseresultat | Operating Profit | `operating_profit` |
| `se-gen-base:ResultatEfterFinansiellaPoster` | Resultat efter fin. poster | Profit After Financial | `profit_after_financial` |
| `se-gen-base:AretsResultat` | Årets resultat | Net Profit | `net_profit` |
| `se-gen-base:Rorelsekostnader` | Rörelsekostnader | Operating Costs | `operating_costs` |
| `se-gen-base:OvrigaExternaKostnader` | Övriga externa kostnader | Other External Costs | `other_external_costs` |

### Balance Sheet - Assets
| XBRL Name | Swedish | English | DB Column |
|-----------|---------|---------|-----------|
| `se-gen-base:Tillgangar` | Tillgångar | Total Assets | `total_assets` |
| `se-gen-base:Omsattningstillgangar` | Omsättningstillgångar | Current Assets | - |
| `se-gen-base:KortfristigaFordringar` | Kortfristiga fordringar | Receivables | `receivables` |
| `se-gen-base:KassaBankExklRedovisningsmedel` | Kassa och bank | Cash | `cash` |

### Balance Sheet - Equity & Liabilities
| XBRL Name | Swedish | English | DB Column |
|-----------|---------|---------|-----------|
| `se-gen-base:EgetKapital` | Eget kapital | Equity | `equity` |
| `se-gen-base:Aktiekapital` | Aktiekapital | Share Capital | `share_capital` |
| `se-gen-base:BundetEgetKapital` | Bundet eget kapital | Restricted Equity | - |
| `se-gen-base:FrittEgetKapital` | Fritt eget kapital | Unrestricted Equity | - |
| `se-gen-base:KortfristigaSkulder` | Kortfristiga skulder | Current Liabilities | `current_liabilities` |

### Key Ratios
| XBRL Name | Swedish | English | DB Column |
|-----------|---------|---------|-----------|
| `se-gen-base:Soliditet` | Soliditet | Equity Ratio | `equity_ratio` |
| `se-gen-base:MedelantaletAnstallda` | Medelantal anställda | Avg Employees | `num_employees` |

### Company Info
| XBRL Name | Swedish | English | DB Column |
|-----------|---------|---------|-----------|
| `se-cd-base:ForetagetsNamn` | Företagets namn | Company Name | `name` |
| `se-cd-base:Organisationsnummer` | Organisationsnummer | Org Number | `orgnr` |
| `se-cd-base:RakenskapsarForstaDag` | Räkenskapsår första dag | Fiscal Year Start | - |
| `se-cd-base:RakenskapsarSistaDag` | Räkenskapsår sista dag | Fiscal Year End | - |

---

## Common Fields (>80% Available)

Additional fields present in most reports:

### Assets
- `se-gen-base:Anlaggningstillgangar` - Fixed Assets
- `se-gen-base:ImmateriellaAnlaggningstillgangar` - Intangible Assets
- `se-gen-base:MateriellaAnlaggningstillgangar` - Tangible Assets
- `se-gen-base:Kundfordringar` - Accounts Receivable

### Liabilities
- `se-gen-base:LangfristigaSkulder` - Long-term Liabilities
- `se-gen-base:Leverantorsskulder` - Accounts Payable
- `se-gen-base:Skatteskulder` - Tax Liabilities

### Personnel
- `se-gen-base:Personalkostnader` - Personnel Costs
- `se-gen-base:LonerAndraErsattningar` - Salaries
- `se-gen-base:SocialaKostnaderInklPensionskostnader` - Social Costs

---

## Extended Fields (<80% Available)

Present in larger/more detailed reports:

### Audit Information (`se-ar-base`)
- `RevisorAnsvar` - Auditor Responsibility
- `UttalandeText` - Audit Opinion
- `RevisionAvslutandeDatum` - Audit Completion Date
- `UnderskriftRevisionsberattelseRevisorTilltalsnamn` - Auditor First Name
- `UnderskriftRevisionsberattelseRevisorEfternamn` - Auditor Last Name

### Board Information (`se-comp-base`)
- `UnderskriftFaststallelseintygForetradareTilltalsnamn` - Board Member First Name
- `UnderskriftFaststallelseintygForetradareEfternamn` - Board Member Last Name
- `UnderskriftFaststallelseintygForetradareForetradarroll` - Board Member Role

### Ratios (larger companies)
- `se-gen-base:Kassalikviditet` - Quick Ratio
- `se-gen-base:AvkastningEgetKapital` - Return on Equity
- `se-gen-base:Balansomslutning` - Balance Sheet Total

---

## Usage Example

```python
from src.parsers import XBRLParser, extract_financials_for_db

# Parse annual report
parser = XBRLParser()
result = parser.parse_zip_file("/path/to/report.zip")

# Access company info
print(f"Company: {result.company_info.name}")
print(f"Org Nr: {result.company_info.orgnr}")

# Access current year financials
current = result.current_year
print(f"Revenue: {current.revenue:,.0f} SEK")
print(f"Net Profit: {current.net_profit:,.0f} SEK")

# Access previous year for comparison
previous = result.previous_year
if previous:
    revenue_change = (current.revenue - previous.revenue) / previous.revenue * 100
    print(f"Revenue Change: {revenue_change:.1f}%")

# Convert to database records
records = extract_financials_for_db(result, company_id=123)
# Returns list of dicts ready for database insertion
```

---

## Files

| File | Purpose |
|------|---------|
| `src/parsers/xbrl_parser.py` | Main parser class |
| `src/parsers/xbrl_taxonomy.py` | XBRL to database mapping |
| `src/parsers/__init__.py` | Package exports |
| `test_annual_reports/ANALYSIS_REPORT.md` | Detailed analysis of 28 documents |
| `test_annual_reports/comprehensive/xbrl_fact_catalog.json` | Complete field catalog |

---

## Data Quality Notes

1. **All values are in SEK** - `unitRef="SEK"` in XBRL
2. **Scale factors** - Some values have `scale="3"` (thousands) or `scale="6"` (millions)
3. **Negative values** - Can be prefix `-` or Swedish `−` (Unicode minus)
4. **Missing fields** - Return `None`, not zero
5. **Multi-year data** - Single document contains 2-4 years of data

---

## Analysis Statistics

From comprehensive analysis of 28 documents from 9 companies:

- **Total facts extracted:** 5,362
- **Unique field names:** 368
- **Fields in ALL documents:** 31 (100% coverage)
- **Facts per document:** 83-425 (varies by company size)
- **Namespaces used:** 6

---

*Generated: 2025-12-09*
*Based on analysis of Bolagsverket VDM API annual reports*
