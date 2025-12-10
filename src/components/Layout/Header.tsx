import { Search, X, Wifi } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'
import { useState, useEffect, useRef } from 'react'

export function Header() {
  const { filters, setFilters } = useMapContext()
  const [searchOpen, setSearchOpen] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

  // Keyboard shortcut (Cmd/Ctrl + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setSearchOpen(true)
        // Focus input after state update
        setTimeout(() => searchInputRef.current?.focus(), 0)
      }
      if (e.key === 'Escape' && searchOpen) {
        setSearchOpen(false)
        setFilters({ ...filters, search: '' })
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [searchOpen, filters, setFilters])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 sticky top-0 z-50">
      {/* Top accent line */}
      <div className="h-1 bg-gradient-to-r from-loop-lime via-emerald-400 to-loop-lime" />

      <div className="px-4 sm:px-6 py-3">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Logo and Title */}
          <div className="flex items-center gap-3 min-w-0">
            <img
              src="/impact-loop-logo.svg"
              alt="Impact Loop"
              className="h-8 sm:h-10 w-auto flex-shrink-0"
            />
            <div className="min-w-0">
              <h1 className="font-bold text-gray-900 text-lg sm:text-xl tracking-tight truncate">
                Loop Tool
              </h1>
              <p className="text-xs text-gray-500 hidden sm:block">Impact Investing Database</p>
            </div>
          </div>

          {/* Center: Search */}
          <div className="flex-1 max-w-md hidden sm:block">
            {searchOpen ? (
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Sök företag, stad, VD, orgnr..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="w-full pl-10 pr-10 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                           placeholder:text-gray-400"
                  autoFocus
                />
                <button
                  onClick={() => {
                    setSearchOpen(false)
                    setFilters({ ...filters, search: '' })
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-200 rounded transition-colors"
                  aria-label="Stäng sök"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setSearchOpen(true)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500
                         bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
              >
                <Search className="w-4 h-4" />
                <span>Sök företag...</span>
                <kbd className="ml-auto hidden md:inline-flex text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">⌘K</kbd>
              </button>
            )}
          </div>

          {/* Mobile search button */}
          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className="sm:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Sök"
          >
            {searchOpen ? <X className="w-5 h-5 text-gray-600" /> : <Search className="w-5 h-5 text-gray-600" />}
          </button>

          {/* Right: Status */}
          <div className="hidden md:flex items-center gap-2 text-sm text-gray-500">
            <div className="flex items-center gap-1.5">
              <Wifi className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-emerald-600 font-medium">Ansluten</span>
            </div>
            <span className="text-gray-300">•</span>
            <span className="tabular-nums">{formatTime(currentTime)}</span>
          </div>
        </div>

        {/* Mobile search field - shown when searchOpen on mobile */}
        {searchOpen && (
          <div className="sm:hidden mt-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Sök företag, stad, VD, orgnr..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="w-full pl-10 pr-4 py-2.5 text-sm bg-gray-50 border border-gray-200 rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                autoFocus
              />
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
