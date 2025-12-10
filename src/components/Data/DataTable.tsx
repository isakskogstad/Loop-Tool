import { TrendingUp, TrendingDown, ExternalLink, ChevronUp, ChevronDown, ChevronsUpDown, Globe, FileText, Award, Users, Linkedin, Bell, DollarSign, Percent, UserCheck, Building, Filter, Download, ChevronLeft, ChevronRight } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'
import { useMapContext } from '../../context/MapContext'
import { useState, useMemo, useEffect } from 'react'

interface DataTableProps {
  companies: CompanyWithCoords[]
  isLoading?: boolean
}

type SortField = 'name' | 'sector' | 'turnover' | 'turnover2023' | 'ebit2023' | 'ebit2024' | 'growth' | 'funding' | 'latestRound' | 'valuation' | 'city' | 'ceo' | 'chairman' | 'boardCount' | 'employees' | 'trademarks' | 'annualReport' | 'investors' | 'equityRatio' | 'announcements' | 'sniCode' | 'parentCompany' | 'ownerCount'
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
  // Always show in millions (mkr) for consistency
  // Values under 1 million show in tkr (thousands)
  if (value >= 1_000_000_000) {
    // Billions - show as "X XXX mkr" for consistency
    const mkr = value / 1_000_000
    return `${mkr.toLocaleString('sv-SE', { maximumFractionDigits: 0 })} mkr`
  }
  if (value >= 1_000_000) {
    const mkr = value / 1_000_000
    // Show decimal for small millions
    if (mkr < 10) {
      return `${mkr.toLocaleString('sv-SE', { maximumFractionDigits: 1 })} mkr`
    }
    return `${Math.round(mkr).toLocaleString('sv-SE')} mkr`
  }
  if (value >= 1_000) {
    return `${Math.round(value / 1_000).toLocaleString('sv-SE')} tkr`
  }
  return `${value.toLocaleString('sv-SE')} kr`
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '-'
  // Swedish format: number followed by % with space (e.g., "+15,5 %")
  const formatted = value.toLocaleString('sv-SE', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  return `${value >= 0 ? '+' : ''}${formatted} %`
}

function formatDate(date: string | null): string {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('sv-SE', { year: 'numeric', month: 'short' })
}

// Capitalize names/cities properly (e.g., "STOCKHOLM" -> "Stockholm", "malmö" -> "Malmö")
function formatName(value: string | null): string {
  if (!value) return '-'
  // Handle all-caps or all-lowercase
  return value
    .toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
    .split('-')
    .map((part, i) => i === 0 ? part : part.charAt(0).toUpperCase() + part.slice(1))
    .join('-')
}

