import { MapProvider, useMapContext } from './context/MapContext'
import { MapView } from './components/Map/MapContainer'
import { DataTable } from './components/Data/DataTable'
import { CompanyPanel } from './components/Company/CompanyPanel'
import { Header } from './components/Layout/Header'
import { Footer } from './components/Layout/Footer'
import { StatsBar } from './components/Stats/StatsBar'
import { useCompanies } from './hooks/useCompanies'
import { motion, AnimatePresence } from 'framer-motion'

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

function MapApp() {
  const { companies, loading, error } = useCompanies()
  const { viewMode } = useMapContext()

  if (error) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white">
        <div className="text-center p-6">
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">⚠️</span>
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

      <div className="min-h-screen w-screen overflow-x-hidden bg-gradient-to-b from-gray-50 to-gray-100 flex flex-col">
        {/* Header */}
        <Header companyCount={companies.length} loading={loading} />

        {/* Stats Bar - adjusted for taller header with filter pills */}
        <div className="pt-[120px]">
          <StatsBar companies={companies} loading={loading} />
        </div>

        {/* Main Content - Map or Table with margins */}
        <main className="flex-1 px-4 sm:px-6 lg:px-8 pb-6">
          <div className="max-w-screen-2xl mx-auto h-full">
            <AnimatePresence mode="wait">
              {viewMode === 'map' ? (
                <motion.div
                  key="map"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.3 }}
                  className="h-[65vh] min-h-[500px] rounded-2xl overflow-hidden shadow-xl border border-gray-200/60"
                >
                  <MapView companies={companies} />
                </motion.div>
              ) : (
                <motion.div
                  key="table"
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  transition={{ duration: 0.3 }}
                  className="h-[65vh] min-h-[500px] rounded-2xl overflow-hidden shadow-xl border border-gray-200/60"
                >
                  <DataTable companies={companies} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>

        {/* Footer */}
        <Footer />

        {/* Company Detail Panel */}
        <CompanyPanel />
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
