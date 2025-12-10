/**
 * Loop-Auto API Client - TypeScript
 * ==================================
 *
 * Type-safe API client for the Swedish Company Data API with XBRL support.
 *
 * Features:
 * - Full TypeScript type safety
 * - Zod runtime validation
 * - Automatic error handling
 * - Retry logic with exponential backoff
 * - Request/response interceptors
 *
 * @example
 * ```typescript
 * const client = new LoopAutoClient({
 *   baseUrl: 'https://loop-auto-api.onrender.com',
 *   apiKey: 'your-api-key'
 * });
 *
 * // Get company with XBRL data
 * const company = await client.getCompany('5566778899');
 *
 * // Get XBRL financials
 * const xbrl = await client.getXBRLFinancials('5566778899');
 *
 * // Search companies
 * const results = await client.searchCompanies({ q: 'Oatly' });
 * ```
 *
 * @author Claude Code (typescript-pro agent)
 * @date 2024-12-09
 */

import { z } from 'zod';
import type {
  XBRLResponse,
  XBRLFinancialsResponse,
  XBRLLatestResponse,
  XBRLSearchFilters,
  XBRLSearchResponse,
  XBRLParseResponse,
  ApiError,
  AnnualReport,
  XBRLFinancialsFlat,
} from './xbrl';
import {
  XBRLResponseSchema,
  XBRLFinancialsResponseSchema,
  XBRLLatestResponseSchema,
  XBRLSearchResponseSchema,
  ApiErrorSchema,
  AnnualReportSchema,
} from './xbrl';

// =============================================================================
// CLIENT CONFIGURATION
// =============================================================================

/**
 * Configuration options for the API client.
 */
export interface ClientConfig {
  /** Base URL of the API (e.g., 'https://loop-auto-api.onrender.com') */
  baseUrl: string;
  /** API key for authentication (X-API-Key header) */
  apiKey?: string;
  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;
  /** Number of retry attempts for failed requests (default: 3) */
  retries?: number;
  /** Whether to validate responses with Zod (default: true) */
  validateResponses?: boolean;
  /** Custom headers to include in all requests */
  headers?: Record<string, string>;
  /** Request interceptor */
  onRequest?: (config: RequestInit) => RequestInit;
  /** Response interceptor */
  onResponse?: <T>(response: T) => T;
  /** Error handler */
  onError?: (error: ApiClientError) => void;
}

/**
 * Default client configuration.
 */
const DEFAULT_CONFIG: Required<Omit<ClientConfig, 'baseUrl' | 'apiKey' | 'onRequest' | 'onResponse' | 'onError'>> = {
  timeout: 30000,
  retries: 3,
  validateResponses: true,
  headers: {},
};

// =============================================================================
// ERROR HANDLING
// =============================================================================

/**
 * API client error with detailed information.
 */
export class ApiClientError extends Error {
  readonly statusCode: number;
  readonly requestId: string | null;
  readonly endpoint: string;
  readonly details: ApiError['details'];

  constructor(
    message: string,
    statusCode: number,
    endpoint: string,
    requestId: string | null = null,
    details?: ApiError['details']
  ) {
    super(message);
    this.name = 'ApiClientError';
    this.statusCode = statusCode;
    this.requestId = requestId;
    this.endpoint = endpoint;
    this.details = details;
  }

  /**
   * Check if error is a not found (404) error.
   */
  isNotFound(): boolean {
    return this.statusCode === 404;
  }

  /**
   * Check if error is a rate limit (429) error.
   */
  isRateLimited(): boolean {
    return this.statusCode === 429;
  }

  /**
   * Check if error is a server error (5xx).
   */
  isServerError(): boolean {
    return this.statusCode >= 500;
  }

  /**
   * Check if error is retryable.
   */
  isRetryable(): boolean {
    return this.isRateLimited() || this.isServerError();
  }
}

/**
 * Validation error when Zod parsing fails.
 */
export class ValidationError extends Error {
  readonly zodError: z.ZodError;
  readonly endpoint: string;

  constructor(zodError: z.ZodError, endpoint: string) {
    super(`Response validation failed for ${endpoint}: ${zodError.message}`);
    this.name = 'ValidationError';
    this.zodError = zodError;
    this.endpoint = endpoint;
  }
}

// =============================================================================
// EXISTING API TYPES (from api.py)
// =============================================================================

/**
 * Company summary from GET /api/v1/companies/{orgnr}/summary
 */
export interface CompanySummary {
  orgnr: string;
  name: string;
  companyType: string | null;
  status: string | null;
  founded: number | null;
  municipality: string | null;
  keyPersons: {
    ceo: string | null;
    chairman: string | null;
  } | null;
  keyFigures: {
    revenue: number | null;
    employees: number | null;
    equityRatio: number | null;
  } | null;
  boardSize: number;
}