// Sector color mapping for subtle color coding
const SECTOR_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Climate Tech': { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  'Health Tech': { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200' },
  'Fintech': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  'EdTech': { bg: 'bg-violet-50', text: 'text-violet-700', border: 'border-violet-200' },
  'Impact': { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  'PropTech': { bg: 'bg-cyan-50', text: 'text-cyan-700', border: 'border-cyan-200' },
  'FoodTech': { bg: 'bg-lime-50', text: 'text-lime-700', border: 'border-lime-200' },
  'Mobility': { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200' },
  'CleanTech': { bg: 'bg-teal-50', text: 'text-teal-700', border: 'border-teal-200' },
  'AgTech': { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  'SaaS': { bg: 'bg-sky-50', text: 'text-sky-700', border: 'border-sky-200' },
  'AI': { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  'E-commerce': { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
}

function getSectorColor(sector: string | null) {
  if (!sector) return { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' }
  // Check for exact match first
  if (SECTOR_COLORS[sector]) return SECTOR_COLORS[sector]
  // Check for partial matches (e.g., "Climate" matches "Climate Tech")
  for (const [key, value] of Object.entries(SECTOR_COLORS)) {
    if (sector.toLowerCase().includes(key.toLowerCase()) || key.toLowerCase().includes(sector.toLowerCase())) {
      return value
    }
  }
  // Default color
  return { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' }
}

// Skeleton Row for loading state
function SkeletonRow({ columns }: { columns: number }) {
  return (
    <tr className="border-t border-gray-100 animate-pulse">
      <td className="px-4 py-4 sticky left-0 bg-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gray-200" />
          <div className="space-y-2">
            <div className="h-4 w-32 bg-gray-200 rounded" />
            <div className="h-3 w-20 bg-gray-100 rounded" />
          </div>
        </div>
      </td>
      {Array.from({ length: columns - 1 }).map((_, i) => (
        <td key={i} className="px-3 py-4">
          <div className="h-4 w-16 bg-gray-200 rounded ml-auto" />
        </td>
      ))}
    </tr>
  )
}

// Empty State component
function EmptyState({ message, onClear }: { message: string; onClear?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <Filter className="w-8 h-8 text-gray-400" />
      </div>
      <p className="text-gray-500 text-sm mb-4">{message}</p>
      {onClear && (
        <button
          onClick={onClear}
          className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
        >
          Rensa filter
        </button>
      )}
    </div>
  )
}

// Pagination component
function Pagination({
  page,
  pageSize,
  total,
  onPageChange
}: {
  page: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
}) {
  const totalPages = Math.ceil(total / pageSize)

  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible + 2) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)

      let start = Math.max(2, page - 1)
      let end = Math.min(totalPages - 1, page + 1)

      if (page <= 3) end = Math.min(maxVisible, totalPages - 1)
      if (page >= totalPages - 2) start = Math.max(2, totalPages - maxVisible + 1)

      if (start > 2) pages.push('ellipsis')
      for (let i = start; i <= end; i++) pages.push(i)
      if (end < totalPages - 1) pages.push('ellipsis')
      if (totalPages > 1) pages.push(totalPages)
    }

    return pages
  }

  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between">
      <p className="text-sm text-gray-500">
        Sida {page} av {totalPages}
        <span className="hidden sm:inline"> · {total.toLocaleString('sv-SE')} företag</span>
      </p>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {getPageNumbers().map((p, i) =>
          p === 'ellipsis' ? (
            <span key={`ellipsis-${i}`} className="px-2 text-gray-400">...</span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                page === p
                  ? 'bg-gray-900 text-white font-medium'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {p}
            </button>
          )
        )}

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

export function DataTable({ companies, isLoading = false }: DataTableProps) {
  const { filters, setFilters, setSelectedCompany } = useMapContext()
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)
  const [expandedBoards, setExpandedBoards] = useState<Set<string>>(new Set())
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 50

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [filters.search, filters.sector])

  const toggleBoardExpand = (orgnr: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setExpandedBoards(prev => {
      const next = new Set(prev)
      if (next.has(orgnr)) {
        next.delete(orgnr)
      } else {
        next.add(orgnr)
      }
      return next
    })
  }

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
          case 'ownerCount':
            comparison = (a.owners?.length || 0) - (b.owners?.length || 0)
            break
        }
        return sortDirection === 'asc' ? comparison : -comparison
      })
    }

    return result
  }, [companies, filters.sector, filters.search, sortField, sortDirection])

  // Paginate data
  const paginatedCompanies = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return sortedAndFilteredCompanies.slice(start, start + pageSize)
  }, [sortedAndFilteredCompanies, currentPage, pageSize])

  // Clear all filters
  const handleClearFilters = () => {
    setFilters({ search: '', sector: null })
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">
            {sortedAndFilteredCompanies.length.toLocaleString('sv-SE')} företag
            {(filters.search || filters.sector) && (
              <span className="text-gray-400"> (filtrerat)</span>
            )}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {(filters.search || filters.sector) && (
            <button
              onClick={handleClearFilters}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Filter className="w-3.5 h-3.5" />
              Rensa filter
            </button>
          )}
          <button
            onClick={() => {
              // Export to CSV
              const headers = ['Företag', 'Orgnr', 'Sektor', 'VD', 'Stad', 'Omsättning 2024', 'EBIT 2024', 'Tillväxt', 'Anställda', 'Webbplats']
              const rows = sortedAndFilteredCompanies.map(c => [
                c.name,
                c.orgnr,
                c.sector || '',
                c.ceo_name || '',
                c.city || '',
                c.turnover_2024_sek || '',
                c.ebit_2024_sek || '',
                c.growth_2023_2024_percent || '',
                c.num_employees || '',
                c.website || ''
              ])
              const csv = [headers, ...rows].map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')).join('\n')
              const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `loop-foretag-${new Date().toISOString().split('T')[0]}.csv`
              a.click()
              URL.revokeObjectURL(url)
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Exportera CSV
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto flex-1">
        <table className="w-full min-w-[2200px]">
          <thead className="sticky top-0 bg-gray-50 border-b border-gray-200 z-10">
            <tr className="text-sm font-semibold text-gray-600">
              {/* Företag - Sticky */}
              <th className="px-4 py-4 text-left w-[220px] sticky left-0 bg-gray-50 z-20 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]">
                <button onClick={() => handleSort('name')} className="flex items-center gap-1.5 hover:text-gray-900">
                  Företag {getSortIcon('name')}
                </button>
              </th>
              <th className="px-3 py-4 text-left w-[120px]">
                <button onClick={() => handleSort('sector')} className="flex items-center gap-1.5 hover:text-gray-900">
                  Sektor {getSortIcon('sector')}
                </button>
              </th>
              <th className="px-3 py-4 text-left w-[130px]">
                <button onClick={() => handleSort('ceo')} className="flex items-center gap-1.5 hover:text-gray-900">
                  VD {getSortIcon('ceo')}
                </button>
              </th>
              <th className="px-3 py-4 text-left w-[120px]">
                <button onClick={() => handleSort('chairman')} className="flex items-center gap-1.5 hover:text-gray-900">
                  Ordförande {getSortIcon('chairman')}
                </button>
              </th>
              <th className="px-3 py-4 text-center w-[70px]">
                <button onClick={() => handleSort('boardCount')} className="flex items-center justify-center gap-1.5 hover:text-gray-900 w-full">
                  Styrelse {getSortIcon('boardCount')}
                </button>
              </th>
              <th className="px-3 py-4 text-center w-[80px]">
                <button onClick={() => handleSort('ownerCount')} className="flex items-center justify-center gap-1.5 hover:text-gray-900 w-full">
                  Ägare {getSortIcon('ownerCount')}
                </button>
              </th>
              {/* VÄRDERING & FUNDING FÖRST - Viktig investeringsdata */}
              <th className="px-3 py-4 text-right w-[100px] bg-emerald-50/50">
                <button onClick={() => handleSort('valuation')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Värdering {getSortIcon('valuation')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[100px] bg-emerald-50/50">
                <button onClick={() => handleSort('funding')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Funding {getSortIcon('funding')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[100px] bg-emerald-50/50">
                <button onClick={() => handleSort('latestRound')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Sen. Runda {getSortIcon('latestRound')}
                </button>
              </th>
              <th className="px-3 py-4 text-center w-[90px] bg-emerald-50/50">
                Runda Datum
              </th>
              {/* NYCKELTAL */}
              <th className="px-3 py-4 text-right w-[100px]">
                <button onClick={() => handleSort('turnover')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Oms 2024 {getSortIcon('turnover')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[100px]">
                <button onClick={() => handleSort('turnover2023')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Oms 2023 {getSortIcon('turnover2023')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[90px]">
                <button onClick={() => handleSort('ebit2023')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  EBIT 2023 {getSortIcon('ebit2023')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[90px]">
                <button onClick={() => handleSort('ebit2024')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  EBIT 2024 {getSortIcon('ebit2024')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[80px]">
                <button onClick={() => handleSort('growth')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Tillväxt {getSortIcon('growth')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[70px]">
                <button onClick={() => handleSort('equityRatio')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Soliditet {getSortIcon('equityRatio')}
                </button>
              </th>
              <th className="px-3 py-4 text-right w-[70px]">
                <button onClick={() => handleSort('employees')} className="flex items-center justify-end gap-1.5 hover:text-gray-900 w-full">
                  Anställda {getSortIcon('employees')}
                </button>
              </th>
              <th className="px-3 py-4 text-left w-[90px]">
                <button onClick={() => handleSort('city')} className="flex items-center gap-1.5 hover:text-gray-900">
                  Stad {getSortIcon('city')}
                </button>
              </th>
              <th className="px-3 py-4 text-left w-[60px]">
                <button onClick={() => handleSort('sniCode')} className="flex items-center gap-1.5 hover:text-gray-900">
                  SNI {getSortIcon('sniCode')}
                </button>
              </th>
              <th className="px-3 py-4 text-center w-[60px]" title="Varumärken">
                <button onClick={() => handleSort('trademarks')} className="flex items-center justify-center gap-1.5 hover:text-gray-900 w-full">
                  VM {getSortIcon('trademarks')}
                </button>
              </th>
              <th className="px-3 py-4 text-center w-[50px]" title="Årsredovisning">ÅR</th>
              <th className="px-3 py-4 text-center w-[70px]" title="Investerare">
                <button onClick={() => handleSort('investors')} className="flex items-center justify-center gap-1.5 hover:text-gray-900 w-full">
                  Inv {getSortIcon('investors')}
                </button>
              </th>
              <th className="px-3 py-4 text-center w-[60px]" title="Kungörelser">
                <button onClick={() => handleSort('announcements')} className="flex items-center justify-center gap-1.5 hover:text-gray-900 w-full">
                  Kung {getSortIcon('announcements')}
                </button>
              </th>
              <th className="px-3 py-4 text-center w-[50px]" title="Emission">Em</th>
              {/* KONCERN - Sist */}
              <th className="px-3 py-4 text-left w-[100px]">
                <button onClick={() => handleSort('parentCompany')} className="flex items-center gap-1.5 hover:text-gray-900">
                  Koncern {getSortIcon('parentCompany')}
                </button>
              </th>
              {/* LÄNKAR */}
              <th className="px-3 py-4 w-[120px] text-center">Länkar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {/* Loading State */}
            {isLoading && Array.from({ length: 10 }).map((_, i) => (
              <SkeletonRow key={`skeleton-${i}`} columns={26} />
            ))}

            {/* Data Rows */}
            {!isLoading && paginatedCompanies.map((company, index) => (
              <tr
                key={company.orgnr}
                onClick={() => setSelectedCompany(company)}
                className={`cursor-pointer transition-colors hover:bg-gray-50 ${
                  index % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'
                }`}
              >
                {/* Company Name - Sticky */}
                <td className={`px-4 py-4 sticky left-0 z-10 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)] ${
                  index % 2 === 0 ? 'bg-white' : 'bg-gray-50/80'
                }`}>
                  <div className="flex items-center gap-3">
                    {company.logo_url ? (
                      <img
                        src={company.logo_url}
                        alt=""
                        className="w-10 h-10 rounded-xl object-contain bg-gray-50 p-1 flex-shrink-0 border border-gray-100"
                      />
                    ) : (
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-base flex-shrink-0"
                        style={{
                          backgroundColor: getLogoColor(company.name).bg,
                          color: getLogoColor(company.name).text
                        }}
                      >
                        {company.name.charAt(0)}
                      </div>
                    )}
                    <div className="min-w-0">
                      <div className="font-semibold text-gray-900 text-sm truncate max-w-[150px]">
                        {company.name}
                      </div>
                      <div className="text-[11px] text-gray-400 font-mono mt-1">{company.orgnr}</div>
                    </div>
                  </div>
                </td>

                {/* Sector */}
                <td className="px-3 py-4">
                  {company.sector ? (
                    <span className={`inline-block px-2.5 py-1 rounded-md text-xs font-medium border ${getSectorColor(company.sector).bg} ${getSectorColor(company.sector).text} ${getSectorColor(company.sector).border} truncate max-w-[110px]`}>
                      {company.sector}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* CEO */}
                <td className="px-3 py-3">
                  {company.ceo_name ? (
                    <span className="text-xs text-gray-700 truncate max-w-[110px] block">{formatName(company.ceo_name)}</span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Chairman */}
                <td className="px-3 py-3">
                  {company.chairman_name ? (
                    <span className="text-xs text-gray-700 truncate max-w-[90px] block">{formatName(company.chairman_name)}</span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Board Count - Expandable */}
                <td className="px-2 py-2">
                  {company.board_members && company.board_members.length > 0 ? (
                    <div className="relative">
                      <button
                        onClick={(e) => toggleBoardExpand(company.orgnr, e)}
                        className="inline-flex items-center gap-0.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-1 py-0.5 rounded transition-colors"
                        title="Klicka för att visa styrelseledamöter"
                      >
                        <UserCheck className="w-3 h-3" />
                        {company.board_members.length}
                      </button>
                      {expandedBoards.has(company.orgnr) && (
                        <div className="absolute left-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-lg shadow-lg p-2 min-w-[180px]">
                          <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wide mb-1">Styrelse</div>
                          <ul className="space-y-0.5">
                            {company.board_members.map((member, i) => (
                              <li key={i} className="text-xs text-gray-700">{member}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* Owners - Expandable like board */}
                <td className="px-2 py-2">
                  {company.owners && company.owners.length > 0 ? (
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setExpandedBoards(prev => {
                            const key = `owners-${company.orgnr}`
                            const next = new Set(prev)
                            if (next.has(key)) next.delete(key)
                            else next.add(key)
                            return next
                          })
                        }}
                        className="inline-flex items-center gap-0.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 px-1 py-0.5 rounded transition-colors"
                        title="Klicka för att visa ägare"
                      >
                        <Users className="w-3 h-3" />
                        {company.owners.length}
                      </button>
                      {expandedBoards.has(`owners-${company.orgnr}`) && (
                        <div className="absolute left-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-lg shadow-lg p-2 min-w-[220px]">
                          <div className="text-[10px] font-medium text-gray-500 uppercase tracking-wide mb-1">Huvudägare</div>
                          <ul className="space-y-1">
                            {company.owners.slice(0, 5).map((owner, i) => (
                              <li key={i} className="text-xs text-gray-700 flex justify-between gap-2">
                                <span className="truncate">{formatName(owner.name)}</span>
                                {owner.percent && (
                                  <span className="text-gray-500 font-mono whitespace-nowrap">{owner.percent.toFixed(1)} %</span>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* VÄRDERING & FUNDING FÖRST - Viktig investeringsdata (med subtil bakgrund) */}
                {/* Valuation */}
                <td className="px-2 py-2 text-right bg-emerald-50/30">
                  <span className="font-semibold text-emerald-800 text-xs tabular-nums">
                    {formatCurrency(company.latest_valuation_sek)}
                  </span>
                </td>

                {/* Total Funding */}
                <td className="px-2 py-2 text-right bg-emerald-50/30">
                  <span className="text-xs text-emerald-700 tabular-nums">
                    {formatCurrency(company.total_funding_sek)}
                  </span>
                </td>

                {/* Latest Round */}
                <td className="px-2 py-2 text-right bg-emerald-50/30">
                  <span className="text-xs text-emerald-700 tabular-nums">
                    {formatCurrency(company.latest_funding_round_sek)}
                  </span>
                </td>

                {/* Latest Funding Date */}
                <td className="px-2 py-2 text-center bg-emerald-50/30">
                  <span className="text-xs text-emerald-600">
                    {formatDate(company.latest_funding_date)}
                  </span>
                </td>

                {/* NYCKELTAL */}
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

                {/* Employees */}
                <td className="px-2 py-2 text-right">
                  {company.num_employees ? (
                    <span className="text-xs text-gray-700 tabular-nums font-medium">
                      {company.num_employees.toLocaleString('sv-SE')}
                    </span>
                  ) : (
                    <span className="text-gray-300 text-xs">-</span>
                  )}
                </td>

                {/* City */}
                <td className="px-2 py-2">
                  {company.city ? (
                    <span className="text-xs text-gray-600 truncate max-w-[70px] block">{formatName(company.city)}</span>
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

                {/* KONCERN - Sist */}
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

                {/* LÄNKAR - Större och tydligare knappar */}
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    {company.website && (
                      <a
                        href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-colors"
                        title="Webbplats"
                      >
                        <Globe className="w-3.5 h-3.5" />
                        Webb
                      </a>
                    )}
                    {company.linkedin_url && (
                      <a
                        href={company.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-colors"
                        title="LinkedIn"
                      >
                        <Linkedin className="w-3.5 h-3.5" />
                      </a>
                    )}
                    <a
                      href={`https://www.allabolag.se/${company.orgnr}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 border border-gray-200 transition-colors"
                      title="Alla Bolag"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Info
                    </a>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Empty State */}
        {!isLoading && sortedAndFilteredCompanies.length === 0 && (
          <EmptyState
            message="Inga företag matchar din sökning"
            onClear={(filters.search || filters.sector) ? handleClearFilters : undefined}
          />
        )}
      </div>

      {/* Footer with Pagination */}
      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50">
        <Pagination
          page={currentPage}
          pageSize={pageSize}
          total={sortedAndFilteredCompanies.length}
          onPageChange={setCurrentPage}
        />
      </div>
    </div>
  )
}
