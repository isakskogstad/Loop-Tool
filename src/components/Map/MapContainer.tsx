import { MapContainer as LeafletMap, TileLayer, ZoomControl, useMapEvents } from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import { CompanyMarker } from './CompanyMarker'
import { ViewportList } from './ViewportList'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'
import { useState, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Sweden bounds
const SWEDEN_CENTER: [number, number] = [62.5, 17.5]
const SWEDEN_BOUNDS: [[number, number], [number, number]] = [
  [55.3, 10.5], // Southwest
  [69.1, 24.2], // Northeast
]

interface MapContainerProps {
  companies: CompanyWithCoords[]
}

// Custom cluster icon - using any for cluster type due to react-leaflet-cluster typing
const createClusterIcon = (cluster: any) => {
  const count = cluster.getChildCount()
  let size = 'small'
  let diameter = 40

  if (count >= 100) {
    size = 'large'
    diameter = 60
  } else if (count >= 20) {
    size = 'medium'
    diameter = 50
  }

  return L.divIcon({
    html: `<div class="cluster-icon cluster-${size}">
      <span>${count}</span>
    </div>`,
    className: 'custom-cluster',
    iconSize: L.point(diameter, diameter),
  })
}

// Component to track map bounds
interface MapBounds {
  north: number
  south: number
  east: number
  west: number
}

function MapBoundsTracker({ onBoundsChange }: { onBoundsChange: (bounds: MapBounds) => void }) {
  const map = useMapEvents({
    moveend: () => {
      const bounds = map.getBounds()
      onBoundsChange({
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      })
    },
    zoomend: () => {
      const bounds = map.getBounds()
      onBoundsChange({
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      })
    },
    load: () => {
      const bounds = map.getBounds()
      onBoundsChange({
        north: bounds.getNorth(),
        south: bounds.getSouth(),
        east: bounds.getEast(),
        west: bounds.getWest(),
      })
    },
  })

  return null
}

export function MapView({ companies }: MapContainerProps) {
  const { filters } = useMapContext()
  const [mapBounds, setMapBounds] = useState<MapBounds | null>(null)

  const handleBoundsChange = useCallback((bounds: MapBounds) => {
    setMapBounds(bounds)
  }, [])

  // Filter companies based on search, sector, AND valid coordinates
  const filteredCompanies = companies.filter(company => {
    // Must have valid coordinates for map view
    if (!company.latitude || !company.longitude) {
      return false
    }
    if (filters.sector && company.sector !== filters.sector) {
      return false
    }
    if (filters.search) {
      const search = filters.search.toLowerCase()
      return (
        company.name.toLowerCase().includes(search) ||
        company.city?.toLowerCase().includes(search) ||
        company.sector?.toLowerCase().includes(search) ||
        company.ceo_name?.toLowerCase().includes(search)
      )
    }
    return true
  })

  return (
    <div className="relative w-full h-full">
      <LeafletMap
        center={SWEDEN_CENTER}
        zoom={5}
        minZoom={4}
        maxZoom={18}
        maxBounds={SWEDEN_BOUNDS}
        maxBoundsViscosity={1.0}
        zoomControl={false}
        className="w-full h-full"
      >
        {/* Track map bounds */}
        <MapBoundsTracker onBoundsChange={handleBoundsChange} />

        {/* Light minimalist tile layer - CartoDB Positron (no attribution overlay) */}
        <TileLayer
          attribution=""
          url="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
        />

        <ZoomControl position="bottomright" />

        <MarkerClusterGroup
          chunkedLoading
          iconCreateFunction={createClusterIcon}
          maxClusterRadius={60}
          spiderfyOnMaxZoom={true}
          showCoverageOnHover={false}
          animate={true}
        >
          {filteredCompanies.map(company => (
            <CompanyMarker key={company.orgnr} company={company} />
          ))}
        </MarkerClusterGroup>
      </LeafletMap>

      {/* Viewport Company List */}
      <ViewportList companies={filteredCompanies} mapBounds={mapBounds} />
    </div>
  )
}
