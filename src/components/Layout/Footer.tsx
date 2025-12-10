import { Database, Github, ExternalLink } from 'lucide-react'

export function Footer() {
  return (
    <footer className="bg-gray-50 text-gray-700 border-t border-gray-200">
      <div className="px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Left: Logo */}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-loop-black flex items-center justify-center">
              <Database className="w-3 h-3 text-loop-lime" />
            </div>
            <span className="text-sm font-medium text-gray-700">Loop Tool</span>
          </div>

          {/* Right: Links */}
          <div className="flex items-center gap-4 text-sm">
            <a
              href="https://impactloop.se"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-gray-500 hover:text-gray-900 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Impact Loop</span>
            </a>
            <a
              href="https://github.com/isakskogstad/Loop-Tool"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-gray-500 hover:text-gray-900 transition-colors"
            >
              <Github className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
