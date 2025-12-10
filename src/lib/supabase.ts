import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://wzkohritxdrstsmwopco.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind6a29ocml0eGRyc3RzbXdvcGNvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyMjkzMjUsImV4cCI6MjA4MDgwNTMyNX0.GigaAVp781QF9rv-AslVD_p4ksT8auWHwXU72H1kOqo'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Types
export interface Owner {
  name: string
  type: string | null
  percent: number | null
}

export interface Trademark {
  name: string
  type: string | null
  status: string | null
  registrationDate: string | null
}

export interface Investor {
  name: string
  type: string | null // 'vc', 'family_office', 'government', etc.
  investmentRound: string | null
  isLeadInvestor: boolean
  website: string | null
}

export interface Industry {
  sniCode: string
  sniDescription: string | null
  isPrimary: boolean
}

export interface EquityOffering {
  offeringType: string
  status: string | null
  amountSek: number | null
  subscriptionStart: string | null
  subscriptionEnd: string | null
  exchange: string | null
}

export interface CompanyWithCoords {
  orgnr: string
  name: string
  latitude: number | null
  longitude: number | null
  city: string | null
  county: string | null
  logo_url: string | null
  website: string | null
  sector: string | null
  // Financials 2024
  turnover_2024_sek: number | null
  ebit_2024_sek: number | null
  // Financials 2023
  turnover_2023_sek: number | null
  ebit_2023_sek: number | null
  // Funding
  total_funding_sek: number | null
  latest_funding_round_sek: number | null
  latest_funding_date: string | null
  latest_valuation_sek: number | null
  // Growth
  growth_2023_2024_percent: number | null
  // Company info
  foundation_date: string | null
  investment_status: string | null
  purpose: string | null
  // People
  ceo_name: string | null
  chairman_name: string | null
  board_members: string[]
  num_employees: number | null
  // Owners
  owners: Owner[]
  largest_owners_text: string | null
  // Trademarks
  trademarks: Trademark[]
  // Annual report
  annual_report_year: number | null
  // Social links
  linkedin_url: string | null
  // Address
  address: string | null
  postal_code: string | null
  // Investors
  investors: Investor[]
  // NEW: Additional fields
  equity_ratio: number | null // Soliditet
  parent_name: string | null // Moderbolag
  group_top_name: string | null // Koncernspets
  industries: Industry[] // SNI-koder
  announcement_count: number // Antal kungörelser
  latest_announcement_date: string | null // Senaste kungörelse
  equity_offering: EquityOffering | null // Aktiv nyemission
}

export interface Role {
  company_orgnr: string
  name: string
  role_type: string
}

