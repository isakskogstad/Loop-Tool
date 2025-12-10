import { Search, X, Map, Table2 } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface HeaderProps {
  companyCount: number
  loading: boolean
}

export function Header({ companyCount, loading }: HeaderProps) {
  const { filters, setFilters, viewMode, setViewMode } = useMapContext()
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header className="fixed top-0 left-0 right-0 z-[999]">
      {/* Glass morphism background with subtle gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/95 via-white/90 to-white/85 backdrop-blur-md border-b border-gray-200/60 shadow-[0_1px_3px_rgba(0,0,0,0.05)]" />

      <div className="relative max-w-screen-xl mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between gap-4">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            {/* Premium logo with subtle glow */}
            <div className="relative w-11 h-11 rounded-xl bg-gradient-to-br from-[#0A0A0A] to-[#1A1A1A] flex items-center justify-center shadow-md group hover:shadow-lg transition-shadow">
              <div className="w-5 h-5 rounded-full bg-[#CDFF00] shadow-[0_0_8px_rgba(205,255,0,0.5)] transition-all group-hover:shadow-[0_0_12px_rgba(205,255,0,0.7)]" />
            </div>

            <div className="flex items-center gap-3">
              <div>
                <h1 className="font-bold text-gray-900 text-lg leading-tight tracking-tight">
                  Loop Data
                </h1>
                <p className="text-xs text-gray-500 font-medium mt-0.5">
                  {loading ? (
                    <span className="inline-flex items-center gap-1">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" />
                      Laddar...
                    </span>
                  ) : (
                    'Impact-företag i Sverige'
                  )}
                </p>
              </div>

              {/* Company count badge */}
              {!loading && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-lime-50 to-lime-100/50 border border-lime-200/60 shadow-sm"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-lime-500 shadow-[0_0_4px_rgba(132,204,22,0.6)]" />
                  <span className="text-xs font-semibold text-lime-900 tabular-nums">
                    {companyCount.toLocaleString('sv-SE')}
                  </span>
                </motion.div>
              )}
            </div>
          </div>

          {/* View Toggle & Search */}
          <div className="flex items-center gap-3">
            {/* View Toggle */}
            <div className="flex items-center bg-gray-100 rounded-xl p-1 shadow-inner">
              <button
                onClick={() => setViewMode('map')}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  viewMode === 'map'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Map className="w-4 h-4" />
                <span className="hidden sm:inline">Karta</span>
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  viewMode === 'table'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Table2 className="w-4 h-4" />
                <span className="hidden sm:inline">Data</span>
              </button>
            </div>

            <AnimatePresence mode="wait">
              {searchOpen ? (
                <motion.div
                  key="search-input"
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: 'auto', opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex items-center gap-2"
                >
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                    <input
                      type="text"
                      placeholder="Sök företag, stad, sektor..."
                      value={filters.search}
                      onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                      className="w-64 sm:w-80 pl-10 pr-4 py-2.5 text-sm bg-white border border-gray-300 rounded-xl
                               focus:outline-none focus:ring-2 focus:ring-lime-400/50 focus:border-lime-400
                               shadow-sm hover:border-gray-400 transition-all
                               placeholder:text-gray-400"
                      autoFocus
                    />
                    {filters.search && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 bg-lime-100 text-lime-700 text-xs font-medium rounded">
                        {filteredCount()} resultat
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      setSearchOpen(false)
                      setFilters({ ...filters, search: '' })
                    }}
                    className="p-2.5 hover:bg-gray-100 rounded-xl transition-colors"
                    aria-label="Stäng sök"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </motion.div>
              ) : (
                <motion.button
                  key="search-button"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={() => setSearchOpen(true)}
                  className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700
                           bg-white hover:bg-gray-50 border border-gray-300 rounded-xl
                           shadow-sm hover:shadow transition-all"
                >
                  <Search className="w-4 h-4" />
                  <span className="hidden sm:inline">Sök företag</span>
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </header>
  )

  // Helper function for filtered count (placeholder - would need actual implementation)
  function filteredCount(): number {
    return companyCount // Simplified
  }
}
