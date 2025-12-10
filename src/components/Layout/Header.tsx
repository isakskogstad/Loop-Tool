import { Search, X } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'
import { useState } from 'react'

interface HeaderProps {
  companyCount: number
  loading: boolean
}

export function Header({ companyCount, loading }: HeaderProps) {
  const { filters, setFilters } = useMapContext()
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header className="fixed top-0 left-0 right-0 z-[999] bg-white/95 backdrop-blur-sm border-b border-gray-100">
      <div className="max-w-screen-xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#0A0A0A] flex items-center justify-center">
              <div className="w-5 h-5 rounded-full bg-[#CDFF00]" />
            </div>
            <div>
              <h1 className="font-bold text-gray-900 text-lg leading-tight">Loop Data</h1>
              <p className="text-xs text-gray-500">
                {loading ? 'Laddar...' : `${companyCount.toLocaleString('sv-SE')} impact-företag`}
              </p>
            </div>
          </div>

          {/* Search */}
          <div className="flex items-center gap-2">
            {searchOpen ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Sök företag, stad, sektor..."
                  value={filters.search}
                  onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                  className="w-64 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-lime-400 focus:border-transparent"
                  autoFocus
                />
                <button
                  onClick={() => {
                    setSearchOpen(false)
                    setFilters({ ...filters, search: '' })
                  }}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setSearchOpen(true)}
                className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Search className="w-4 h-4" />
                <span className="hidden sm:inline">Sök</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