// Fetch all companies from loop_table with enriched data
export async function fetchCompaniesWithCoords(): Promise<CompanyWithCoords[]> {
  console.log('Starting fetchCompaniesWithCoords...')

  // 1. Fetch ALL companies from loop_table (primary source - 1214 companies)
  const { data: loopData, error: loopError } = await supabase
    .from('loop_table')
    .select(`
      orgnr,
      company_name,
      sector,
      city,
      foundation_date,
      total_funding_sek,
      latest_funding_round_sek,
      latest_funding_date,
      latest_valuation_sek,
      turnover_2024_sek,
      turnover_2023_sek,
      ebit_2024_sek,
      ebit_2023_sek,
      growth_2023_2024_percent,
      investment_status,
      largest_owners
    `)
    .order('turnover_2024_sek', { ascending: false, nullsFirst: false })

  console.log('Loop table query result:', { count: loopData?.length, error: loopError })

  if (loopError) {
    console.error('Loop table query error:', loopError)
    throw loopError
  }

  // 2. Fetch coordinates and extra info from companies table
  const { data: companiesData, error: companiesError } = await supabase
    .from('companies')
    .select(`
      orgnr,
      latitude,
      longitude,
      county,
      logo_url,
      website,
      num_employees,
      purpose,
      linkedin_url,
      address,
      postal_code,
      postal_city,
      equity_ratio,
      parent_name,
      group_top_name
    `)

  console.log('Companies query result:', { count: companiesData?.length, error: companiesError })

  if (companiesError) {
    console.error('Companies query error:', companiesError)
    throw companiesError
  }

  // 3. Fetch roles (VD, ordforande, styrelseledamoter)
  const { data: rolesData, error: rolesError } = await supabase
    .from('roles')
    .select(`
      company_orgnr,
      name,
      role_type
    `)
    .in('role_type', ['Verkställande direktör', 'Extern verkställande direktör', 'Ordförande', 'Ledamot'])

  console.log('Roles query result:', { count: rolesData?.length, error: rolesError })

  if (rolesError) {
    console.error('Roles query error:', rolesError)
  }

  // 4. Fetch owners from loop_owners
  const { data: ownersData, error: ownersError } = await supabase
    .from('loop_owners')
    .select(`
      orgnr,
      owner_name,
      owner_type,
      ownership_percent
    `)
    .eq('is_current', true)
    .order('ownership_percent', { ascending: false, nullsFirst: false })

  console.log('Owners query result:', { count: ownersData?.length, error: ownersError })

  // 5. Fetch trademarks
  const { data: trademarksData, error: trademarksError } = await supabase
    .from('trademarks')
    .select(`
      company_orgnr,
      trademark_name,
      trademark_type,
      status,
      registration_date
    `)

  console.log('Trademarks query result:', { count: trademarksData?.length, error: trademarksError })

  // 6. Fetch latest annual reports
  const { data: reportsData, error: reportsError } = await supabase
    .from('annual_reports')
    .select(`
      company_orgnr,
      fiscal_year
    `)
    .order('fiscal_year', { ascending: false })

  console.log('Annual reports query result:', { count: reportsData?.length, error: reportsError })

  // 7. Fetch investors from view
  const { data: investorsData, error: investorsError } = await supabase
    .from('company_investors_view')
    .select(`
      company_orgnr,
      investor_name,
      investor_type,
      investment_round,
      is_lead_investor,
      investor_website
    `)
    .eq('is_current', true)

  console.log('Investors query result:', { count: investorsData?.length, error: investorsError })

  // 8. Fetch industries (SNI-koder)
  const { data: industriesData, error: industriesError } = await supabase
    .from('industries')
    .select(`
      company_orgnr,
      sni_code,
      sni_description,
      is_primary
    `)
    .order('is_primary', { ascending: false })

  console.log('Industries query result:', { count: industriesData?.length, error: industriesError })

  // 9. Fetch announcements (kungörelser) - count and latest per company
  const { data: announcementsData, error: announcementsError } = await supabase
    .from('announcements')
    .select(`
      company_orgnr,
      announcement_date
    `)
    .order('announcement_date', { ascending: false })

  console.log('Announcements query result:', { count: announcementsData?.length, error: announcementsError })

  // 10. Fetch active equity offerings (nyemissioner)
  const { data: offeringsData, error: offeringsError } = await supabase
    .from('equity_offerings')
    .select(`
      company_orgnr,
      offering_type,
      status,
      amount_sek,
      subscription_start,
      subscription_end,
      exchange
    `)
    .in('status', ['active', 'upcoming'])

  console.log('Equity offerings query result:', { count: offeringsData?.length, error: offeringsError })

  // Create lookup maps
  const companiesMap = new Map(companiesData?.map(c => [c.orgnr, c]) || [])

  // Group roles by company
  const rolesMap = new Map<string, Role[]>()
  rolesData?.forEach(role => {
    const existing = rolesMap.get(role.company_orgnr) || []
    existing.push(role)
    rolesMap.set(role.company_orgnr, existing)
  })

  // Group owners by company (top 5)
  const ownersMap = new Map<string, Owner[]>()
  ownersData?.forEach(owner => {
    const existing = ownersMap.get(owner.orgnr) || []
    if (existing.length < 5) {
      existing.push({
        name: owner.owner_name,
        type: owner.owner_type,
        percent: owner.ownership_percent
      })
    }
    ownersMap.set(owner.orgnr, existing)
  })

  // Group trademarks by company
  const trademarksMap = new Map<string, Trademark[]>()
  trademarksData?.forEach(tm => {
    const existing = trademarksMap.get(tm.company_orgnr) || []
    existing.push({
      name: tm.trademark_name || '',
      type: tm.trademark_type,
      status: tm.status,
      registrationDate: tm.registration_date
    })
    trademarksMap.set(tm.company_orgnr, existing)
  })

  // Get latest annual report year per company
  const reportsMap = new Map<string, number>()
  reportsData?.forEach(report => {
    if (!reportsMap.has(report.company_orgnr)) {
      reportsMap.set(report.company_orgnr, report.fiscal_year)
    }
  })

  // Group investors by company
  const investorsMap = new Map<string, Investor[]>()
  investorsData?.forEach(inv => {
    const existing = investorsMap.get(inv.company_orgnr) || []
    existing.push({
      name: inv.investor_name,
      type: inv.investor_type,
      investmentRound: inv.investment_round,
      isLeadInvestor: inv.is_lead_investor || false,
      website: inv.investor_website
    })
    investorsMap.set(inv.company_orgnr, existing)
  })

  // Group industries by company
  const industriesMap = new Map<string, Industry[]>()
  industriesData?.forEach(ind => {
    const existing = industriesMap.get(ind.company_orgnr) || []
    existing.push({
      sniCode: ind.sni_code,
      sniDescription: ind.sni_description,
      isPrimary: ind.is_primary || false
    })
    industriesMap.set(ind.company_orgnr, existing)
  })

  // Count announcements per company and get latest date
  const announcementsMap = new Map<string, { count: number, latestDate: string | null }>()
  announcementsData?.forEach(ann => {
    const existing = announcementsMap.get(ann.company_orgnr)
    if (!existing) {
      announcementsMap.set(ann.company_orgnr, {
        count: 1,
        latestDate: ann.announcement_date
      })
    } else {
      existing.count++
      // Keep the latest date (already sorted desc, so first is latest)
    }
  })

  // Map equity offerings by company
  const offeringsMap = new Map<string, EquityOffering>()
  offeringsData?.forEach(off => {
    if (off.company_orgnr && !offeringsMap.has(off.company_orgnr)) {
      offeringsMap.set(off.company_orgnr, {
        offeringType: off.offering_type,
        status: off.status,
        amountSek: off.amount_sek,
        subscriptionStart: off.subscription_start,
        subscriptionEnd: off.subscription_end,
        exchange: off.exchange
      })
    }
  })

  // Merge all data
  const result = (loopData || []).map(company => {
    const companyInfo = companiesMap.get(company.orgnr)
    const roles = rolesMap.get(company.orgnr) || []
    const owners = ownersMap.get(company.orgnr) || []
    const trademarks = trademarksMap.get(company.orgnr) || []
    const annualReportYear = reportsMap.get(company.orgnr) || null
    const investors = investorsMap.get(company.orgnr) || []
    const industries = industriesMap.get(company.orgnr) || []
    const announcementInfo = announcementsMap.get(company.orgnr)
    const equityOffering = offeringsMap.get(company.orgnr) || null

    // Find VD
    const vd = roles.find(r =>
      r.role_type === 'Verkställande direktör' ||
      r.role_type === 'Extern verkställande direktör'
    )

    // Find chairman
    const chairman = roles.find(r => r.role_type === 'Ordförande')

    // Find board members (excluding VD and chairman)
    const boardMembers = roles
      .filter(r => r.role_type === 'Ledamot')
      .map(r => r.name)
      .slice(0, 5)

    // Parse coordinates
    const lat = companyInfo?.latitude
      ? (typeof companyInfo.latitude === 'string' ? parseFloat(companyInfo.latitude) : Number(companyInfo.latitude))
      : null
    const lng = companyInfo?.longitude
      ? (typeof companyInfo.longitude === 'string' ? parseFloat(companyInfo.longitude) : Number(companyInfo.longitude))
      : null

    return {
      orgnr: company.orgnr,
      name: company.company_name,
      latitude: lat,
      longitude: lng,
      city: company.city,
      county: companyInfo?.county || null,
      logo_url: companyInfo?.logo_url || null,
      website: companyInfo?.website || null,
      sector: company.sector,
      // Financials 2024
      turnover_2024_sek: company.turnover_2024_sek,
      ebit_2024_sek: company.ebit_2024_sek,
      // Financials 2023
      turnover_2023_sek: company.turnover_2023_sek,
      ebit_2023_sek: company.ebit_2023_sek,
      // Funding
      total_funding_sek: company.total_funding_sek,
      latest_funding_round_sek: company.latest_funding_round_sek,
      latest_funding_date: company.latest_funding_date,
      latest_valuation_sek: company.latest_valuation_sek,
      // Growth
      growth_2023_2024_percent: company.growth_2023_2024_percent,
      // Company info
      foundation_date: company.foundation_date,
      investment_status: company.investment_status,
      purpose: companyInfo?.purpose || null,
      // People
      ceo_name: vd?.name || null,
      chairman_name: chairman?.name || null,
      board_members: boardMembers,
      num_employees: companyInfo?.num_employees || null,
      // Owners
      owners: owners,
      largest_owners_text: company.largest_owners,
      // Trademarks
      trademarks: trademarks,
      // Annual report
      annual_report_year: annualReportYear,
      // Social links
      linkedin_url: companyInfo?.linkedin_url || null,
      // Address
      address: companyInfo?.address || null,
      postal_code: companyInfo?.postal_code || null,
      // Investors
      investors: investors,
      // NEW: Additional fields
      equity_ratio: companyInfo?.equity_ratio ? Number(companyInfo.equity_ratio) : null,
      parent_name: companyInfo?.parent_name || null,
      group_top_name: companyInfo?.group_top_name || null,
      industries: industries,
      announcement_count: announcementInfo?.count || 0,
      latest_announcement_date: announcementInfo?.latestDate || null,
      equity_offering: equityOffering,
    }
  })

  console.log(`Returning ${result.length} companies`)
  return result
}

