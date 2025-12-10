import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, ChevronUp, ChevronDown, Database, RefreshCw, FileText } from 'lucide-react'

interface EventItem {
  id: string
  type: 'fetch' | 'update' | 'sync' | 'report'
  message: string
  company?: string
  timestamp: Date
}

// Simulated events - in production this would come from actual API calls
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
    case 'sync': return Activity
    case 'report': return FileText
    default: return Activity
  }
}

const getEventColor = (type: EventItem['type']) => {
  switch (type) {
    case 'fetch': return 'text-blue-500 bg-blue-50'
    case 'update': return 'text-emerald-500 bg-emerald-50'
    case 'sync': return 'text-purple-500 bg-purple-50'
    case 'report': return 'text-amber-500 bg-amber-50'
    default: return 'text-gray-500 bg-gray-50'
  }
}

export function EventLog() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [expanded, setExpanded] = useState(false)

  // Generate initial events and periodic updates
  useEffect(() => {
    // Generate some initial events
    const initialEvents: EventItem[] = []
    for (let i = 0; i < 5; i++) {
      const event = generateEvent()
      event.timestamp = new Date(Date.now() - (i * 30000)) // Spread over last 2.5 min
      initialEvents.push(event)
    }
    setEvents(initialEvents)

    // Add new events periodically (every 15-45 seconds)
    const interval = setInterval(() => {
      const newEvent = generateEvent()
      setEvents(prev => [newEvent, ...prev.slice(0, 9)]) // Keep max 10 events
    }, 15000 + Math.random() * 30000)

    return () => clearInterval(interval)
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const latestEvent = events[0]

  if (!latestEvent) return null

  const Icon = getEventIcon(latestEvent.type)
  const colorClass = getEventColor(latestEvent.type)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 1, duration: 0.4 }}
      className="fixed bottom-4 right-4 z-50"
    >
      <div className={`bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden transition-all duration-300 ${
        expanded ? 'w-80' : 'w-72'
      }`}>
        {/* Header - Always visible */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-3 py-2.5 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded-lg ${colorClass}`}>
              <Activity className="w-3.5 h-3.5" />
            </div>
            <span className="text-xs font-semibold text-gray-700">Händelser</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-400 tabular-nums">{formatTime(latestEvent.timestamp)}</span>
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            )}
          </div>
        </button>

        {/* Latest Event - Always shown */}
        <AnimatePresence mode="wait">
          <motion.div
            key={latestEvent.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.2 }}
            className="px-3 pb-2.5 border-t border-gray-100"
          >
            <div className="flex items-start gap-2 pt-2">
              <div className={`p-1 rounded ${colorClass} mt-0.5`}>
                <Icon className="w-3 h-3" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-600 leading-snug">
                  {latestEvent.message}{' '}
                  <span className="font-semibold text-gray-900">{latestEvent.company}</span>
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
              transition={{ duration: 0.2 }}
              className="border-t border-gray-100 overflow-hidden"
            >
              <div className="max-h-48 overflow-y-auto">
                {events.slice(1).map((event, index) => {
                  const EventIcon = getEventIcon(event.type)
                  const eventColor = getEventColor(event.type)
                  return (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="px-3 py-2 hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0"
                    >
                      <div className="flex items-start gap-2">
                        <div className={`p-1 rounded ${eventColor} mt-0.5 opacity-70`}>
                          <EventIcon className="w-2.5 h-2.5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] text-gray-500 leading-snug">
                            {event.message}{' '}
                            <span className="font-medium text-gray-700">{event.company}</span>
                          </p>
                          <span className="text-[9px] text-gray-400 tabular-nums">
                            {formatTime(event.timestamp)}
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Subtle pulse indicator for new events */}
        {!expanded && (
          <div className="absolute top-2 right-12 w-2 h-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-loop-lime opacity-75 animate-ping" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-loop-lime" />
          </div>
        )}
      </div>
    </motion.div>
  )
}