/**
 * Financial period from existing API.
 */
export interface FinancialPeriod {
  periodYear: number;
  isConsolidated: boolean;
  revenue: number | null;
  netProfit: number | null;
  totalAssets: number | null;
  equity: number | null;
  equityRatio: number | null;
  returnOnEquity: number | null;
  numEmployees: number | null;
}

/**
 * Board/role member.
 */
export interface RoleMember {
  name: string;
  birthYear: number | null;
  roleType: string;
  roleCategory: string | null;
}

/**
 * Search result.
 */
export interface SearchResult {
  orgnr: string;
  name: string;
  companyType: string | null;
  status: string | null;
  postalCity: string | null;
  revenue: number | null;
  numEmployees: number | null;
}

/**
 * Lookup result.
 */
export interface LookupResult {
  orgnr: string;
  name: string;
  orgForm: string | null;
  registrationDate: string | null;
  postalAddress: string | null;
}

/**
 * Complete company data.
 */
export interface Company {
  orgnr: string;
  name: string;
  companyType: string | null;
  status: string | null;
  founded: number | null;
  registeredAddress: string | null;
  postalCity: string | null;
  postalCode: string | null;
  municipality: string | null;

  // Key figures
  revenue: number | null;
  numEmployees: number | null;
  equityRatio: number | null;

  // Group info
  isGroup: boolean;
  companiesInGroup: number | null;
  parentOrgnr: string | null;
  parentName: string | null;

  // Related data
  roles: RoleMember[];
  financials: FinancialPeriod[];
  industries: Array<{
    sniCode: string;
    description: string;
    isPrimary: boolean;
  }>;
  trademarks: Array<{
    name: string;
    registrationNumber: string | null;
    status: string | null;
  }>;
  relatedCompanies: Array<{
    orgnr: string;
    name: string;
    relation: string;
  }>;
  announcements: Array<{
    type: string;
    date: string;
    description: string;
  }>;

  // Metadata
  _meta?: {
    sources: Record<string, boolean>;
    lastRefresh: string;
  };
}

/**
 * Search filters for companies.
 */
export interface CompanySearchFilters {
  q?: string;
  municipality?: string;
  minRevenue?: number;
  maxRevenue?: number;
  minEmployees?: number;
  status?: string;
  limit?: number;
}

/**
 * Enrich request.
 */
export interface EnrichRequest {
  orgnr: string;
  forceRefresh?: boolean;
}

/**
 * Batch enrich request.
 */
export interface BatchEnrichRequest {
  orgnrs: string[];
  forceRefresh?: boolean;
}

// =============================================================================
// EQUITY OFFERINGS TYPES
// =============================================================================

/**
 * Type of equity offering.
 */
export type EquityOfferingType =
  | 'nyemission'
  | 'foretradesemission'
  | 'riktad_emission'
  | 'ipo'
  | 'listbyte'
  | 'spridningsemission';

/**
 * Status of an equity offering.
 */
export type EquityOfferingStatus = 'upcoming' | 'active' | 'completed' | 'cancelled';

/**
 * Equity offering (nyemission/börsnotering).
 */
export interface EquityOffering {
  id: string;
  companyName: string;
  companyOrgnr: string | null;
  slug: string;
  sourceUrl: string;
  offeringType: EquityOfferingType;
  exchange: string | null;
  listingStatus: string | null;
  subscriptionStart: string | null;
  subscriptionEnd: string | null;
  recordDate: string | null;
  listingDate: string | null;
  amountSek: number | null;
  subscriptionPriceSek: number | null;
  preMoneyValuation: number | null;
  postMoneyValuation: number | null;
  sharesBefore: number | null;
  sharesOffered: number | null;
  sharesAfter: number | null;
  quotaValue: number | null;
  prospectusUrl: string | null;
  memorandumUrl: string | null;
  companyWebsite: string | null;
  description: string | null;
  terms: string | null;
  status: EquityOfferingStatus;
  source: string;
  scrapedAt: string;
  lastUpdated: string | null;
}

/**
 * Filters for equity offerings search.
 */
export interface EquityOfferingFilters {
  type?: EquityOfferingType | 'all';
  status?: EquityOfferingStatus | 'all';
  exchange?: string;
  companyOrgnr?: string;
  limit?: number;
}

// =============================================================================
// ZOD SCHEMAS FOR EXISTING TYPES
// =============================================================================

