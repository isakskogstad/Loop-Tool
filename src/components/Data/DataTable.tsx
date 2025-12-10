import { TrendingUp, TrendingDown, ExternalLink, ChevronUp, ChevronDown, ChevronsUpDown, Building2, Globe, FileText, Award, Users, Linkedin, Bell, DollarSign, Percent, UserCheck, Building } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'
import { useState, useMemo } from 'react'

interface DataTableProps {
  companies: CompanyWithCoords[]
}

type SortField = 'name' | 'sector' | 'turnover' | 'turnover2023' | 'ebit2023' | 'ebit2024' | 'growth' | 'funding' | 'latestRound' | 'valuation' | 'city' | 'ceo' | 'chairman' | 'boardCount' | 'employees' | 'trademarks' | 'annualReport' | 'investors' | 'equityRatio' | 'announcements' | 'sniCode' | 'parentCompany'
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

function formatDate(date: string | null): string {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('sv-SE', { year: 'numeric', month: 'short' })
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
          case 'turnover2023':
            comparison = (a.turnover_2023_sek || 0) - (b.turnover_2023_sek || 0)
            break
          case 'ebit2023':
            comparison = (a.ebit_2023_sek || 0) - (b.ebit_2023_sek || 0)
            break
          case 'growth':
            comparison = (a.growth_2023_2024_percent || -Infinity) - (b.growth_2023_2024_percent || -Infinity)
            break
          case 'funding':
            comparison = (a.total_funding_sek || 0) - (b.total_funding_sek || 0)
            break
          case 'latestRound':
            comparison = (a.latest_funding_round_sek || 0) - (b.latest_funding_round_sek || 0)
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
          case 'trademarks':
            comparison = (a.trademarks?.length || 0) - (b.trademarks?.length || 0)
            break
          case 'annualReport':
            comparison = (a.annual_report_year || 0) - (b.annual_report_year || 0)
            break
          case 'investors':
            comparison = (a.investors?.length || 0) - (b.investors?.length || 0)
            break
          case 'chairman':
            comparison = (a.chairman_name || '').localeCompare(b.chairman_name || '', 'sv')
            break
          case 'boardCount':
            comparison = (a.board_members?.length || 0) - (b.board_members?.length || 0)
            break
          case 'ebit2024':
            comparison = (a.ebit_2024_sek || 0) - (b.ebit_2024_sek || 0)
            break
          case 'equityRatio':
            comparison = (a.equity_ratio || 0) - (b.equity_ratio || 0)
            break
          case 'announcements':
            comparison = (a.announcement_count || 0) - (b.announcement_count || 0)
            break
          case 'sniCode':
            comparison = (a.industries?.[0]?.sniCode || '').localeCompare(b.industries?.[0]?.sniCode || '', 'sv')
            break
          case 'parentCompany':
            comparison = (a.parent_name || a.group_top_name || '').localeCompare(b.parent_name || b.group_top_name || '', 'sv')
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
        <table className="w-full min-w-[2200px]">
          <thead className="sticky top-0 bg-gray-50 border-b border-gray-200 z-10">
            <tr className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3 text-left w-[200px]">
                <button onClick={() => handleSort('name')} className="flex items-center gap-1 hover:text-gray-900">
                  Företag {getSortIcon('name')}
                </button>
              </th>
              <th className="px-2 py-3 text-left w-[120px]">
                <button onClick={() => handleSort('sector')} className="flex items-center gap-1 hover:text-gray-900">
                  Sektor {getSortIcon('sector')}
                </button>
              </th>
              <th className="px-2 py-3 text-left w-[120px]">
                <button onClick={() => handleSort('ceo')} className="flex items-center gap-1 hover:text-gray-900">
                  VD {getSortIcon('ceo')}
                </button>
              </th>
              <th className="px-2 py-3 text-left w-[100px]">
                <button onClick={() => handleSort('chairman')} className="flex items-center gap-1 hover:text-gray-900">
                  Ordf. {getSortIcon('chairman')}
                </button>
              </th>
              <th className="px-2 py-3 text-center w-[45px]">
                <button onClick={() => handleSort('boardCount')} className="flex items-center justify-center gap-1 hover:text-gray-900 w-full">
                  Styr {getSortIcon('boardCount')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[80px]">
                <button onClick={() => handleSort('turnover')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Oms. 24 {getSortIcon('turnover')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[80px]">
                <button onClick={() => handleSort('turnover2023')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Oms. 23 {getSortIcon('turnover2023')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[70px]">
                <button onClick={() => handleSort('ebit2023')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  EBIT 23 {getSortIcon('ebit2023')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[70px]">
                <button onClick={() => handleSort('ebit2024')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  EBIT 24 {getSortIcon('ebit2024')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[70px]">
                <button onClick={() => handleSort('growth')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Tillv. {getSortIcon('growth')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[55px]">
                <button onClick={() => handleSort('equityRatio')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Sol. {getSortIcon('equityRatio')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[80px]">
                <button onClick={() => handleSort('funding')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Tot. Fund {getSortIcon('funding')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[80px]">
                <button onClick={() => handleSort('latestRound')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Sen. Runda {getSortIcon('latestRound')}
                </button>
              </th>
              <th className="px-2 py-3 text-center w-[75px]">
                <button onClick={() => handleSort('annualReport')} className="flex items-center justify-center gap-1 hover:text-gray-900 w-full">
                  Runddat. {getSortIcon('annualReport')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[70px]">
                <button onClick={() => handleSort('valuation')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Värd. {getSortIcon('valuation')}
                </button>
              </th>
              <th className="px-2 py-3 text-right w-[50px]">
                <button onClick={() => handleSort('employees')} className="flex items-center justify-end gap-1 hover:text-gray-900 w-full">
                  Anst {getSortIcon('employees')}
                </button>
              </th>
              <th className="px-2 py-3 text-left w-[80px]">
                <button onClick={() => handleSort('city')} className="flex items-center gap-1 hover:text-gray-900">
                  Stad {getSortIcon('city')}
                </button>
              </th>
              <th className="px-2 py-3 text-left w-[55px]">
                <button onClick={() => handleSort('sniCode')} className="flex items-center gap-1 hover:text-gray-900">
                  SNI {getSortIcon('sniCode')}
                </button>
              </th>
              <th className="px-2 py-3 text-left w-[90px]">
                <button onClick={() => handleSort('parentCompany')} className="flex items-center gap-1 hover:text-gray-900">
                  Koncern {getSortIcon('parentCompany')}
                </button>
              </th>
              <th className="px-2 py-3 text-center w-[50px]">
                <button onClick={() => handleSort('trademarks')} className="flex items-center justify-center gap-1 hover:text-gray-900 w-full">
                  VM {getSortIcon('trademarks')}
                </button>
              </th>
              <th className="px-2 py-3 text-center w-[50px]">ÅR</th>
              <th className="px-2 py-3 text-center w-[55px]">
                <button onClick={() => handleSort('investors')} className="flex items-center justify-center gap-1 hover:text-gray-900 w-full">
                  Inv. {getSortIcon('investors')}
                </button>
              </th>
              <th className="px-2 py-3 text-center w-[50px]">
                <button onClick={() => handleSort('announcements')} className="flex items-center justify-center gap-1 hover:text-gray-900 w-full">
                  Kung. {getSortIcon('announcements')}
                </button>
              </th>
              <th className="px-2 py-3 text-center w-[45px]">Em.</th>
              <th className="px-2 py-3 w-[60px]"></th>
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
                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    {company.logo_url ? (
                      <img
                        src={company.logo_url}
                        alt=""
                        className="w-7 h-7 rounded-lg object-contain bg-gray-100 p-0.5"
                      />
                    ) : (
                      <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center font-semibold text-xs"
                        style={{
                          backgroundColor: getLogoColor(company.name).bg,
                          color: getLogoColor(company.name).text
                        }}
                      >
                        {company.name.charAt(0)}
                      </div>
                    )}
                    <div className="min-w-0">
                      <div className="font-medium text-gray-900 text-sm truncate max-w-[140px]">
                        {company.name}
                      </div>
                      <div className="text-[10px] text-gray-400 font-mono">{company.orgnr}</div>
                    </div>
                  </div>
                </td>

                {/* Sector */}
                <td className="px-2 py-2">
                  {company.sector ? (
                    <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 truncate max-w-[110px]">
                      {company.sector}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* CEO */}
                <td className="px-2 py-2">
                  {company.ceo_name ? (
                    <span className="text-xs text-gray-700 truncate max-w-[110px] block">{company.ceo_name}</span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Chairman */}
                <td className="px-2 py-2">
                  {company.chairman_name ? (
                    <span className="text-xs text-gray-700 truncate max-w-[90px] block">{company.chairman_name}</span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Board Count */}
                <td className="px-2 py-2 text-center">
                  {company.board_members && company.board_members.length > 0 ? (
                    <span
                      className="inline-flex items-center gap-0.5 text-xs text-gray-600"
                      title={company.board_members.join(', ')}
                    >
                      <UserCheck className="w-3 h-3" />
                      {company.board_members.length}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Turnover 2024 */}
                <td className="px-2 py-2 text-right">
                  <span className="font-medium text-gray-900 text-xs tabular-nums">
                    {formatCurrency(company.turnover_2024_sek)}
                  </span>
                </td>

                {/* Turnover 2023 */}
                <td className="px-2 py-2 text-right">
                  <span className="text-xs text-gray-600 tabular-nums">
                    {formatCurrency(company.turnover_2023_sek)}
                  </span>
                </td>

                {/* EBIT 2023 */}
                <td className="px-2 py-2 text-right">
                  <span className={`text-xs tabular-nums ${
                    company.ebit_2023_sek && company.ebit_2023_sek < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {formatCurrency(company.ebit_2023_sek)}
                  </span>
                </td>

                {/* EBIT 2024 */}
                <td className="px-2 py-2 text-right">
                  <span className={`text-xs tabular-nums ${
                    company.ebit_2024_sek && company.ebit_2024_sek < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {formatCurrency(company.ebit_2024_sek)}
                  </span>
                </td>

                {/* Growth */}
                <td className="px-2 py-2 text-right">
                  {company.growth_2023_2024_percent !== null ? (
                    <span className={`inline-flex items-center gap-0.5 font-medium text-xs tabular-nums ${
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
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Equity Ratio (Soliditet) */}
                <td className="px-2 py-2 text-right">
                  {company.equity_ratio !== null ? (
                    <span className={`inline-flex items-center gap-0.5 text-xs tabular-nums ${
                      company.equity_ratio >= 30 ? 'text-green-600' : company.equity_ratio >= 15 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      <Percent className="w-3 h-3" />
                      {company.equity_ratio.toFixed(0)}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Total Funding */}
                <td className="px-2 py-2 text-right">
                  <span className="text-xs text-gray-600 tabular-nums">
                    {formatCurrency(company.total_funding_sek)}
                  </span>
                </td>

                {/* Latest Round */}
                <td className="px-2 py-2 text-right">
                  <span className="text-xs text-gray-600 tabular-nums">
                    {formatCurrency(company.latest_funding_round_sek)}
                  </span>
                </td>

                {/* Latest Funding Date */}
                <td className="px-2 py-2 text-center">
                  <span className="text-xs text-gray-500">
                    {formatDate(company.latest_funding_date)}
                  </span>
                </td>

                {/* Valuation */}
                <td className="px-2 py-2 text-right">
                  <span className="text-xs text-gray-600 tabular-nums">
                    {formatCurrency(company.latest_valuation_sek)}
                  </span>
                </td>

                {/* Employees */}
                <td className="px-2 py-2 text-right">
                  {company.num_employees ? (
                    <span className="text-xs text-gray-600 tabular-nums">{company.num_employees}</span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* City */}
                <td className="px-2 py-2">
                  {company.city ? (
                    <span className="text-xs text-gray-600 truncate max-w-[70px] block">{company.city}</span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* SNI Code */}
                <td className="px-2 py-2">
                  {company.industries && company.industries.length > 0 ? (
                    <span
                      className="text-xs text-gray-600 truncate max-w-[50px] block font-mono"
                      title={`${company.industries[0].sniCode}: ${company.industries[0].sniDescription || ''}`}
                    >
                      {company.industries[0].sniCode}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Parent Company / Group */}
                <td className="px-2 py-2">
                  {(company.parent_name || company.group_top_name) ? (
                    <span
                      className="inline-flex items-center gap-0.5 text-xs text-gray-600 truncate max-w-[80px]"
                      title={company.group_top_name || company.parent_name || ''}
                    >
                      <Building className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate">{company.parent_name || company.group_top_name}</span>
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Trademarks */}
                <td className="px-2 py-2 text-center">
                  {company.trademarks && company.trademarks.length > 0 ? (
                    <span className="inline-flex items-center gap-0.5 text-xs text-amber-700">
                      <Award className="w-3 h-3" />
                      {company.trademarks.length}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Annual Report */}
                <td className="px-2 py-2 text-center">
                  {company.annual_report_year ? (
                    <a
                      href={`https://www.allabolag.se/${company.orgnr}/arsredovisning`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-0.5 text-xs text-blue-600 hover:text-blue-800"
                      title={`Årsredovisning ${company.annual_report_year}`}
                    >
                      <FileText className="w-3 h-3" />
                      {company.annual_report_year}
                    </a>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Investors */}
                <td className="px-2 py-2 text-center">
                  {company.investors && company.investors.length > 0 ? (
                    <span
                      className="inline-flex items-center gap-0.5 text-xs text-purple-700"
                      title={company.investors.map(i => i.name).join(', ')}
                    >
                      <Users className="w-3 h-3" />
                      {company.investors.length}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Announcements */}
                <td className="px-2 py-2 text-center">
                  {company.announcement_count > 0 ? (
                    <span
                      className="inline-flex items-center gap-0.5 text-xs text-orange-600"
                      title={`${company.announcement_count} kungörelser${company.latest_announcement_date ? `, senast ${formatDate(company.latest_announcement_date)}` : ''}`}
                    >
                      <Bell className="w-3 h-3" />
                      {company.announcement_count}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Equity Offering */}
                <td className="px-2 py-2 text-center">
                  {company.equity_offering ? (
                    <span
                      className="inline-flex items-center gap-0.5 text-xs text-green-700 font-medium"
                      title={`${company.equity_offering.offeringType}${company.equity_offering.amountSek ? ` - ${formatCurrency(company.equity_offering.amountSek)}` : ''}`}
                    >
                      <DollarSign className="w-3 h-3" />
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Actions */}
                <td className="px-2 py-2">
                  <div className="flex items-center gap-0.5">
                    {company.linkedin_url && (
                      <a
                        href={company.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="p-1 rounded text-gray-400 hover:text-blue-700 hover:bg-blue-50 transition-colors"
                        title="LinkedIn"
                      >
                        <Linkedin className="w-3 h-3" />
                      </a>
                    )}
                    {company.website && (
                      <a
                        href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="p-1 rounded text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                        title="Webbplats"
                      >
                        <Globe className="w-3 h-3" />
                      </a>
                    )}
                    <a
                      href={`https://www.allabolag.se/${company.orgnr}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="p-1 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                      title="Alla Bolag"
                    >
                      <ExternalLink className="w-3 h-3" />
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
