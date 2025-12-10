import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://wzkohritxdrstsmwopco.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind6a29ocml0eGRyc3RzbXdvcGNvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyMjkzMjUsImV4cCI6MjA4MDgwNTMyNX0.GigaAVp781QF9rv-AslVD_p4ksT8auWHwXU72H1kOqo'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Types
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
  turnover_2024_sek: number | null
  turnover_2023_sek: number | null
  ebit_2024_sek: number | null
  ebit_2023_sek: number | null
  total_funding_sek: number | null
  latest_valuation_sek: number | null
  growth_2023_2024_percent: number | null
  foundation_date: string | null
  ceo_name: string | null
  chairman_name: string | null
  board_members: string[]
  num_employees: number | null
  investment_status: string | null
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
      latest_valuation_sek,
      turnover_2024_sek,
      turnover_2023_sek,
      ebit_2024_sek,
      ebit_2023_sek,
      growth_2023_2024_percent,
      investment_status
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
      num_employees
    `)

  console.log('Companies query result:', { count: companiesData?.length, error: companiesError })

  if (companiesError) {
    console.error('Companies query error:', companiesError)
    throw companiesError
  }

  // 3. Fetch roles (VD, ordförande, styrelseledamöter)
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
    // Don't throw - roles are optional
  }

  // Create lookup maps
  const companiesMap = new Map(companiesData?.map(c => [c.orgnr, c]) || [])

  // Group roles by company
  const rolesMap = new Map<string, Role[]>()
  rolesData?.forEach(role => {
    const existing = rolesMap.get(role.company_orgnr) || []
    existing.push(role)
    rolesMap.set(role.company_orgnr, existing)
  })

  // Merge all data
  const result = (loopData || []).map(company => {
    const companyInfo = companiesMap.get(company.orgnr)
    const roles = rolesMap.get(company.orgnr) || []

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
      .slice(0, 5) // Max 5 board members

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
      turnover_2024_sek: company.turnover_2024_sek,
      turnover_2023_sek: company.turnover_2023_sek,
      ebit_2024_sek: company.ebit_2024_sek,
      ebit_2023_sek: company.ebit_2023_sek,
      total_funding_sek: company.total_funding_sek,
      latest_valuation_sek: company.latest_valuation_sek,
      growth_2023_2024_percent: company.growth_2023_2024_percent,
      foundation_date: company.foundation_date,
      ceo_name: vd?.name || null,
      chairman_name: chairman?.name || null,
      board_members: boardMembers,
      num_employees: companyInfo?.num_employees || null,
      investment_status: company.investment_status,
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