const CompanySummarySchema = z.object({
  orgnr: z.string(),
  name: z.string(),
  company_type: z.string().nullable(),
  status: z.string().nullable(),
  founded: z.number().nullable(),
  municipality: z.string().nullable(),
  key_persons: z
    .object({
      ceo: z.string().nullable(),
      chairman: z.string().nullable(),
    })
    .nullable(),
  key_figures: z
    .object({
      revenue: z.number().nullable(),
      employees: z.number().nullable(),
      equity_ratio: z.number().nullable(),
    })
    .nullable(),
  board_size: z.number(),
});

const SearchResultSchema = z.object({
  orgnr: z.string(),
  name: z.string(),
  company_type: z.string().nullable().optional(),
  status: z.string().nullable().optional(),
  postal_city: z.string().nullable().optional(),
  revenue: z.number().nullable().optional(),
  num_employees: z.number().nullable().optional(),
});

const LookupResultSchema = z.object({
  orgnr: z.string(),
  name: z.string(),
  org_form: z.string().nullable().optional(),
  registration_date: z.string().nullable().optional(),
  postal_address: z.string().nullable().optional(),
});

// =============================================================================
// API CLIENT
// =============================================================================

/**
 * Type-safe API client for Loop-Auto Swedish Company Data API.
 */
export class LoopAutoClient {
  private readonly config: Required<
    Omit<ClientConfig, 'apiKey' | 'onRequest' | 'onResponse' | 'onError'>
  > & {
    apiKey?: string;
    onRequest?: ClientConfig['onRequest'];
    onResponse?: ClientConfig['onResponse'];
    onError?: ClientConfig['onError'];
  };

  constructor(config: ClientConfig) {
    this.config = {
      ...DEFAULT_CONFIG,
      ...config,
    };

    // Ensure baseUrl doesn't end with /
    this.config.baseUrl = this.config.baseUrl.replace(/\/$/, '');
  }

  // ===========================================================================
  // PRIVATE METHODS
  // ===========================================================================

