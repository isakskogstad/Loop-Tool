import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { CompanyWithCoords } from '../lib/supabase'

interface MapContextType {
  selectedCompany: CompanyWithCoords | null
  setSelectedCompany: (company: CompanyWithCoords | null) => void
  hoveredCompany: CompanyWithCoords | null
  setHoveredCompany: (company: CompanyWithCoords | null) => void
  filters: {
    sector: string | null
    search: string
  }
  setFilters: (filters: { sector: string | null; search: string }) => void
}

const MapContext = createContext<MapContextType | null>(null)

export function MapProvider({ children }: { children: ReactNode }) {
  const [selectedCompany, setSelectedCompany] = useState<CompanyWithCoords | null>(null)
  const [hoveredCompany, setHoveredCompany] = useState<CompanyWithCoords | null>(null)
  const [filters, setFilters] = useState({ sector: null as string | null, search: '' })

  return (
    <MapContext.Provider value={{
      selectedCompany,
      setSelectedCompany,
      hoveredCompany,
      setHoveredCompany,
      filters,
      setFilters,
    }}>
      {children}
    </MapContext.Provider>
  )
}

export function useMapContext() {
  const context = useContext(MapContext)
  if (!context) {
    throw new Error('useMapContext must be used within MapProvider')
  }
  return context
}
