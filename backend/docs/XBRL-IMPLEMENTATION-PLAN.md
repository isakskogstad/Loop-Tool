# XBRL Implementation Plan - Strategic Overview

**Skapad:** 2025-12-09
**Baserat på:** 5 specialistagenter (Backend Architect, Code Reviewer, Security Auditor, TypeScript Pro, Testing Engineer)

---

## Executive Summary

### Status
- ✅ XBRL Parser implementerad (700+ rader)
- ✅ Taxonomy mapping skapad (60+ fält)
- ✅ 28 dokument analyserade från 9 företag
- ⚠️ 2 HIGH säkerhetsproblem kräver åtgärd
- ⚠️ 3 CRITICAL kodbuggar identifierade

### Rekommendation
**FÖR DEPLOYMENT:** Fixa säkerhetsproblem och kritiska buggar först (estimerat 2-4 timmar), sedan deploy i 4 faser över 2-3 veckor.

---

## Agenternas Sammanfattade Fynd

### 1. Backend Architect - Databasdesign ✅
- **Nya tabeller:** `annual_reports`, `xbrl_facts`, `audit_history`, `board_history`
- **Nya kolumner:** 20+ nya fält i `financials`
- **API endpoints:** 7 nya endpoints för XBRL-data
- **Bedömning:** Robust arkitektur, redo för implementation

### 2. Code Reviewer - Kodkvalitet ⚠️
- **Quality Score:** 7/10
- **Critical Issues:** 3 (måste fixas)
- **High Priority:** 4 (bör fixas)
- **Styrkor:** Välstrukturerad, bra dokumentation
- **Svagheter:** Importfel, tyst exception-hantering, fragil regex

### 3. Security Auditor - Säkerhet 🚨
- **Risk Level:** HIGH
- **HIGH Issues:** 2 (ZIP bomb, XXE attack)
- **MEDIUM Issues:** 3
- **Rekommendation:** Fix required before deployment

### 4. TypeScript Pro - API Types ✅
- **Filer skapade:** 7 (types, schemas, client, examples)
- **TypeScript coverage:** 100%
- **Zod schemas:** Komplett runtime-validering
- **Status:** Redo att använda

### 5. Testing Engineer - Kvalitetssäkring ✅
- **Tester skapade:** 68
- **Pass rate:** 100%
- **Code coverage:** 89%
- **Dokumentation:** Komplett testplan och rapport

---

## KRITISKA ÅTGÄRDER (Måste fixas före deployment)

### 🚨 PRIO 1: Säkerhetsproblem (2-4 timmar)

#### 1.1 ZIP Bomb Protection
**Fil:** `src/parsers/xbrl_parser.py:340-357`
**Risk:** HIGH - Denial of Service

```python
# LÄGG TILL i klassen XBRLParser:
MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50 MB max
MAX_COMPRESSION_RATIO = 100

def _extract_xhtml_from_zip(self, content: bytes) -> Optional[str]:
    try:
        # ZIP bomb protection
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            total_size = sum(info.file_size for info in zf.infolist())
            if total_size > self.MAX_ZIP_SIZE:
                self._add_error(f"ZIP too large: {total_size} bytes")
                return None

            if len(content) > 0:
                ratio = total_size / len(content)
                if ratio > self.MAX_COMPRESSION_RATIO:
                    self._add_error(f"Suspicious compression ratio: {ratio}")
                    return None

            # Path traversal protection
            xhtml_files = [
                f for f in zf.namelist()
                if self._is_safe_zip_entry(f) and
                   f.endswith(('.xhtml', '.html')) and
                   not f.startswith('__MACOSX')
            ]
            # ... resten av metoden

def _is_safe_zip_entry(self, filename: str) -> bool:
    """Validate ZIP entry name."""
    if filename.startswith('/') or filename.startswith('\\'):
        return False
    if '..' in filename:
        return False
    return True
```

#### 1.2 XXE Attack Prevention
**Fil:** `src/parsers/xbrl_parser.py:365`
**Risk:** HIGH - Information Disclosure

```python
# ÄNDRA från:
soup = BeautifulSoup(content, 'lxml')

# TILL:
soup = BeautifulSoup(content, 'html.parser')  # Säkrare för untrusted input
```

### 🔴 PRIO 2: Kritiska Kodbuggar (1-2 timmar)

#### 2.1 Import Error i __init__.py
**Fil:** `src/parsers/__init__.py:35`

