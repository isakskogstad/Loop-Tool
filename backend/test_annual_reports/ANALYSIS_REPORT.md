# Comprehensive Annual Report Analysis Report

**Generated:** 2025-12-09
**Companies Analyzed:** 9 (with documents)
**Total Documents:** 28
**Total XBRL Facts Extracted:** 5,362
**Unique Fact Names:** 368

---

## Executive Summary

### Key Findings

1. **Format:** All annual reports are in **iXBRL format** (ZIP containing XHTML with embedded XBRL tags)
2. **Consistency:** 31 XBRL facts are present in **ALL** documents (100% coverage)
3. **Rich Data:** Up to 425 facts per document with financial, organizational, and audit data
4. **Multi-year:** Each document contains historical comparison data (2-4 years)
5. **Structured:** Data is already tagged - no AI/OCR needed for extraction

### Documents Per Company

| Company | Years Available | Facts Range |
|---------|-----------------|-------------|
| Sanctify Financial Technologies | 4 (2020-2023) | 155-255 |
| GeoGuessr | 3 (2018-2020) | 131-163 |
| Noberu Stockholm | 1 (2024) | 287 |
| SecTrade Konsult | 5 (2020-2024) | 148-164 |
| Smartify Sverige | 2 (2023-2024) | 306-317 |
| Braive | 6 (2019-2024) | 133-191 |
| Arrowhead Game Studios | 2 (2022-2023) | 421-425 |
| Talentium | 1 (2024) | 93 |
| ABIOSÈ | 4 (2020-2023) | 83-113 |

---

## XBRL Namespaces Used

| Namespace | Purpose | Facts Count |
|-----------|---------|-------------|
| `se-gen-base` | General financial data | 309 |
| `se-ar-base` | Audit report data | 22 |
| `se-cd-base` | Company description | 15 |
| `se-comp-base` | Company compliance | 9 |
| `se-bol-base` | Company law compliance | 9 |
| `se-misc-base` | Miscellaneous | 4 |

---

## Fields Available in ALL Documents (100% Coverage)

These 31 fields can be reliably extracted from any annual report:

### Financial Statement Data
| XBRL Field | Description | Database Column |
|------------|-------------|-----------------|
| `se-gen-base:Nettoomsattning` | Revenue | `revenue` |
| `se-gen-base:Rorelseresultat` | Operating Result | `operating_profit` |
| `se-gen-base:ResultatEfterFinansiellaPoster` | Profit After Financial Items | `profit_after_financial` |
| `se-gen-base:ResultatForeSkatt` | Profit Before Tax | NEW |
| `se-gen-base:AretsResultat` | Net Profit | `net_profit` |
| `se-gen-base:RorelseintakterLagerforandringarMm` | Operating Income + Inventory Change | NEW |
| `se-gen-base:Rorelsekostnader` | Operating Costs | `operating_costs` |
| `se-gen-base:OvrigaExternaKostnader` | Other External Costs | `other_external_costs` |
| `se-gen-base:Personalkostnader` | Personnel Costs | NEW (partial) |

### Balance Sheet Data
| XBRL Field | Description | Database Column |
|------------|-------------|-----------------|
| `se-gen-base:Tillgangar` | Total Assets | `total_assets` |
| `se-gen-base:Omsattningstillgangar` | Current Assets | NEW |
| `se-gen-base:KortfristigaFordringar` | Short-term Receivables | `receivables` |
| `se-gen-base:OvrigaFordringarKortfristiga` | Other Short-term Receivables | NEW |
| `se-gen-base:KassaBankExklRedovisningsmedel` | Cash and Bank | `cash` |
| `se-gen-base:EgetKapital` | Equity | `equity` |
| `se-gen-base:BundetEgetKapital` | Restricted Equity | NEW |
| `se-gen-base:FrittEgetKapital` | Unrestricted Equity | NEW |
| `se-gen-base:Aktiekapital` | Share Capital | `share_capital` |
| `se-gen-base:EgetKapitalSkulder` | Equity + Liabilities | NEW |
| `se-gen-base:KortfristigaSkulder` | Current Liabilities | `current_liabilities` |
| `se-gen-base:OvrigaKortfristigaSkulder` | Other Current Liabilities | NEW |

### Key Ratios & Other
| XBRL Field | Description | Database Column |
|------------|-------------|-----------------|
| `se-gen-base:Soliditet` | Equity Ratio | `solidity` / `equity_ratio` |
| `se-gen-base:MedelantaletAnstallda` | Average Employees | `num_employees` |
| `se-gen-base:AretsResultatEgetKapital` | Net Profit in Equity | NEW |
| `se-gen-base:BalanseratResultat` | Retained Earnings | NEW |

