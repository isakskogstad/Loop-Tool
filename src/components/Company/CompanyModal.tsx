import { X, MapPin, Calendar, TrendingUp, TrendingDown, Briefcase, Users, ExternalLink, Building2, Globe, Linkedin, FileText, Award, DollarSign, PieChart } from 'lucide-react'
import { useMapContext } from '../../context/MapContext'

// Color palette for generated logos
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
    return `${(value / 1_000_000_000).toFixed(1)} mdr kr`
  }
  if (value >= 1_000_000) {
    return `${Math.round(value / 1_000_000)} mkr`
  }
  if (value >= 1_000) {
    return `${Math.round(value / 1_000)} tkr`
  }
  return `${value} kr`
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
}

function formatDate(date: string | null): string {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('sv-SE')
}

interface SectionProps {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
}

function Section({ title, icon, children }: SectionProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-100">
        <span className="text-gray-400">{icon}</span>
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">{title}</h3>
      </div>
      {children}
    </div>
  )
}

interface DataRowProps {
  label: string
  value: React.ReactNode
  highlight?: boolean
}

function DataRow({ label, value, highlight }: DataRowProps) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm ${highlight ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>{value}</span>
    </div>
  )
}

export function CompanyModal() {
  const { selectedCompany, setSelectedCompany } = useMapContext()

  if (!selectedCompany) return null

  const company = selectedCompany
  const logoColor = getLogoColor(company.name)
  const foundedYear = company.foundation_date ? new Date(company.foundation_date).getFullYear() : null

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={() => setSelectedCompany(null)}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 z-10">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-4">
              {company.logo_url ? (
                <img
                  src={company.logo_url}
                  alt={company.name}
                  className="w-14 h-14 rounded-lg object-contain bg-gray-50 p-1"
                />
              ) : (
                <div
                  className="w-14 h-14 rounded-lg flex items-center justify-center text-xl font-bold"
                  style={{ backgroundColor: logoColor.bg, color: logoColor.text }}
                >
                  {company.name.charAt(0)}
                </div>
              )}
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{company.name}</h2>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-sm text-gray-500 font-mono">{company.orgnr}</span>
                  {company.sector && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 rounded">
                      {company.sector}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={() => setSelectedCompany(null)}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Stang"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-120px)] px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Left Column */}
            <div>
              {/* Company Info */}
              <Section title="Foretag" icon={<Building2 className="w-4 h-4" />}>
                {company.city && (
                  <DataRow
                    label="Stad"
                    value={
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-gray-400" />
                        {company.city}{company.county ? `, ${company.county}` : ''}
                      </span>
                    }
                  />
                )}
                {foundedYear && <DataRow label="Grundat" value={foundedYear} />}
                {company.num_employees && <DataRow label="Anstallda" value={company.num_employees} highlight />}
                {company.investment_status && <DataRow label="Investeringsstatus" value={company.investment_status} />}
                {company.purpose && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 leading-relaxed">{company.purpose}</p>
                  </div>
                )}
              </Section>

              {/* Financials 2024 */}
              <Section title="Finansiellt 2024" icon={<Briefcase className="w-4 h-4" />}>
                <DataRow label="Omsattning" value={formatCurrency(company.turnover_2024_sek)} highlight />
                <DataRow label="EBIT" value={formatCurrency(company.ebit_2024_sek)} />
                <DataRow
                  label="Tillvaxt"
                  value={
                    company.growth_2023_2024_percent !== null ? (
                      <span className={`flex items-center gap-1 ${company.growth_2023_2024_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {company.growth_2023_2024_percent >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        {formatPercent(company.growth_2023_2024_percent)}
                      </span>
                    ) : '-'
                  }
                />
              </Section>

              {/* Financials 2023 */}
              {(company.turnover_2023_sek || company.ebit_2023_sek) && (
                <Section title="Finansiellt 2023" icon={<Calendar className="w-4 h-4" />}>
                  <DataRow label="Omsattning" value={formatCurrency(company.turnover_2023_sek)} />
                  <DataRow label="EBIT" value={formatCurrency(company.ebit_2023_sek)} />
                </Section>
              )}

              {/* Trademarks */}
              {company.trademarks.length > 0 && (
                <Section title={`Varumarken (${company.trademarks.length})`} icon={<Award className="w-4 h-4" />}>
                  <div className="space-y-2">
                    {company.trademarks.slice(0, 5).map((tm, i) => (
                      <div key={i} className="flex justify-between items-center py-1">
                        <span className="text-sm text-gray-700">{tm.name}</span>
                        {tm.status && (
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            tm.status === 'Registrerat' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {tm.status}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}
            </div>

            {/* Right Column */}
            <div>
              {/* Funding */}
              <Section title="Finansiering" icon={<DollarSign className="w-4 h-4" />}>
                <DataRow label="Total finansiering" value={formatCurrency(company.total_funding_sek)} highlight />
                <DataRow label="Senaste runda" value={formatCurrency(company.latest_funding_round_sek)} />
                {company.latest_funding_date && (
                  <DataRow label="Senaste runddatum" value={formatDate(company.latest_funding_date)} />
                )}
                <DataRow label="Vardering" value={formatCurrency(company.latest_valuation_sek)} highlight />
              </Section>

              {/* Leadership */}
              <Section title="Ledning" icon={<Users className="w-4 h-4" />}>
                {company.ceo_name && <DataRow label="VD" value={company.ceo_name} highlight />}
                {company.chairman_name && <DataRow label="Ordforande" value={company.chairman_name} />}
                {company.board_members.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-500 mb-1">Styrelseledamoter</p>
                    <div className="flex flex-wrap gap-1">
                      {company.board_members.map((member, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">
                          {member}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </Section>

              {/* Owners */}
              {company.owners.length > 0 && (
                <Section title="Agare" icon={<PieChart className="w-4 h-4" />}>
                  <div className="space-y-2">
                    {company.owners.map((owner, i) => (
                      <div key={i} className="flex justify-between items-center py-1">
                        <span className="text-sm text-gray-700">{owner.name}</span>
                        {owner.percent !== null && (
                          <span className="text-sm font-medium text-gray-900">{owner.percent.toFixed(1)}%</span>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* Investors */}
              {company.investors && company.investors.length > 0 && (
                <Section title={`Investerare (${company.investors.length})`} icon={<Users className="w-4 h-4" />}>
                  <div className="space-y-2">
                    {company.investors.map((investor, i) => (
                      <div key={i} className="flex justify-between items-center py-1">
                        <div className="min-w-0 flex-1">
                          <span className="text-sm text-gray-700 block truncate">{investor.name}</span>
                          {investor.type && (
                            <span className="text-xs text-gray-400">{investor.type}</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {investor.isLeadInvestor && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded font-medium">Lead</span>
                          )}
                          {investor.investmentRound && (
                            <span className="text-xs text-gray-500">{investor.investmentRound}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* Annual Report */}
              {company.annual_report_year && (
                <Section title="Arsredovisning" icon={<FileText className="w-4 h-4" />}>
                  <DataRow label="Senaste ar" value={company.annual_report_year} />
                  <a
                    href={`https://www.allabolag.se/${company.orgnr}/arsredovisning`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-2 text-sm text-blue-600 hover:text-blue-800"
                  >
                    <FileText className="w-3 h-3" />
                    Se arsredovisning
                  </a>
                </Section>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t border-gray-100 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {company.website && (
                <a
                  href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-700 hover:text-gray-900 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                >
                  <Globe className="w-3.5 h-3.5" />
                  Webbplats
                </a>
              )}
              {company.linkedin_url && (
                <a
                  href={company.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-700 hover:text-gray-900 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                >
                  <Linkedin className="w-3.5 h-3.5" />
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
              <ExternalLink className="w-3.5 h-3.5" />
              Visa pa Allabolag
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
