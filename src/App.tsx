import { MapProvider, useMapContext } from './context/MapContext'
import { MapView } from './components/Map/MapContainer'
import { DataTable } from './components/Data/DataTable'
import { CompanyModal } from './components/Company/CompanyModal'
import { Header } from './components/Layout/Header'
import { Footer } from './components/Layout/Footer'
import { EventLog } from './components/Layout/EventLog'
import { useCompanies } from './hooks/useCompanies'
import { motion, AnimatePresence } from 'framer-motion'
import { Map, Table2 } from 'lucide-react'

function LoadingScreen() {
  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
      className="fixed inset-0 z-[9999] flex flex-col items-center justify-center overflow-hidden"
    >
      {/* Dark premium background */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-loop-black to-gray-900" />

      {/* Content container */}
      <div className="relative z-10 text-center">
        {/* Logo text with letter flip animation */}
        <div className="flex items-center justify-center gap-[0.15em] overflow-hidden">
          {/* "Loop" letters - white */}
          {'Loop'.split('').map((letter, i) => (
            <motion.span
              key={`loop-${i}`}
              initial={{ opacity: 0, y: '100%', rotateX: -90 }}
              animate={{ opacity: 1, y: 0, rotateX: 0 }}
              transition={{
                duration: 0.6,
                delay: 0.1 + i * 0.1,
                ease: [0.16, 1, 0.3, 1],
              }}
              className="inline-block font-serif font-bold text-white"
              style={{ fontSize: 'clamp(3rem, 12vw, 8rem)', transformOrigin: 'top center' }}
            >
              {letter}
            </motion.span>
          ))}

          {/* Space */}
          <span className="inline-block w-[0.3em]" />

          {/* "Tool" letters - lime */}
          {'Tool'.split('').map((letter, i) => (
            <motion.span
              key={`tool-${i}`}
              initial={{ opacity: 0, y: '100%', rotateX: -90 }}
              animate={{ opacity: 1, y: 0, rotateX: 0 }}
              transition={{
                duration: 0.6,
                delay: 0.6 + i * 0.1,
                ease: [0.16, 1, 0.3, 1],
              }}
              className="inline-block font-serif font-bold text-loop-lime"
              style={{ fontSize: 'clamp(3rem, 12vw, 8rem)', transformOrigin: 'top center' }}
            >
              {letter}
            </motion.span>
          ))}
        </div>

        {/* Underline that grows */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.8, delay: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="h-1 mx-auto mt-4 rounded-full origin-left"
          style={{
            background: 'linear-gradient(90deg, #CDFF00, #14b8a6)',
            width: '80%',
            maxWidth: '400px',
          }}
        />

        {/* Tagline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.6, ease: 'easeOut' }}
          className="mt-6 text-lg text-gray-400 font-medium tracking-wide"
        >
          Impact Investing Database
        </motion.p>

        {/* Loading indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
          className="mt-8 flex items-center justify-center gap-3"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-4 h-4 border-2 border-loop-lime border-t-transparent rounded-full"
          />
          <span className="text-sm text-gray-500 font-medium">Laddar data...</span>
        </motion.div>
      </div>
    </motion.div>
  )
}

// View Toggle Component
function ViewToggle() {
  const { viewMode, setViewMode } = useMapContext()

  return (
    <div className="flex justify-center py-4 bg-gray-50 border-t border-gray-200">
      <div className="inline-flex items-center bg-white rounded-2xl p-1.5 shadow-lg border border-gray-200">
        <button
          onClick={() => setViewMode('map')}
          className={`relative flex items-center gap-3 px-8 py-3.5 rounded-xl text-base font-semibold transition-all duration-300 ${
            viewMode === 'map'
              ? 'text-gray-900'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {viewMode === 'map' && (
            <motion.div
              layoutId="viewToggleBackground"
              className="absolute inset-0 bg-loop-lime rounded-xl shadow-md"
              initial={false}
              transition={{ type: 'spring', stiffness: 500, damping: 35 }}
            />
          )}
          <Map className="w-5 h-5 relative z-10" />
          <span className="relative z-10">Karta</span>
        </button>

        <button
          onClick={() => setViewMode('table')}
          className={`relative flex items-center gap-3 px-8 py-3.5 rounded-xl text-base font-semibold transition-all duration-300 ${
            viewMode === 'table'
              ? 'text-gray-900'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {viewMode === 'table' && (
            <motion.div
              layoutId="viewToggleBackground"
              className="absolute inset-0 bg-loop-lime rounded-xl shadow-md"
              initial={false}
              transition={{ type: 'spring', stiffness: 500, damping: 35 }}
            />
          )}
          <Table2 className="w-5 h-5 relative z-10" />
          <span className="relative z-10">Tabell</span>
        </button>
      </div>
    </div>
  )
}

function MapApp() {
  const { companies, loading, error } = useCompanies()
  const { viewMode } = useMapContext()

  if (error) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-gray-100">
        <div className="text-center p-6">
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Något gick fel</h2>
          <p className="text-sm text-gray-500 mb-4">{error.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            Försök igen
          </button>
        </div>
      </div>
    )
  }

  return (
    <>
      <AnimatePresence>
        {loading && <LoadingScreen />}
      </AnimatePresence>

      {/* Centered showcase container */}
      <div className="min-h-screen w-screen bg-gray-100 flex flex-col items-center p-4 sm:p-6 lg:p-8">
        {/* Main tool container - centered widget */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="w-full max-w-[1600px] bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-200"
        >
          {/* Integrated Header - part of the widget */}
          <Header />

          {/* Main Content - Map or Table */}
          <div className="relative">
            <AnimatePresence mode="wait">
              {viewMode === 'map' ? (
                <motion.div
                  key="map"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
                  className="h-[70vh] min-h-[500px]"
                >
                  <MapView companies={companies} />
                </motion.div>
              ) : (
                <motion.div
                  key="table"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
                  className="h-[70vh] min-h-[500px]"
                >
                  <DataTable companies={companies} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* View Toggle - Below Content */}
          <ViewToggle />

          {/* Footer integrated into widget */}
          <Footer />
        </motion.div>

        {/* Company Detail Modal */}
        <CompanyModal />

        {/* Event Log - Bottom Right */}
        <EventLog />
      </div>
    </>
  )
}

export default function App() {
  return (
    <MapProvider>
      <MapApp />
    </MapProvider>
  )
}
