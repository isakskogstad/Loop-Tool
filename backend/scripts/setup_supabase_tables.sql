-- Loop-Auto: Supabase Tables Setup
-- Migrated from SQLite to PostgreSQL

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =====================================================
-- MAIN TABLES
-- =====================================================

-- Companies (main table with ~45 columns)
CREATE TABLE IF NOT EXISTS companies (
    orgnr TEXT PRIMARY KEY,
    name TEXT,
    status TEXT,
    status_date TEXT,
    org_form TEXT,
    org_form_code TEXT,
    registration_date TEXT,

    -- Address
    address TEXT,
    postal_code TEXT,
    city TEXT,
    municipality TEXT,
    municipality_code TEXT,
    county TEXT,
    county_code TEXT,

    -- Contact
    phone TEXT,
    email TEXT,
    website TEXT,

    -- Registrations (Priority 1)
    f_skatt BOOLEAN,
    moms_registered BOOLEAN,
    employer_registered BOOLEAN,

    -- Economic summary (latest)
    revenue BIGINT,
    net_profit BIGINT,
    num_employees INTEGER,
    share_capital BIGINT,

    -- Key ratios (Priority 2)
    solidity NUMERIC,
    liquidity NUMERIC,
    cash_liquidity NUMERIC,
    return_on_equity NUMERIC,
    return_on_total_capital NUMERIC,
    profit_margin NUMERIC,

    -- Group structure
    parent_orgnr TEXT,
    parent_name TEXT,
    group_top_orgnr TEXT,
    group_top_name TEXT,

    -- Extended info (Priority 4)
    lei_code TEXT,
    signatory_text TEXT,
    business_description TEXT,

    -- Sources tracking
    source_basic TEXT,
    source_board TEXT,
    source_financials TEXT,

    -- Timestamps
    last_enriched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Persons table
CREATE TABLE IF NOT EXISTS persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    birth_date TEXT,
    birth_year INTEGER,
    city TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Roles table (company-person relationship)
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT REFERENCES companies(orgnr) ON DELETE CASCADE,
    person_id UUID REFERENCES persons(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role_type TEXT NOT NULL,
    role_category TEXT,
    from_date TEXT,
    to_date TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- NOTE: signatories table removed (data stored in companies.signatory_text instead)

-- Financials table (historical data, ~50 columns)
CREATE TABLE IF NOT EXISTS financials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT REFERENCES companies(orgnr) ON DELETE CASCADE,
    period_year INTEGER,
    period_month INTEGER,
    period_type TEXT,
    currency TEXT DEFAULT 'SEK',

    -- Income Statement
    revenue BIGINT,
    revenue_change_percent NUMERIC,
    gross_profit BIGINT,
    operating_profit BIGINT,
    profit_before_tax BIGINT,
    net_profit BIGINT,

    -- Personnel
    num_employees INTEGER,
    personnel_costs BIGINT,

    -- Balance Sheet - Assets
    total_assets BIGINT,
    fixed_assets BIGINT,
    intangible_assets BIGINT,
    tangible_assets BIGINT,
    financial_assets BIGINT,
    current_assets BIGINT,
    inventory BIGINT,
    accounts_receivable BIGINT,
    cash_and_equivalents BIGINT,

    -- Balance Sheet - Liabilities & Equity
    equity BIGINT,
    share_capital BIGINT,
    retained_earnings BIGINT,
    untaxed_reserves BIGINT,
    provisions BIGINT,
    long_term_debt BIGINT,
    short_term_debt BIGINT,
    current_liabilities BIGINT,
    accounts_payable BIGINT,
    total_liabilities BIGINT,

    -- Key Ratios
    solidity NUMERIC,
    liquidity NUMERIC,
    cash_liquidity NUMERIC,
    return_on_equity NUMERIC,
    return_on_total_capital NUMERIC,
    profit_margin NUMERIC,
    debt_ratio NUMERIC,
    interest_coverage_ratio NUMERIC,

    -- Audit
    auditor_name TEXT,
    audit_firm TEXT,

    -- Metadata
    source TEXT,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(company_orgnr, period_year)
);

-- NOTE: vehicles table removed (Merinfo scraper deprecated 2025-12-09)
-- NOTE: beneficial_owners table removed (Merinfo scraper deprecated 2025-12-09)

-- Announcements table
CREATE TABLE IF NOT EXISTS announcements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT REFERENCES companies(orgnr) ON DELETE CASCADE,
    date TEXT,
    type TEXT,
    content TEXT,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Related companies table (group structure)
CREATE TABLE IF NOT EXISTS related_companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT REFERENCES companies(orgnr) ON DELETE CASCADE,
    related_orgnr TEXT,
    related_name TEXT,
    relation_type TEXT,
    ownership_percent NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Industries table (SNI codes)
CREATE TABLE IF NOT EXISTS industries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT REFERENCES companies(orgnr) ON DELETE CASCADE,
    sni_code TEXT,
    sni_description TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trademarks table
CREATE TABLE IF NOT EXISTS trademarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT REFERENCES companies(orgnr) ON DELETE CASCADE,
    name TEXT,
    registration_number TEXT,
    registration_date TEXT,
    expiry_date TEXT,
    status TEXT,
    classes TEXT,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cache metadata table
CREATE TABLE IF NOT EXISTS cache_metadata (
    orgnr TEXT PRIMARY KEY,
    last_refresh TIMESTAMPTZ,
    last_basic_refresh TIMESTAMPTZ,
    last_board_refresh TIMESTAMPTZ,
    last_financial_refresh TIMESTAMPTZ,
    source TEXT
);

-- NOTE: merinfo_hashes table removed (Merinfo scraper deprecated 2025-12-09)
-- Legacy table may still exist in database but is no longer used

-- =====================================================
-- HISTORY TABLES (for tracking changes over time)
-- =====================================================

-- Companies history
CREATE TABLE IF NOT EXISTS companies_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orgnr TEXT NOT NULL,
    snapshot_date TIMESTAMPTZ DEFAULT NOW(),
    data JSONB NOT NULL
);

