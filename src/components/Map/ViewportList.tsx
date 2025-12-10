import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronUp, ChevronDown, MapPin, TrendingUp } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'

interface ViewportListProps {
  companies: CompanyWithCoords[]
  mapBounds: {
    north: number
    south: number
    east: number
    west: number
  } | null
}

function formatCurrency(value: number | null): string {
  if (!value) return '-'
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)} mdr`
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(0)} mkr`
  }
  return `${(value / 1_000).toFixed(0)} tkr`
}

export function ViewportList({ companies, mapBounds }: ViewportListProps) {
  const [expanded, setExpanded] = useState(true)
  const { setSelectedCompany } = useMapContext()

  // Filter companies that are within current viewport
  const visibleCompanies = useMemo(() => {
    if (!mapBounds) return []

    return companies.filter(company => {
      if (!company.latitude || !company.longitude) return false

      return (
        company.latitude >= mapBounds.south &&
        company.latitude <= mapBounds.north &&
        company.longitude >= mapBounds.west &&
        company.longitude <= mapBounds.east
      )
    }).slice(0, 15) // Limit to 15 companies
  }, [companies, mapBounds])

  // Group by city
  const cityCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    visibleCompanies.forEach(c => {
      const city = c.city || 'Okänd'
      counts[city] = (counts[city] || 0) + 1
    })
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
  }, [visibleCompanies])

  if (visibleCompanies.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3, duration: 0.4 }}
      className="absolute top-4 left-4 z-40 w-72"
    >
      <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200 overflow-hidden">
        {/* Header */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-loop-lime/20">
              <MapPin className="w-4 h-4 text-gray-800" />
            </div>
            <div className="text-left">
              <span className="text-sm font-semibold text-gray-900">
                {visibleCompanies.length} företag i vy
              </span>
              {cityCounts.length > 0 && (
                <p className="text-[10px] text-gray-500">
                  {cityCounts.map(([city]) => city).join(', ')}
                </p>
              )}
            </div>
          </div>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </button>

        {/* Company List */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="border-t border-gray-100"
            >
              <div className="max-h-64 overflow-y-auto">
                {visibleCompanies.map((company, index) => (
                  <motion.button
                    key={company.orgnr}
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.03 }}
                    onClick={() => setSelectedCompany(company)}
                    className="w-full px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0 text-left"
                  >
                    {/* Logo or Initial */}
                    <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0 overflow-hidden">
                      {company.logo_url ? (
                        <img
                          src={company.logo_url}
                          alt={company.name}
                          className="w-full h-full object-contain p-1"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none'
                            e.currentTarget.parentElement!.innerHTML = `<span class="text-xs font-bold text-gray-600">${company.name.charAt(0)}</span>`
                          }}
                        />
                      ) : (
                        <span className="text-xs font-bold text-gray-600">
                          {company.name.charAt(0)}
                        </span>
                      )}
                    </div>

                    {/* Company Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-gray-900 truncate">
                        {company.name}
                      </p>
                      <div className="flex items-center gap-2 text-[10px] text-gray-500">
                        {company.city && <span>{company.city}</span>}
                        {company.sector && (
                          <>
                            <span className="text-gray-300">•</span>
                            <span className="truncate">{company.sector}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Quick Metric */}
                    {company.latest_valuation_sek && (
                      <div className="flex items-center gap-1 text-[10px] font-medium text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                        <TrendingUp className="w-2.5 h-2.5" />
                        {formatCurrency(company.latest_valuation_sek)}
                      </div>
                    )}
                  </motion.button>
                ))}
              </div>

              {/* Footer if more companies */}
              {companies.filter(c => c.latitude && c.longitude).length > 15 && (
                <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
                  <p className="text-[10px] text-gray-500 text-center">
                    Zooma in för att se fler företag
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
