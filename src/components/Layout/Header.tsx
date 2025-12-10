import { Search, X, Map, Table2, Filter, Sparkles } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface HeaderProps {
  companyCount: number
  loading: boolean
}

// Popular sectors to show as quick filters
const QUICK_SECTORS = ['Climate Tech', 'Health Tech', 'Fintech', 'EdTech', 'Impact']

export function Header({ companyCount, loading }: HeaderProps) {
  const { filters, setFilters, viewMode, setViewMode } = useMapContext()
  const [searchOpen, setSearchOpen] = useState(false)
  const [showFilters, setShowFilters] = useState(false)

  return (
    <header className="relative bg-gradient-to-r from-white via-gray-50/50 to-white border-b border-gray-200">
      {/* Subtle gradient accent line at top */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-loop-lime via-teal-400 to-loop-lime" />

      <div className="relative px-4 sm:px-6 py-4 pt-5">
        <div className="flex items-center justify-between gap-4">
          {/* Logo & Title */}
          <div className="flex items-center gap-4">
            {/* Premium logo with glow effect */}
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="relative w-12 h-12 rounded-2xl bg-gradient-to-br from-[#0A0A0A] via-[#1A1A1A] to-[#0A0A0A] flex items-center justify-center shadow-lg group hover:shadow-xl transition-all duration-300"
            >
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-loop-lime/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-loop-lime via-loop-lime-dark to-loop-lime shadow-[0_0_12px_rgba(205,255,0,0.6)] group-hover:shadow-[0_0_20px_rgba(205,255,0,0.8)] transition-all duration-300" />
            </motion.div>

            <div className="flex items-center gap-2 sm:gap-4">
              <div>
                <h1 className="font-serif font-bold text-gray-900 text-lg sm:text-2xl leading-tight tracking-tight">
                  Loop Tool
                </h1>
                <p className="text-[10px] sm:text-xs text-gray-500 font-medium mt-0.5 sm:mt-1 hidden xs:block">
                  {loading ? (
                    <span className="inline-flex items-center gap-1.5">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" />
                      Laddar...
                    </span>
                  ) : (
                    'Impact Ecosystem'
                  )}
                </p>
              </div>

              {/* Company count badge */}
              {!loading && (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.3, duration: 0.5 }}
                  className="hidden md:flex items-center gap-2 px-4 py-2 rounded-2xl bg-gradient-to-r from-loop-lime via-loop-lime to-loop-lime-dark shadow-md shadow-lime-200/50 border border-lime-300/30 group hover:shadow-lg hover:shadow-lime-200/60 transition-all duration-300"
                >
                  <div className="w-2 h-2 rounded-full bg-loop-black shadow-[0_0_6px_rgba(10,10,10,0.8)] animate-pulse" />
                  <span className="text-sm font-bold text-loop-black tabular-nums">
                    {companyCount.toLocaleString('sv-SE')}
                  </span>
                  <span className="text-xs font-semibold text-loop-black/70">
                    företag
                  </span>
                </motion.div>
              )}
            </div>
          </div>

          {/* View Toggle & Search */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Premium View Toggle with lime accent */}
            <div className="flex items-center bg-loop-black rounded-xl sm:rounded-2xl p-0.5 sm:p-1 shadow-xl border border-gray-800">
              <button
                onClick={() => setViewMode('map')}
                className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-5 py-2 sm:py-2.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-bold transition-all duration-300 ${
                  viewMode === 'map'
                    ? 'bg-gradient-to-r from-loop-lime to-loop-lime-dark text-loop-black shadow-lg shadow-lime-500/30 scale-105'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Map className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="hidden sm:inline">Karta</span>
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-5 py-2 sm:py-2.5 rounded-lg sm:rounded-xl text-xs sm:text-sm font-bold transition-all duration-300 ${
                  viewMode === 'table'
                    ? 'bg-gradient-to-r from-loop-lime to-loop-lime-dark text-loop-black shadow-lg shadow-lime-500/30 scale-105'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <Table2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
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
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
                    <input
                      type="text"
                      placeholder="Sök företag, stad, sektor..."
                      value={filters.search}
                      onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                      className="w-64 sm:w-96 pl-12 pr-4 py-3 text-sm bg-white/90 backdrop-blur-sm border border-gray-300 rounded-2xl
                               focus:outline-none focus:ring-2 focus:ring-loop-lime/60 focus:border-loop-lime
                               shadow-lg hover:border-gray-400 hover:shadow-xl transition-all duration-300
                               placeholder:text-gray-400 font-medium"
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
                    className="p-3 hover:bg-gray-100 rounded-2xl transition-all duration-300 hover:scale-110"
                    aria-label="Stäng sök"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </motion.div>
              ) : (
                <motion.button
                  key="search-button"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  onClick={() => setSearchOpen(true)}
                  className="flex items-center gap-2 px-5 py-3 text-sm font-semibold text-gray-700
                           bg-white/90 backdrop-blur-sm hover:bg-white border border-gray-300 rounded-2xl
                           shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300"
                >
                  <Search className="w-5 h-5" />
                  <span className="hidden sm:inline">Sök företag</span>
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Quick Filter Pills */}
        {!loading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex items-center gap-2 mt-4 overflow-x-auto pb-1 scrollbar-hide"
          >
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide mr-2 flex-shrink-0">
              Filter:
            </span>

            {/* All button */}
            <button
              onClick={() => setFilters({ ...filters, sector: null })}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 flex-shrink-0 ${
                !filters.sector
                  ? 'bg-loop-lime text-loop-black shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Sparkles className="w-3 h-3" />
              Alla
            </button>

            {/* Sector pills */}
            {QUICK_SECTORS.map((sector) => (
              <button
                key={sector}
                onClick={() => setFilters({ ...filters, sector: filters.sector === sector ? null : sector })}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 flex-shrink-0 ${
                  filters.sector === sector
                    ? 'bg-primary-blue text-white shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {sector}
              </button>
            ))}

            {/* Filter button for more */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all duration-200 flex-shrink-0"
            >
              <Filter className="w-3 h-3" />
              Mer
            </button>
          </motion.div>
        )}
      </div>
    </header>
  )

  // Helper function for filtered count (placeholder - would need actual implementation)
  function filteredCount(): number {
    return companyCount // Simplified
  }
}
