/**
 * Loop-Auto API Client - Usage Examples
 * ======================================
 *
 * Practical examples showing how to use the TypeScript API client
 * for Swedish company data and XBRL financials.
 *
 * @author Claude Code (typescript-pro agent)
 * @date 2024-12-09
 */

import {
  LoopAutoClient,
  createClient,
  ApiClientError,
  ValidationError,
  PeriodType,
  type Company,
  type XBRLFinancialsFlat,
  type XBRLLatestResponse,
  type SearchResult,
} from './index';

// =============================================================================
// BASIC SETUP
// =============================================================================

/**
 * Example 1: Create client with API key (production)
 */
function setupProductionClient(): LoopAutoClient {
  return createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
    // Optional: customize behavior
    timeout: 30000,
    retries: 3,
    validateResponses: true,
  });
}

/**
 * Example 2: Create client for local development
 */
function setupDevClient(): LoopAutoClient {
  return new LoopAutoClient({
    baseUrl: 'http://localhost:8000',
    // No API key needed in dev mode
    validateResponses: false, // Faster without validation
  });
}

/**
 * Example 3: Client with custom interceptors
 */
function setupClientWithInterceptors(): LoopAutoClient {
  return createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
    onRequest: (config) => {
      console.log('Making request:', config);
      return config;
    },
    onResponse: <T>(response: T): T => {
      console.log('Got response:', response);
      return response;
    },
    onError: (error) => {
      console.error('API error:', error.message, error.requestId);
      // Could send to error tracking service
    },
  });
}

// =============================================================================
// COMPANY DATA EXAMPLES
// =============================================================================

/**
 * Example 4: Get complete company data
 */
async function getCompanyExample(): Promise<void> {
  const client = createClient({
    apiKey: '2A6uNO2Z9HKTYLCBMQmGalaIJfNUJNjEJwuq1RpjHUg',
  });

  try {
    // Get Oatly AB
    const company = await client.getCompany('5564461043');

    console.log('Company:', company.name);
    console.log('Status:', company.status);
    console.log('Revenue:', company.revenue?.toLocaleString('sv-SE'), 'SEK');
    console.log('Employees:', company.numEmployees);

    // Access board members
    console.log('\nBoard members:');
    company.roles
      .filter((r) => r.roleCategory === 'BOARD')
      .forEach((r) => console.log(`  - ${r.name} (${r.roleType})`));

    // Access financial history
    console.log('\nFinancial history:');
    company.financials.forEach((f) => {
      console.log(
        `  ${f.periodYear}: Revenue ${f.revenue?.toLocaleString('sv-SE')} SEK`
      );
    });
  } catch (error) {
    if (error instanceof ApiClientError) {
      if (error.isNotFound()) {
        console.log('Company not found');
      } else if (error.isRateLimited()) {
        console.log('Rate limited, try again later');
      } else {
        console.error('API error:', error.message);
      }
    }
    throw error;
  }
}

/**
 * Example 5: Get company summary (lightweight)
 */
async function getCompanySummaryExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  const summary = await client.getCompanySummary('5564461043');

  console.log('Summary:', summary.name);
  console.log('CEO:', summary.keyPersons?.ceo);
  console.log('Chairman:', summary.keyPersons?.chairman);
  console.log('Key figures:', summary.keyFigures);
  console.log('Board size:', summary.boardSize);
}

/**
 * Example 6: Search companies
 */
async function searchCompaniesExample(): Promise<SearchResult[]> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  // Search by name
  const results = await client.searchCompanies({
    q: 'Oatly',
    limit: 10,
  });

  console.log(`Found ${results.length} companies:`);
  results.forEach((r) => {
    console.log(`  ${r.orgnr}: ${r.name}`);
    console.log(`    Revenue: ${r.revenue?.toLocaleString('sv-SE')} SEK`);
    console.log(`    Employees: ${r.numEmployees}`);
  });

  // Search with filters
  const largeCompanies = await client.searchCompanies({
    municipality: 'Stockholm',
    minRevenue: 100000000, // 100M SEK
    minEmployees: 50,
    status: 'ACTIVE',
    limit: 20,
  });

  console.log(`\nLarge Stockholm companies: ${largeCompanies.length}`);

  return results;
}

/**
 * Example 7: Look up company by name
 */
