import { MapContainer as LeafletMap, TileLayer, ZoomControl } from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import { CompanyMarker } from './CompanyMarker'
import { FloatingStats } from './FloatingStats'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'
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

export function MapView({ companies }: MapContainerProps) {
  const { filters } = useMapContext()

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
        {/* Light minimalist tile layer - CartoDB Positron */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
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

      {/* Floating Stats Panel */}
      <FloatingStats companies={filteredCompanies} filteredCount={filteredCompanies.length} />
    </div>
  )
}
