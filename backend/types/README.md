# @loop-auto/api-types

TypeScript types and API client for the Loop-Auto Swedish Company Data API.

## Installation

```bash
npm install @loop-auto/api-types
# or
yarn add @loop-auto/api-types
```

## Quick Start

```typescript
import { createClient } from '@loop-auto/api-types';

// Create client
const client = createClient({
  apiKey: 'your-api-key'
});

// Get company data
const company = await client.getCompany('5564461043');
console.log(company.name); // "Oatly AB"

// Get XBRL financials
const xbrl = await client.getXBRLLatest('5564461043');
console.log(xbrl.current.revenue); // 7250000000
```

## Features

- Full TypeScript type safety
- Zod runtime validation
- Automatic retry with exponential backoff
- Request/response interceptors
- Support for all API endpoints including XBRL data

## XBRL Financial Data

The client supports extracting financial data from Swedish annual reports (XBRL/iXBRL format):

```typescript
// Get all XBRL reports
const reports = await client.getXBRLReports('5564461043');

// Get flat financials for easy consumption
const financials = await client.getXBRLFinancials('5564461043', {
  years: [2023, 2022, 2021]
});

// Get latest with year-over-year comparison
const latest = await client.getXBRLLatest('5564461043');
console.log(latest.yoyChanges.revenueChange); // +15.2%
```

### Available Financial Fields

| Category | Fields |
|----------|--------|
| **Income Statement** | revenue, operatingProfit, netProfit, personnelCosts, depreciation, etc. |
| **Balance Sheet - Assets** | totalAssets, fixedAssets, currentAssets, cash, receivables, etc. |
| **Balance Sheet - Equity** | equity, shareCapital, retainedEarnings, etc. |
| **Balance Sheet - Liabilities** | currentLiabilities, longTermLiabilities, accountsPayable, etc. |
| **Key Ratios** | equityRatio, quickRatio, returnOnEquity |
| **Employees** | numEmployees, totalSalaries, socialCosts |
| **Audit** | auditorName, auditFirm, auditDate, auditOpinion |

## API Reference

### Client Methods

#### Company Data
- `getCompany(orgnr)` - Complete company data
- `getCompanySummary(orgnr)` - Quick summary
- `getCompanyBoard(orgnr)` - Board members and management
- `getCompanyFinancials(orgnr, options)` - Financial history
- `getCompanyStructure(orgnr)` - Corporate structure
- `getCompanyAnnouncements(orgnr)` - Official announcements

#### XBRL Data
- `getXBRLReports(orgnr)` - All annual reports
- `getXBRLFinancials(orgnr, options)` - Flat financial data
- `getXBRLLatest(orgnr)` - Latest with YoY comparison
- `searchXBRL(filters)` - Search by financial criteria

#### Search
- `searchCompanies(filters)` - Search with filters
- `lookupCompany(name)` - Look up by name

#### Enrichment
- `enrichCompany(request)` - Enrich single company
- `enrichBatch(request)` - Batch enrich (max 10)

## Types

Import specific types:

```typescript
import type {
  Company,
  XBRLFinancialsFlat,
  AnnualReport,
  SearchResult,
} from '@loop-auto/api-types';
```

## Zod Schemas

For runtime validation:

```typescript
import {
  XBRLFinancialsFlatSchema,
  AnnualReportSchema,
} from '@loop-auto/api-types';

// Validate response
const validated = XBRLFinancialsFlatSchema.parse(data);
```

## Error Handling

```typescript
import { ApiClientError, ValidationError } from '@loop-auto/api-types';

try {
  await client.getCompany('invalid');
} catch (error) {
  if (error instanceof ApiClientError) {
    if (error.isNotFound()) {
      console.log('Company not found');
    } else if (error.isRateLimited()) {
      console.log('Rate limited, try again later');
    }
  }
}
```

## Configuration

```typescript
const client = createClient({
  baseUrl: 'https://loop-auto-api.onrender.com', // default
  apiKey: 'your-key',
  timeout: 30000,
  retries: 3,
  validateResponses: true,
  onError: (error) => console.error(error),
});
```

## License

MIT