// Stats functions
export async function fetchStats() {
  const [companies, owners, sectors, financials] = await Promise.all([
    supabase.from('loop_table').select('id', { count: 'exact', head: true }),
    supabase.from('loop_owners').select('id', { count: 'exact', head: true }),
    supabase.from('loop_sectors').select('id', { count: 'exact', head: true }),
    supabase.from('loop_financials_history').select('id', { count: 'exact', head: true }),
  ])

  return {
    companies: companies.count || 0,
    owners: owners.count || 0,
    sectors: sectors.count || 0,
    financials: financials.count || 0,
  }
}

export async function fetchSectorDistribution() {
  const { data, error } = await supabase
    .from('loop_sectors')
    .select('sector_name')

  if (error) throw error

  const counts: Record<string, number> = {}
  data?.forEach(s => {
    counts[s.sector_name] = (counts[s.sector_name] || 0) + 1
  })

  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
}

// Get last sync time for status display
export async function fetchLastSyncTime(): Promise<Date | null> {
  const { data, error } = await supabase
    .from('poit_sync_stats')
    .select('sync_completed_at')
    .eq('status', 'completed')
    .order('sync_completed_at', { ascending: false })
    .limit(1)
    .single()

  if (error || !data) return null
  return new Date(data.sync_completed_at)
}
