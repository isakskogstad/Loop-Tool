import { Search, X, Map, Table2, Filter } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'
import { useState, useEffect } from 'react'

interface HeaderProps {
  companyCount: number
  loading: boolean
}

const QUICK_SECTORS = ['Climate Tech', 'Health Tech', 'Fintech', 'EdTech', 'Impact']

export function Header({ companyCount, loading }: HeaderProps) {
  const { filters, setFilters, viewMode, setViewMode } = useMapContext()
  const [searchOpen, setSearchOpen] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <header className="bg-white border-b border-gray-200">
      {/* Top accent line */}
      <div className="h-1 bg-gradient-to-r from-loop-lime via-teal-400 to-loop-lime" />

      <div className="px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between gap-4">
          {/* Logo & Title */}
          <div className="flex items-center gap-4">
            {/* Logo */}
            <div className="w-10 h-10 rounded-xl bg-loop-black flex items-center justify-center">
              <div className="w-5 h-5 rounded-full bg-loop-lime" />
            </div>

            <div className="flex items-center gap-3">
              <div>
                <h1 className="font-semibold text-gray-900 text-lg sm:text-xl">
                  Loop Tool
                </h1>
              </div>

              {/* Company count badge */}
              {!loading && (
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-loop-lime/20 border border-loop-lime/30">
                  <span className="text-sm font-semibold text-loop-black tabular-nums">
                    {companyCount.toLocaleString('sv-SE')}
                  </span>
                  <span className="text-xs text-gray-600">
                    foretag
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* View Toggle & Search */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* View Toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('map')}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
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
                className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'table'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Table2 className="w-4 h-4" />
                <span className="hidden sm:inline">Data</span>
              </button>
            </div>

            {/* Search */}
            {searchOpen ? (
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Sok foretag, stad, sektor..."
                    value={filters.search}
                    onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                    className="w-48 sm:w-72 pl-9 pr-3 py-2 text-sm bg-white border border-gray-200 rounded-lg
                             focus:outline-none focus:ring-2 focus:ring-loop-lime/50 focus:border-loop-lime"
                    autoFocus
                  />
                </div>
                <button
                  onClick={() => {
                    setSearchOpen(false)
                    setFilters({ ...filters, search: '' })
                  }}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Stang sok"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600
                         bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
              >
                <Search className="w-4 h-4" />
                <span className="hidden sm:inline">Sok foretag</span>
              </button>
            )}

            {/* Status indicator */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg border border-gray-100">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-xs text-gray-500">Online</span>
              </div>
              <div className="w-px h-4 bg-gray-200" />
              <span className="text-xs text-gray-500 tabular-nums">{formatTime(currentTime)}</span>
            </div>
          </div>
        </div>

        {/* Quick Filter Pills */}
        {!loading && (
          <div className="flex items-center gap-2 mt-3 overflow-x-auto pb-1">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wide mr-1 flex-shrink-0">
              Filter:
            </span>

            {/* All button */}
            <button
              onClick={() => setFilters({ ...filters, sector: null })}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex-shrink-0 ${
                !filters.sector
                  ? 'bg-loop-lime text-loop-black'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Alla
            </button>

            {/* Sector pills */}
            {QUICK_SECTORS.map((sector) => (
              <button
                key={sector}
                onClick={() => setFilters({ ...filters, sector: filters.sector === sector ? null : sector })}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex-shrink-0 ${
                  filters.sector === sector
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {sector}
              </button>
            ))}

            {/* More filter button */}
            <button
              className="flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors flex-shrink-0"
            >
              <Filter className="w-3 h-3" />
              Mer
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
