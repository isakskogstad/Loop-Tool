import { Marker, Tooltip } from 'react-leaflet'
import L from 'leaflet'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'

interface CompanyMarkerProps {
  company: CompanyWithCoords
}

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

// Custom marker icon
const createMarkerIcon = (_hasLogo: boolean, isSelected: boolean) => {
  const color = isSelected ? '#CDFF00' : '#0A0A0A'
  const borderColor = isSelected ? '#0A0A0A' : '#CDFF00'

  return L.divIcon({
    html: `<div class="company-marker ${isSelected ? 'selected' : ''}" style="
      background: ${color};
      border: 2px solid ${borderColor};
      width: 12px;
      height: 12px;
      border-radius: 50%;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      transition: all 0.2s ease;
    "></div>`,
    className: 'custom-marker',
    iconSize: L.point(12, 12),
    iconAnchor: L.point(6, 6),
  })
}

export function CompanyMarker({ company }: CompanyMarkerProps) {
  const { selectedCompany, setSelectedCompany, setHoveredCompany } = useMapContext()
  const isSelected = selectedCompany?.orgnr === company.orgnr

  // At this point, coordinates are guaranteed to exist (filtered in MapContainer)
  if (!company.latitude || !company.longitude) return null

  return (
    <Marker
      position={[company.latitude, company.longitude]}
      icon={createMarkerIcon(!!company.logo_url, isSelected)}
      eventHandlers={{
        click: () => setSelectedCompany(company),
        mouseover: () => setHoveredCompany(company),
        mouseout: () => setHoveredCompany(null),
      }}
    >
      <Tooltip
        direction="top"
        offset={[0, -10]}
        opacity={1}
        className="company-tooltip"
      >
        <div className="p-2 min-w-[200px]">
          <div className="font-semibold text-gray-900 text-sm">{company.name}</div>
          {company.sector && (
            <div className="text-xs text-gray-600 mt-0.5">{company.sector}</div>
          )}
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            {company.city && <span>{company.city}</span>}
            {company.turnover_2024_sek && (
              <span className="font-medium text-gray-700">
                {formatCurrency(company.turnover_2024_sek)}
              </span>
            )}
          </div>
        </div>
      </Tooltip>
    </Marker>
  )
}
