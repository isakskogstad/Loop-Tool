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
      className="h-full overflow-auto bg-white"
    >
      <div className="min-w-[900px]">
        {/* Table Header */}
        <div className="sticky top-0 bg-gray-50 border-b border-gray-200 z-10">
          <div className="grid grid-cols-12 gap-4 px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
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

        {/* Table Body */}
        <div className="divide-y divide-gray-100">
          {filteredCompanies.map((company, index) => (
            <motion.div
              key={company.orgnr}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.02, duration: 0.2 }}
              onClick={() => setSelectedCompany(company)}
              className="grid grid-cols-12 gap-4 px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors group"
            >
              {/* Company Name & Logo */}
              <div className="col-span-3 flex items-center gap-3">
                {company.logo_url ? (
                  <img
                    src={company.logo_url}
                    alt={company.name}
                    className="w-8 h-8 rounded-lg object-contain bg-gray-100"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#CDFF00] to-[#a8d900] flex items-center justify-center text-[#0A0A0A] font-bold text-xs">
                    {company.name.charAt(0)}
                  </div>
                )}
                <div className="min-w-0">
                  <div className="font-medium text-gray-900 truncate group-hover:text-[#0A0A0A]">
                    {company.name}
                  </div>
                  <div className="text-xs text-gray-400 font-mono">{company.orgnr}</div>
                </div>
              </div>

              {/* Sector */}
              <div className="col-span-2 flex items-center">
                {company.sector ? (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 truncate">
                    {company.sector}
                  </span>
                ) : (
                  <span className="text-gray-300">-</span>
                )}
              </div>

              {/* Turnover */}
              <div className="col-span-1 flex items-center justify-end">
                <span className="font-medium text-gray-900 tabular-nums">
                  {formatCurrency(company.turnover_2024_sek)}
                </span>
              </div>

              {/* Growth */}
              <div className="col-span-1 flex items-center justify-end gap-1">
                {company.growth_2023_2024_percent !== null ? (
                  <>
                    {company.growth_2023_2024_percent >= 0 ? (
                      <TrendingUp className="w-3 h-3 text-green-500" />
                    ) : (
                      <TrendingDown className="w-3 h-3 text-red-500" />
                    )}
                    <span className={`font-medium tabular-nums ${
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
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
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

      {/* Footer with count */}
      <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-3">
        <p className="text-sm text-gray-500">
          Visar <span className="font-medium text-gray-900">{filteredCompanies.length}</span> av {companies.length} företag
        </p>
      </div>
    </motion.div>
  )
}
