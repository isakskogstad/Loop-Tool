import { motion, AnimatePresence } from 'framer-motion'
import { X, MapPin, Calendar, TrendingUp, Briefcase, Users, ExternalLink, ArrowUpRight, ArrowDownRight } from 'lucide-react'
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
  trend?: 'up' | 'down' | null
  delay?: number
}

function StatCard({ icon, label, value, subValue, highlight, trend, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className={`relative p-4 rounded-xl border transition-all duration-200 group hover:shadow-md ${
        highlight
          ? 'bg-gradient-to-br from-lime-50 to-lime-100/30 border-lime-200 hover:border-lime-300 hover:shadow-lime-100'
          : 'bg-white border-gray-200 hover:border-gray-300'
      }`}
    >
      {/* Subtle gradient overlay on hover */}
      <div className={`absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity ${
        highlight ? 'bg-gradient-to-br from-lime-100/50 to-transparent' : 'bg-gradient-to-br from-gray-50 to-transparent'
      }`} />

      <div className="relative">
        <div className="flex items-center gap-2 text-gray-500 text-xs mb-2">
          <div className={`p-1 rounded ${highlight ? 'bg-lime-200/50' : 'bg-gray-100'}`}>
            {icon}
          </div>
          <span className="font-medium">{label}</span>
        </div>
        <div className={`font-bold text-lg tabular-nums ${highlight ? 'text-lime-700' : 'text-gray-900'}`}>
          {value}
          {trend && (
            <span className="inline-block ml-1.5">
              {trend === 'up' ? (
                <ArrowUpRight className="w-4 h-4 text-green-600 inline" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-red-600 inline" />
              )}
            </span>
          )}
        </div>
        {subValue && (
          <div className="text-xs text-gray-500 mt-1">{subValue}</div>
        )}
      </div>
    </motion.div>
  )
}

export function CompanyPanel() {
  const { selectedCompany, setSelectedCompany } = useMapContext()

  return (
    <AnimatePresence>
      {selectedCompany && (
        <>
          {/* Backdrop overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedCompany(null)}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[999] md:hidden"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full sm:w-[440px] bg-white shadow-2xl z-[1000] overflow-y-auto"
          >
            {/* Header with gradient */}
            <div className="sticky top-0 bg-gradient-to-b from-white via-white to-white/95 backdrop-blur-sm border-b border-gray-200 z-10">
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    {selectedCompany.logo_url ? (
                      <motion.img
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        src={selectedCompany.logo_url}
                        alt={selectedCompany.name}
                        className="w-14 h-14 rounded-xl object-contain bg-gray-50 border border-gray-200 flex-shrink-0 shadow-sm"
                      />
                    ) : (
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="w-14 h-14 rounded-xl bg-gradient-to-br from-lime-400 via-lime-500 to-lime-600 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-lime-200 flex-shrink-0"
                      >
                        {selectedCompany.name.charAt(0)}
                      </motion.div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h2 className="font-bold text-gray-900 text-xl leading-tight mb-1.5 pr-2">
                        {selectedCompany.name}
                      </h2>
                      {selectedCompany.sector && (
                        <span className="inline-block px-2.5 py-1 bg-lime-100 text-lime-700 text-xs font-semibold rounded-full">
                          {selectedCompany.sector}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedCompany(null)}
                    className="p-2 hover:bg-gray-100 rounded-xl transition-colors flex-shrink-0"
                    aria-label="Stäng"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-5 space-y-6">
              {/* Location */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="flex items-center gap-2 text-gray-600 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
              >
                <MapPin className="w-4 h-4 text-gray-400" />
                <span className="text-sm font-medium">
                  {[selectedCompany.city, selectedCompany.county].filter(Boolean).join(', ') || 'Sverige'}
                </span>
              </motion.div>

              {/* Key Metrics */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-1">
                  Nyckeltal
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <StatCard
                    icon={<Briefcase className="w-3.5 h-3.5" />}
                    label="Omsättning 2024"
                    value={formatCurrency(selectedCompany.turnover_2024_sek)}
                    highlight={!!selectedCompany.turnover_2024_sek}
                    delay={0.15}
                  />
                  <StatCard
                    icon={<TrendingUp className="w-3.5 h-3.5" />}
                    label="Tillväxt"
                    value={formatPercent(selectedCompany.growth_2023_2024_percent)}
                    highlight={selectedCompany.growth_2023_2024_percent !== null && selectedCompany.growth_2023_2024_percent > 0}
                    trend={
                      selectedCompany.growth_2023_2024_percent !== null
                        ? selectedCompany.growth_2023_2024_percent > 0
                          ? 'up'
                          : 'down'
                        : null
                    }
                    delay={0.2}
                  />
                  <StatCard
                    icon={<Users className="w-3.5 h-3.5" />}
                    label="Total Funding"
                    value={formatCurrency(selectedCompany.total_funding_sek)}
                    delay={0.25}
                  />
                  <StatCard
                    icon={<Calendar className="w-3.5 h-3.5" />}
                    label="Värdering"
                    value={formatCurrency(selectedCompany.latest_valuation_sek)}
                    delay={0.3}
                  />
                </div>
              </div>

              {/* Additional Info */}
              <div>
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-1">
                  Företagsinfo
                </h3>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.35 }}
                  className="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden"
                >
                  {selectedCompany.investment_status && (
                    <div className="flex justify-between px-4 py-3 border-b border-gray-200 hover:bg-white transition-colors">
                      <span className="text-gray-600 text-sm font-medium">Investeringsstatus</span>
                      <span className="text-gray-900 text-sm font-semibold">{selectedCompany.investment_status}</span>
                    </div>
                  )}
                  {selectedCompany.foundation_date && (
                    <div className="flex justify-between px-4 py-3 border-b border-gray-200 hover:bg-white transition-colors">
                      <span className="text-gray-600 text-sm font-medium">Grundat</span>
                      <span className="text-gray-900 text-sm font-semibold">
                        {new Date(selectedCompany.foundation_date).getFullYear()}
                      </span>
                    </div>
                  )}
                  {selectedCompany.ceo_contact && (
                    <div className="flex justify-between px-4 py-3 border-b border-gray-200 hover:bg-white transition-colors">
                      <span className="text-gray-600 text-sm font-medium">VD</span>
                      <span className="text-gray-900 text-sm font-semibold">{selectedCompany.ceo_contact}</span>
                    </div>
                  )}
                  <div className="flex justify-between px-4 py-3 hover:bg-white transition-colors">
                    <span className="text-gray-600 text-sm font-medium">Org.nr</span>
                    <span className="text-gray-900 text-sm font-mono font-semibold">{selectedCompany.orgnr}</span>
                  </div>
                </motion.div>
              </div>

              {/* Actions */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="pt-2"
              >
                <a
                  href={`https://www.allabolag.se/${selectedCompany.orgnr}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-3.5 bg-gradient-to-r from-gray-900 to-gray-800 hover:from-gray-800 hover:to-gray-700 text-white rounded-xl font-semibold transition-all shadow-md hover:shadow-lg group"
                >
                  <ExternalLink className="w-4 h-4 group-hover:scale-110 transition-transform" />
                  Visa på Allabolag
                </a>
              </motion.div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
