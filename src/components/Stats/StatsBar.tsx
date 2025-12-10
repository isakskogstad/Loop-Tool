import { useEffect, useState } from 'react'
import type { FC } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Building2, Wallet, Zap } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'

interface StatsBarProps {
  companies: CompanyWithCoords[]
  loading: boolean
}

// Animated counter hook
function useAnimatedCounter(value: number, duration: number = 2000) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (value === 0) return

    const steps = 60
    const increment = value / steps
    const stepDuration = duration / steps
    let current = 0

    const timer = setInterval(() => {
      current += increment
      if (current >= value) {
        setCount(value)
        clearInterval(timer)
      } else {
        setCount(Math.floor(current))
      }
    }, stepDuration)

    return () => clearInterval(timer)
  }, [value, duration])

  return count
}

// Hero stat component - larger and more prominent
function HeroStat({ value, label, suffix = '', icon }: { value: number; label: string; suffix?: string; icon: React.ReactNode }) {
  const animatedValue = useAnimatedCounter(value)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="relative bg-gradient-to-br from-loop-black via-gray-900 to-loop-black rounded-3xl p-6 text-white overflow-hidden group"
    >
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-loop-lime/10 via-transparent to-primary-blue/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Glow effect */}
      <div className="absolute -top-20 -right-20 w-40 h-40 bg-loop-lime/20 rounded-full blur-3xl" />

      <div className="relative">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-loop-lime/20 rounded-xl">
            {icon}
          </div>
          <span className="text-sm font-semibold text-gray-400 uppercase tracking-wider">{label}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-5xl sm:text-6xl font-bold tabular-nums bg-gradient-to-r from-loop-lime via-white to-loop-lime bg-clip-text text-transparent">
            {animatedValue.toLocaleString('sv-SE')}
          </span>
          {suffix && <span className="text-2xl font-semibold text-gray-400">{suffix}</span>}
        </div>
      </div>
    </motion.div>
  )
}

// Regular stat component
function StatCard({ value, label, suffix = '', prefix = '', icon, gradient, delay = 0 }: {
  value: number
  label: string
  suffix?: string
  prefix?: string
  icon: React.ReactNode
  gradient: string
  delay?: number
}) {
  const animatedValue = useAnimatedCounter(value)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      className="relative bg-white rounded-2xl p-5 border border-gray-200/60 shadow-sm hover:shadow-xl hover:border-gray-300 transition-all duration-300 group overflow-hidden"
    >
      {/* Hover gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />

      <div className="relative flex items-center gap-4">
        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-lg group-hover:scale-110 group-hover:shadow-xl transition-all duration-300`}>
          <div className="text-white">{icon}</div>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-900 tabular-nums">
            {prefix}{animatedValue.toLocaleString('sv-SE')}{suffix}
          </p>
        </div>
      </div>
    </motion.div>
  )
}

export const StatsBar: FC<StatsBarProps> = ({ companies, loading }) => {
  if (loading) {
    return (
      <div className="w-full px-4 sm:px-6 py-6">
        <div className="max-w-screen-xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-1 h-36 bg-gray-200 rounded-3xl animate-pulse" />
            <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-100 rounded-2xl animate-pulse" />
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Calculate statistics
  const totalCompanies = companies.length

  const totalFunding = companies.reduce((sum, c) => sum + (c.total_funding_sek || 0), 0) / 1_000_000_000 // Billions

  const companiesWithGrowth = companies.filter(c =>
    c.growth_2023_2024_percent !== null && c.growth_2023_2024_percent > 0
  ).length

  const avgGrowth = companies.reduce((sum, c) => {
    if (c.growth_2023_2024_percent !== null) {
      return sum + c.growth_2023_2024_percent
    }
    return sum
  }, 0) / (companies.filter(c => c.growth_2023_2024_percent !== null).length || 1)

  return (
    <div className="w-full px-4 sm:px-6 py-6">
      <div className="max-w-screen-xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Hero stat - Company count */}
          <div className="md:col-span-1">
            <HeroStat
              value={totalCompanies}
              label="Impact-företag"
              icon={<Building2 className="w-5 h-5 text-loop-lime" />}
            />
          </div>

          {/* Regular stats */}
          <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              value={Math.round(totalFunding * 10) / 10}
              label="Total Funding"
              suffix=" mdr kr"
              icon={<Wallet className="w-5 h-5" />}
              gradient="from-primary-blue to-blue-600"
              delay={0.1}
            />

            <StatCard
              value={Math.round(avgGrowth * 10) / 10}
              label="Snitt Tillväxt"
              suffix="%"
              prefix={avgGrowth >= 0 ? '+' : ''}
              icon={<TrendingUp className="w-5 h-5" />}
              gradient="from-teal to-emerald-500"
              delay={0.2}
            />

            <StatCard
              value={companiesWithGrowth}
              label="Positiv Tillväxt"
              icon={<Zap className="w-5 h-5" />}
              gradient="from-purple to-pink-500"
              delay={0.3}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
