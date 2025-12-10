# Loop Data Platform

En komplett plattform för Impact Loops företagsdatabas med automatisk POIT-övervakning.

## 🌐 Live Demo

[https://isakskogstad.github.io/Loop-Tool/](https://isakskogstad.github.io/Loop-Tool/)

---

## 📊 Loop Tool (Frontend)

Visuell showcase för Impact Loops förbättrade företagsdatabas.

### Features

- **Live Data** - Realtidsdata från Supabase PostgreSQL
- **Interaktiv Tabell** - 1,200+ svenska impact-företag
- **Sektoranalys** - Visualisering av sektorfördelning
- **Före/Efter Jämförelse** - Se skillnaden mot original Excel

### Tech Stack

- React + TypeScript
- Vite
- Tailwind CSS 4
- Framer Motion
- Recharts
- Supabase

### Development

```bash
npm install
npm run dev
```

---

## 🔔 POIT Monitor (Backend)

Automatisk övervakning av [Post- och Inrikes Tidningar](https://poit.bolagsverket.se) med notifikationer för bevakade företag.

### Features

- ✅ **Automatisk scraping** av POIT-kungörelser (konkurser, registreringar, kallelser)
- ✅ **Matchning** mot 1,200+ bevakade företag från Impact Loop-portföljen
- ✅ **Email-notifikationer** via Resend när bevakade företag dyker upp
- ✅ **GitHub Actions** - Kör automatiskt 3x/dag (07:00, 13:00, 19:00 CET)

### Quick Start

```bash
cd poit-monitor
pip install -r requirements.txt

# Kör sync manuellt
python scripts/poit_sync.py --debug
```

### API Endpoints

| Endpoint | Beskrivning |
|----------|-------------|
| `GET /api/v1/watchlist` | Hämta bevakningslista |
| `POST /api/v1/watchlist` | Lägg till bevakning |
| `GET /api/v1/announcements` | Hämta kungörelser |
| `GET /api/v1/stats` | Sync-statistik |

📖 **Full dokumentation:** [poit-monitor/README.md](poit-monitor/README.md)

---

## 📈 Databasjämförelse

| Original (Excel) | Förbättrad (Supabase) |
|-----------------|----------------------|
| 1 sheet, 18 kolumner | 6+ relaterade tabeller |
| Ägare som text | 4,941 strukturerade poster |
| Sektorer kommaseparerade | 1,449 normaliserade |
| 2 års finansdata | 2,202 historiska poster |

---

## 🏗️ Projektstruktur

```
Loop-Tool/
├── src/                      # React frontend
├── poit-monitor/             # POIT övervakning (Python)
│   ├── src/
│   │   ├── scrapers/         # Web scraping
│   │   ├── api.py            # FastAPI endpoints
│   │   └── poit_monitor.py   # Sync service
│   └── scripts/              # CLI verktyg
└── .github/workflows/        # GitHub Actions
```

---

## 🔐 Environment Variables

### Frontend (.env)
```
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

### POIT Monitor (GitHub Secrets)
```
SUPABASE_URL=...
SUPABASE_KEY=...        # service_role key
RESEND_API_KEY=...
```

---

Built for **Impact Loop** | Powered by **Supabase**