### Company Information
| XBRL Field | Description | Database Column |
|------------|-------------|-----------------|
| `se-cd-base:ForetagetsNamn` | Company Name | `name` |
| `se-cd-base:Organisationsnummer` | Org Number | `orgnr` |
| `se-cd-base:RakenskapsarForstaDag` | Fiscal Year Start | NEW |
| `se-cd-base:RakenskapsarSistaDag` | Fiscal Year End | NEW |

### Disposition
| XBRL Field | Description | Database Column |
|------------|-------------|-----------------|
| `se-gen-base:ForslagDisposition` | Proposed Disposition | NEW |
| `se-gen-base:ForslagDispositionBalanserasINyRakning` | Proposed to Retained | NEW |
| `se-gen-base:ForandringEgetKapitalAretsResultatAretsResultat` | Equity Change from Profit | NEW |

---

## Database Gap Analysis

### Currently in Database (financials table) - 60 columns
Already have good coverage of basic financials.

### NEW Data Available from XBRL (not in database)

#### High Value - Financial Details
| XBRL Field | Value |
|------------|-------|
| `se-gen-base:ResultatForeSkatt` | Profit before tax |
| `se-gen-base:Omsattningstillgangar` | Current assets total |
| `se-gen-base:BundetEgetKapital` | Restricted equity |
| `se-gen-base:FrittEgetKapital` | Free equity |
| `se-gen-base:BalanseratResultat` | Retained earnings |
| `se-gen-base:Kassalikviditet` | Quick ratio |
| `se-gen-base:AvkastningEgetKapital` | Return on equity |
| `se-gen-base:Balansomslutning` | Balance sheet total |

#### Medium Value - Cost Breakdown
| XBRL Field | Value |
|------------|-------|
| `se-gen-base:RavarorFornodenheterKostnader` | Raw materials costs |
| `se-gen-base:HandelsvarorKostnader` | Goods costs |
| `se-gen-base:LonerAndraErsattningar` | Salaries total |
| `se-gen-base:SocialaKostnaderInklPensionskostnader` | Social costs incl pension |
| `se-gen-base:OvrigaSocialaAvgifterEnligtLagAvtal` | Other social costs |
| `se-gen-base:PensionskostnaderOvrigaAnstallda` | Pension costs - other |
| `se-gen-base:PensionskostnaderStyrelsenVerkstallandeDirektorenMotsvarandeBefattningshavare` | Pension costs - board/CEO |

#### Medium Value - Asset Details
| XBRL Field | Value |
|------------|-------|
| `se-gen-base:ImmateriellaAnlaggningstillgangar` | Intangible assets |
| `se-gen-base:MateriellaAnlaggningstillgangar` | Tangible assets |
| `se-gen-base:FinansiellaAnlaggningstillgangar` | Financial assets |
| `se-gen-base:Anlaggningstillgangar` | Fixed assets total |
| `se-gen-base:InventarierVerktygInstallationer` | Equipment |
| `se-gen-base:BalanseradeUtgifterUtvecklingsarbetenLiknandeArbeten` | Capitalized R&D |
| `se-gen-base:AndelarKoncernforetag` | Shares in group companies |

#### Medium Value - Liability Details
| XBRL Field | Value |
|------------|-------|
| `se-gen-base:LangfristigaSkulder` | Long-term liabilities |
| `se-gen-base:Leverantorsskulder` | Accounts payable |
| `se-gen-base:Skatteskulder` | Tax liabilities |
| `se-gen-base:UpplupnaKostnaderForutbetaldaIntakter` | Accrued expenses |
| `se-gen-base:ObeskattadeReserver` | Untaxed reserves |
| `se-gen-base:Periodiseringsfonder` | Tax allocation reserves |

#### Special Value - Group Information
| XBRL Field | Value |
|------------|-------|
| `se-gen-base:FordringarKoncernforetagKortfristiga` | Receivables from group |
| `se-gen-base:SkulderKoncernforetagKortfristiga` | Liabilities to group |
| `se-gen-base:NotUpplysningModerforetag` | Parent company info |
| `se-gen-base:AndelarKoncernforetagAnskaffningsvarden` | Group company shares cost |