```python
# ÄNDRA från:
OPTIONAL_FINANCIAL_MAPPINGS,

# TILL:
OPTIONAL_AUDIT_MAPPINGS,
OPTIONAL_BOARD_MAPPINGS,
```

#### 2.2 Silent Exception Swallowing
**Fil:** `src/parsers/xbrl_parser.py:530`

```python
# ÄNDRA från:
except Exception:
    return None

# TILL:
except (InvalidOperation, ValueError) as e:
    self._add_warning(f"Failed to parse numeric value '{raw_value}': {e}")
    return None
```

#### 2.3 Encoding Error Handling
**Fil:** `src/parsers/xbrl_parser.py:357`

```python
# ÄNDRA från:
return xhtml_content.decode('utf-8', errors='ignore')

# TILL:
try:
    return xhtml_content.decode('utf-8')
except UnicodeDecodeError:
    self._add_warning("UTF-8 decode failed, trying latin-1")
    return xhtml_content.decode('latin-1')
```

---

## IMPLEMENTERINGSPLAN - 4 FASER

### Fas 1: Säkerhet & Bugfixes (Vecka 1, Dag 1-2)
**Mål:** Produktionsklar kod

| Task | Fil | Tid | Prioritet |
|------|-----|-----|-----------|
| ZIP bomb protection | xbrl_parser.py | 1h | CRITICAL |
| XXE prevention | xbrl_parser.py | 30min | CRITICAL |
| Fix import error | __init__.py | 15min | CRITICAL |
| Fix exception handling | xbrl_parser.py | 30min | HIGH |
| Fix encoding handling | xbrl_parser.py | 30min | HIGH |
| Kör testsuite | - | 30min | - |

**Verifiering:**
```bash
pytest tests/test_xbrl_parser.py -v
# Förväntat: 68 tests passed
```

### Fas 2: Databasmigrering (Vecka 1, Dag 3-5)
**Mål:** Nya tabeller och kolumner i produktion

#### Steg 2.1: Skapa migration
```sql
-- migrations/002_xbrl_support.sql

-- Tabell: annual_reports
CREATE TABLE IF NOT EXISTS annual_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT NOT NULL REFERENCES companies(orgnr),
    document_id TEXT,
    fiscal_year INTEGER NOT NULL,
    fiscal_year_start DATE,
    fiscal_year_end DATE,
    total_facts_extracted INTEGER,
    namespaces_used TEXT[],
    is_audited BOOLEAN DEFAULT true,
    auditor_first_name TEXT,
    auditor_last_name TEXT,
    audit_firm TEXT,
    audit_completion_date DATE,
    audit_opinion TEXT,
    processing_status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_orgnr, fiscal_year)
);

-- Tabell: xbrl_facts
CREATE TABLE IF NOT EXISTS xbrl_facts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    annual_report_id UUID REFERENCES annual_reports(id),
    company_orgnr TEXT NOT NULL,
    xbrl_name TEXT NOT NULL,
    namespace TEXT NOT NULL,
    local_name TEXT NOT NULL,
    period_type TEXT NOT NULL,
    value_numeric NUMERIC,
    value_text TEXT,
    unit_ref TEXT,
    category TEXT,
    availability TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabell: audit_history
CREATE TABLE IF NOT EXISTS audit_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT NOT NULL REFERENCES companies(orgnr),
    fiscal_year INTEGER NOT NULL,
    auditor_first_name TEXT,
    auditor_last_name TEXT,
    audit_firm TEXT,
    audit_completion_date DATE,
    audit_opinion TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_orgnr, fiscal_year)
);

-- Nya kolumner i financials
ALTER TABLE financials
ADD COLUMN IF NOT EXISTS profit_before_tax BIGINT,
ADD COLUMN IF NOT EXISTS restricted_equity BIGINT,
ADD COLUMN IF NOT EXISTS unrestricted_equity BIGINT,
ADD COLUMN IF NOT EXISTS quick_ratio NUMERIC,
ADD COLUMN IF NOT EXISTS source_annual_report_id UUID;

-- Index
CREATE INDEX idx_annual_reports_company ON annual_reports(company_orgnr);
CREATE INDEX idx_xbrl_facts_report ON xbrl_facts(annual_report_id);
CREATE INDEX idx_xbrl_facts_name ON xbrl_facts(xbrl_name);
```

#### Steg 2.2: Kör migration
```bash
# Via Supabase MCP
mcp__supabase__apply_migration(name="xbrl_support", query=<SQL ovan>)
```

