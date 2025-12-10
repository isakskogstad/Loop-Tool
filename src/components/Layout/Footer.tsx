import { motion } from 'framer-motion'
import { Database, Github, ExternalLink, Heart } from 'lucide-react'

export function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-gray-50 text-gray-700 border-t border-gray-200"
    >
      <div className="px-6 py-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Left: Logo & Description */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-900 to-gray-700 flex items-center justify-center shadow-sm">
              <Database className="w-4 h-4 text-loop-lime" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-gray-900">Loop Tool</h3>
              <p className="text-xs text-gray-500">
                Impact investing database
              </p>
            </div>
          </div>

          {/* Center: Links */}
          <div className="flex items-center gap-4 text-sm">
            <a
              href="https://impactloop.se"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-gray-500 hover:text-gray-900 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Impact Loop
            </a>
            <a
              href="https://github.com/isakskogstad/Loop-Tool"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-gray-500 hover:text-gray-900 transition-colors"
            >
              <Github className="w-3.5 h-3.5" />
              GitHub
            </a>
          </div>

          {/* Right: Credits */}
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <span>Byggd med</span>
            <Heart className="w-3 h-3 text-red-400" />
            <span>för svenska impact-investerare</span>
          </div>
        </div>
      </div>
    </motion.footer>
  )
}
