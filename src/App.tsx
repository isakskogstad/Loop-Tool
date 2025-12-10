import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, Users, TrendingUp, Building2, ArrowRight, Check, X, Table, BarChart3, Sparkles } from 'lucide-react'
import { fetchLoopCompanies, fetchStats, fetchSectorDistribution, fetchTopCompanies, type LoopCompany } from './lib/supabase'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

function App() {
  const [showIntro, setShowIntro] = useState(true)
  const [stats, setStats] = useState({ companies: 0, owners: 0, sectors: 0, financials: 0 })
  const [companies, setCompanies] = useState<LoopCompany[]>([])
  const [sectorData, setSectorData] = useState<{ name: string; count: number }[]>([])
  const [topCompanies, setTopCompanies] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const dataRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const timer = setTimeout(() => setShowIntro(false), 3000)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, companiesData, sectorsData, topData] = await Promise.all([
          fetchStats(),
          fetchLoopCompanies(50),
          fetchSectorDistribution(),
          fetchTopCompanies(10)
        ])
        setStats(statsData)
        setCompanies(companiesData)
        setSectorData(sectorsData)
        setTopCompanies(topData)
      } catch (error) {
        console.error('Error loading data:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const formatCurrency = (value: number | null) => {
    if (!value) return '-'
    if (value >= 1000000000) return `${(value / 1000000000).toFixed(1)} mdr`
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)} mkr`
    if (value >= 1000) return `${(value / 1000).toFixed(0)} tkr`
    return value.toString()
  }

  const formatPercent = (value: number | null) => {
    if (value === null || value === undefined) return '-'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(1)}%`
  }

  const scrollToData = () => {
    dataRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-loop-black">
      {/* Intro Animation */}
      <AnimatePresence>
        {showIntro && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-loop-black"
            exit={{ opacity: 0 }}
            transition={{ duration: 0.8 }}
          >
            <motion.div className="text-center">
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ duration: 0.8, type: 'spring' }}
                className="w-24 h-24 mx-auto mb-8 rounded-full bg-loop-lime flex items-center justify-center"
              >
                <Database className="w-12 h-12 text-loop-black" />
              </motion.div>
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.6 }}
                className="text-4xl md:text-6xl font-bold text-white mb-4"
              >
                Loop <span className="text-loop-lime">Data</span>
              </motion.h1>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8, duration: 0.6 }}
                className="text-gray-400 text-xl"
              >
                Impact Investing Database 2.0
              </motion.p>
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: 1.2, duration: 1.5 }}
                className="mt-8 h-1 bg-loop-lime rounded-full w-48 mx-auto origin-left"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hero Section */}
      <section className="min-h-screen flex flex-col justify-center px-6 md:px-12 lg:px-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-loop-black via-loop-gray to-loop-black opacity-50" />
        <div className="absolute top-20 right-20 w-96 h-96 bg-loop-lime/5 rounded-full blur-3xl" />
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-loop-lime/10 rounded-full blur-3xl" />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: showIntro ? 0 : 1, y: showIntro ? 30 : 0 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="relative z-10 max-w-5xl"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-loop-lime/10 border border-loop-lime/30 mb-8">
            <Sparkles className="w-4 h-4 text-loop-lime" />
            <span className="text-loop-lime text-sm font-medium">Förbättrad Databas</span>
          </div>

          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold leading-tight mb-6">
            <span className="text-white">Impact Loop</span>
            <br />
            <span className="text-loop-lime text-glow">Data Platform</span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 max-w-2xl mb-12 leading-relaxed">
            En helt ny nivå av datakvalitet för svenska impact-företag.
            Strukturerat, validerat och redo för analys.
          </p>

          <div className="flex flex-wrap gap-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={scrollToData}
              className="inline-flex items-center gap-2 px-8 py-4 bg-loop-lime text-loop-black font-semibold rounded-lg hover:bg-loop-lime-dark transition-colors"
            >
              Utforska Data
              <ArrowRight className="w-5 h-5" />
            </motion.button>
            <motion.a
              href="#comparison"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="inline-flex items-center gap-2 px-8 py-4 border border-white/20 text-white font-semibold rounded-lg hover:bg-white/5 transition-colors"
            >
              Se Jämförelse
            </motion.a>
          </div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: showIntro ? 0 : 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-12 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center pt-2"
          >
            <div className="w-1 h-2 bg-loop-lime rounded-full" />
          </motion.div>
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="py-24 px-6 md:px-12 lg:px-24 bg-loop-gray">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-7xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Databas i Realtid</h2>
          <p className="text-gray-400 text-lg mb-12">Live-data från Supabase PostgreSQL</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Building2, label: 'Företag', value: stats.companies, color: 'text-loop-lime' },
              { icon: Users, label: 'Ägarposter', value: stats.owners, color: 'text-blue-400' },
              { icon: Table, label: 'Sektorer', value: stats.sectors, color: 'text-purple-400' },
              { icon: BarChart3, label: 'Finansiella poster', value: stats.financials, color: 'text-green-400' },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                className="bg-loop-black p-6 rounded-xl border border-white/10 card-hover"
              >
                <stat.icon className={`w-8 h-8 ${stat.color} mb-4`} />
                <div className="text-4xl md:text-5xl font-bold text-white mb-2 stat-number">
                  {loading ? '...' : stat.value.toLocaleString('sv-SE')}
                </div>
                <div className="text-gray-400">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Comparison Section */}
      <section id="comparison" className="py-24 px-6 md:px-12 lg:px-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-7xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Före & Efter</h2>
          <p className="text-gray-400 text-lg mb-12">Se skillnaden mellan original Excel och ny databasstruktur</p>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Before */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-loop-gray rounded-xl p-8 border border-red-500/30"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                  <X className="w-5 h-5 text-red-500" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Original: loop.xlsx</h3>
                  <p className="text-gray-400 text-sm">En platt Excel-fil</p>
                </div>
              </div>
              <ul className="space-y-4">
                {[
                  '1 sheet, 18 kolumner',
                  'Ägare som text i en kolumn',
                  'Sektorer kommaseparerade',
                  'Endast 2 års finansdata',
                  'Inkonsistent formatering',
                  'Ingen validering',
                  'Manuella uppdateringar',
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-gray-300">
                    <X className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* After */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="bg-loop-gray rounded-xl p-8 border border-loop-lime/30 glow-lime"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-loop-lime/20 flex items-center justify-center">
                  <Check className="w-5 h-5 text-loop-lime" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Ny: Supabase PostgreSQL</h3>
                  <p className="text-gray-400 text-sm">Normaliserad relationsdatabas</p>
                </div>
              </div>
              <ul className="space-y-4">
                {[
                  '6+ relaterade tabeller',
                  '4,941 strukturerade ägarposter',
                  '1,449 normaliserade sektorer',
                  '2,202 finansiella poster (historik)',
                  'Standardiserat, validerat',
                  'RLS-säkerhet, API-redo',
                  'Automatiska uppdateringar',
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-gray-300">
                    <Check className="w-5 h-5 text-loop-lime mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* Sector Chart */}
      <section className="py-24 px-6 md:px-12 lg:px-24 bg-loop-gray">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-7xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Sektorfördelning</h2>
          <p className="text-gray-400 text-lg mb-12">Top 10 impact-sektorer efter antal företag</p>

          <div className="bg-loop-black rounded-xl p-6 border border-white/10">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={sectorData} layout="vertical" margin={{ left: 20, right: 30 }}>
                <XAxis type="number" stroke="#666" />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="#666"
                  width={180}
                  tick={{ fill: '#999', fontSize: 12 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {sectorData.map((_, index) => (
                    <Cell key={index} fill={index === 0 ? '#CDFF00' : `rgba(205, 255, 0, ${0.8 - index * 0.07})`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </section>

      {/* Data Table Section */}
      <section ref={dataRef} className="py-24 px-6 md:px-12 lg:px-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-7xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Impact-Företag</h2>
          <p className="text-gray-400 text-lg mb-12">Live-data från loop_table (sorterad efter omsättning 2024)</p>

          <div className="bg-loop-gray rounded-xl border border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-loop-black">
                    <th className="text-left p-4 text-loop-lime font-semibold border-b border-white/10">Företag</th>
                    <th className="text-left p-4 text-loop-lime font-semibold border-b border-white/10">Sektor</th>
                    <th className="text-left p-4 text-loop-lime font-semibold border-b border-white/10">Stad</th>
                    <th className="text-right p-4 text-loop-lime font-semibold border-b border-white/10">Omsättning 2024</th>
                    <th className="text-right p-4 text-loop-lime font-semibold border-b border-white/10">Tillväxt</th>
                    <th className="text-right p-4 text-loop-lime font-semibold border-b border-white/10">Total Funding</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-gray-400">
                        <div className="flex items-center justify-center gap-3">
                          <div className="w-5 h-5 border-2 border-loop-lime border-t-transparent rounded-full animate-spin" />
                          Laddar data...
                        </div>
                      </td>
                    </tr>
                  ) : (
                    companies.slice(0, 20).map((company, index) => (
                      <motion.tr
                        key={company.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.03 }}
                        className="border-b border-white/5 hover:bg-white/5 transition-colors"
                      >
                        <td className="p-4 text-white font-medium">{company.company_name}</td>
                        <td className="p-4 text-gray-400 text-sm max-w-48 truncate">{company.sector || '-'}</td>
                        <td className="p-4 text-gray-400">{company.city || '-'}</td>
                        <td className="p-4 text-right text-white font-mono">{formatCurrency(company.turnover_2024_sek)}</td>
                        <td className={`p-4 text-right font-mono ${company.growth_2023_2024_percent && company.growth_2023_2024_percent > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {formatPercent(company.growth_2023_2024_percent)}
                        </td>
                        <td className="p-4 text-right text-loop-lime font-mono">{formatCurrency(company.total_funding_sek)}</td>
                      </motion.tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-4 bg-loop-black border-t border-white/10 text-center text-gray-400">
              Visar {Math.min(20, companies.length)} av {stats.companies} företag
            </div>
          </div>
        </motion.div>
      </section>

      {/* Top Companies */}
      <section className="py-24 px-6 md:px-12 lg:px-24 bg-loop-gray">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-7xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Top 10 efter Omsättning</h2>
          <p className="text-gray-400 text-lg mb-12">De största impact-bolagen i databasen</p>

          <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-4">
            {topCompanies.map((company, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className={`p-6 rounded-xl border ${index === 0 ? 'bg-loop-lime/10 border-loop-lime/50' : 'bg-loop-black border-white/10'} card-hover`}
              >
                <div className={`text-3xl font-bold mb-3 ${index === 0 ? 'text-loop-lime' : 'text-white/30'}`}>
                  #{index + 1}
                </div>
                <h3 className="text-white font-semibold mb-2 line-clamp-2">{company.company_name}</h3>
                <div className="text-2xl font-bold text-loop-lime mb-1">
                  {formatCurrency(company.turnover_2024_sek)}
                </div>
                <div className="text-sm text-gray-400">{company.city || 'Sverige'}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 md:px-12 lg:px-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto text-center"
        >
          <div className="w-20 h-20 mx-auto mb-8 rounded-full bg-loop-lime flex items-center justify-center glow-lime">
            <TrendingUp className="w-10 h-10 text-loop-black" />
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Redo att ta nästa steg?
          </h2>
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
            Denna databas är byggd för att stödja Impact Loops vision -
            strukturerad data som möjliggör bättre investeringar och större impact.
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-loop-lime/10 border border-loop-lime/30">
            <Database className="w-4 h-4 text-loop-lime" />
            <span className="text-loop-lime text-sm font-medium">Powered by Supabase</span>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 md:px-12 lg:px-24 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-gray-400 text-sm">
            © 2024 Loop Data Platform. Built for Impact Loop.
          </div>
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <span>Live data from</span>
            <span className="text-loop-lime font-semibold">Supabase PostgreSQL</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
