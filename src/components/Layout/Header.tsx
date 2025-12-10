import { Search, X } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'
import { useState, useEffect } from 'react'

export function Header() {
  const { filters, setFilters } = useMapContext()
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
      <div className="h-1.5 bg-gradient-to-r from-loop-lime via-teal-400 to-loop-lime" />

      <div className="px-6 py-6">
        {/* Centered Title Section with Logo */}
        <div className="flex flex-col items-center justify-center mb-4">
          <div className="flex items-center gap-5">
            {/* ImpactLoop Logo */}
            <img
              src="/impact-loop-logo.svg"
              alt="Impact Loop"
              className="h-14 w-auto"
            />
            <div className="text-center">
              <h1 className="font-bold text-gray-900 text-3xl sm:text-4xl tracking-tight">
                Loop Tool
              </h1>
              <p className="text-base text-gray-500 mt-1">Impact Investing Database</p>
            </div>
          </div>
        </div>

        {/* Search and Status Row - Centered */}
        <div className="flex items-center justify-center gap-4 flex-wrap">
          {/* Search */}
          {searchOpen ? (
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Sök företag, stad, VD, orgnr..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="w-64 sm:w-96 pl-12 pr-4 py-3 text-base bg-white border-2 border-gray-200 rounded-xl
                           focus:outline-none focus:ring-2 focus:ring-loop-lime/50 focus:border-loop-lime"
                  autoFocus
                />
              </div>
              <button
                onClick={() => {
                  setSearchOpen(false)
                  setFilters({ ...filters, search: '' })
                }}
                className="p-3 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Stäng sök"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setSearchOpen(true)}
              className="flex items-center gap-2.5 px-6 py-3 text-base font-semibold text-gray-600
                       bg-gray-50 hover:bg-gray-100 border-2 border-gray-200 rounded-xl transition-colors"
            >
              <Search className="w-5 h-5" />
              <span>Sök företag</span>
            </button>
          )}

          {/* Status indicator */}
          <div className="hidden lg:flex items-center gap-3 px-4 py-2.5 bg-gray-50 rounded-xl border border-gray-100">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm text-gray-500 font-medium">Online</span>
            </div>
            <div className="w-px h-5 bg-gray-200" />
            <span className="text-sm text-gray-500 tabular-nums font-medium">{formatTime(currentTime)}</span>
          </div>
        </div>
      </div>
    </header>
  )
}