async function lookupCompanyExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  const lookup = await client.lookupCompany('IKEA', 5);

  console.log(`Search: "${lookup.query}"`);
  console.log(`Found: ${lookup.count} matches`);
  lookup.results.forEach((r) => {
    console.log(`  ${r.orgnr}: ${r.name} (${r.orgForm})`);
  });
}

// =============================================================================
// XBRL FINANCIAL DATA EXAMPLES
// =============================================================================

/**
 * Example 8: Get XBRL annual reports
 */
async function getXBRLReportsExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  const xbrl = await client.getXBRLReports('5564461043');

  console.log(`XBRL data for: ${xbrl.name}`);
  console.log(`Total reports: ${xbrl.totalReports}`);

  xbrl.reports.forEach((report) => {
    console.log(`\nReport for fiscal year ${report.company.fiscalYearEnd}:`);
    console.log(`  Source: ${report.meta.source}`);
    console.log(`  Facts extracted: ${report.meta.totalFacts}`);

    // Access structured financials
    report.financials.forEach((period) => {
      if (period.periodType === PeriodType.CURRENT_YEAR) {
        console.log(`\n  Current year (${period.fiscalYear}):`);
        console.log(
          `    Revenue: ${period.incomeStatement.revenue?.toLocaleString('sv-SE')} SEK`
        );
        console.log(
          `    Net profit: ${period.incomeStatement.netProfit?.toLocaleString('sv-SE')} SEK`
        );
        console.log(
          `    Total assets: ${period.assets.totalAssets?.toLocaleString('sv-SE')} SEK`
        );
        console.log(`    Employees: ${period.employees.numEmployees}`);
      }
    });

    // Access audit info
    if (report.audit) {
      console.log(
        `  Auditor: ${report.audit.auditorFirstName} ${report.audit.auditorLastName}`
      );
      console.log(`  Audit firm: ${report.audit.auditFirm}`);
    }
  });
}

/**
 * Example 9: Get XBRL financials in flat format
 */
async function getXBRLFinancialsExample(): Promise<XBRLFinancialsFlat[]> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  const response = await client.getXBRLFinancials('5564461043', {
    years: [2023, 2022, 2021],
    consolidated: false,
  });

  console.log(`Financials for: ${response.name}`);
  console.log(`Available years: ${response.fiscalYears.join(', ')}`);

  response.financials.forEach((fin) => {
    console.log(`\n${fin.fiscalYear} (${fin.periodType}):`);
    console.log(`  Revenue: ${fin.revenue?.toLocaleString('sv-SE')} SEK`);
    console.log(`  Net profit: ${fin.netProfit?.toLocaleString('sv-SE')} SEK`);
    console.log(`  Total assets: ${fin.totalAssets?.toLocaleString('sv-SE')} SEK`);
    console.log(`  Equity: ${fin.equity?.toLocaleString('sv-SE')} SEK`);
    console.log(`  Equity ratio: ${fin.equityRatio}%`);
    console.log(`  Employees: ${fin.numEmployees}`);
  });

  return response.financials;
}

/**
 * Example 10: Get latest XBRL with year-over-year comparison
 */
async function getXBRLLatestExample(): Promise<XBRLLatestResponse> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  const latest = await client.getXBRLLatest('5564461043');

  console.log(`Latest financials for: ${latest.name}`);
  console.log(`Fiscal year: ${latest.fiscalYear}`);

  console.log('\nCurrent year:');
  console.log(`  Revenue: ${latest.current.revenue?.toLocaleString('sv-SE')} SEK`);
  console.log(`  Net profit: ${latest.current.netProfit?.toLocaleString('sv-SE')} SEK`);

  if (latest.previous) {
    console.log('\nPrevious year:');
    console.log(
      `  Revenue: ${latest.previous.revenue?.toLocaleString('sv-SE')} SEK`
    );
    console.log(
      `  Net profit: ${latest.previous.netProfit?.toLocaleString('sv-SE')} SEK`
    );
  }

  console.log('\nYear-over-year changes:');
  if (latest.yoyChanges.revenueChange !== null) {
    const sign = latest.yoyChanges.revenueChange >= 0 ? '+' : '';
    console.log(`  Revenue: ${sign}${latest.yoyChanges.revenueChange.toFixed(1)}%`);
  }
  if (latest.yoyChanges.profitChange !== null) {
    const sign = latest.yoyChanges.profitChange >= 0 ? '+' : '';
    console.log(`  Profit: ${sign}${latest.yoyChanges.profitChange.toFixed(1)}%`);
  }
  if (latest.yoyChanges.employeesChange !== null) {
    const sign = latest.yoyChanges.employeesChange >= 0 ? '+' : '';
    console.log(`  Employees: ${sign}${latest.yoyChanges.employeesChange.toFixed(1)}%`);
  }

  return latest;
}

