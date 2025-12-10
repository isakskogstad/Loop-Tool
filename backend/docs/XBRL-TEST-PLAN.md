# XBRL Parser Test Plan

**Version:** 1.0
**Date:** 2025-12-09
**Author:** MCP Testing Engineer
**Status:** DRAFT

---

## Executive Summary

This test plan provides comprehensive quality assurance for the XBRL parser implementation used to extract financial data from Swedish annual reports (arsredovisningar). The parser is critical for production use and must handle various document formats reliably.

### Scope

| Component | File | Description |
|-----------|------|-------------|
| XBRLParser | `src/parsers/xbrl_parser.py` | Main parser class |
| xbrl_taxonomy | `src/parsers/xbrl_taxonomy.py` | Field mapping definitions |
| Test Suite | `tests/test_xbrl_parser.py` | Pytest test implementation |

### Test Data

| Location | Content | Count |
|----------|---------|-------|
| `test_annual_reports/` | Real ZIP documents | 4 files |
| `test_annual_reports/comprehensive/` | Pre-analyzed JSON facts | 28 files |

---

## 1. Unit Tests

### 1.1 `_parse_numeric_value()` - Numeric Parsing

**Priority:** HIGH
**Risk:** Incorrect financial data extraction

| Test Case | Input | Expected | Status |
|-----------|-------|----------|--------|
| Simple integer | "1234" | Decimal(1234) | IMPLEMENTED |
| With spaces (thousand sep) | "1 234 567" | Decimal(1234567) | IMPLEMENTED |
| Swedish decimal (comma) | "1234,56" | Decimal(1234.56) | IMPLEMENTED |
| Negative dash prefix | "-1234" | Decimal(-1234) | IMPLEMENTED |
| Negative Unicode minus | "\u22121234" | Decimal(-1234) | IMPLEMENTED |
| Negative parentheses | "(1234)" | Decimal(-1234) | IMPLEMENTED |
| Scale factor 3 (thousands) | "1234", scale=3 | Decimal(1234000) | IMPLEMENTED |
| Scale factor 6 (millions) | "50", scale=6 | Decimal(50000000) | IMPLEMENTED |
| Empty value | "" | None | IMPLEMENTED |
| Non-breaking space | "1\xa0234" | Decimal(1234) | IMPLEMENTED |
| Complex negative with scale | "-2 829", scale=3 | Decimal(-2829000) | IMPLEMENTED |

### 1.2 `_infer_period_type()` - Context Inference

**Priority:** HIGH
**Risk:** Data assigned to wrong period

| Test Case | Input | Expected | Status |
|-----------|-------|----------|--------|
| period0 | "period0" | CURRENT_YEAR | IMPLEMENTED |
| period1 | "period1" | PREVIOUS_YEAR | IMPLEMENTED |
| period2 | "period2" | TWO_YEARS_AGO | IMPLEMENTED |
| period3 | "period3" | THREE_YEARS_AGO | IMPLEMENTED |
| balans0 | "balans0" | CURRENT_YEAR | IMPLEMENTED |
| balans1 | "balans1" | PREVIOUS_YEAR | IMPLEMENTED |
| Case insensitive | "Period0" | CURRENT_YEAR | IMPLEMENTED |
| Unknown context | "unknown" | None | IMPLEMENTED |

### 1.3 `_parse_date()` - Date Parsing

**Priority:** MEDIUM
**Risk:** Incorrect fiscal year dates

| Test Case | Input | Expected | Status |
|-----------|-------|----------|--------|
| ISO format | "2023-12-31" | date(2023,12,31) | IMPLEMENTED |
| Compact format | "20231231" | date(2023,12,31) | IMPLEMENTED |
| European dot | "31.12.2023" | date(2023,12,31) | IMPLEMENTED |
| European slash | "31/12/2023" | date(2023,12,31) | IMPLEMENTED |
| Invalid format | "invalid" | None | IMPLEMENTED |
| Empty string | "" | None | IMPLEMENTED |
| With whitespace | "  2023-12-31  " | date(2023,12,31) | IMPLEMENTED |

