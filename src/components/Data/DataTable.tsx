import { TrendingUp, TrendingDown, MapPin, ExternalLink, ChevronUp, ChevronDown, ChevronsUpDown, User, Users, Building2, Globe } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'
import { useState, useMemo } from 'react'

interface DataTableProps {
  companies: CompanyWithCoords[]
}

type SortField = 'name' | 'sector' | 'turnover' | 'growth' | 'funding' | 'valuation' | 'city' | 'ceo' | 'employees'
type SortDirection = 'asc' | 'desc' | null

// Color palette for generated logos - same as CompanyModal
const LOGO_COLORS = [
  { bg: '#E8F5E9', text: '#2E7D32' }, // Green
  { bg: '#E3F2FD', text: '#1565C0' }, // Blue
  { bg: '#FFF3E0', text: '#EF6C00' }, // Orange
  { bg: '#F3E5F5', text: '#7B1FA2' }, // Purple
  { bg: '#FFEBEE', text: '#C62828' }, // Red
  { bg: '#E0F7FA', text: '#00838F' }, // Cyan
  { bg: '#FFF8E1', text: '#F9A825' }, // Amber
  { bg: '#F1F8E9', text: '#558B2F' }, // Light Green
  { bg: '#FCE4EC', text: '#AD1457' }, // Pink
  { bg: '#ECEFF1', text: '#455A64' }, // Blue Grey
]

function getLogoColor(name: string) {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return LOGO_COLORS[Math.abs(hash) % LOGO_COLORS.length]
}