-- Roles history
CREATE TABLE IF NOT EXISTS roles_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_orgnr TEXT NOT NULL,
    snapshot_date TIMESTAMPTZ DEFAULT NOW(),
    roles_json JSONB NOT NULL
);

-- NOTE: vehicles_history table removed (Merinfo scraper deprecated 2025-12-09)
-- NOTE: beneficial_owners_history table removed (Merinfo scraper deprecated 2025-12-09)

-- =====================================================
-- COMPANY REGISTRY (for name lookup - 887k records)
-- =====================================================

-- Company registry table with FTS
CREATE TABLE IF NOT EXISTS company_registry (
    orgnr TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    org_form TEXT,
    registration_date TEXT,
    postal_address TEXT,
    business_description TEXT,

    -- Full-text search vector (auto-generated)
    name_search TSVECTOR GENERATED ALWAYS AS (to_tsvector('swedish', coalesce(name, ''))) STORED
);

-- Registry metadata
CREATE TABLE IF NOT EXISTS registry_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Companies indexes
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_status ON companies(status);
CREATE INDEX IF NOT EXISTS idx_companies_municipality ON companies(municipality);
CREATE INDEX IF NOT EXISTS idx_companies_county ON companies(county);

-- Roles indexes
CREATE INDEX IF NOT EXISTS idx_roles_company ON roles(company_orgnr);
CREATE INDEX IF NOT EXISTS idx_roles_person ON roles(person_id);

-- Financials indexes
CREATE INDEX IF NOT EXISTS idx_financials_company ON financials(company_orgnr);
CREATE INDEX IF NOT EXISTS idx_financials_year ON financials(period_year);

-- NOTE: vehicles indexes removed (table deprecated)
-- NOTE: beneficial_owners indexes removed (table deprecated)

-- Industries indexes
CREATE INDEX IF NOT EXISTS idx_industries_company ON industries(company_orgnr);
CREATE INDEX IF NOT EXISTS idx_industries_sni ON industries(sni_code);

-- Trademarks indexes
CREATE INDEX IF NOT EXISTS idx_trademarks_company ON trademarks(company_orgnr);

-- History indexes
CREATE INDEX IF NOT EXISTS idx_companies_history_orgnr ON companies_history(orgnr);
CREATE INDEX IF NOT EXISTS idx_roles_history_company ON roles_history(company_orgnr);
-- NOTE: vehicles_history and beneficial_owners_history indexes removed (tables deprecated)

-- Company registry indexes (for FTS)
CREATE INDEX IF NOT EXISTS idx_company_registry_fts ON company_registry USING GIN(name_search);
CREATE INDEX IF NOT EXISTS idx_company_registry_name_trgm ON company_registry USING GIN(name gin_trgm_ops);

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Full-text search function for company registry
CREATE OR REPLACE FUNCTION search_companies_fts(
    search_term TEXT,
    result_limit INTEGER DEFAULT 20
)
RETURNS TABLE(orgnr TEXT, name TEXT, org_form TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT cr.orgnr, cr.name, cr.org_form
    FROM company_registry cr
    WHERE cr.name_search @@ plainto_tsquery('swedish', search_term)
    ORDER BY ts_rank(cr.name_search, plainto_tsquery('swedish', search_term)) DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for companies table
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
