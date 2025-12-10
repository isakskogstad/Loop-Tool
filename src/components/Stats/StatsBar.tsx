import { useEffect, useState } from 'react'
import type { FC } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, Building2, Target, Sparkles } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'

interface StatsBarProps {
  companies: CompanyWithCoords[]
  loading: boolean
}

interface StatItemProps {
  icon: React.ReactNode
  label: string
  value: number
  suffix?: string
  prefix?: string
  delay?: number
  gradient?: string
}

function StatItem({ icon, label, value, suffix = '', prefix = '', delay = 0, gradient = 'from-loop-lime to-loop-lime-dark' }: StatItemProps) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (value === 0) return

    const duration = 2000 // 2 seconds
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
  }, [value])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: 'easeOut' }}
      className="group relative"
    >
      {/* Gradient background on hover */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity duration-300`} />

      <div className="relative px-6 py-5 rounded-2xl bg-white/60 backdrop-blur-sm border border-gray-200/60 shadow-sm hover:shadow-lg hover:border-gray-300/60 transition-all duration-300">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-md group-hover:shadow-lg group-hover:scale-110 transition-all duration-300`}>
            <div className="text-white">
              {icon}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-500 mb-1 uppercase tracking-wide">
              {label}
            </p>
            <p className="text-3xl font-bold text-gray-900 tabular-nums">
              {prefix}{count.toLocaleString('sv-SE')}{suffix}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export const StatsBar: FC<StatsBarProps> = ({ companies, loading }) => {
  if (loading) {
    return (
      <div className="w-full px-6 py-8 bg-gradient-to-b from-white/80 to-gray-50/80 backdrop-blur-md border-b border-gray-200/60">
        <div className="max-w-screen-xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-100 rounded-2xl animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Calculate statistics
  const totalCompanies = companies.length

  const totalFunding = companies.reduce((sum, company) =>
    sum + (company.total_funding_sek || 0), 0
  ) / 1_000_000 // Convert to millions

  const companiesWithGrowth = companies.filter(c =>
    c.growth_2023_2024_percent !== null && c.growth_2023_2024_percent > 0
  ).length

  const avgGrowth = companies.reduce((sum, company) => {
    if (company.growth_2023_2024_percent !== null && company.growth_2023_2024_percent > 0) {
      return sum + company.growth_2023_2024_percent
    }
    return sum
  }, 0) / (companiesWithGrowth || 1)

  return (
    <div className="w-full px-6 py-8 bg-gradient-to-b from-white/80 to-gray-50/80 backdrop-blur-md border-b border-gray-200/60">
      <div className="max-w-screen-xl mx-auto">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6"
        >
          <h2 className="text-2xl md:text-3xl font-serif font-bold text-gray-900 mb-2">
            Impact-företag i Sverige
          </h2>
          <p className="text-sm text-gray-500 font-medium">
            Översikt av svenska impact-företag med fokus på tillväxt och finansiering
          </p>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatItem
            icon={<Building2 className="w-6 h-6" />}
            label="Företag"
            value={totalCompanies}
            delay={0.1}
            gradient="from-primary-blue to-blue-600"
          />

          <StatItem
            icon={<TrendingUp className="w-6 h-6" />}
            label="Total Finansiering"
            value={Math.round(totalFunding)}
            suffix=" mkr"
            delay={0.2}
            gradient="from-loop-lime to-loop-lime-dark"
          />

          <StatItem
            icon={<Target className="w-6 h-6" />}
            label="Snitt Tillväxt"
            value={Math.round(avgGrowth * 10) / 10}
            suffix="%"
            prefix="+"
            delay={0.3}
            gradient="from-teal to-green-500"
          />

          <StatItem
            icon={<Sparkles className="w-6 h-6" />}
            label="Med Positiv Tillväxt"
            value={companiesWithGrowth}
            delay={0.4}
            gradient="from-purple to-pink-600"
          />
        </div>
      </div>
    </div>
  )
}
