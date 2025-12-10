import { motion, AnimatePresence } from 'framer-motion'
import { X, MapPin, Calendar, TrendingUp, Briefcase, Users, ExternalLink } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'

// Format currency for display
function formatCurrency(value: number | null): string {
  if (!value) return '-'
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)} mdr kr`
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(0)} mkr`
  }
  return `${(value / 1_000).toFixed(0)} tkr`
}

function formatPercent(value: number | null): string {
  if (!value) return '-'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string
  subValue?: string
  highlight?: boolean
}

function StatCard({ icon, label, value, subValue, highlight }: StatCardProps) {
  return (
    <div className={`p-3 rounded-lg ${highlight ? 'bg-lime-50 border border-lime-200' : 'bg-gray-50'}`}>
      <div className="flex items-center gap-2 text-gray-500 text-xs mb-1">
        {icon}
        <span>{label}</span>
      </div>
      <div className={`font-semibold ${highlight ? 'text-lime-700' : 'text-gray-900'}`}>
        {value}
      </div>
      {subValue && (
        <div className="text-xs text-gray-500 mt-0.5">{subValue}</div>
      )}
    </div>
  )
}

export function CompanyPanel() {
  const { selectedCompany, setSelectedCompany } = useMapContext()

  return (
    <AnimatePresence>
      {selectedCompany && (
        <motion.div
          initial={{ x: '100%', opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: '100%', opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className="fixed right-0 top-0 h-full w-full sm:w-[400px] bg-white shadow-2xl z-[1000] overflow-y-auto"
        >
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-100 p-4 z-10">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                {selectedCompany.logo_url ? (
                  <img
                    src={selectedCompany.logo_url}
                    alt={selectedCompany.name}
                    className="w-12 h-12 rounded-lg object-contain bg-gray-100"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-lime-400 to-lime-500 flex items-center justify-center text-white font-bold text-lg">
                    {selectedCompany.name.charAt(0)}
                  </div>
                )}
                <div>
                  <h2 className="font-bold text-gray-900 text-lg leading-tight">
                    {selectedCompany.name}
                  </h2>
                  {selectedCompany.sector && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-lime-100 text-lime-700 text-xs font-medium rounded-full">
                      {selectedCompany.sector}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setSelectedCompany(null)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-4 space-y-6">
            {/* Location */}
            <div className="flex items-center gap-2 text-gray-600">
              <MapPin className="w-4 h-4" />
              <span>
                {[selectedCompany.city, selectedCompany.county].filter(Boolean).join(', ') || 'Sverige'}
              </span>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-3">
              <StatCard
                icon={<Briefcase className="w-3.5 h-3.5" />}
                label="Omsättning 2024"
                value={formatCurrency(selectedCompany.turnover_2024_sek)}
                highlight={!!selectedCompany.turnover_2024_sek}
              />
              <StatCard
                icon={<TrendingUp className="w-3.5 h-3.5" />}
                label="Tillväxt"
                value={formatPercent(selectedCompany.growth_2023_2024_percent)}
                highlight={selectedCompany.growth_2023_2024_percent !== null && selectedCompany.growth_2023_2024_percent > 0}
              />
              <StatCard
                icon={<Users className="w-3.5 h-3.5" />}
                label="Total Funding"
                value={formatCurrency(selectedCompany.total_funding_sek)}
              />
              <StatCard
                icon={<Calendar className="w-3.5 h-3.5" />}
                label="Värdering"
                value={formatCurrency(selectedCompany.latest_valuation_sek)}
              />
            </div>

            {/* Additional Info */}
            <div className="space-y-3">
              {selectedCompany.investment_status && (
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-500 text-sm">Investeringsstatus</span>
                  <span className="text-gray-900 text-sm font-medium">{selectedCompany.investment_status}</span>
                </div>
              )}
              {selectedCompany.foundation_date && (
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-500 text-sm">Grundat</span>
                  <span className="text-gray-900 text-sm font-medium">
                    {new Date(selectedCompany.foundation_date).getFullYear()}
                  </span>
                </div>
              )}
              {selectedCompany.ceo_contact && (
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-500 text-sm">VD</span>
                  <span className="text-gray-900 text-sm font-medium">{selectedCompany.ceo_contact}</span>
                </div>
              )}
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-gray-500 text-sm">Org.nr</span>
                <span className="text-gray-900 text-sm font-mono">{selectedCompany.orgnr}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-4">
              <a
                href={`https://www.allabolag.se/${selectedCompany.orgnr}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-3 bg-gray-900 hover:bg-gray-800 text-white rounded-lg font-medium transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                Visa på Allabolag
              </a>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
