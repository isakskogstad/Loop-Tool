# Loop Tool - Frontend & UX Guide

## Översikt

Loop Tool är byggt med **React + TypeScript + Tailwind CSS** och använder Vite som build-verktyg.

---

## Filstruktur

```
src/
├── App.tsx                      # Huvudkomponent, loading screen, view toggle
├── main.tsx                     # React entry point
├── index.css                    # Globala CSS-stilar och Tailwind imports
│
├── components/
│   ├── Company/
│   │   ├── CompanyModal.tsx     # Företagsdetaljer (modal med flikar)
│   │   └── CompanyPanel.tsx     # Företagspanel på kartan
│   │
│   ├── Data/
│   │   └── DataTable.tsx        # Tabellvy med infinite scroll
│   │
│   ├── Layout/
│   │   ├── Header.tsx           # Sidhuvud med titel och sök
│   │   ├── Footer.tsx           # Sidfot
│   │   └── EventLog.tsx         # Händelselogg (bottom-right)
│   │
│   ├── Map/
│   │   ├── MapContainer.tsx     # Leaflet-karta
│   │   ├── CompanyMarker.tsx    # Företagsmarkörer
│   │   ├── FloatingStats.tsx    # Statistik-overlay på kartan
│   │   └── ViewportList.tsx     # Lista över synliga företag
│   │
│   └── Stats/
│       └── StatsBar.tsx         # Statistikbar
│
├── context/
│   └── MapContext.tsx           # Global state (filter, vald företag, view mode)
│
├── hooks/
│   └── useCompanies.ts          # Data-fetching från Supabase
│
└── lib/
    └── supabase.ts              # Supabase-klient och typer
```

---

## Nyckelfilar för UX/Design

### 1. Konfiguration

| Fil | Beskrivning |
|-----|-------------|
| `tailwind.config.js` | **Designsystem** - färger, typsnitt, spacing, animationer |
| `src/index.css` | Globala stilar, Tailwind imports, custom utilities |
| `index.html` | HTML-template, Google Fonts, favicon |

### 2. Layout & Navigation

| Fil | Ansvarar för |
|-----|--------------|
| `src/App.tsx` | Loading screen, view toggle (karta/tabell), huvudlayout |
| `src/components/Layout/Header.tsx` | Titel "Loop Tool", sökfält, status |
| `src/components/Layout/Footer.tsx` | Copyright, länkar |
| `src/components/Layout/EventLog.tsx` | Live händelselogg (bottom-right) |

### 3. Vyer

| Fil | Ansvarar för |
|-----|--------------|
| `src/components/Map/MapContainer.tsx` | Kartvy med Leaflet |
| `src/components/Data/DataTable.tsx` | Tabellvy med infinite scroll |

### 4. Företagsvisning

| Fil | Ansvarar för |
|-----|--------------|
| `src/components/Company/CompanyModal.tsx` | Detaljerad företagsvy (modal med flikar) |
| `src/components/Company/CompanyPanel.tsx` | Kompakt företagsinfo på kartan |
| `src/components/Map/CompanyMarker.tsx` | Markörer och kluster på kartan |

### 5. State & Data

| Fil | Ansvarar för |
|-----|--------------|
| `src/context/MapContext.tsx` | Global state: filter, selectedCompany, viewMode |
| `src/hooks/useCompanies.ts` | Hämtar företagsdata från Supabase |
| `src/lib/supabase.ts` | Supabase-klient, TypeScript-typer |

---

## Designsystem (tailwind.config.js)

### Färger

```js
'loop-lime': '#CDFF00'      // Accent-färg (grön/lime)
'loop-black': '#0A0A0A'     // Mörk bakgrund
'loop-gray': '#1A1A1A'      // Sekundär mörk
brand: { 50-950 }           // Emerald-baserad skala
accent: { 50-900 }          // Orange accent
```

### Typsnitt

```js
'display': 'Plus Jakarta Sans'   // Rubriker
'body': 'DM Sans'                // Brödtext
'serif': 'DM Serif Display'      // Logo/titlar
'mono': 'JetBrains Mono'         // Kod/orgnr
```

### Animationer

- `fade-in`, `fade-in-up`, `slide-in-right`
- `pulse-soft`, `pulse-glow`
- `shimmer` (loading states)

---

## Vanliga Ändringar

### Ändra färgschema
→ Redigera `tailwind.config.js` under `theme.extend.colors`

### Ändra typsnitt
→ Redigera `tailwind.config.js` under `theme.extend.fontFamily`
→ Lägg till fonts i `index.html` (Google Fonts)

### Ändra header/titel
→ Redigera `src/components/Layout/Header.tsx`

### Ändra tabellkolumner
→ Redigera `src/components/Data/DataTable.tsx`
→ Kolumnrubriker: `<thead>` sektion (~rad 430-555)
→ Cellinnehåll: `<tbody>` sektion (~rad 556-960)

### Ändra företagsmodal
→ Redigera `src/components/Company/CompanyModal.tsx`
→ Flikar definieras i `tabs` array
→ Innehåll per flik i respektive `TabPanel`

### Ändra kartdesign
→ Redigera `src/components/Map/MapContainer.tsx`
→ Markörer: `src/components/Map/CompanyMarker.tsx`

### Ändra loading screen
→ Redigera `src/App.tsx` → `LoadingScreen` funktion

### Ändra händelselogg
→ Redigera `src/components/Layout/EventLog.tsx`

---

## State Management

All global state hanteras via `MapContext`:

```tsx
const {
  filters,           // { search: string, sector: string | null }
  setFilters,        // Uppdatera filter
  selectedCompany,   // Valt företag (öppnar modal)
  setSelectedCompany,
  viewMode,          // 'map' | 'table'
  setViewMode
} = useMapContext()
```

---

## Build & Deploy

```bash
npm run dev      # Lokal utveckling (localhost:5173)
npm run build    # Produktions-build → dist/
npm run preview  # Förhandsgranska build
```

**Deployed på:** https://loop-tool-frontend.onrender.com

---

## Tech Stack

- **React 18** + TypeScript
- **Vite** (build tool)
- **Tailwind CSS** (styling)
- **Framer Motion** (animationer)
- **Leaflet** + react-leaflet (karta)
- **Supabase** (databas)
- **Lucide React** (ikoner)