### 1.4 `_parse_attributes()` - Attribute Parsing

**Priority:** MEDIUM

| Test Case | Input | Expected | Status |
|-----------|-------|----------|--------|
| Double quotes | name="test" | {"name": "test"} | IMPLEMENTED |
| Single quotes | name='test' | {"name": "test"} | IMPLEMENTED |
| Multiple attrs | name="a" ctx="b" | {"name":"a","ctx":"b"} | IMPLEMENTED |

---

## 2. Integration Tests

### 2.1 Real Document Parsing

**Priority:** CRITICAL
**Test Documents:**

| File | Company | Size | Facts |
|------|---------|------|-------|
| `5590179924_SecTrade_Konsult_AB_2020.zip` | SecTrade | Small | ~160 |
| `5569914046_Podspace_AB_2019.zip` | Podspace | Small | ~150 |
| `5569201998_Modular_Finance_AB_2021.zip` | Modular Finance | Medium | ~200 |
| `5568022171_BONESUPPORT_HOLDING_AB_2022.zip` | BONESUPPORT | Large | ~420 |

**Test Cases:**

| Test Case | Description | Status |
|-----------|-------------|--------|
| Parse all documents | All 4 documents parse successfully | IMPLEMENTED |
| Core fields present | Essential fields in all docs | IMPLEMENTED |
| Multi-year data | Historical data extraction | IMPLEMENTED |
| Fact count reasonable | 50-500 facts per document | IMPLEMENTED |

### 2.2 Context Reference Verification

**Priority:** HIGH

| Context Pattern | Description | Status |
|-----------------|-------------|--------|
| period0, period1 | Income statement periods | IMPLEMENTED |
| balans0, balans1 | Balance sheet instants | IMPLEMENTED |
| Mixed contexts | Both in same document | IMPLEMENTED |

### 2.3 31 Core Fields Extraction

**Priority:** CRITICAL

Based on ANALYSIS_REPORT.md, these 31 fields appear in ALL documents:

**Income Statement (100% coverage):**
- [ ] `se-gen-base:Nettoomsattning` (Revenue)
- [ ] `se-gen-base:Rorelseresultat` (Operating Profit)
- [ ] `se-gen-base:ResultatEfterFinansiellaPoster` (Profit After Financial)
- [ ] `se-gen-base:ResultatForeSkatt` (Profit Before Tax)
- [ ] `se-gen-base:AretsResultat` (Net Profit)
- [ ] `se-gen-base:Rorelsekostnader` (Operating Costs)
- [ ] `se-gen-base:OvrigaExternaKostnader` (Other External Costs)
- [ ] `se-gen-base:Personalkostnader` (Personnel Costs)

**Balance Sheet Assets (100% coverage):**
- [ ] `se-gen-base:Tillgangar` (Total Assets)
- [ ] `se-gen-base:Omsattningstillgangar` (Current Assets)
- [ ] `se-gen-base:KortfristigaFordringar` (Receivables)
- [ ] `se-gen-base:KassaBankExklRedovisningsmedel` (Cash)

**Balance Sheet Equity (100% coverage):**
- [ ] `se-gen-base:EgetKapital` (Equity)
- [ ] `se-gen-base:BundetEgetKapital` (Restricted Equity)
- [ ] `se-gen-base:FrittEgetKapital` (Unrestricted Equity)
- [ ] `se-gen-base:Aktiekapital` (Share Capital)

**Balance Sheet Liabilities (100% coverage):**
- [ ] `se-gen-base:KortfristigaSkulder` (Current Liabilities)
- [ ] `se-gen-base:EgetKapitalSkulder` (Equity + Liabilities)

**Key Ratios (100% coverage):**
- [ ] `se-gen-base:Soliditet` (Equity Ratio)
- [ ] `se-gen-base:MedelantaletAnstallda` (Avg Employees)

