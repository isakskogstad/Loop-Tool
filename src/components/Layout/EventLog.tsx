import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, RefreshCw, Database, FileText, CheckCircle } from 'lucide-react'

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

const getEventIconClass = (type: EventItem['type']) => {
  switch (type) {
    case 'fetch': return 'text-blue-600 bg-blue-50'
    case 'update': return 'text-emerald-600 bg-emerald-50'
    case 'sync': return 'text-emerald-600 bg-emerald-50'
    case 'report': return 'text-amber-600 bg-amber-50'
    default: return 'text-gray-600 bg-gray-50'
  }
}

function formatRelativeTime(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 5) return 'Just nu'
  if (seconds < 60) return `för ${seconds}s sedan`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `för ${minutes}min sedan`
  return date.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })
}

export function EventLog() {
  const [events, setEvents] = useState<EventItem[]>([])
  const [expanded, setExpanded] = useState(false)
  const [, setTick] = useState(0) // For re-rendering relative times

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

    // Update relative times every 10 seconds
    const tickInterval = setInterval(() => setTick(t => t + 1), 10000)

    return () => {
      clearInterval(interval)
      clearInterval(tickInterval)
    }
  }, [])

  const latestEvent = events[0]
  if (!latestEvent) return null

  const LatestIcon = getEventIcon(latestEvent.type)
  const latestIconClass = getEventIconClass(latestEvent.type)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 1, duration: 0.4 }}
      className="fixed bottom-4 right-4 z-50"
    >
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden w-80">
        {/* Header */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className="relative">
              <div className="w-2 h-2 bg-emerald-500 rounded-full" />
              <span className="absolute inset-0 w-2 h-2 bg-emerald-400 rounded-full animate-ping opacity-75" />
            </div>
            <span className="text-sm font-medium text-gray-900">Händelser</span>
            <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full">
              {events.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">{formatRelativeTime(latestEvent.timestamp)}</span>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
          </div>
        </button>

        {/* Latest Event - Always visible */}
        <AnimatePresence mode="wait">
          <motion.div
            key={latestEvent.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.2 }}
            className="px-4 py-3 border-t border-gray-50 flex items-start gap-3"
          >
            <div className={`mt-0.5 w-8 h-8 rounded-lg flex items-center justify-center ${latestIconClass}`}>
              <LatestIcon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900">
                {latestEvent.message.replace(' för', '')}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                <span className="font-medium">{latestEvent.company}</span>
              </p>
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
              <div className="max-h-64 overflow-y-auto">
                {events.slice(1).map((event, index) => {
                  const EventIcon = getEventIcon(event.type)
                  const iconClass = getEventIconClass(event.type)
                  return (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.03 }}
                      className="px-4 py-2.5 flex items-start gap-3 hover:bg-gray-50 transition-colors"
                    >
                      <div className={`mt-0.5 w-6 h-6 rounded-md flex items-center justify-center ${iconClass} opacity-80`}>
                        <EventIcon className="w-3 h-3" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-700">
                          {event.message.replace(' för', '')}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs font-medium text-gray-900">{event.company}</span>
                          <span className="text-[10px] text-gray-400">{formatRelativeTime(event.timestamp)}</span>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
