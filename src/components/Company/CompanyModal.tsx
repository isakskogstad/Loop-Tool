import { useState, useEffect, useCallback } from 'react'
import { X, MapPin, TrendingUp, TrendingDown, Users, Globe, ExternalLink, Building2, ChevronDown, Briefcase, DollarSign, PieChart, Calendar, Award, Linkedin } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'

// -----------------------------------------------------------------------------
// HELPER FUNCTIONS
// -----------------------------------------------------------------------------

const formatNumber = (num: number | undefined | null, suffix?: string): string => {
  if (num === undefined || num === null) return '-'
  if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(1)} mdr${suffix ? ' ' + suffix : ''}`
  if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(0)} mkr${suffix ? ' ' + suffix : ''}`
  if (Math.abs(num) >= 1e3) return `${(num / 1e3).toFixed(0)} tkr${suffix ? ' ' + suffix : ''}`
  return `${num}${suffix ? ' ' + suffix : ''}`
}

const formatPercent = (num: number | undefined | null): string => {
  if (num === undefined || num === null) return '-'
  const prefix = num > 0 ? '+' : ''
  return `${prefix}${num.toFixed(1)}%`
}

const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

// -----------------------------------------------------------------------------
// SUB-COMPONENTS
// -----------------------------------------------------------------------------

interface StatCardProps {
  label: string
  value: string
  trend?: number | null
  highlight?: boolean
}

const StatCard: React.FC<StatCardProps> = ({ label, value, trend, highlight }) => {
  const isPositive = trend !== undefined && trend !== null && trend > 0
  const isNegative = trend !== undefined && trend !== null && trend < 0

  return (
    <div className={`text-center p-4 rounded-2xl transition-colors ${highlight ? 'bg-emerald-50' : 'bg-gray-50'}`}>
      <p className={`text-2xl font-bold font-display ${highlight ? 'text-emerald-600' : isNegative ? 'text-red-600' : 'text-gray-900'}`}>
        {value}
      </p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
      {trend !== undefined && trend !== null && (
        <div className={`flex items-center justify-center gap-0.5 mt-1 text-xs font-medium ${isPositive ? 'text-emerald-600' : isNegative ? 'text-red-600' : 'text-gray-400'}`}>
          {isPositive ? <TrendingUp className="w-3 h-3" /> : isNegative ? <TrendingDown className="w-3 h-3" /> : null}
          <span>{formatPercent(trend)}</span>
        </div>
      )}
    </div>
  )
}

interface PersonCardProps {
  name: string
  role: string
  variant?: 'primary' | 'secondary'
}