#### Audit Information
| XBRL Field | Value |
|------------|-------|
| `se-ar-base:RevisorAnsvar` | Auditor responsibility |
| `se-ar-base:UttalandeText` | Audit opinion |
| `se-ar-base:RevisionAvslutandeDatum` | Audit completion date |
| `se-ar-base:UnderskriftRevisionsberattelseRevisorTilltalsnamn` | Auditor first name |
| `se-ar-base:UnderskriftRevisionsberattelseRevisorEfternamn` | Auditor last name |
| `se-cd-base:ValtRevisionsbolagsnamn` | Audit firm name |

#### Board/Signature Information
| XBRL Field | Value |
|------------|-------|
| `se-comp-base:UnderskriftFaststallelseintygForetradareTilltalsnamn` | Board member first name |
| `se-comp-base:UnderskriftFaststallelseintygForetradareEfternamn` | Board member last name |
| `se-comp-base:UnderskriftFaststallelseintygForetradareForetradarroll` | Board member role |
| `se-gen-base:FordelningStyrelseledamoterAndelKvinnor` | % women on board |
| `se-gen-base:FordelningStyrelseledamoterAndelMan` | % men on board |

---

## Structural Variations Between Documents

### Variation by Company Size/Type

| Factor | Small Companies | Large Companies |
|--------|-----------------|-----------------|
| Facts count | 80-150 | 300-425 |
| Has cash flow | Often no | Usually yes |
| Has audit report | Sometimes | Always |
| Has notes detail | Minimal | Extensive |
| Historical years | 2 | 3-4 |

### Namespace Variations

| Namespace | When Used |
|-----------|-----------|
| `se-ar-base` | Only when audited |
| `se-bol-base` | Some compliance docs |
| `se-comp-base` | Alternative compliance |
| `se-misc-base` | Custom/undefined fields |

### Period Context Patterns

| Context ID | Meaning |
|------------|---------|
| `period0` | Current year |
| `period1` | Previous year |
| `period2` | 2 years ago |
| `period3` | 3 years ago |
| `balans0` | Current balance date |
| `balans1` | Previous balance date |

---

## Recommended Extraction Strategy

### Phase 1: Core Financial Data (Always Available)
Extract the 31 fields that are present in ALL documents.

### Phase 2: Extended Financial Data (Usually Available)
Extract 50+ additional fields that are present in >80% of documents.

### Phase 3: Special Data (When Available)
Extract audit info, board composition, group details when present.

### Dynamic Extraction Method

```python
# Recommended approach
PRIORITY_FIELDS = {
    # Level 1: Always available (100%)
    "core": [
        "se-gen-base:Nettoomsattning",
        "se-gen-base:Rorelseresultat",
        "se-gen-base:AretsResultat",
        "se-gen-base:Tillgangar",
        "se-gen-base:EgetKapital",
        # ... other core fields
    ],

    # Level 2: Usually available (>80%)
    "extended": [
        "se-gen-base:Leverantorsskulder",
        "se-gen-base:Kundfordringar",
        "se-gen-base:LangfristigaSkulder",
        # ... other extended fields
    ],

    # Level 3: Sometimes available (<80%)
    "optional": [
        "se-ar-base:RevisorAnsvar",
        "se-gen-base:Kassalikviditet",
        # ... other optional fields
    ]
}

def extract_facts(xhtml_content):
    """Extract all available facts, categorized by availability."""
    facts = {}
    for level, field_list in PRIORITY_FIELDS.items():
        for field in field_list:
            value = extract_field(xhtml_content, field)
            if value is not None:
                facts[field] = value
    return facts
```

---

## Summary: Data Availability vs Current Database

| Category | XBRL Available | In Database | Gap |
|----------|---------------|-------------|-----|
| Core financials | 31 fields | ~25 fields | 6 new |
| Extended financials | 100+ fields | ~35 fields | 65+ new |
| Cost breakdown | 15+ fields | ~8 fields | 7+ new |
| Asset details | 20+ fields | ~6 fields | 14+ new |
| Liability details | 15+ fields | ~6 fields | 9+ new |
| Group info | 10+ fields | ~4 fields | 6+ new |
| Audit info | 15+ fields | 0 fields | 15 new |
| Board composition | 10+ fields | 0 fields | 10 new |

**Total potential new data points: 130+ fields**

---

## Recommendations

1. **Implement XBRL Parser** - Build robust parser for iXBRL format
2. **Store Raw Facts** - Create `xbrl_facts` table for all extracted data
3. **Map to Existing Schema** - Link XBRL fields to existing columns
4. **Add Time Series** - Store multi-year data from single document
5. **Automated Sync** - Integrate into daily sync workflow