**Verifiering:**
```sql
SELECT COUNT(*) FROM information_schema.tables
WHERE table_name IN ('annual_reports', 'xbrl_facts', 'audit_history');
-- Förväntat: 3
```

### Fas 3: Backend Integration (Vecka 2)
**Mål:** API endpoints och sync-service

#### Steg 3.1: Skapa storage client
**Fil:** `src/xbrl_storage.py` (från Backend Architect)

#### Steg 3.2: Skapa sync service
**Fil:** `src/annual_report_sync.py` (från Backend Architect)

#### Steg 3.3: Lägg till API endpoints
**Fil:** `src/api.py`

```python
# Nya endpoints att lägga till:
@app.get("/api/v1/companies/{orgnr}/financials/{year}")
@app.get("/api/v1/companies/{orgnr}/xbrl-facts")
@app.get("/api/v1/companies/{orgnr}/audit-info")
@app.get("/api/v1/companies/{orgnr}/annual-reports")
```

**Verifiering:**
```bash
curl https://loop-auto-api.onrender.com/api/v1/companies/5566599766/annual-reports
# Förväntat: JSON med årsredovisningar
```

### Fas 4: Data Population (Vecka 3)
**Mål:** Fylla databasen med XBRL-data

#### Steg 4.1: Backfill-script
```python
# scripts/backfill_xbrl.py
async def backfill():
    db = get_database()
    sync = get_sync_service()

    # Hämta alla företag
    companies = db.client.table('companies').select('orgnr').execute()
    orgnrs = [c['orgnr'] for c in companies.data]

    # Synca i batchar
    for batch in chunks(orgnrs, 50):
        results = await sync.sync_batch(batch)
        print(f"Processed {len(batch)} companies")
```

#### Steg 4.2: Integrera i daily-sync
```yaml
# .github/workflows/daily-sync.yml
# Lägg till efter befintlig sync:
- name: Sync Annual Reports
  run: python -c "import asyncio; from scripts.backfill_xbrl import backfill; asyncio.run(backfill())"
```

**Verifiering:**
```sql
SELECT COUNT(*) FROM annual_reports WHERE processing_status = 'processed';
SELECT COUNT(DISTINCT company_orgnr) FROM xbrl_facts;
```

---

## Riskanalys

| Risk | Sannolikhet | Konsekvens | Mitigation |
|------|-------------|------------|------------|
| ZIP bomb attack | Låg | Hög | Implementera size limits (Fas 1) |
| API rate limiting från Bolagsverket | Medium | Medium | Respektera rate limits, caching |
| Inkonsistent XBRL-data | Medium | Låg | Robust error handling, warnings |
| Databasmigrering misslyckas | Låg | Hög | Backup före migration, rollback-plan |

---

## Resursallokering

| Fas | Tidsåtgång | Beroenden |
|-----|------------|-----------|
| Fas 1: Säkerhet | 2-4 timmar | Inga |
| Fas 2: Databas | 4-8 timmar | Fas 1 klar |
| Fas 3: Backend | 8-16 timmar | Fas 2 klar |
| Fas 4: Data | 2-4 timmar | Fas 3 klar |
| **TOTALT** | **16-32 timmar** | |

---

## Verifieringschecklista

### Efter Fas 1
- [ ] Alla 68 tester passerar
- [ ] Inga CRITICAL/HIGH säkerhetsproblem

### Efter Fas 2
- [ ] Nya tabeller skapade i Supabase
- [ ] Index verifierade
- [ ] Befintlig funktionalitet fungerar

### Efter Fas 3
- [ ] Nya API endpoints svarar
- [ ] XBRL-data kan hämtas via API
- [ ] Rate limiting fungerar

### Efter Fas 4
- [ ] >1000 företag har XBRL-data
- [ ] Daily sync inkluderar årsredovisningar
- [ ] Monitoring alertar vid fel

---

## Nästa Steg

**Omedelbart (idag):**
1. Fixa kritiska säkerhetsproblem (ZIP bomb, XXE)
2. Fixa importfel i __init__.py
3. Kör testsuite för verifiering

**Denna vecka:**
4. Skapa och kör databasmigration
5. Implementera storage client och sync service

**Nästa vecka:**
6. Deploy API endpoints
7. Starta data population
8. Övervaka och finjustera

---

*Genererad av 5 specialistagenter: Backend Architect, Code Reviewer, Security Auditor, TypeScript Pro, Testing Engineer*