**Company Info (100% coverage):**
- [ ] `se-cd-base:ForetagetsNamn` (Company Name)
- [ ] `se-cd-base:Organisationsnummer` (Org Number)
- [ ] `se-cd-base:RakenskapsarForstaDag` (Fiscal Year Start)
- [ ] `se-cd-base:RakenskapsarSistaDag` (Fiscal Year End)

---

## 3. Regression Tests

### 3.1 Consistent Output

**Priority:** HIGH

| Test Case | Description | Status |
|-----------|-------------|--------|
| Deterministic parsing | Same doc = same result | IMPLEMENTED |
| Fact count stability | Consistent fact counts | IMPLEMENTED |
| Value stability | Same values extracted | IMPLEMENTED |

### 3.2 Known Value Verification

**Priority:** CRITICAL

Compare parsed values against pre-analyzed JSON facts in `comprehensive/` directory.

| Document | Key Values to Verify |
|----------|---------------------|
| SecTrade 2020 | Revenue ~2.8 MSEK, Soliditet 80% |
| BONESUPPORT 2022 | 400+ facts, multi-year |

---

## 4. Performance Tests

### 4.1 Timing Requirements

**Priority:** MEDIUM

| Test Case | Target | Status |
|-----------|--------|--------|
| Small document (<100KB) | < 1 second | IMPLEMENTED |
| Large document (~3MB) | < 5 seconds | IMPLEMENTED |
| Batch (4 documents) | < 8 seconds | IMPLEMENTED |

### 4.2 Resource Usage

**Priority:** LOW

| Metric | Target | Status |
|--------|--------|--------|
| Memory per document | < 100 MB | TODO |
| CPU during parse | Single thread | TODO |
| 100 document batch | < 2 min total | TODO |

---

## 5. Data Quality Tests

### 5.1 Value Validation

**Priority:** HIGH

| Test Case | Validation Rule | Status |
|-----------|-----------------|--------|
| Organization number | 10 digits, valid checksum | IMPLEMENTED |
| Revenue | Typically positive | IMPLEMENTED |
| Total assets | Must be positive | IMPLEMENTED |
| Equity ratio | Between -100% and 100% | IMPLEMENTED |
| Employees | Non-negative integer | IMPLEMENTED |

### 5.2 Balance Sheet Integrity

**Priority:** HIGH

| Test Case | Rule | Status |
|-----------|------|--------|
| Assets = Equity + Liabilities | Accounting equation | IMPLEMENTED |
| Current assets <= Total assets | Asset hierarchy | TODO |
| Equity <= Total assets | Solvency check | TODO |

### 5.3 Date Logic

**Priority:** MEDIUM

| Test Case | Rule | Status |
|-----------|------|--------|
| Fiscal year start < end | Date ordering | IMPLEMENTED |
| Fiscal year ~12 months | 300-400 days | IMPLEMENTED |
| Report date after fiscal end | Sequence check | TODO |

---

## 6. Edge Cases

### 6.1 Error Handling

**Priority:** CRITICAL

| Test Case | Scenario | Expected | Status |
|-----------|----------|----------|--------|
| Empty ZIP | No files in archive | ParseError | IMPLEMENTED |
| No XHTML | ZIP without XHTML | ParseError | IMPLEMENTED |
| Corrupt ZIP | Invalid ZIP bytes | ParseError | IMPLEMENTED |
| No XBRL tags | Valid XHTML, no data | Empty result | IMPLEMENTED |
| Nested ZIP | ZIP within ZIP | Parse inner | IMPLEMENTED |
| Missing company info | No se-cd-base tags | Empty strings | IMPLEMENTED |
| Strict mode | Error in strict | Raises exception | IMPLEMENTED |

### 6.2 Format Variations

**Priority:** HIGH

| Test Case | Variation | Status |
|-----------|-----------|--------|
| Different namespace prefixes | se-gen-base vs SE-GEN-BASE | TODO |
| XHTML vs HTML extension | Both should work | IMPLEMENTED |
| UTF-8 encoding | Swedish characters (a, a, o) | TODO |
| BOM markers | With/without BOM | TODO |

---

## 7. Test Execution

