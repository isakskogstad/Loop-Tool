import { motion } from 'framer-motion'
import { Database, Github, ExternalLink, Heart } from 'lucide-react'

export function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white border-t border-gray-700"
    >
      <div className="max-w-screen-xl mx-auto px-6 py-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Left: Logo & Description */}
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-loop-lime to-loop-lime-dark flex items-center justify-center shadow-lg shadow-lime-900/30">
              <Database className="w-5 h-5 text-loop-black" />
            </div>
            <div>
              <h3 className="font-serif font-bold text-lg">Loop Data Platform</h3>
              <p className="text-xs text-gray-400">
                Datadriven insikt i svenska impact-företag
              </p>
            </div>
          </div>

          {/* Center: Links */}
          <div className="flex items-center gap-6 text-sm">
            <a
              href="https://impactloop.se"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-gray-300 hover:text-loop-lime transition-colors group"
            >
              <ExternalLink className="w-4 h-4 group-hover:scale-110 transition-transform" />
              Impact Loop
            </a>
            <a
              href="https://github.com/isakskogstad/Loop-Tool"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-gray-300 hover:text-loop-lime transition-colors group"
            >
              <Github className="w-4 h-4 group-hover:scale-110 transition-transform" />
              GitHub
            </a>
          </div>

          {/* Right: Credits */}
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>Byggd med</span>
            <Heart className="w-3 h-3 text-red-400" />
            <span>för svenska impact-investerare</span>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-4 pt-4 border-t border-gray-700/50 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-500">
          <p>© 2025 Loop Data Platform. Data från Supabase.</p>
          <p className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            Realtidsdata " {new Date().toLocaleDateString('sv-SE')}
          </p>
        </div>
      </div>
    </motion.footer>
  )
}
