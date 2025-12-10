import { useState, useEffect } from 'react'
import { fetchCompaniesWithCoords } from '../lib/supabase'
import type { CompanyWithCoords } from '../lib/supabase'

export function useCompanies() {
  const [companies, setCompanies] = useState<CompanyWithCoords[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        console.log('Fetching companies with coordinates...')
        const data = await fetchCompaniesWithCoords()
        console.log(`Fetched ${data.length} companies`)
        if (data.length > 0) {
          console.log('Sample company:', data[0])
        }
        setCompanies(data)
      } catch (err) {
        console.error('Error fetching companies:', err)
        setError(err instanceof Error ? err : new Error('Failed to fetch companies'))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return { companies, loading, error }
}