### 7.1 Running Tests

```bash
# All tests
pytest tests/test_xbrl_parser.py -v

# With coverage
pytest tests/test_xbrl_parser.py --cov=src/parsers --cov-report=html

# Specific category
pytest tests/test_xbrl_parser.py -k "TestParseNumericValue" -v

# Performance tests only
pytest tests/test_xbrl_parser.py -k "TestPerformance" -v

# Skip slow tests
pytest tests/test_xbrl_parser.py -m "not slow"
```

### 7.2 Test Categories

| Category | pytest marker | Count |
|----------|--------------|-------|
| Unit tests | default | ~35 |
| Integration tests | -k "TestRealDocuments" | ~5 |
| Regression tests | -k "TestRegression" | ~3 |
| Performance tests | -k "TestPerformance" | ~3 |
| Data quality tests | -k "TestDataQuality" | ~5 |

---

## 8. CI/CD Recommendations

### 8.1 GitHub Actions Workflow

```yaml
name: XBRL Parser Tests

on:
  push:
    paths:
      - 'src/parsers/**'
      - 'tests/test_xbrl_parser.py'
  pull_request:
    paths:
      - 'src/parsers/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-cov

      - name: Run unit tests
        run: pytest tests/test_xbrl_parser.py -v --tb=short

      - name: Run with coverage
        run: |
          pytest tests/test_xbrl_parser.py --cov=src/parsers --cov-fail-under=80

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 8.2 Quality Gates

| Gate | Threshold | Blocking |
|------|-----------|----------|
| Unit tests pass | 100% | YES |
| Integration tests pass | 100% | YES |
| Code coverage | >= 80% | YES |
| Performance (large doc) | < 5s | NO |

---

## 9. Known Issues & Limitations

### 9.1 Current Limitations

1. **Encoding detection** - Assumes UTF-8, may fail on other encodings
2. **Nested contexts** - Does not parse dimensional contexts fully
3. **Group reports** - Consolidated reports not fully tested
4. **Cash flow** - Not all cash flow fields mapped

### 9.2 Future Enhancements

1. Add support for full XBRL validation
2. Implement dimensional context parsing
3. Add XML schema validation
4. Support for older report formats

---

## 10. Test Report Template

```markdown
## XBRL Parser Test Report

### Summary
- **Date:** YYYY-MM-DD
- **Version:** x.x.x
- **Status:** PASS/FAIL

### Test Results

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| Unit | X | X | X |
| Integration | X | X | X |
| Regression | X | X | X |
| Performance | X | X | X |
| Data Quality | X | X | X |

### Coverage
- Line coverage: XX%
- Branch coverage: XX%

### Issues Found
- [List any issues]

### Performance Metrics
| Document | Parse Time | Facts |
|----------|------------|-------|
| SecTrade | XXms | XX |
| BONESUPPORT | XXms | XX |

### Recommendations
1. [List recommendations]
```

---

## Appendix A: Test Fixtures Reference

### Sample XHTML Structure

```xml
<ix:nonFraction
    name="se-gen-base:Nettoomsattning"
    contextRef="period0"
    unitRef="SEK"
    decimals="0"
    scale="3">10 500</ix:nonFraction>
```

### Context Definition

```xml
<xbrli:context id="period0">
    <xbrli:period>
        <xbrli:startDate>2023-01-01</xbrli:startDate>
        <xbrli:endDate>2023-12-31</xbrli:endDate>
    </xbrli:period>
</xbrli:context>
```

---

## Appendix B: Field Availability Matrix

| Field | Core | Common | Extended | Optional |
|-------|------|--------|----------|----------|
| Nettoomsattning | X | | | |
| Rorelseresultat | X | | | |
| AretsResultat | X | | | |
| Tillgangar | X | | | |
| EgetKapital | X | | | |
| Anlaggningstillgangar | | X | | |
| LangfristigaSkulder | | X | | |
| Kassalikviditet | | | X | |
| Audit info | | | | X |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-09 | MCP Testing Engineer | Initial draft |
