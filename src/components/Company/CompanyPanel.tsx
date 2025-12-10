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
      whileHover={{ scale: 1.02 }}
      className={`relative p-5 rounded-2xl border transition-all duration-300 group hover:shadow-xl ${
        highlight
          ? 'bg-gradient-to-br from-loop-lime/10 via-loop-lime/5 to-white border-loop-lime/30 hover:border-loop-lime/50 hover:shadow-lime-200/30'
          : 'bg-gradient-to-br from-white to-gray-50 border-gray-200 hover:border-gray-300'
      }`}
    >
      {/* Premium gradient overlay on hover */}
      <div className={`absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${
        highlight ? 'bg-gradient-to-br from-loop-lime/10 to-transparent' : 'bg-gradient-to-br from-primary-blue/5 to-transparent'
      }`} />

      <div className="relative">
        <div className="flex items-center gap-2 text-gray-500 text-xs mb-3">
          <div className={`p-1.5 rounded-xl ${highlight ? 'bg-loop-lime/30' : 'bg-gray-100'}`}>
            {icon}
          </div>
          <span className="font-semibold uppercase tracking-wide">{label}</span>
        </div>
        <div className={`font-bold text-xl tabular-nums ${highlight ? 'text-loop-black' : 'text-gray-900'}`}>
          {value}
          {trend && (
            <span className="inline-block ml-2">
              {trend === 'up' ? (
                <ArrowUpRight className="w-5 h-5 text-green-600 inline" />
              ) : (
                <ArrowDownRight className="w-5 h-5 text-red-600 inline" />
              )}
            </span>
          )}
        </div>
        {subValue && (
          <div className="text-xs text-gray-500 mt-1.5 font-medium">{subValue}</div>
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

          {/* Panel - Premium design with glassmorphism */}
          <motion.div
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full sm:w-[480px] bg-gradient-to-b from-white via-gray-50 to-white shadow-2xl z-[1000] overflow-y-auto border-l border-gray-200"
          >
            {/* Header with premium gradient */}
            <div className="sticky top-0 bg-gradient-to-br from-white/95 via-gray-50/95 to-white/95 backdrop-blur-xl border-b border-gray-200 z-10 shadow-md">
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    {selectedCompany.logo_url ? (
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0, rotate: -5 }}
                        animate={{ scale: 1, opacity: 1, rotate: 0 }}
                        transition={{ type: 'spring', damping: 15 }}
                        className="relative"
                      >
                        <div className="absolute inset-0 bg-gradient-to-br from-loop-lime/20 to-primary-blue/20 rounded-2xl blur-md" />
                        <img
                          src={selectedCompany.logo_url}
                          alt={selectedCompany.name}
                          className="relative w-16 h-16 rounded-2xl object-contain bg-white p-2 border-2 border-gray-200 shadow-lg"
                        />
                      </motion.div>
                    ) : (
                      <motion.div
                        initial={{ scale: 0.8, opacity: 0, rotate: -5 }}
                        animate={{ scale: 1, opacity: 1, rotate: 0 }}
                        transition={{ type: 'spring', damping: 15 }}
                        className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-loop-lime via-loop-lime-dark to-loop-lime flex items-center justify-center text-loop-black font-bold text-2xl shadow-xl shadow-lime-200/50 flex-shrink-0"
                      >
                        {selectedCompany.name.charAt(0)}
                      </motion.div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h2 className="font-serif font-bold text-gray-900 text-2xl leading-tight mb-2 pr-2">
                        {selectedCompany.name}
                      </h2>
                      {selectedCompany.sector && (
                        <span className="inline-block px-3 py-1.5 bg-gradient-to-r from-primary-blue/10 to-purple/10 text-primary-blue border border-primary-blue/30 text-xs font-bold rounded-xl shadow-sm">
                          {selectedCompany.sector}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedCompany(null)}
                    className="p-2.5 hover:bg-gray-100 rounded-2xl transition-all duration-300 flex-shrink-0 hover:scale-110 hover:rotate-90"
                    aria-label="Stäng"
                  >
                    <X className="w-6 h-6 text-gray-500" />
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
                className="flex items-center gap-3 text-gray-700 px-4 py-3 bg-gradient-to-r from-gray-50 to-white rounded-2xl border border-gray-200 shadow-sm"
              >
                <div className="p-2 bg-primary-blue/10 rounded-xl">
                  <MapPin className="w-4 h-4 text-primary-blue" />
                </div>
                <span className="text-sm font-semibold">
                  {[selectedCompany.city, selectedCompany.county].filter(Boolean).join(', ') || 'Sverige'}
                </span>
              </motion.div>

              {/* Key Metrics */}
              <div>
                <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 px-1 flex items-center gap-2">
                  <div className="w-1 h-4 bg-gradient-to-b from-loop-lime to-loop-lime-dark rounded-full" />
                  Nyckeltal
                </h3>
                <div className="grid grid-cols-2 gap-4">
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
                <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 px-1 flex items-center gap-2">
                  <div className="w-1 h-4 bg-gradient-to-b from-primary-blue to-purple rounded-full" />
                  Företagsinfo
                </h3>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.35 }}
                  className="bg-gradient-to-br from-gray-50 to-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm"
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
                  {selectedCompany.ceo_name && (
                    <div className="flex justify-between px-4 py-3 border-b border-gray-200 hover:bg-white transition-colors">
                      <span className="text-gray-600 text-sm font-medium">VD</span>
                      <span className="text-gray-900 text-sm font-semibold">{selectedCompany.ceo_name}</span>
                    </div>
                  )}
                  {selectedCompany.chairman_name && (
                    <div className="flex justify-between px-4 py-3 border-b border-gray-200 hover:bg-white transition-colors">
                      <span className="text-gray-600 text-sm font-medium">Ordförande</span>
                      <span className="text-gray-900 text-sm font-semibold">{selectedCompany.chairman_name}</span>
                    </div>
                  )}
                  {selectedCompany.num_employees && (
                    <div className="flex justify-between px-4 py-3 border-b border-gray-200 hover:bg-white transition-colors">
                      <span className="text-gray-600 text-sm font-medium">Anställda</span>
                      <span className="text-gray-900 text-sm font-semibold">{selectedCompany.num_employees}</span>
                    </div>
                  )}
                  {selectedCompany.board_members.length > 0 && (
                    <div className="flex justify-between px-4 py-3 border-b border-gray-200 hover:bg-white transition-colors">
                      <span className="text-gray-600 text-sm font-medium">Styrelseledamöter</span>
                      <span className="text-gray-900 text-sm font-semibold">{selectedCompany.board_members.length} st</span>
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
                  className="flex items-center justify-center gap-3 w-full py-4 bg-gradient-to-r from-primary-blue via-primary-blue to-purple hover:from-purple hover:to-primary-blue text-white rounded-2xl font-bold transition-all shadow-lg hover:shadow-xl hover:scale-105 group"
                >
                  <ExternalLink className="w-5 h-5 group-hover:scale-110 group-hover:rotate-12 transition-transform" />
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
