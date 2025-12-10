import { MapProvider, useMapContext } from './context/MapContext'
import { MapView } from './components/Map/MapContainer'
import { DataTable } from './components/Data/DataTable'
import { CompanyPanel } from './components/Company/CompanyPanel'
import { Header } from './components/Layout/Header'
import { useCompanies } from './hooks/useCompanies'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2 } from 'lucide-react'

function LoadingScreen() {
  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-white"
    >
      <div className="text-center">
        <div className="w-16 h-16 rounded-2xl bg-[#0A0A0A] flex items-center justify-center mx-auto mb-4">
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-8 h-8 rounded-full bg-[#CDFF00]"
          />
        </div>
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm">Laddar företagsdata...</span>
        </div>
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

      <div className="h-screen w-screen overflow-hidden bg-gray-50">
        {/* Header */}
        <Header companyCount={companies.length} loading={loading} />

        {/* Main Content - Map or Table */}
        <main className="pt-[60px] h-full">
          <AnimatePresence mode="wait">
            {viewMode === 'map' ? (
              <motion.div
                key="map"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="h-full"
              >
                <MapView companies={companies} />
              </motion.div>
            ) : (
              <motion.div
                key="table"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
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
