import { MapProvider, useMapContext } from './context/MapContext'
import { MapView } from './components/Map/MapContainer'
import { DataTable } from './components/Data/DataTable'
import { CompanyPanel } from './components/Company/CompanyPanel'
import { Header } from './components/Layout/Header'
import { Footer } from './components/Layout/Footer'
import { StatsBar } from './components/Stats/StatsBar'
import { useCompanies } from './hooks/useCompanies'
import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'

function LoadingScreen() {
  const [progress, setProgress] = useState(0)
  const [loadingText, setLoadingText] = useState('Initierar')

  useEffect(() => {
    // Simulate loading progress
    const texts = [
      'Initierar',
      'Ansluter till databas',
      'Hämtar impact-företag',
      'Förbereder kartan',
      'Nästan klart'
    ]

    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + Math.random() * 15 + 5
        const textIndex = Math.min(Math.floor(newProgress / 20), texts.length - 1)
        setLoadingText(texts[textIndex])
        return Math.min(newProgress, 95)
      })
    }, 200)

    return () => clearInterval(interval)
  }, [])

  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8, ease: 'easeInOut' }}
      className="fixed inset-0 z-[9999] flex items-center justify-center overflow-hidden"
    >
      {/* Dark premium background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0A0A0A] via-[#111111] to-[#0A0A0A]" />

      {/* Animated gradient orbs */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-loop-lime/20 blur-[100px]"
      />
      <motion.div
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-primary-blue/20 blur-[100px]"
      />

      {/* Content container */}
      <div className="relative z-10 text-center px-6 max-w-md w-full">
        {/* Logo animation */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.8, type: 'spring', bounce: 0.4 }}
          className="relative w-28 h-28 mx-auto mb-8"
        >
          {/* Outer glow ring */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 rounded-3xl border-2 border-loop-lime/30"
            style={{
              background: 'conic-gradient(from 0deg, transparent, rgba(205,255,0,0.3), transparent)',
            }}
          />

          {/* Logo container */}
          <div className="absolute inset-2 rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center shadow-2xl border border-gray-700/50">
            <motion.div
              animate={{
                scale: [1, 1.15, 1],
                boxShadow: [
                  '0 0 20px rgba(205,255,0,0.5)',
                  '0 0 40px rgba(205,255,0,0.8)',
                  '0 0 20px rgba(205,255,0,0.5)',
                ],
              }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              className="w-12 h-12 rounded-full bg-gradient-to-br from-loop-lime via-loop-lime-dark to-loop-lime"
            />
          </div>
        </motion.div>

        {/* Brand name with letter animation */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mb-8"
        >
          <h1 className="text-5xl sm:text-6xl font-serif font-bold tracking-tight mb-2">
            {'Loop Tool'.split('').map((letter, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + i * 0.05, duration: 0.4 }}
                className={letter === ' ' ? 'inline-block w-3' : 'inline-block'}
                style={{
                  background: 'linear-gradient(135deg, #CDFF00 0%, #FFFFFF 50%, #CDFF00 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  color: 'transparent',
                }}
              >
                {letter}
              </motion.span>
            ))}
          </h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="text-gray-400 text-sm font-medium tracking-widest uppercase"
          >
            Impact Ecosystem Sverige
          </motion.p>
        </motion.div>

        {/* Progress bar */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0.8 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ delay: 0.6 }}
          className="mb-4"
        >
          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden border border-gray-700/50">
            <motion.div
              className="h-full bg-gradient-to-r from-loop-lime via-loop-lime-dark to-loop-lime rounded-full"
              initial={{ width: '0%' }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3 }}
              style={{
                boxShadow: '0 0 20px rgba(205,255,0,0.6)',
              }}
            />
          </div>
        </motion.div>

        {/* Loading text */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="flex items-center justify-center gap-3"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            className="w-4 h-4 border-2 border-loop-lime border-t-transparent rounded-full"
          />
          <span className="text-sm text-gray-400 font-medium">
            {loadingText}...
          </span>
          <span className="text-sm text-loop-lime font-bold tabular-nums">
            {Math.round(progress)}%
          </span>
        </motion.div>

        {/* Animated particles */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              initial={{
                opacity: 0,
                x: Math.random() * 400 - 200,
                y: 100,
              }}
              animate={{
                opacity: [0, 1, 0],
                y: -100,
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                delay: i * 0.5,
                ease: 'easeOut',
              }}
              className="absolute left-1/2 bottom-0 w-1 h-1 rounded-full bg-loop-lime"
            />
          ))}
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
