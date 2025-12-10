import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, RefreshCw, Database, FileText, CheckCircle, Activity, Zap } from 'lucide-react'

interface EventItem {
  id: string
  type: 'fetch' | 'update' | 'sync' | 'report'
  message: string
  company?: string
  timestamp: Date
}

const eventTypes = [
  { type: 'fetch' as const, messages: ['Hämtade årsredovisning för', 'Laddade företagsdata för', 'Hämtade finansiell data för'] },
  { type: 'update' as const, messages: ['Uppdaterade styrelseledamöter för', 'Synkade ägardata för', 'Uppdaterade VD-info för'] },
  { type: 'sync' as const, messages: ['Synkroniserade med Bolagsverket för', 'Verifierade orgnr för', 'Kontrollerade status för'] },
  { type: 'report' as const, messages: ['Genererade rapport för', 'Exporterade data för', 'Skapade sammanställning för'] },
]

const sampleCompanies = [
  'Northvolt', 'Klarna', 'Spotify', 'Einride', 'Vattenfall', 'H&M', 'IKEA',
  'Volvo Cars', 'Ericsson', 'Atlas Copco', 'Hexagon', 'Evolution Gaming',
  'Oatly', 'Karma', 'Epidemic Sound', 'Kry', 'Matsmart', 'NA-KD'
]

function generateEvent(): EventItem {
  const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)]
  const message = eventType.messages[Math.floor(Math.random() * eventType.messages.length)]
  const company = sampleCompanies[Math.floor(Math.random() * sampleCompanies.length)]

  return {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type: eventType.type,
    message,
    company,
    timestamp: new Date(),
  }
}

const getEventIcon = (type: EventItem['type']) => {
  switch (type) {
    case 'fetch': return Database
    case 'update': return RefreshCw
    case 'sync': return CheckCircle
    case 'report': return FileText
    default: return CheckCircle
  }
}

const getEventColors = (type: EventItem['type']) => {
  switch (type) {
    case 'fetch': return { icon: 'text-blue-500', bg: 'bg-blue-500/10', ring: 'ring-blue-500/20' }
    case 'update': return { icon: 'text-emerald-500', bg: 'bg-emerald-500/10', ring: 'ring-emerald-500/20' }
    case 'sync': return { icon: 'text-teal-500', bg: 'bg-teal-500/10', ring: 'ring-teal-500/20' }
    case 'report': return { icon: 'text-amber-500', bg: 'bg-amber-500/10', ring: 'ring-amber-500/20' }
    default: return { icon: 'text-gray-500', bg: 'bg-gray-500/10', ring: 'ring-gray-500/20' }
  }
}

function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 5) return 'Just nu'
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}min`
  return date.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })
}

export function EventLog() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [expanded, setExpanded] = useState(false)
  const [, setTick] = useState(0)

  useEffect(() => {
    const initialEvents: EventItem[] = []
    for (let i = 0; i < 5; i++) {
      const event = generateEvent()
      event.timestamp = new Date(Date.now() - (i * 30000))
      initialEvents.push(event)
    }
    setEvents(initialEvents)

    const interval = setInterval(() => {
      const newEvent = generateEvent()
      setEvents(prev => [newEvent, ...prev.slice(0, 9)])
    }, 15000 + Math.random() * 30000)

    const tickInterval = setInterval(() => setTick(t => t + 1), 10000)

    return () => {
      clearInterval(interval)
      clearInterval(tickInterval)
    }
  }, [])

  const latestEvent = events[0]
  if (!latestEvent) return null

  const LatestIcon = getEventIcon(latestEvent.type)
  const latestColors = getEventColors(latestEvent.type)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: 1.2, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="fixed bottom-6 right-6 z-50"
    >
      <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl shadow-gray-900/10 border border-gray-200/50 overflow-hidden w-[340px]">
        {/* Premium Header with gradient */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-5 py-4 flex items-center justify-between bg-gradient-to-r from-gray-50 to-white hover:from-gray-100 hover:to-gray-50 transition-all duration-300"
        >
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/30">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <span className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white animate-pulse" />
            </div>
            <div className="text-left">
              <span className="text-sm font-semibold text-gray-900 block">Händelselogg</span>
              <span className="text-xs text-gray-500">{events.length} aktiviteter</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
              Live
            </span>
            <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`} />
          </div>
        </button>

        {/* Latest Event - Always visible with emphasis */}
        <AnimatePresence mode="wait">
          <motion.div
            key={latestEvent.id}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="px-5 py-4 border-t border-gray-100 bg-gradient-to-r from-white to-gray-50/50"
          >
            <div className="flex items-start gap-4">
              <div className={`w-10 h-10 rounded-xl ${latestColors.bg} ring-1 ${latestColors.ring} flex items-center justify-center flex-shrink-0`}>
                <LatestIcon className={`w-5 h-5 ${latestColors.icon}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="w-3 h-3 text-amber-500" />
                  <span className="text-xs font-medium text-amber-600">Senaste</span>
                  <span className="text-xs text-gray-400">· {formatRelativeTime(latestEvent.timestamp)}</span>
                </div>
                <p className="text-sm text-gray-900 font-medium">
                  {latestEvent.message.replace(' för', '')}
                </p>
                <p className="text-sm text-gray-600 mt-0.5">
                  {latestEvent.company}
                </p>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Expanded Event List */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="border-t border-gray-100 overflow-hidden"
            >
              <div className="px-2 py-2">
                <div className="max-h-72 overflow-y-auto scrollbar-hide">
                  {events.slice(1).map((event, index) => {
                    const EventIcon = getEventIcon(event.type)
                    const colors = getEventColors(event.type)
                    return (
                      <motion.div
                        key={event.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05, ease: [0.16, 1, 0.3, 1] }}
                        className="px-3 py-3 flex items-start gap-3 hover:bg-gray-50 rounded-xl transition-colors cursor-default group"
                      >
                        <div className={`w-8 h-8 rounded-lg ${colors.bg} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform`}>
                          <EventIcon className={`w-4 h-4 ${colors.icon}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-700">
                            {event.message.replace(' för', '')}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs font-medium text-gray-900">{event.company}</span>
                            <span className="w-1 h-1 rounded-full bg-gray-300" />
                            <span className="text-xs text-gray-400">{formatRelativeTime(event.timestamp)}</span>
                          </div>
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              </div>

              {/* Footer */}
              <div className="px-5 py-3 bg-gray-50 border-t border-gray-100">
                <p className="text-xs text-gray-500 text-center">
                  Visar senaste {events.length} händelser
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
