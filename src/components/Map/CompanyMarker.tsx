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
    return `${(value / 1_000_000_000).toFixed(1)} mdr`
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(0)} mkr`
  }
  return `${(value / 1_000).toFixed(0)} tkr`
}

// Create marker icon - with logo if available, otherwise styled dot
const createMarkerIcon = (logoUrl: string | null, isSelected: boolean, companyName: string) => {
  const size = 36 // Fixed size regardless of zoom
  const borderColor = isSelected ? '#CDFF00' : '#fff'
  const shadowColor = isSelected ? 'rgba(205, 255, 0, 0.5)' : 'rgba(0, 0, 0, 0.25)'

  if (logoUrl) {
    // Company has logo - show it as marker
    return L.divIcon({
      html: `<div class="company-logo-marker ${isSelected ? 'selected' : ''}" style="
        width: ${size}px;
        height: ${size}px;
        border-radius: 8px;
        border: 2.5px solid ${borderColor};
        background: white;
        box-shadow: 0 3px 12px ${shadowColor};
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        cursor: pointer;
      ">
        <img src="${logoUrl}" alt="${companyName}" style="
          width: 100%;
          height: 100%;
          object-fit: contain;
          padding: 3px;
        " onerror="this.style.display='none'; this.parentElement.innerHTML='<span style=font-size:14px;font-weight:600;color:#374151>${companyName.charAt(0)}</span>'" />
      </div>`,
      className: 'custom-logo-marker',
      iconSize: L.point(size, size),
      iconAnchor: L.point(size / 2, size / 2),
    })
  }

  // No logo - show initial letter in styled circle
  const initial = companyName.charAt(0).toUpperCase()
  return L.divIcon({
    html: `<div class="company-initial-marker ${isSelected ? 'selected' : ''}" style="
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      border: 2.5px solid ${borderColor};
      background: linear-gradient(135deg, #0A0A0A 0%, #1f2937 100%);
      box-shadow: 0 3px 12px ${shadowColor};
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      cursor: pointer;
    ">
      <span style="color: #CDFF00; font-size: 14px; font-weight: 700;">${initial}</span>
    </div>`,
    className: 'custom-initial-marker',
    iconSize: L.point(size, size),
    iconAnchor: L.point(size / 2, size / 2),
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
      icon={createMarkerIcon(company.logo_url, isSelected, company.name)}
      eventHandlers={{
        click: () => setSelectedCompany(company),
        mouseover: () => setHoveredCompany(company),
        mouseout: () => setHoveredCompany(null),
      }}
    >
      <Tooltip
        direction="top"
        offset={[0, -22]}
        opacity={1}
        className="company-tooltip-modern"
      >
        <div className="bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden min-w-[240px]">
          {/* Header with gradient */}
          <div className="bg-gradient-to-r from-gray-900 to-gray-800 px-4 py-3">
            <h3 className="font-bold text-white text-sm leading-tight">{company.name}</h3>
            {company.sector && (
              <span className="inline-block mt-1 px-2 py-0.5 bg-loop-lime/20 text-loop-lime text-xs font-medium rounded-full">
                {company.sector}
              </span>
            )}
          </div>

          {/* Content */}
          <div className="px-4 py-3 space-y-2">
            {/* Location */}
            {company.city && (
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>{company.city}</span>
              </div>
            )}

            {/* Key metrics */}
            <div className="grid grid-cols-2 gap-2 pt-1">
              {company.latest_valuation_sek && (
                <div className="bg-emerald-50 rounded-lg px-2 py-1.5">
                  <div className="text-[10px] text-emerald-600 font-medium uppercase">Värdering</div>
                  <div className="text-xs font-bold text-emerald-800">{formatCurrency(company.latest_valuation_sek)}</div>
                </div>
              )}
              {company.turnover_2024_sek && (
                <div className="bg-gray-50 rounded-lg px-2 py-1.5">
                  <div className="text-[10px] text-gray-500 font-medium uppercase">Omsättning</div>
                  <div className="text-xs font-bold text-gray-800">{formatCurrency(company.turnover_2024_sek)}</div>
                </div>
              )}
              {company.num_employees && (
                <div className="bg-blue-50 rounded-lg px-2 py-1.5">
                  <div className="text-[10px] text-blue-600 font-medium uppercase">Anställda</div>
                  <div className="text-xs font-bold text-blue-800">{company.num_employees.toLocaleString('sv-SE')}</div>
                </div>
              )}
              {company.ceo_name && (
                <div className="bg-purple-50 rounded-lg px-2 py-1.5">
                  <div className="text-[10px] text-purple-600 font-medium uppercase">VD</div>
                  <div className="text-xs font-bold text-purple-800 truncate">{company.ceo_name.split(' ').slice(-1)[0]}</div>
                </div>
              )}
            </div>
          </div>

          {/* Footer hint */}
          <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
            <span className="text-[10px] text-gray-400">Klicka för mer information</span>
          </div>
        </div>
      </Tooltip>
    </Marker>
  )
}
