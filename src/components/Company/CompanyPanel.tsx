import { motion, AnimatePresence } from 'framer-motion'
import { X, MapPin, Building2, Users, ExternalLink, ChevronDown } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'
import { useState } from 'react'

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
  if (value === null || value === undefined) return '-'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

interface SectionProps {
  title: string
  defaultOpen?: boolean
  children: React.ReactNode
}

function Section({ title, defaultOpen = true, children }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border-b border-gray-100 last:border-b-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between py-3 text-left hover:bg-gray-50 transition-colors"
      >
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function InfoRow({ label, value, mono = false }: { label: string; value: string | number | null; mono?: boolean }) {
  if (!value) return null
  return (
    <div className="flex justify-between py-2">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm text-gray-900 font-medium ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  )
}

export function CompanyPanel() {
  const { selectedCompany, setSelectedCompany } = useMapContext()

  return (
    <AnimatePresence>
      {selectedCompany && (
        <>
          {/* Backdrop overlay - mobile only */}
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
            className="fixed right-0 top-0 h-full w-full sm:w-[420px] bg-white shadow-2xl z-[1000] overflow-y-auto border-l border-gray-200"
          >
            {/* Header */}
            <div className="sticky top-0 bg-white/95 backdrop-blur-sm border-b border-gray-100 z-10">
              <div className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    {selectedCompany.logo_url ? (
                      <img
                        src={selectedCompany.logo_url}
                        alt={selectedCompany.name}
                        className="w-12 h-12 rounded-xl object-contain bg-gray-50 p-1.5 border border-gray-200"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-700 font-bold text-lg border border-emerald-100">
                        {selectedCompany.name.charAt(0)}
                      </div>
                    )}
                    <div className="min-w-0">
                      <h2 className="font-semibold text-gray-900 text-lg leading-tight truncate">
                        {selectedCompany.name}
                      </h2>
                      <div className="flex items-center gap-2 mt-0.5">
                        {selectedCompany.sector && (
                          <span className="text-xs text-gray-500">{selectedCompany.sector}</span>
                        )}
                        {selectedCompany.city && (
                          <span className="flex items-center gap-1 text-xs text-gray-400">
                            <MapPin className="w-3 h-3" />
                            {selectedCompany.city}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedCompany(null)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Stäng"
                  >
                    <X className="w-5 h-5 text-gray-400" />
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-4 space-y-1">
              {/* Key Metrics - Always visible */}
              <div className="grid grid-cols-2 gap-3 pb-4 border-b border-gray-100">
                <div className="p-3 bg-gray-50 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Omsättning 2024</div>
                  <div className="font-semibold text-gray-900">{formatCurrency(selectedCompany.turnover_2024_sek)}</div>
                </div>
                <div className="p-3 bg-gray-50 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Tillväxt</div>
                  <div className={`font-semibold ${
                    selectedCompany.growth_2023_2024_percent !== null && selectedCompany.growth_2023_2024_percent > 0
                      ? 'text-emerald-600'
                      : selectedCompany.growth_2023_2024_percent !== null && selectedCompany.growth_2023_2024_percent < 0
                        ? 'text-red-600'
                        : 'text-gray-900'
                  }`}>
                    {formatPercent(selectedCompany.growth_2023_2024_percent)}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Total Funding</div>
                  <div className="font-semibold text-gray-900">{formatCurrency(selectedCompany.total_funding_sek)}</div>
                </div>
                <div className="p-3 bg-gray-50 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">Värdering</div>
                  <div className="font-semibold text-gray-900">{formatCurrency(selectedCompany.latest_valuation_sek)}</div>
                </div>
              </div>

              {/* Company Info Section */}
              <Section title="Företagsinfo">
                <div className="space-y-0.5">
                  <InfoRow label="Org.nr" value={selectedCompany.orgnr} mono />
                  <InfoRow label="Grundat" value={selectedCompany.foundation_date ? new Date(selectedCompany.foundation_date).getFullYear() : null} />
                  <InfoRow label="Investeringsstatus" value={selectedCompany.investment_status} />
                  <InfoRow label="Anställda" value={selectedCompany.num_employees} />
                  <InfoRow
                    label="Plats"
                    value={[selectedCompany.city, selectedCompany.county].filter(Boolean).join(', ') || null}
                  />
                </div>
              </Section>

              {/* Leadership Section */}
              {(selectedCompany.ceo_name || selectedCompany.chairman_name || selectedCompany.board_members.length > 0) && (
                <Section title="Ledning & Styrelse">
                  <div className="space-y-3">
                    {selectedCompany.ceo_name && (
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center">
                          <Users className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{selectedCompany.ceo_name}</div>
                          <div className="text-xs text-gray-500">VD</div>
                        </div>
                      </div>
                    )}
                    {selectedCompany.chairman_name && (
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-purple-50 flex items-center justify-center">
                          <Building2 className="w-4 h-4 text-purple-600" />
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{selectedCompany.chairman_name}</div>
                          <div className="text-xs text-gray-500">Ordförande</div>
                        </div>
                      </div>
                    )}
                    {selectedCompany.board_members.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-100">
                        <div className="text-xs text-gray-500 mb-2">Styrelseledamöter ({selectedCompany.board_members.length})</div>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedCompany.board_members.map((member, i) => (
                            <span key={i} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-md">
                              {member}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Section>
              )}

              {/* Funding Section */}
              {(selectedCompany.total_funding_sek || selectedCompany.latest_valuation_sek) && (
                <Section title="Finansiering" defaultOpen={false}>
                  <div className="space-y-0.5">
                    <InfoRow label="Total Funding" value={formatCurrency(selectedCompany.total_funding_sek)} />
                    <InfoRow label="Senaste värdering" value={formatCurrency(selectedCompany.latest_valuation_sek)} />
                  </div>
                </Section>
              )}

              {/* Actions */}
              <div className="pt-4">
                <a
                  href={`https://www.allabolag.se/${selectedCompany.orgnr}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-2.5 bg-gray-900 hover:bg-gray-800 text-white rounded-lg font-medium text-sm transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  Visa på Allabolag
                </a>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
