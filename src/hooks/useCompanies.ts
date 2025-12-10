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
        const data = await fetchCompaniesWithCoords()
        setCompanies(data)
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch companies'))
        console.error('Error fetching companies:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return { companies, loading, error }
}