const PersonCard: React.FC<PersonCardProps> = ({ name, role, variant = 'secondary' }) => (
  <div className="p-4 bg-gray-50 rounded-xl">
    <p className="text-xs text-gray-500 mb-3">{role}</p>
    <div className="flex items-center gap-3">
      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${variant === 'primary' ? 'bg-emerald-100' : 'bg-gray-200'}`}>
        <span className={`text-base font-semibold ${variant === 'primary' ? 'text-emerald-700' : 'text-gray-600'}`}>
          {getInitials(name)}
        </span>
      </div>
      <p className="font-medium text-gray-900">{name}</p>
    </div>
  </div>
)

interface OwnershipBarProps {
  owners: Array<{ name: string; percent: number | null }>
}

const OwnershipBar: React.FC<OwnershipBarProps> = ({ owners }) => {
  const colors = ['bg-emerald-500', 'bg-teal-400', 'bg-cyan-400', 'bg-blue-400', 'bg-indigo-400', 'bg-purple-400', 'bg-pink-400']
  const validOwners = owners.filter(o => o.percent !== null)

  return (
    <div>
      <div className="flex h-3 rounded-full overflow-hidden bg-gray-100">
        {validOwners.map((owner, index) => (
          <div
            key={owner.name}
            className={`${colors[index % colors.length]} transition-all duration-300`}
            style={{ width: `${owner.percent}%` }}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3">
        {validOwners.map((owner, index) => (
          <div key={owner.name} className="flex items-center gap-1.5 text-xs">
            <span className={`w-2 h-2 rounded-full ${colors[index % colors.length]}`} />
            <span className="text-gray-600">{owner.name}</span>
            <span className="font-medium text-gray-900">{owner.percent?.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

interface SectionHeaderProps {
  title: string
  icon?: React.ReactNode
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ title, icon }) => (
  <div className="flex items-center gap-2 mb-3">
    {icon && <span className="text-gray-400">{icon}</span>}
    <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{title}</h3>
  </div>
)

interface InfoRowProps {
  label: string
  value: React.ReactNode
}

const InfoRow: React.FC<InfoRowProps> = ({ label, value }) => (
  <div className="flex justify-between py-1">
    <span className="text-sm text-gray-500">{label}</span>
    <span className="text-sm font-medium text-gray-900">{value}</span>
  </div>
)

// -----------------------------------------------------------------------------
// TAB COMPONENTS
// -----------------------------------------------------------------------------

type TabId = 'overview' | 'financials' | 'people' | 'ownership'

interface Tab {
  id: TabId
  label: string
}

const tabs: Tab[] = [
  { id: 'overview', label: 'Översikt' },
  { id: 'financials', label: 'Finansiellt' },
  { id: 'people', label: 'Ledning' },
  { id: 'ownership', label: 'Ägare' },
]

interface TabNavProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
}

const TabNav: React.FC<TabNavProps> = ({ activeTab, onTabChange }) => (
  <div className="flex gap-1 p-1 bg-gray-100 rounded-xl">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        onClick={() => onTabChange(tab.id)}
        className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
          activeTab === tab.id
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        {tab.label}
      </button>
    ))}
  </div>
)

// -----------------------------------------------------------------------------
// TAB CONTENT COMPONENTS
// -----------------------------------------------------------------------------

import type { CompanyWithCoords } from '../../lib/supabase'

interface TabContentProps {
  company: CompanyWithCoords
}

const OverviewTab: React.FC<TabContentProps> = ({ company }) => {
  const foundedYear = company.foundation_date ? new Date(company.foundation_date).getFullYear() : null

  return (
    <div className="space-y-6">
      {/* Quick stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Omsättning" value={formatNumber(company.turnover_2024_sek)} />
        <StatCard label="EBIT" value={formatNumber(company.ebit_2024_sek)} />
        <StatCard
          label="Tillväxt"
          value={formatPercent(company.growth_2023_2024_percent)}
          highlight={company.growth_2023_2024_percent !== null && company.growth_2023_2024_percent > 0}
        />
        <StatCard label="Anställda" value={company.num_employees?.toString() || '-'} />
      </div>

      {/* Two column layout */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Left: Company info */}
        <div>
          <SectionHeader title="Företagsinfo" icon={<Building2 className="w-4 h-4" />} />
          <div className="space-y-1">
            {company.city && (
              <InfoRow
                label="Stad"
                value={
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-gray-400" />
                    {company.city}{company.county ? `, ${company.county}` : ''}
                  </span>
                }
              />
            )}
            {foundedYear && <InfoRow label="Grundat" value={foundedYear} />}
            {company.sector && <InfoRow label="Sektor" value={company.sector} />}
            <InfoRow label="Org.nr" value={<span className="font-mono text-xs">{company.orgnr}</span>} />
          </div>
        </div>

        {/* Right: Leadership preview */}
        <div>
          <SectionHeader title="Ledning" icon={<Users className="w-4 h-4" />} />
          <div className="space-y-2">
            {company.ceo_name && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                  <span className="text-xs font-medium text-emerald-700">{getInitials(company.ceo_name)}</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{company.ceo_name}</p>
                  <p className="text-xs text-gray-500">VD</p>
                </div>
              </div>
            )}
            {company.chairman_name && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                  <span className="text-xs font-medium text-gray-600">{getInitials(company.chairman_name)}</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{company.chairman_name}</p>
                  <p className="text-xs text-gray-500">Ordförande</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ownership preview */}
      {company.owners && company.owners.length > 0 && (
        <div>
          <SectionHeader title="Ägare" icon={<PieChart className="w-4 h-4" />} />
          <OwnershipBar owners={company.owners} />
        </div>
      )}

      {/* Description */}
      {company.purpose && (
        <details className="group">
          <summary className="flex items-center justify-between cursor-pointer">
            <SectionHeader title="Verksamhetsbeskrivning" />
            <ChevronDown className="w-4 h-4 text-gray-400 group-open:rotate-180 transition-transform" />
          </summary>
          <p className="mt-2 text-sm text-gray-600 leading-relaxed">{company.purpose}</p>
        </details>
      )}
    </div>
  )
}

const FinancialsTab: React.FC<TabContentProps> = ({ company }) => {
  return (
    <div className="space-y-6">
      {/* Main metrics 2024 */}
      <div>
        <SectionHeader title="Finansiellt 2024" icon={<Briefcase className="w-4 h-4" />} />
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-xs text-gray-500 mb-1">Omsättning</p>
            <p className="text-2xl font-bold text-gray-900 font-display">{formatNumber(company.turnover_2024_sek)}</p>
            {company.growth_2023_2024_percent !== null && (
              <div className={`flex items-center gap-1 mt-1 text-sm font-medium ${company.growth_2023_2024_percent > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {company.growth_2023_2024_percent > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                <span>{formatPercent(company.growth_2023_2024_percent)} vs föregående år</span>
              </div>
            )}
          </div>

          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-xs text-gray-500 mb-1">EBIT</p>
            <p className={`text-2xl font-bold font-display ${company.ebit_2024_sek && company.ebit_2024_sek < 0 ? 'text-red-600' : 'text-gray-900'}`}>
              {formatNumber(company.ebit_2024_sek)}
            </p>
          </div>
        </div>
      </div>

      {/* 2023 data */}
      {(company.turnover_2023_sek || company.ebit_2023_sek) && (
        <div>
          <SectionHeader title="Finansiellt 2023" icon={<Calendar className="w-4 h-4" />} />
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-xl">
              <p className="text-xs text-gray-500 mb-1">Omsättning</p>
              <p className="text-xl font-bold text-gray-900">{formatNumber(company.turnover_2023_sek)}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-xl">
              <p className="text-xs text-gray-500 mb-1">EBIT</p>
              <p className={`text-xl font-bold ${company.ebit_2023_sek && company.ebit_2023_sek < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                {formatNumber(company.ebit_2023_sek)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Key metrics */}
      <div>
        <SectionHeader title="Nyckeltal" />
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Anställda" value={company.num_employees?.toString() || '-'} />
          <StatCard label="Total Funding" value={formatNumber(company.total_funding_sek)} />
          <StatCard label="Värdering" value={formatNumber(company.latest_valuation_sek)} />
        </div>
      </div>

      {/* Funding */}
      {(company.total_funding_sek || company.latest_funding_round_sek) && (
        <div>
          <SectionHeader title="Finansiering" icon={<DollarSign className="w-4 h-4" />} />
          <div className="p-4 bg-emerald-50 rounded-xl">
            <p className="text-xs text-emerald-600 mb-1">Total finansiering</p>
            <p className="text-2xl font-bold text-emerald-700 font-display">{formatNumber(company.total_funding_sek)}</p>
            {company.latest_funding_round_sek && (
              <p className="text-sm text-emerald-600 mt-1">
                Senaste runda: {formatNumber(company.latest_funding_round_sek)}
                {company.latest_funding_date && ` (${new Date(company.latest_funding_date).toLocaleDateString('sv-SE')})`}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const PeopleTab: React.FC<TabContentProps> = ({ company }) => (
  <div className="space-y-6">
    {/* CEO & Chairman */}
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {company.ceo_name && <PersonCard name={company.ceo_name} role="Verkställande direktör" variant="primary" />}
      {company.chairman_name && <PersonCard name={company.chairman_name} role="Styrelseordförande" />}
    </div>

    {/* Board members */}
    {company.board_members && company.board_members.length > 0 && (
      <div>
        <SectionHeader title={`Styrelseledamöter (${company.board_members.length})`} icon={<Users className="w-4 h-4" />} />
        <div className="flex flex-wrap gap-2">
          {company.board_members.map((member: string, i: number) => (
            <span key={i} className="inline-flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-sm">
              <span className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600">
                {getInitials(member)}
              </span>
              {member}
            </span>
          ))}
        </div>
      </div>
    )}

    {/* Investors */}
    {company.investors && company.investors.length > 0 && (
      <div>
        <SectionHeader title={`Investerare (${company.investors.length})`} />
        <div className="space-y-2">
          {company.investors.map((investor, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-900 truncate">{investor.name}</p>
                {investor.type && <p className="text-xs text-gray-500">{investor.type}</p>}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {investor.isLeadInvestor && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded font-medium">Lead</span>
                )}
                {investor.investmentRound && <span className="text-xs text-gray-500">{investor.investmentRound}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
)

const OwnershipTab: React.FC<TabContentProps> = ({ company }) => {
  if (!company.owners || company.owners.length === 0) {
    return (
      <div className="text-center py-8">
        <PieChart className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">Ingen ägarinformation tillgänglig</p>
      </div>
    )
  }

  const colors = ['bg-emerald-500', 'bg-teal-400', 'bg-cyan-400', 'bg-blue-400', 'bg-indigo-400', 'bg-purple-400', 'bg-pink-400']

  return (
    <div className="space-y-6">
      {/* Ownership visualization */}
      <div>
        <SectionHeader title="Ägarfördelning" />
        <OwnershipBar owners={company.owners} />
      </div>

      {/* Detailed list */}
      <div>
        <SectionHeader title="Ägare" />
        <div className="space-y-3">
          {company.owners.map((owner: { name: string; percent: number | null }, index: number) => (
            <div key={owner.name} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg ${colors[index % colors.length]} flex items-center justify-center`}>
                  <span className="text-sm font-medium text-white">{getInitials(owner.name)}</span>
                </div>
                <p className="font-medium text-gray-900">{owner.name}</p>
              </div>
              <p className="text-lg font-bold text-gray-900">{owner.percent?.toFixed(1)}%</p>
            </div>
          ))}
        </div>
      </div>

      {/* Trademarks */}
      {company.trademarks && company.trademarks.length > 0 && (
        <div>
          <SectionHeader title={`Varumärken (${company.trademarks.length})`} icon={<Award className="w-4 h-4" />} />
          <div className="space-y-2">
            {company.trademarks.slice(0, 5).map((tm, i) => (
              <div key={i} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                <span className="text-sm text-gray-700">{tm.name}</span>
                {tm.status && (
                  <span className={`text-xs px-2 py-0.5 rounded ${tm.status === 'Registrerat' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {tm.status}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// -----------------------------------------------------------------------------
// MAIN MODAL COMPONENT
// -----------------------------------------------------------------------------

export function CompanyModal() {
  const { selectedCompany, setSelectedCompany } = useMapContext()
  const [activeTab, setActiveTab] = useState<TabId>('overview')

  // Reset tab when company changes
  useEffect(() => {
    setActiveTab('overview')
  }, [selectedCompany?.orgnr])

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedCompany(null)
    }

    if (selectedCompany) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [selectedCompany, setSelectedCompany])

  // Handle backdrop click
  const handleBackdropClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) setSelectedCompany(null)
  }, [setSelectedCompany])

  if (!selectedCompany) return null

  const company = selectedCompany

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview': return <OverviewTab company={company} />
      case 'financials': return <FinancialsTab company={company} />
      case 'people': return <PeopleTab company={company} />
      case 'ownership': return <OwnershipTab company={company} />
      default: return null
    }
  }

  return (
    <div
      className="modal-backdrop animate-fade-in"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="modal-content animate-scale-in max-w-3xl">
        {/* Header with gradient */}
        <div className="relative bg-gradient-to-r from-emerald-600 to-teal-500 px-6 py-6">
          {/* Close button */}
          <button
            onClick={() => setSelectedCompany(null)}
            className="absolute top-4 right-4 p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
            aria-label="Stäng"
          >
            <X className="w-5 h-5 text-white" />
          </button>

          {/* Company info */}
          <div className="flex items-center gap-4">
            {/* Logo/Avatar */}
            <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center shrink-0">
              {company.logo_url ? (
                <img src={company.logo_url} alt="" className="w-10 h-10 object-contain" />
              ) : (
                <span className="text-2xl font-bold text-white">{getInitials(company.name)}</span>
              )}
            </div>

            {/* Text */}
            <div className="min-w-0">
              <h2 id="modal-title" className="text-2xl font-bold text-white truncate font-display">
                {company.name}
              </h2>
              <div className="flex items-center gap-3 mt-1 flex-wrap">
                <span className="text-sm text-white/80 font-mono">{company.orgnr}</span>
                {company.sector && (
                  <span className="px-2.5 py-0.5 rounded-full bg-white/20 text-xs font-medium text-white">
                    {company.sector}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="px-6 py-4 border-b border-gray-100">
          <TabNav activeTab={activeTab} onTabChange={setActiveTab} />
        </div>

        {/* Content */}
        <div className="px-6 py-5 max-h-[50vh] overflow-y-auto">
          {renderTabContent()}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {company.website && (
              <a
                href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <Globe className="w-4 h-4" />
                Webbplats
              </a>
            )}
            {company.linkedin_url && (
              <a
                href={company.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <Linkedin className="w-4 h-4" />
                LinkedIn
              </a>
            )}
          </div>

          <a
            href={`https://www.allabolag.se/${company.orgnr}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            Visa på Allabolag
          </a>
        </div>
      </div>
    </div>
  )
}

export default CompanyModal
