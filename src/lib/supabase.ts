import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://wzkohritxdrstsmwopco.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind6a29ocml0eGRyc3RzbXdvcGNvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMwNTYzNDgsImV4cCI6MjA0ODYzMjM0OH0.v58VJ1RY2mKqyP2rRV8F6OQ6I6BNLv5u7pQJJq_Gl0E'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export interface LoopCompany {
  id: string
  orgnr: string
  company_name: string
  sector: string | null
  investment_status: string | null
  ceo_contact: string | null
  city: string | null
  foundation_date: string | null
  total_funding_sek: number | null
  latest_funding_round_sek: number | null
  latest_funding_date: string | null
  latest_valuation_sek: number | null
  turnover_2024_sek: number | null
  ebit_2024_sek: number | null
  turnover_2023_sek: number | null
  ebit_2023_sek: number | null
  growth_2023_2024_percent: number | null
  largest_owners: string | null
}

export interface LoopOwner {
  id: string
  orgnr: string
  owner_name: string
  owner_type: string | null
  ownership_percent: number | null
}

export interface LoopSector {
  id: string
  orgnr: string
  sector_name: string
  is_primary: boolean
}

export async function fetchLoopCompanies(limit = 100): Promise<LoopCompany[]> {
  const { data, error } = await supabase
    .from('loop_table')
    .select('*')
    .order('turnover_2024_sek', { ascending: false, nullsFirst: false })
    .limit(limit)

  if (error) throw error
  return data || []
}

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

export async function fetchTopCompanies(limit = 10) {
  const { data, error } = await supabase
    .from('loop_table')
    .select('company_name, turnover_2024_sek, growth_2023_2024_percent, sector, city')
    .not('turnover_2024_sek', 'is', null)
    .order('turnover_2024_sek', { ascending: false })
    .limit(limit)

  if (error) throw error
  return data || []
}

// Map data types
export interface CompanyWithCoords {
  orgnr: string
  name: string
  latitude: number
  longitude: number
  city: string | null
  county: string | null
  logo_url: string | null
  sector: string | null
  turnover_2024_sek: number | null
  total_funding_sek: number | null
  latest_valuation_sek: number | null
  growth_2023_2024_percent: number | null
  foundation_date: string | null
  ceo_contact: string | null
  investment_status: string | null
}

export async function fetchCompaniesWithCoords(): Promise<CompanyWithCoords[]> {
  // Join companies (with coords) and loop_table (with financials)
  const { data, error } = await supabase
    .from('companies')
    .select(`
      orgnr,
      name,
      latitude,
      longitude,
      city,
      county,
      logo_url
    `)
    .not('latitude', 'is', null)
    .not('longitude', 'is', null)

  if (error) throw error

  // Get loop_table data for enrichment
  const { data: loopData, error: loopError } = await supabase
    .from('loop_table')
    .select(`
      orgnr,
      sector,
      turnover_2024_sek,
      total_funding_sek,
      latest_valuation_sek,
      growth_2023_2024_percent,
      foundation_date,
      ceo_contact,
      investment_status
    `)

  if (loopError) throw loopError

  // Create lookup map for loop_table data
  const loopMap = new Map(loopData?.map(l => [l.orgnr, l]) || [])

  // Merge data
  return (data || []).map(company => {
    const loopInfo = loopMap.get(company.orgnr)
    return {
      orgnr: company.orgnr,
      name: company.name,
      latitude: parseFloat(company.latitude),
      longitude: parseFloat(company.longitude),
      city: company.city,
      county: company.county,
      logo_url: company.logo_url,
      sector: loopInfo?.sector || null,
      turnover_2024_sek: loopInfo?.turnover_2024_sek || null,
      total_funding_sek: loopInfo?.total_funding_sek || null,
      latest_valuation_sek: loopInfo?.latest_valuation_sek || null,
      growth_2023_2024_percent: loopInfo?.growth_2023_2024_percent || null,
      foundation_date: loopInfo?.foundation_date || null,
      ceo_contact: loopInfo?.ceo_contact || null,
      investment_status: loopInfo?.investment_status || null,
    }
  })
}