function formatCurrency(value: number | null): string {
  if (!value) return '-'
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)} mdr`
  }
  if (value >= 1_000_000) {
    return `${Math.round(value / 1_000_000)} mkr`
  }
  if (value >= 1_000) {
    return `${Math.round(value / 1_000)} tkr`
  }
  return `${value}`
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}

export function DataTable({ companies }: DataTableProps) {
  const { filters, setSelectedCompany } = useMapContext()
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortField(null)
        setSortDirection(null)
      }
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ChevronsUpDown className="w-3 h-3 text-gray-300" />
    }
    if (sortDirection === 'asc') {
      return <ChevronUp className="w-3 h-3 text-loop-lime" />
    }
    return <ChevronDown className="w-3 h-3 text-loop-lime" />
  }

  const sortedAndFilteredCompanies = useMemo(() => {
    let result = companies.filter(company => {
      if (filters.sector && company.sector !== filters.sector) return false
      if (filters.search) {
        const search = filters.search.toLowerCase()
        return (
          company.name.toLowerCase().includes(search) ||
          company.city?.toLowerCase().includes(search) ||
          company.sector?.toLowerCase().includes(search) ||
          company.ceo_name?.toLowerCase().includes(search) ||
          company.orgnr.includes(search)
        )
      }
      return true
    })

    if (sortField && sortDirection) {
      result = [...result].sort((a, b) => {
        let comparison = 0
        switch (sortField) {
          case 'name':
            comparison = a.name.localeCompare(b.name, 'sv')
            break
          case 'sector':
            comparison = (a.sector || '').localeCompare(b.sector || '', 'sv')
            break
          case 'turnover':
            comparison = (a.turnover_2024_sek || 0) - (b.turnover_2024_sek || 0)
            break
          case 'growth':
            comparison = (a.growth_2023_2024_percent || -Infinity) - (b.growth_2023_2024_percent || -Infinity)
            break
          case 'funding':
            comparison = (a.total_funding_sek || 0) - (b.total_funding_sek || 0)
            break
          case 'valuation':
            comparison = (a.latest_valuation_sek || 0) - (b.latest_valuation_sek || 0)
            break
          case 'city':
            comparison = (a.city || '').localeCompare(b.city || '', 'sv')
            break
          case 'ceo':
            comparison = (a.ceo_name || '').localeCompare(b.ceo_name || '', 'sv')
            break
          case 'employees':
            comparison = (a.num_employees || 0) - (b.num_employees || 0)
            break
        }
        return sortDirection === 'asc' ? comparison : -comparison
      })
    }

    return result
  }, [companies, filters.sector, filters.search, sortField, sortDirection])

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Table Header */}
      <div className="overflow-x-auto flex-1">
        <table className="w-full min-w-[1200px]">
          <thead className="sticky top-0 bg-gray-50 border-b border-gray-200 z-10">
            <tr className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3 text-left w-[220px]">
                <button onClick={() => handleSort('name')} className="flex items-center gap-1 hover:text-gray-900">
                  Företag {getSortIcon('name')}
                </button>
              </th>
              <th className="px-3 py-3 text-left w-[140px]">
                <button onClick={() => handleSort('sector')} className="flex items-center gap-1 hover:text-gray-900">
                  Sektor {getSortIcon('sector')}
                </button>
              </th>
              <th className="px-3 py-3 text-left w-[150px]">
                <button onClick={() => handleSort('ceo')} className="flex items-center gap-1 hover:text-gray-900">
                  VD {getSortIcon('ceo')}
                </button>
              </th>
              <th className="px-3 py-3 text-right w-[90px]">
                <button onClick={() => handleSort('turnover')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Oms. 2024 {getSortIcon('turnover')}
                </button>
              </th>
              <th className="px-3 py-3 text-right w-[80px]">
                <button onClick={() => handleSort('growth')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Tillväxt {getSortIcon('growth')}
                </button>
              </th>
              <th className="px-3 py-3 text-right w-[80px]">
                <button onClick={() => handleSort('funding')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Funding {getSortIcon('funding')}
                </button>
              </th>
              <th className="px-3 py-3 text-right w-[80px]">
                <button onClick={() => handleSort('valuation')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Värdering {getSortIcon('valuation')}
                </button>
              </th>
              <th className="px-3 py-3 text-right w-[60px]">
                <button onClick={() => handleSort('employees')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Anst. {getSortIcon('employees')}
                </button>
              </th>
              <th className="px-3 py-3 text-left w-[100px]">
                <button onClick={() => handleSort('city')} className="flex items-center gap-1 hover:text-gray-900">
                  Stad {getSortIcon('city')}
                </button>
              </th>
              <th className="px-3 py-3 text-center w-[100px]">Styrelse</th>
              <th className="px-3 py-3 w-[50px]"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sortedAndFilteredCompanies.map((company, index) => (
              <tr
                key={company.orgnr}
                onClick={() => setSelectedCompany(company)}
                className={`cursor-pointer transition-colors hover:bg-gray-50 ${
                  index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'
                }`}
              >
                {/* Company Name */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {company.logo_url ? (
                      <img
                        src={company.logo_url}
                        alt=""
                        className="w-8 h-8 rounded-lg object-contain bg-gray-100 p-1"
                      />
                    ) : (
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center font-semibold text-sm"
                        style={{
                          backgroundColor: getLogoColor(company.name).bg,
                          color: getLogoColor(company.name).text
                        }}
                      >
                        {company.name.charAt(0)}
                      </div>
                    )}
                    <div className="min-w-0">
                      <div className="font-medium text-gray-900 text-sm truncate max-w-[160px]">
                        {company.name}
                      </div>
                      <div className="text-xs text-gray-400 font-mono">{company.orgnr}</div>
                    </div>
                  </div>
                </td>

                {/* Sector */}
                <td className="px-3 py-3">
                  {company.sector ? (
                    <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-blue-50 text-blue-700 truncate max-w-[130px]">
                      {company.sector}
                    </span>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>

                {/* CEO */}
                <td className="px-3 py-3">
                  {company.ceo_name ? (
                    <div className="flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                      <span className="text-sm text-gray-700 truncate max-w-[120px]">{company.ceo_name}</span>
                    </div>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>

                {/* Turnover */}
                <td className="px-3 py-3 text-right">
                  <span className="font-medium text-gray-900 text-sm tabular-nums">
                    {formatCurrency(company.turnover_2024_sek)}
                  </span>
                </td>

                {/* Growth */}
                <td className="px-3 py-3 text-right">
                  {company.growth_2023_2024_percent !== null ? (
                    <span className={`inline-flex items-center gap-0.5 font-medium text-sm tabular-nums ${
                      company.growth_2023_2024_percent >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {company.growth_2023_2024_percent >= 0 ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      {formatPercent(company.growth_2023_2024_percent)}
                    </span>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>

                {/* Funding */}
                <td className="px-3 py-3 text-right">
                  <span className="text-sm text-gray-600 tabular-nums">
                    {formatCurrency(company.total_funding_sek)}
                  </span>
                </td>

                {/* Valuation */}
                <td className="px-3 py-3 text-right">
                  <span className="text-sm text-gray-600 tabular-nums">
                    {formatCurrency(company.latest_valuation_sek)}
                  </span>
                </td>

                {/* Employees */}
                <td className="px-3 py-3 text-right">
                  {company.num_employees ? (
                    <span className="text-sm text-gray-600 tabular-nums">{company.num_employees}</span>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>

                {/* City */}
                <td className="px-3 py-3">
                  {company.city ? (
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-gray-400 flex-shrink-0" />
                      <span className="text-sm text-gray-600 truncate max-w-[80px]">{company.city}</span>
                    </div>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>

                {/* Board */}
                <td className="px-3 py-3">
                  {company.board_members.length > 0 || company.chairman_name ? (
                    <div className="flex items-center justify-center gap-1">
                      <Users className="w-3.5 h-3.5 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {company.board_members.length + (company.chairman_name ? 1 : 0)}
                      </span>
                    </div>
                  ) : (
                    <span className="text-gray-300 text-center block">-</span>
                  )}
                </td>

                {/* Actions */}
                <td className="px-3 py-3">
                  <div className="flex items-center gap-1">
                    {company.website && (
                      <a
                        href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="p-1.5 rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                        title="Webbplats"
                      >
                        <Globe className="w-3.5 h-3.5" />
                      </a>
                    )}
                    <a
                      href={`https://www.allabolag.se/${company.orgnr}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="p-1.5 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                      title="Alla Bolag"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Empty State */}
        {sortedAndFilteredCompanies.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500">
            <Building2 className="w-10 h-10 text-gray-300 mb-3" />
            <p className="text-sm">Inga företag matchar din sökning</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50">
        <div className="flex items-center justify-between text-sm">
          <p className="text-gray-600">
            Visar <span className="font-semibold text-gray-900">{sortedAndFilteredCompanies.length}</span> av <span className="font-semibold text-gray-900">{companies.length}</span> företag
          </p>
          {sortField && (
            <p className="text-xs text-gray-400">
              Sorterat: {sortField} ({sortDirection === 'asc' ? '↑' : '↓'})
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
