import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, MapPin, ExternalLink, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'
import { useState, useMemo } from 'react'

interface DataTableProps {
  companies: CompanyWithCoords[]
}

type SortField = 'name' | 'sector' | 'turnover' | 'growth' | 'funding' | 'valuation' | 'city'
type SortDirection = 'asc' | 'desc' | null

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

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}

export function DataTable({ companies }: DataTableProps) {
  const { filters, setSelectedCompany } = useMapContext()
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  // Handle sort click
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortField(null)
        setSortDirection(null)
      }
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Get sort icon for column
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ChevronsUpDown className="w-3.5 h-3.5 text-gray-400" />
    }
    if (sortDirection === 'asc') {
      return <ChevronUp className="w-3.5 h-3.5 text-primary-blue" />
    }
    return <ChevronDown className="w-3.5 h-3.5 text-primary-blue" />
  }

  // Filter and sort companies
  const sortedAndFilteredCompanies = useMemo(() => {
    // First filter
    let result = companies.filter(company => {
      if (filters.sector && company.sector !== filters.sector) return false
      if (filters.search) {
        const search = filters.search.toLowerCase()
        return (
          company.name.toLowerCase().includes(search) ||
          company.city?.toLowerCase().includes(search) ||
          company.sector?.toLowerCase().includes(search)
        )
      }
      return true
    })

    // Then sort if a sort field is selected
    if (sortField && sortDirection) {
      result = [...result].sort((a, b) => {
        let comparison = 0

        switch (sortField) {
          case 'name':
            comparison = a.name.localeCompare(b.name, 'sv')
            break
          case 'sector':
            comparison = (a.sector || '').localeCompare(b.sector || '', 'sv')
            break
          case 'turnover':
            comparison = (a.turnover_2024_sek || 0) - (b.turnover_2024_sek || 0)
            break
          case 'growth':
            comparison = (a.growth_2023_2024_percent || -Infinity) - (b.growth_2023_2024_percent || -Infinity)
            break
          case 'funding':
            comparison = (a.total_funding_sek || 0) - (b.total_funding_sek || 0)
            break
          case 'valuation':
            comparison = (a.latest_valuation_sek || 0) - (b.latest_valuation_sek || 0)
            break
          case 'city':
            comparison = (a.city || '').localeCompare(b.city || '', 'sv')
            break
        }

        return sortDirection === 'asc' ? comparison : -comparison
      })
    }

    return result
  }, [companies, filters.sector, filters.search, sortField, sortDirection])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-full overflow-auto bg-gradient-to-b from-white to-gray-50"
    >
      <div className="min-w-[900px]">
        {/* Table Header - Light theme for showcase */}
        <div className="sticky top-0 bg-white border-b-2 border-gray-200 z-10 shadow-sm">
          <div className="grid grid-cols-12 gap-4 px-6 py-4 text-xs font-bold text-gray-600 uppercase tracking-wider">
            <button
              onClick={() => handleSort('name')}
              className="col-span-3 flex items-center gap-1.5 hover:text-gray-900 transition-colors text-left"
            >
              Företag {getSortIcon('name')}
            </button>
            <button
              onClick={() => handleSort('sector')}
              className="col-span-2 flex items-center gap-1.5 hover:text-gray-900 transition-colors text-left"
            >
              Sektor {getSortIcon('sector')}
            </button>
            <button
              onClick={() => handleSort('turnover')}
              className="col-span-1 flex items-center justify-end gap-1.5 hover:text-gray-900 transition-colors"
            >
              Omsättning {getSortIcon('turnover')}
            </button>
            <button
              onClick={() => handleSort('growth')}
              className="col-span-1 flex items-center justify-end gap-1.5 hover:text-gray-900 transition-colors"
            >
              Tillväxt {getSortIcon('growth')}
            </button>
            <button
              onClick={() => handleSort('funding')}
              className="col-span-1 flex items-center justify-end gap-1.5 hover:text-gray-900 transition-colors"
            >
              Funding {getSortIcon('funding')}
            </button>
            <button
              onClick={() => handleSort('valuation')}
              className="col-span-1 flex items-center justify-end gap-1.5 hover:text-gray-900 transition-colors"
            >
              Värdering {getSortIcon('valuation')}
            </button>
            <button
              onClick={() => handleSort('city')}
              className="col-span-2 flex items-center gap-1.5 hover:text-gray-900 transition-colors text-left"
            >
              Plats {getSortIcon('city')}
            </button>
            <div className="col-span-1"></div>
          </div>
        </div>

        {/* Table Body - Zebra striping with gradients */}
        <div className="divide-y divide-gray-100">
          {sortedAndFilteredCompanies.map((company, index) => (
            <motion.div
              key={company.orgnr}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(index * 0.015, 0.5), duration: 0.25 }}
              onClick={() => setSelectedCompany(company)}
              className={`grid grid-cols-12 gap-4 px-6 py-5 cursor-pointer transition-all duration-300 group hover:scale-[1.01] hover:shadow-lg hover:z-10 rounded-lg mx-2 my-1 ${
                index % 2 === 0
                  ? 'bg-white hover:bg-gradient-to-r hover:from-white hover:to-gray-50'
                  : 'bg-gray-50/50 hover:bg-gradient-to-r hover:from-gray-50 hover:to-white'
              }`}
            >
              {/* Company Name & Logo */}
              <div className="col-span-3 flex items-center gap-3">
                {company.logo_url ? (
                  <div className="relative">
                    <img
                      src={company.logo_url}
                      alt={company.name}
                      className="w-10 h-10 rounded-xl object-contain bg-gradient-to-br from-gray-50 to-gray-100 p-1.5 border border-gray-200 shadow-sm group-hover:shadow-md transition-all duration-300"
                    />
                  </div>
                ) : (
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-loop-lime via-loop-lime-dark to-loop-lime flex items-center justify-center text-loop-black font-bold text-sm shadow-md group-hover:shadow-lg transition-all duration-300 group-hover:scale-110">
                    {company.name.charAt(0)}
                  </div>
                )}
                <div className="min-w-0">
                  <div className="font-semibold text-gray-900 truncate group-hover:text-primary-blue transition-colors duration-300">
                    {company.name}
                  </div>
                  <div className="text-xs text-gray-400 font-mono mt-0.5">{company.orgnr}</div>
                </div>
              </div>

              {/* Sector */}
              <div className="col-span-2 flex items-center">
                {company.sector ? (
                  <span className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-primary-blue/10 to-purple/10 text-primary-blue border border-primary-blue/20 truncate group-hover:shadow-md transition-all duration-300">
                    {company.sector}
                  </span>
                ) : (
                  <span className="text-gray-300">-</span>
                )}
              </div>

              {/* Turnover */}
              <div className="col-span-1 flex items-center justify-end">
                <span className="font-bold text-gray-900 tabular-nums text-sm">
                  {formatCurrency(company.turnover_2024_sek)}
                </span>
              </div>

              {/* Growth */}
              <div className="col-span-1 flex items-center justify-end gap-1.5">
                {company.growth_2023_2024_percent !== null ? (
                  <>
                    <div className={`p-1 rounded-lg ${
                      company.growth_2023_2024_percent >= 0 ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {company.growth_2023_2024_percent >= 0 ? (
                        <TrendingUp className="w-3.5 h-3.5 text-green-600" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5 text-red-600" />
                      )}
                    </div>
                    <span className={`font-bold tabular-nums text-sm ${
                      company.growth_2023_2024_percent >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatPercent(company.growth_2023_2024_percent)}
                    </span>
                  </>
                ) : (
                  <span className="text-gray-300">-</span>
                )}
              </div>

              {/* Funding */}
              <div className="col-span-1 flex items-center justify-end">
                <span className="text-gray-600 tabular-nums">
                  {formatCurrency(company.total_funding_sek)}
                </span>
              </div>

              {/* Valuation */}
              <div className="col-span-1 flex items-center justify-end">
                <span className="text-gray-600 tabular-nums">
                  {formatCurrency(company.latest_valuation_sek)}
                </span>
              </div>

              {/* Location */}
              <div className="col-span-2 flex items-center gap-1 text-gray-500">
                <MapPin className="w-3 h-3 flex-shrink-0" />
                <span className="truncate text-sm">
                  {company.city || company.county || 'Sverige'}
                </span>
              </div>

              {/* Actions */}
              <div className="col-span-1 flex items-center justify-end">
                <a
                  href={`https://www.allabolag.se/${company.orgnr}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-gradient-to-br hover:from-primary-blue hover:to-purple transition-all duration-300 hover:shadow-lg hover:scale-110"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Empty State */}
        {sortedAndFilteredCompanies.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500">
            <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <MapPin className="w-6 h-6 text-gray-400" />
            </div>
            <p className="text-sm">Inga företag matchar din sökning</p>
          </div>
        )}
      </div>

      {/* Footer with count - Light theme */}
      <div className="sticky bottom-0 bg-white border-t-2 border-gray-200 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600 font-medium">
            Visar <span className="font-bold text-gray-900 tabular-nums">{sortedAndFilteredCompanies.length}</span> av <span className="font-bold text-gray-900 tabular-nums">{companies.length}</span> företag
          </p>
          {sortField && (
            <p className="text-xs text-gray-500">
              Sorterat på: <span className="text-primary-blue font-semibold">{sortField}</span> ({sortDirection === 'asc' ? '↑' : '↓'})
            </p>
          )}
        </div>
      </div>
    </motion.div>
  )
}