/**
 * Example 11: Search XBRL data
 */
async function searchXBRLExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  // Find profitable companies with >100M revenue
  const results = await client.searchXBRL({
    minYear: 2022,
    maxYear: 2023,
    minRevenue: 100000000,
    isProfitable: true,
    hasAudit: true,
    page: 1,
    pageSize: 20,
  });

  console.log(`Found ${results.pagination.totalItems} companies`);
  console.log(`Page ${results.pagination.page} of ${results.pagination.totalPages}`);

  results.results.forEach((r) => {
    console.log(`\n${r.orgnr}: ${r.name}`);
    console.log(`  Year: ${r.fiscalYear}`);
    console.log(`  Revenue: ${r.revenue?.toLocaleString('sv-SE')} SEK`);
    console.log(`  Net profit: ${r.netProfit?.toLocaleString('sv-SE')} SEK`);
    console.log(`  Employees: ${r.numEmployees}`);
  });
}

// =============================================================================
// ENRICHMENT EXAMPLES
// =============================================================================

/**
 * Example 12: Enrich a single company
 */
async function enrichCompanyExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  // Enrich with fresh data
  const result = await client.enrichCompany({
    orgnr: '5564461043',
    forceRefresh: true,
  });

  console.log(`Enriched: ${result.name}`);
  console.log(`Success: ${result.success}`);
  console.log('Sources used:', result.sourcesUsed);
}

/**
 * Example 13: Batch enrich multiple companies
 */
async function enrichBatchExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  // Enrich multiple companies at once
  const result = await client.enrichBatch({
    orgnrs: ['5564461043', '5560125790', '5591674995'],
    forceRefresh: false,
  });

  console.log(`Processed: ${result.processed}`);
  console.log(`Successful: ${result.successful}`);
  console.log(`Failed: ${result.failed}`);

  Object.entries(result.results).forEach(([orgnr, status]) => {
    console.log(`  ${orgnr}: ${status.success ? status.name : 'FAILED'}`);
  });
}

// =============================================================================
// ERROR HANDLING EXAMPLES
// =============================================================================

/**
 * Example 14: Comprehensive error handling
 */
async function errorHandlingExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  try {
    await client.getCompany('0000000000'); // Invalid orgnr
  } catch (error) {
    if (error instanceof ApiClientError) {
      console.log('API Error:');
      console.log(`  Status: ${error.statusCode}`);
      console.log(`  Message: ${error.message}`);
      console.log(`  Request ID: ${error.requestId}`);
      console.log(`  Endpoint: ${error.endpoint}`);

      if (error.isNotFound()) {
        console.log('  -> Company not found');
      } else if (error.isRateLimited()) {
        console.log('  -> Rate limited, implement backoff');
      } else if (error.isServerError()) {
        console.log('  -> Server error, will retry automatically');
      }

      // Access validation errors
      if (error.details?.errors) {
        console.log('  Validation errors:');
        error.details.errors.forEach((e) => {
          console.log(`    - ${e.field}: ${e.message}`);
        });
      }
    } else if (error instanceof ValidationError) {
      console.log('Validation Error:');
      console.log(`  Endpoint: ${error.endpoint}`);
      console.log(`  Issues: ${error.zodError.issues.length}`);
      error.zodError.issues.forEach((issue) => {
        console.log(`    - ${issue.path.join('.')}: ${issue.message}`);
      });
    } else {
      throw error;
    }
  }
}

// =============================================================================
// ADVANCED USAGE EXAMPLES
// =============================================================================

/**
 * Example 15: Build financial report
 */
