/**
 * Loop-Auto API Types - TypeScript
 * =================================
 *
 * Complete TypeScript type definitions for the Swedish Company Data API.
 *
 * @example
 * ```typescript
 * import {
 *   // Client
 *   LoopAutoClient,
 *   createClient,
 *
 *   // Types
 *   XBRLFinancialsFlat,
 *   Company,
 *   AnnualReport,
 *
 *   // Zod Schemas
 *   XBRLFinancialsFlatSchema,
 *   AnnualReportSchema,
 *
 *   // Enums
 *   PeriodType,
 *   DataSource,
 * } from './types';
 * ```
 *
 * @author Claude Code (typescript-pro agent)
 * @date 2024-12-09
 */

// =============================================================================
// XBRL TYPES & SCHEMAS
// =============================================================================

export {
  // Enums
  FieldAvailability,
  PeriodType,
  DataSource,

  // Income Statement
  type IncomeStatement,

  // Balance Sheet
  type BalanceSheetAssets,
  type BalanceSheetEquityLiabilities,

  // Key Ratios & Employees
  type KeyRatios,
  type EmployeeInfo,

  // Financial Period Types
  type XBRLFinancialPeriod,
  type XBRLFinancialsFlat,

  // Audit & Board
  type AuditInfo,
  type BoardInfo,
  type BoardMember,

  // Company & Report
  type XBRLCompanyInfo,
  type AnnualReport,

  // API Response Types
  type ApiError,
  type PaginationMeta,
  type XBRLResponse,
  type XBRLFinancialsResponse,
  type XBRLLatestResponse,
  type XBRLParseResponse,
  type XBRLSearchFilters,
  type XBRLSearchResponse,

  // Zod Schemas
  PeriodTypeSchema,
  DataSourceSchema,
  IncomeStatementSchema,
  BalanceSheetAssetsSchema,
  BalanceSheetEquityLiabilitiesSchema,
  KeyRatiosSchema,
  EmployeeInfoSchema,
  XBRLFinancialPeriodSchema,
  XBRLFinancialsFlatSchema,
  AuditInfoSchema,
  BoardMemberSchema,
  BoardInfoSchema,
  XBRLCompanyInfoSchema,
  AnnualReportMetaSchema,
  AnnualReportSchema,
  ApiErrorSchema,
  PaginationMetaSchema,
  XBRLResponseSchema,
  XBRLFinancialsResponseSchema,
  XBRLLatestResponseSchema,
  XBRLSearchFiltersSchema,
  XBRLSearchResponseSchema,

  // Inferred Types
  type IncomeStatementInferred,
  type BalanceSheetAssetsInferred,
  type XBRLFinancialPeriodInferred,
  type AnnualReportInferred,
} from './xbrl';

// =============================================================================
// API CLIENT
// =============================================================================

export {
  // Client Class
  LoopAutoClient,
  createClient,

  // Configuration
  type ClientConfig,

  // Errors
  ApiClientError,
  ValidationError,

  // Existing API Types
  type CompanySummary,
  type FinancialPeriod,
  type RoleMember,
  type SearchResult,
  type LookupResult,
  type Company,
  type CompanySearchFilters,
  type EnrichRequest,
  type BatchEnrichRequest,
} from './api-client';

// =============================================================================
// NYEMISSIONER CLIENT
// =============================================================================

export {
  // Client Class
  NyemissionerClient,

  // Types
  type Nyemission,
  type NyemissionDetails,
  type Borsnotering,
  type BorsnoteringDetails,
  type Owner,
  type SearchFilters as NyemissionerSearchFilters,
  type ListResponse as NyemissionerListResponse,
  type ClientConfig as NyemissionerClientConfig,
} from './nyemissioner-client';

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export { default } from './api-client';
