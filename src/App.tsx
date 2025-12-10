import { MapProvider, useMapContext } from './context/MapContext'
import { MapView } from './components/Map/MapContainer'
import { DataTable } from './components/Data/DataTable'
import { CompanyPanel } from './components/Company/CompanyPanel'
import { Header } from './components/Layout/Header'
import { StatsBar } from './components/Stats/StatsBar'
import { useCompanies } from './hooks/useCompanies'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2 } from 'lucide-react'

function LoadingScreen() {
  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-gradient-to-br from-white via-gray-50 to-gray-100"
    >
      <div className="text-center">
        {/* Premium animated logo */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="relative w-24 h-24 rounded-3xl bg-gradient-to-br from-[#0A0A0A] via-[#1A1A1A] to-[#0A0A0A] flex items-center justify-center mx-auto mb-6 shadow-2xl"
        >
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-loop-lime/10 to-transparent" />
          <motion.div
            animate={{
              scale: [1, 1.3, 1],
              rotate: [0, 180, 360]
            }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            className="w-12 h-12 rounded-full bg-gradient-to-br from-loop-lime via-loop-lime-dark to-loop-lime shadow-[0_0_30px_rgba(205,255,0,0.8)]"
          />
        </motion.div>

        {/* Loading text with animation */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-3"
        >
          <h2 className="font-serif font-bold text-2xl text-gray-900">Loop Data</h2>
          <div className="flex items-center justify-center gap-3 text-gray-600">
            <Loader2 className="w-5 h-5 animate-spin text-primary-blue" />
            <span className="text-sm font-semibold">Laddar impact-företag...</span>
          </div>
        </motion.div>

        {/* Animated dots */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="flex justify-center gap-2 mt-8"
        >
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{
                y: [0, -10, 0],
                backgroundColor: ['#CDFF00', '#2E54FF', '#CDFF00']
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2
              }}
              className="w-2 h-2 rounded-full"
            />
          ))}
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

      <div className="h-screen w-screen overflow-hidden bg-gradient-to-b from-gray-50 to-gray-100">
        {/* Header */}
        <Header companyCount={companies.length} loading={loading} />

        {/* Stats Bar */}
        <div className="pt-[76px]">
          <StatsBar companies={companies} loading={loading} />
        </div>

        {/* Main Content - Map or Table */}
        <main className="h-[calc(100vh-76px-180px)]">
          <AnimatePresence mode="wait">
            {viewMode === 'map' ? (
              <motion.div
                key="map"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.3 }}
                className="h-full"
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
                className="h-full"
              >
                <DataTable companies={companies} />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

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