async function buildFinancialReportExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  const orgnr = '5564461043';

  // Fetch all data in parallel
  const [company, xbrlLatest, board] = await Promise.all([
    client.getCompanySummary(orgnr),
    client.getXBRLLatest(orgnr),
    client.getCompanyBoard(orgnr),
  ]);

  // Build report
  const report = {
    company: {
      name: company.name,
      orgnr: company.orgnr,
      status: company.status,
      ceo: company.keyPersons?.ceo,
      chairman: company.keyPersons?.chairman,
      boardSize: company.boardSize,
    },
    financials: {
      fiscalYear: xbrlLatest.fiscalYear,
      revenue: xbrlLatest.current.revenue,
      netProfit: xbrlLatest.current.netProfit,
      totalAssets: xbrlLatest.current.totalAssets,
      equity: xbrlLatest.current.equity,
      equityRatio: xbrlLatest.current.equityRatio,
      employees: xbrlLatest.current.numEmployees,
    },
    yoyChanges: xbrlLatest.yoyChanges,
    board: board.board.map((m) => ({
      name: m.name,
      role: m.roleType,
    })),
    management: board.management.map((m) => ({
      name: m.name,
      role: m.roleType,
    })),
  };

  console.log('Financial Report:');
  console.log(JSON.stringify(report, null, 2));
}

/**
 * Example 16: Compare multiple companies
 */
async function compareCompaniesExample(): Promise<void> {
  const client = createClient({
    apiKey: process.env.LOOP_AUTO_API_KEY,
  });

  const orgnrs = ['5564461043', '5560125790', '5591674995'];

  // Fetch XBRL data for all companies
  const results = await Promise.all(
    orgnrs.map(async (orgnr) => {
      try {
        const latest = await client.getXBRLLatest(orgnr);
        return {
          orgnr,
          name: latest.name,
          revenue: latest.current.revenue,
          profit: latest.current.netProfit,
          assets: latest.current.totalAssets,
          employees: latest.current.numEmployees,
          revenueGrowth: latest.yoyChanges.revenueChange,
        };
      } catch {
        return null;
      }
    })
  );

  // Filter out failures and sort by revenue
  const validResults = results
    .filter((r): r is NonNullable<typeof r> => r !== null)
    .sort((a, b) => (b.revenue ?? 0) - (a.revenue ?? 0));

  console.log('Company Comparison (sorted by revenue):');
  console.log('----------------------------------------');

  validResults.forEach((r, i) => {
    console.log(`\n${i + 1}. ${r.name} (${r.orgnr})`);
    console.log(`   Revenue: ${r.revenue?.toLocaleString('sv-SE')} SEK`);
    console.log(`   Profit: ${r.profit?.toLocaleString('sv-SE')} SEK`);
    console.log(`   Assets: ${r.assets?.toLocaleString('sv-SE')} SEK`);
    console.log(`   Employees: ${r.employees}`);
    if (r.revenueGrowth !== null) {
      const sign = r.revenueGrowth >= 0 ? '+' : '';
      console.log(`   Revenue YoY: ${sign}${r.revenueGrowth.toFixed(1)}%`);
    }
  });
}

// =============================================================================
// RUN EXAMPLES
// =============================================================================

/**
 * Run all examples (for testing).
 */
async function runAllExamples(): Promise<void> {
  console.log('=== Loop-Auto API Client Examples ===\n');

  try {
    console.log('--- Example: Get Company ---');
    await getCompanyExample();

    console.log('\n--- Example: Search Companies ---');
    await searchCompaniesExample();

    console.log('\n--- Example: XBRL Latest ---');
    await getXBRLLatestExample();

    console.log('\n--- Example: Financial Report ---');
    await buildFinancialReportExample();

    console.log('\n--- Example: Compare Companies ---');
    await compareCompaniesExample();

    console.log('\n=== All examples completed ===');
  } catch (error) {
    console.error('Example failed:', error);
  }
}

// Export examples for use in other files
export {
  setupProductionClient,
  setupDevClient,
  setupClientWithInterceptors,
  getCompanyExample,
  getCompanySummaryExample,
  searchCompaniesExample,
  lookupCompanyExample,
  getXBRLReportsExample,
  getXBRLFinancialsExample,
  getXBRLLatestExample,
  searchXBRLExample,
  enrichCompanyExample,
  enrichBatchExample,
  errorHandlingExample,
  buildFinancialReportExample,
  compareCompaniesExample,
  runAllExamples,
};
