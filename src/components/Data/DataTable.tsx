import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, MapPin, ExternalLink } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'

interface DataTableProps {
  companies: CompanyWithCoords[]
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

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}

export function DataTable({ companies }: DataTableProps) {
  const { filters, setSelectedCompany } = useMapContext()

  // Filter companies based on search
  const filteredCompanies = companies.filter(company => {
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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-full overflow-auto bg-gradient-to-b from-white to-gray-50"
    >
      <div className="min-w-[900px]">
        {/* Table Header - Premium sticky with glassmorphism */}
        <div className="sticky top-0 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-b border-gray-700 z-10 shadow-lg">
          <div className="grid grid-cols-12 gap-4 px-6 py-4 text-xs font-bold text-white uppercase tracking-wider">
            <div className="col-span-3">Företag</div>
            <div className="col-span-2">Sektor</div>
            <div className="col-span-1 text-right">Omsättning</div>
            <div className="col-span-1 text-right">Tillväxt</div>
            <div className="col-span-1 text-right">Funding</div>
            <div className="col-span-1 text-right">Värdering</div>
            <div className="col-span-2">Plats</div>
            <div className="col-span-1"></div>
          </div>
        </div>

        {/* Table Body - Zebra striping with gradients */}
        <div className="divide-y divide-gray-100">
          {filteredCompanies.map((company, index) => (
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
        {filteredCompanies.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500">
            <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <MapPin className="w-6 h-6 text-gray-400" />
            </div>
            <p className="text-sm">Inga företag matchar din sökning</p>
          </div>
        )}
      </div>

      {/* Footer with count - Premium gradient */}
      <div className="sticky bottom-0 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-t border-gray-700 px-6 py-4 shadow-lg">
        <p className="text-sm text-gray-300 font-medium">
          Visar <span className="font-bold text-white tabular-nums">{filteredCompanies.length}</span> av <span className="font-bold text-white tabular-nums">{companies.length}</span> företag
        </p>
      </div>
    </motion.div>
  )
}