  /**
   * Build full URL with query parameters.
   */
  private buildUrl(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined>
  ): string {
    const url = new URL(`${this.config.baseUrl}${endpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.set(key, String(value));
        }
      });
    }

    return url.toString();
  }

  /**
   * Build request headers.
   */
  private buildHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...this.config.headers,
    };

    if (this.config.apiKey) {
      headers['X-API-Key'] = this.config.apiKey;
    }

    return headers;
  }

  /**
   * Sleep for specified milliseconds.
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Execute request with retry logic.
   */
  private async executeWithRetry<T>(
    endpoint: string,
    init: RequestInit,
    schema?: z.ZodType<T>
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.retries; attempt++) {
      try {
        // Apply request interceptor
        let requestInit = { ...init };
        if (this.config.onRequest) {
          requestInit = this.config.onRequest(requestInit);
        }

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(
          () => controller.abort(),
          this.config.timeout
        );

        try {
          const response = await fetch(
            this.buildUrl(endpoint),
            {
              ...requestInit,
              signal: controller.signal,
            }
          );

          clearTimeout(timeoutId);

          // Handle error responses
          if (!response.ok) {
            const errorBody = await response.json().catch(() => ({}));
            const requestId = response.headers.get('X-Request-ID');

            const error = new ApiClientError(
              errorBody.message || `HTTP ${response.status}`,
              response.status,
              endpoint,
              requestId,
              errorBody.details
            );

            // Retry only if retryable and we have attempts left
            if (error.isRetryable() && attempt < this.config.retries) {
              const backoffMs = Math.min(1000 * Math.pow(2, attempt), 30000);
              await this.sleep(backoffMs);
              lastError = error;
              continue;
            }

            if (this.config.onError) {
              this.config.onError(error);
            }
            throw error;
          }

          // Parse response
          let data = await response.json();

          // Validate with Zod if schema provided and validation enabled
          if (schema && this.config.validateResponses) {
            const result = schema.safeParse(data);
            if (!result.success) {
              throw new ValidationError(result.error, endpoint);
            }
            data = result.data;
          }

          // Apply response interceptor
          if (this.config.onResponse) {
            data = this.config.onResponse(data);
          }

          return data;
        } catch (error) {
          clearTimeout(timeoutId);

          // Handle abort (timeout)
          if (error instanceof Error && error.name === 'AbortError') {
            throw new ApiClientError(
              'Request timeout',
              408,
              endpoint,
              null
            );
          }

          throw error;
        }
      } catch (error) {
        lastError = error as Error;

        // Don't retry non-retryable errors
        if (
          error instanceof ApiClientError &&
          !error.isRetryable()
        ) {
          throw error;
        }

        if (error instanceof ValidationError) {
          throw error;
        }

        // Retry network errors
        if (attempt < this.config.retries) {
          const backoffMs = Math.min(1000 * Math.pow(2, attempt), 30000);
          await this.sleep(backoffMs);
          continue;
        }
      }
    }

    throw lastError || new Error('Unknown error');
  }

  /**
   * Execute GET request.
   */
  private async get<T>(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined>,
    schema?: z.ZodType<T>
  ): Promise<T> {
    const url = this.buildUrl(endpoint, params);

    return this.executeWithRetry<T>(
      url.replace(this.config.baseUrl, ''),
      {
        method: 'GET',
        headers: this.buildHeaders(),
      },
      schema
    );
  }

  /**
   * Execute POST request.
   */
  private async post<T>(
    endpoint: string,
    body: unknown,
    schema?: z.ZodType<T>
  ): Promise<T> {
    return this.executeWithRetry<T>(
      endpoint,
      {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify(body),
      },
      schema
    );
  }

  // ===========================================================================
  // PUBLIC API - INFO
  // ===========================================================================

  /**
   * Get API info.
   */
  async getInfo(): Promise<{
    name: string;
    version: string;
    sources: string[];
    docs: string;
  }> {
    return this.get('/');
  }

  /**
   * Get health status.
   */
  async getHealth(): Promise<{
    status: 'healthy' | 'degraded';
    timestamp: string;
    database: {
      type: string;
      companiesCached: number;
      status: string;
    };
    sources: Record<
      string,
      {
        state: string;
        requests: number;
        successRate: string;
      }
    >;
  }> {
    return this.get('/health');
  }

  /**
   * Get performance metrics.
   */
  async getMetrics(): Promise<{
    summary: {
      avgFetchTimeMs: number;
      totalRequests: number;
    };
    circuitBreakers: Record<string, unknown>;
  }> {
    return this.get('/api/v1/metrics');
  }

  /**
   * Get database statistics.
   */
  async getStats(): Promise<{
    database: {
      companies: number;
      databaseType: string;
    };
    sources: Record<string, string>;
  }> {
    return this.get('/api/v1/stats');
  }

  // ===========================================================================
  // PUBLIC API - COMPANIES
  // ===========================================================================

  /**
   * Get complete company data.
   *
   * @param orgnr - Organization number (10 digits)
   * @param refresh - Force refresh from sources
   */
  async getCompany(orgnr: string, refresh = false): Promise<Company> {
    const data = await this.get<Record<string, unknown>>(
      `/api/v1/companies/${orgnr}`,
      { refresh }
    );

    // Transform snake_case to camelCase
    return this.transformCompany(data);
  }

  /**
   * Get company summary.
   */
  async getCompanySummary(orgnr: string): Promise<CompanySummary> {
    const data = await this.get(
      `/api/v1/companies/${orgnr}/summary`,
      undefined,
      CompanySummarySchema
    );

    return {
      orgnr: data.orgnr,
      name: data.name,
      companyType: data.company_type,
      status: data.status,
      founded: data.founded,
      municipality: data.municipality,
      keyPersons: data.key_persons
        ? {
            ceo: data.key_persons.ceo,
            chairman: data.key_persons.chairman,
          }
        : null,
      keyFigures: data.key_figures
        ? {
            revenue: data.key_figures.revenue,
            employees: data.key_figures.employees,
            equityRatio: data.key_figures.equity_ratio,
          }
        : null,
      boardSize: data.board_size,
    };
  }

  /**
   * Get company board members and management.
   */
  async getCompanyBoard(orgnr: string): Promise<{
    orgnr: string;
    name: string;
    board: RoleMember[];
    management: RoleMember[];
    auditors: RoleMember[];
    other: RoleMember[];
    totalCount: number;
  }> {
    const data = await this.get<Record<string, unknown>>(
      `/api/v1/companies/${orgnr}/board`
    );

    return {
      orgnr: data.orgnr as string,
      name: data.name as string,
      board: this.transformRoles(data.board as Record<string, unknown>[]),
      management: this.transformRoles(data.management as Record<string, unknown>[]),
      auditors: this.transformRoles(data.auditors as Record<string, unknown>[]),
      other: this.transformRoles(data.other as Record<string, unknown>[]),
      totalCount: data.total_count as number,
    };
  }

  /**
   * Get company financial history.
   */
  async getCompanyFinancials(
    orgnr: string,
    options?: { consolidated?: boolean; years?: number }
  ): Promise<{
    orgnr: string;
    name: string;
    isConsolidated: boolean;
    periods: FinancialPeriod[];
  }> {
    const data = await this.get<Record<string, unknown>>(
      `/api/v1/companies/${orgnr}/financials`,
      {
        consolidated: options?.consolidated,
        years: options?.years,
      }
    );

    return {
      orgnr: data.orgnr as string,
      name: data.name as string,
      isConsolidated: data.is_consolidated as boolean,
      periods: this.transformFinancials(data.periods as Record<string, unknown>[]),
    };
  }

  /**
   * Get company corporate structure.
   */
  async getCompanyStructure(orgnr: string): Promise<{
    orgnr: string;
    name: string;
    isGroup: boolean;
    companiesInGroup: number | null;
    parent: { orgnr: string; name: string } | null;
    relatedCompanies: Array<{
      orgnr: string;
      name: string;
      relation: string;
    }>;
    industries: Array<{
      sniCode: string;
      description: string;
    }>;
  }> {
    const data = await this.get<Record<string, unknown>>(
      `/api/v1/companies/${orgnr}/structure`
    );

    return {
      orgnr: data.orgnr as string,
      name: data.name as string,
      isGroup: data.is_group as boolean,
      companiesInGroup: data.companies_in_group as number | null,
      parent: data.parent as { orgnr: string; name: string } | null,
      relatedCompanies: (data.related_companies as Record<string, unknown>[])?.map(
        (r) => ({
          orgnr: r.orgnr as string,
          name: r.name as string,
          relation: r.relation as string,
        })
      ) || [],
      industries: (data.industries as Record<string, unknown>[])?.map((i) => ({
        sniCode: (i.sni_code || i.code) as string,
        description: i.description as string,
      })) || [],
    };
  }

  /**
   * Get company announcements (kungörelser).
   */
  async getCompanyAnnouncements(
    orgnr: string,
    limit = 10
  ): Promise<{
    orgnr: string;
    name: string;
    announcements: Array<{
      type: string;
      date: string;
      description: string;
    }>;
    totalCount: number;
  }> {
    const data = await this.get<Record<string, unknown>>(
      `/api/v1/companies/${orgnr}/announcements`,
      { limit }
    );

    return {
      orgnr: data.orgnr as string,
      name: data.name as string,
      announcements: (data.announcements as Record<string, unknown>[])?.map(
        (a) => ({
          type: a.type as string,
          date: a.date as string,
          description: a.description as string,
        })
      ) || [],
      totalCount: data.total_count as number,
    };
  }

  // ===========================================================================
  // PUBLIC API - HISTORY
  // ===========================================================================

  /**
   * Get complete company history.
   */
  async getCompanyHistory(orgnr: string): Promise<{
    companyHistory: Array<Record<string, unknown>>;
    rolesHistory: Array<Record<string, unknown>>;
    metadata: {
      orgnr: string;
      companySnapshots: number;
      rolesSnapshots: number;
    };
  }> {
    const data = await this.get<Record<string, unknown>>(
      `/api/v1/companies/${orgnr}/history`
    );

    return {
      companyHistory: data.company_history as Array<Record<string, unknown>>,
      rolesHistory: data.roles_history as Array<Record<string, unknown>>,
      metadata: {
        orgnr: (data.metadata as Record<string, unknown>)?.orgnr as string,
        companySnapshots: (data.metadata as Record<string, unknown>)
          ?.company_snapshots as number,
        rolesSnapshots: (data.metadata as Record<string, unknown>)
          ?.roles_snapshots as number,
      },
    };
  }

  /**
   * Get board/roles history.
   */
  async getBoardHistory(
    orgnr: string,
    limit = 50
  ): Promise<{
    orgnr: string;
    snapshots: Array<Record<string, unknown>>;
    totalSnapshots: number;
  }> {
    const data = await this.get<Record<string, unknown>>(
      `/api/v1/companies/${orgnr}/history/board`,
      { limit }
    );

    return {
      orgnr: data.orgnr as string,
      snapshots: data.snapshots as Array<Record<string, unknown>>,
      totalSnapshots: data.total_snapshots as number,
    };
  }

  // ===========================================================================
  // PUBLIC API - SEARCH
  // ===========================================================================

  /**
   * Search companies with filters.
   */
  async searchCompanies(filters: CompanySearchFilters): Promise<SearchResult[]> {
    const params: Record<string, string | number | undefined> = {
      q: filters.q,
      municipality: filters.municipality,
      min_revenue: filters.minRevenue,
      max_revenue: filters.maxRevenue,
      min_employees: filters.minEmployees,
      status: filters.status,
      limit: filters.limit,
    };

    const data = await this.get<Array<Record<string, unknown>>>(
      '/api/v1/search/companies',
      params
    );

    return data.map((r) => ({
      orgnr: r.orgnr as string,
      name: r.name as string,
      companyType: r.company_type as string | null,
      status: r.status as string | null,
      postalCity: r.postal_city as string | null,
      revenue: r.revenue as number | null,
      numEmployees: r.num_employees as number | null,
    }));
  }

  /**
   * Look up company by name.
   */
  async lookupCompany(
    name: string,
    limit = 20
  ): Promise<{
    query: string;
    results: LookupResult[];
    count: number;
    searchType: string;
    registrySource: string;
  }> {
    const data = await this.get<Record<string, unknown>>('/api/v1/lookup', {
      name,
      limit,
    });

    return {
      query: data.query as string,
      results: (data.results as Array<Record<string, unknown>>).map((r) => ({
        orgnr: r.orgnr as string,
        name: r.name as string,
        orgForm: r.org_form as string | null,
        registrationDate: r.registration_date as string | null,
        postalAddress: r.postal_address as string | null,
      })),
      count: data.count as number,
      searchType: data.search_type as string,
      registrySource: data.registry_source as string,
    };
  }

  /**
   * Get company registry statistics.
   */
  async getLookupStats(): Promise<{
    status: string;
    totalCompanies: number;
    source: string;
    databaseType: string;
  }> {
    const data = await this.get<Record<string, unknown>>('/api/v1/lookup/stats');

    return {
      status: data.status as string,
      totalCompanies: data.total_companies as number,
      source: data.source as string,
      databaseType: data.database_type as string,
    };
  }

  // ===========================================================================
  // PUBLIC API - ENRICHMENT
  // ===========================================================================

  /**
   * Enrich a single company.
   */
  async enrichCompany(request: EnrichRequest): Promise<{
    success: boolean;
    orgnr: string;
    name: string;
    sourcesUsed: Record<string, boolean>;
    data: Company;
  }> {
    const data = await this.post<Record<string, unknown>>('/api/v1/enrich', {
      orgnr: request.orgnr,
      force_refresh: request.forceRefresh ?? false,
    });

    return {
      success: data.success as boolean,
      orgnr: data.orgnr as string,
      name: data.name as string,
      sourcesUsed: data.sources_used as Record<string, boolean>,
      data: this.transformCompany(data.data as Record<string, unknown>),
    };
  }

  /**
   * Enrich multiple companies (max 10).
   */
  async enrichBatch(request: BatchEnrichRequest): Promise<{
    processed: number;
    successful: number;
    failed: number;
    results: Record<
      string,
      {
        success: boolean;
        name: string | null;
      }
    >;
  }> {
    const data = await this.post<Record<string, unknown>>('/api/v1/enrich/batch', {
      orgnrs: request.orgnrs,
      force_refresh: request.forceRefresh ?? false,
    });

    return {
      processed: data.processed as number,
      successful: data.successful as number,
      failed: data.failed as number,
      results: data.results as Record<
        string,
        { success: boolean; name: string | null }
      >,
    };
  }

  // ===========================================================================
  // PUBLIC API - XBRL (NEW)
  // ===========================================================================

  /**
   * Get XBRL annual reports for a company.
   *
   * @param orgnr - Organization number
   * @returns XBRL response with all annual reports
   */
  async getXBRLReports(orgnr: string): Promise<XBRLResponse> {
    return this.get(
      `/api/v1/companies/${orgnr}/xbrl`,
      undefined,
      XBRLResponseSchema
    );
  }

  /**
   * Get XBRL financials in flat format for easy consumption.
   *
   * @param orgnr - Organization number
   * @param options - Filter options
   */
  async getXBRLFinancials(
    orgnr: string,
    options?: {
      years?: number[];
      consolidated?: boolean;
    }
  ): Promise<XBRLFinancialsResponse> {
    const params: Record<string, string | number | boolean | undefined> = {};

    if (options?.years) {
      params.years = options.years.join(',');
    }
    if (options?.consolidated !== undefined) {
      params.consolidated = options.consolidated;
    }

    return this.get(
      `/api/v1/companies/${orgnr}/xbrl/financials`,
      params,
      XBRLFinancialsResponseSchema
    );
  }

  /**
   * Get latest XBRL financials with year-over-year comparison.
   *
   * @param orgnr - Organization number
   */
  async getXBRLLatest(orgnr: string): Promise<XBRLLatestResponse> {
    return this.get(
      `/api/v1/companies/${orgnr}/xbrl/latest`,
      undefined,
      XBRLLatestResponseSchema
    );
  }

  /**
   * Search companies by XBRL financial data.
   *
   * @param filters - Search filters
   */
  async searchXBRL(filters: XBRLSearchFilters): Promise<XBRLSearchResponse> {
    const params: Record<string, string | number | boolean | undefined> = {
      min_year: filters.minYear,
      max_year: filters.maxYear,
      min_revenue: filters.minRevenue,
      max_revenue: filters.maxRevenue,
      min_employees: filters.minEmployees,
      has_audit: filters.hasAudit,
      is_profitable: filters.isProfitable,
      page: filters.page,
      page_size: filters.pageSize,
    };

    return this.get('/api/v1/xbrl/search', params, XBRLSearchResponseSchema);
  }

  /**
   * Parse XBRL from uploaded file.
   * Note: This endpoint accepts multipart/form-data.
   *
   * @param file - ZIP file containing XBRL annual report
   */
  async parseXBRL(file: File | Blob): Promise<XBRLParseResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      this.buildUrl('/api/v1/xbrl/parse'),
      {
        method: 'POST',
        headers: {
          ...(this.config.apiKey && { 'X-API-Key': this.config.apiKey }),
          ...this.config.headers,
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new ApiClientError(
        errorBody.message || `HTTP ${response.status}`,
        response.status,
        '/api/v1/xbrl/parse',
        response.headers.get('X-Request-ID'),
        errorBody.details
      );
    }

    return response.json();
  }

  // ===========================================================================
  // PRIVATE TRANSFORM METHODS
  // ===========================================================================

  /**
   * Transform snake_case company data to camelCase.
   */
  private transformCompany(data: Record<string, unknown>): Company {
    return {
      orgnr: data.orgnr as string,
      name: data.name as string,
      companyType: data.company_type as string | null,
      status: data.status as string | null,
      founded: data.founded as number | null,
      registeredAddress: data.registered_address as string | null,
      postalCity: data.postal_city as string | null,
      postalCode: data.postal_code as string | null,
      municipality: data.municipality as string | null,
      revenue: data.revenue as number | null,
      numEmployees: data.num_employees as number | null,
      equityRatio: data.equity_ratio as number | null,
      isGroup: (data.is_group as boolean) || false,
      companiesInGroup: data.companies_in_group as number | null,
      parentOrgnr: data.parent_orgnr as string | null,
      parentName: data.parent_name as string | null,
      roles: this.transformRoles(
        (data.roles as Record<string, unknown>[]) || []
      ),
      financials: this.transformFinancials(
        (data.financials as Record<string, unknown>[]) || []
      ),
      industries: ((data.industries as Record<string, unknown>[]) || []).map(
        (i) => ({
          sniCode: (i.sni_code || i.code) as string,
          description: i.description as string,
          isPrimary: (i.is_primary as boolean) || false,
        })
      ),
      trademarks: ((data.trademarks as Record<string, unknown>[]) || []).map(
        (t) => ({
          name: (t.name || t.trademark_name) as string,
          registrationNumber: t.registration_number as string | null,
          status: t.status as string | null,
        })
      ),
      relatedCompanies: (
        (data.related_companies as Record<string, unknown>[]) || []
      ).map((r) => ({
        orgnr: r.orgnr as string,
        name: r.name as string,
        relation: r.relation as string,
      })),
      announcements: ((data.announcements as Record<string, unknown>[]) || []).map(
        (a) => ({
          type: a.type as string,
          date: a.date as string,
          description: a.description as string,
        })
      ),
      _meta: data._meta as Company['_meta'],
    };
  }

  /**
   * Transform roles array.
   */
  private transformRoles(roles: Record<string, unknown>[]): RoleMember[] {
    return roles.map((r) => ({
      name: r.name as string,
      birthYear: r.birth_year as number | null,
      roleType: r.role_type as string,
      roleCategory: r.role_category as string | null,
    }));
  }

  /**
   * Transform financials array.
   */
  private transformFinancials(
    financials: Record<string, unknown>[]
  ): FinancialPeriod[] {
    return financials.map((f) => ({
      periodYear: f.period_year as number,
      isConsolidated: (f.is_consolidated as boolean) || false,
      revenue: f.revenue as number | null,
      netProfit: f.net_profit as number | null,
      totalAssets: f.total_assets as number | null,
      equity: f.equity as number | null,
      equityRatio: f.equity_ratio as number | null,
      returnOnEquity: f.return_on_equity as number | null,
      numEmployees: f.num_employees as number | null,
    }));
  }

  // ===========================================================================
  // EQUITY OFFERINGS METHODS
  // ===========================================================================

  /**
   * List equity offerings (nyemissioner and börsnoteringar).
   *
   * @param filters - Optional filters
   * @returns Array of equity offerings
   *
   * @example
   * ```typescript
   * // Get all active offerings
   * const offerings = await client.listEquityOfferings({ status: 'active' });
   *
   * // Get only IPOs
   * const ipos = await client.listEquityOfferings({ type: 'ipo' });
   *
   * // Get offerings on Spotlight
   * const spotlight = await client.listEquityOfferings({ exchange: 'Spotlight' });
   * ```
   */
  async listEquityOfferings(
    filters?: EquityOfferingFilters
  ): Promise<EquityOffering[]> {
    const params = new URLSearchParams();

    if (filters?.type && filters.type !== 'all') {
      params.set('offering_type', `eq.${filters.type}`);
    }
    if (filters?.status && filters.status !== 'all') {
      params.set('status', `eq.${filters.status}`);
    }
    if (filters?.exchange) {
      params.set('exchange', `eq.${filters.exchange}`);
    }
    if (filters?.companyOrgnr) {
      params.set('company_orgnr', `eq.${filters.companyOrgnr}`);
    }
    if (filters?.limit) {
      params.set('limit', filters.limit.toString());
    }

    params.set('order', 'created_at.desc');

    const queryString = params.toString();
    const data = await this.get<Record<string, unknown>[]>(
      `/api/v1/offerings${queryString ? `?${queryString}` : ''}`
    );

    return data.map((item: Record<string, unknown>) => this.transformEquityOffering(item));
  }

  /**
   * Get a specific equity offering by slug.
   *
   * @param slug - The offering slug (e.g., "3-prospect-invest-ab-2")
   * @returns Equity offering details
   *
   * @example
   * ```typescript
   * const offering = await client.getEquityOffering('tessin-nordic-holding-ab');
   * console.log(offering.exchange, offering.status);
   * ```
   */
  async getEquityOffering(slug: string): Promise<EquityOffering | null> {
    const data = await this.get<Record<string, unknown> | null>(
      `/api/v1/offerings/${encodeURIComponent(slug)}`
    );

    if (!data) return null;
    return this.transformEquityOffering(data);
  }

  /**
   * Get all equity offerings for a specific company.
   *
   * @param orgnr - Company organization number
   * @returns Array of equity offerings for the company
   *
   * @example
   * ```typescript
   * const offerings = await client.getCompanyOfferings('5590855721');
   * console.log(`Found ${offerings.length} offerings for company`);
   * ```
   */
  async getCompanyOfferings(orgnr: string): Promise<EquityOffering[]> {
    const data = await this.get<Record<string, unknown>[]>(
      `/api/v1/companies/${orgnr}/offerings`
    );

    return data.map((item: Record<string, unknown>) => this.transformEquityOffering(item));
  }

  /**
   * Transform raw equity offering data to typed object.
   */
  private transformEquityOffering(
    data: Record<string, unknown>
  ): EquityOffering {
    return {
      id: data.id as string,
      companyName: data.company_name as string,
      companyOrgnr: data.company_orgnr as string | null,
      slug: data.slug as string,
      sourceUrl: data.source_url as string,
      offeringType: data.offering_type as EquityOfferingType,
      exchange: data.exchange as string | null,
      listingStatus: data.listing_status as string | null,
      subscriptionStart: data.subscription_start as string | null,
      subscriptionEnd: data.subscription_end as string | null,
      recordDate: data.record_date as string | null,
      listingDate: data.listing_date as string | null,
      amountSek: data.amount_sek as number | null,
      subscriptionPriceSek: data.subscription_price_sek as number | null,
      preMoneyValuation: data.pre_money_valuation as number | null,
      postMoneyValuation: data.post_money_valuation as number | null,
      sharesBefore: data.shares_before as number | null,
      sharesOffered: data.shares_offered as number | null,
      sharesAfter: data.shares_after as number | null,
      quotaValue: data.quota_value as number | null,
      prospectusUrl: data.prospectus_url as string | null,
      memorandumUrl: data.memorandum_url as string | null,
      companyWebsite: data.company_website as string | null,
      description: data.description as string | null,
      terms: data.terms as string | null,
      status: data.status as EquityOfferingStatus,
      source: data.source as string,
      scrapedAt: data.scraped_at as string,
      lastUpdated: data.last_updated as string | null,
    };
  }
}

// =============================================================================
// FACTORY FUNCTION
// =============================================================================

/**
 * Create a pre-configured API client.
 *
 * @example
 * ```typescript
 * // Production
 * const client = createClient({
 *   apiKey: process.env.LOOP_AUTO_API_KEY
 * });
 *
 * // Development
 * const devClient = createClient({
 *   baseUrl: 'http://localhost:8000'
 * });
 * ```
 */
export function createClient(
  config?: Partial<ClientConfig>
): LoopAutoClient {
  return new LoopAutoClient({
    baseUrl: config?.baseUrl ?? 'https://loop-auto-api.onrender.com',
    ...config,
  });
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default LoopAutoClient;
