import type { FC } from 'react'
import { motion } from 'framer-motion'
import { Building2, TrendingUp, DollarSign } from 'lucide-react'
import type { CompanyWithCoords } from '../../lib/supabase'

interface FloatingStatsProps {
  companies: CompanyWithCoords[]
  filteredCount?: number
}

export const FloatingStats: FC<FloatingStatsProps> = ({ companies, filteredCount }) => {
  const totalCompanies = filteredCount !== undefined ? filteredCount : companies.length

  const companiesWithGrowth = companies.filter(c =>
    c.growth_2023_2024_percent !== null && c.growth_2023_2024_percent > 0
  ).length

  const avgFunding = companies.reduce((sum, c) =>
    sum + (c.total_funding_sek || 0), 0
  ) / (companies.length || 1) / 1_000_000 // Convert to millions

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.5 }}
      className="fixed bottom-6 left-6 z-[400] pointer-events-auto"
    >
      <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200/60 overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-b border-gray-700">
          <h3 className="font-bold text-white text-sm uppercase tracking-wide">
            Snabbstatistik
          </h3>
        </div>

        {/* Stats Grid */}
        <div className="p-4 space-y-3">
          {/* Total Companies */}
          <div className="flex items-center gap-3 group">
            <div className="p-2.5 bg-gradient-to-br from-primary-blue to-purple rounded-xl shadow-md group-hover:shadow-lg transition-all">
              <Building2 className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Företag</p>
              <p className="text-xl font-bold text-gray-900 tabular-nums">{totalCompanies}</p>
            </div>
          </div>

          {/* Companies with Growth */}
          <div className="flex items-center gap-3 group">
            <div className="p-2.5 bg-gradient-to-br from-teal to-green-500 rounded-xl shadow-md group-hover:shadow-lg transition-all">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Positiv tillväxt</p>
              <p className="text-xl font-bold text-gray-900 tabular-nums">{companiesWithGrowth}</p>
            </div>
          </div>

          {/* Average Funding */}
          <div className="flex items-center gap-3 group">
            <div className="p-2.5 bg-gradient-to-br from-loop-lime to-loop-lime-dark rounded-xl shadow-md group-hover:shadow-lg transition-all">
              <DollarSign className="w-4 h-4 text-loop-black" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Snitt funding</p>
              <p className="text-xl font-bold text-gray-900 tabular-nums">
                {Math.round(avgFunding)} <span className="text-sm font-medium">mkr</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
