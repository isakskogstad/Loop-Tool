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
