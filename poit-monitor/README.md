# POIT Monitor 🔔

Automatisk övervakning av [Post- och Inrikes Tidningar (POIT)](https://poit.bolagsverket.se) med notifikationer för bevakade företag.

## Funktioner

- ✅ **Automatisk scraping** av POIT-kungörelser (konkurser, registreringar, kallelser, etc.)
- ✅ **Matchning** mot 1200+ bevakade företag från Impact Loop-portföljen
- ✅ **Email-notifikationer** via Resend när bevakade företag dyker upp
- ✅ **API endpoints** för att hantera bevakningar
- ✅ **GitHub Actions** för schemalagd körning (07:00, 13:00, 19:00 CET)

## Quick Start

### 1. Installera dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurera environment

Skapa `.env` fil:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
RESEND_API_KEY=re_your-api-key
```

### 3. Kör sync manuellt

```bash
# Full sync med debug
python scripts/poit_sync.py --debug

# Dry run (ingen databas-skrivning)
python scripts/poit_sync.py --dry-run --debug

# Endast konkurser
python scripts/poit_sync.py --categories konkurser --debug
```

### 4. Starta API lokalt

```bash
uvicorn src.api:app --reload --port 8000
```

## API Endpoints

| Endpoint | Metod | Beskrivning |
|----------|-------|-------------|
| `/api/v1/watchlist` | GET | Hämta bevakningslista |
| `/api/v1/watchlist` | POST | Lägg till bevakning |
| `/api/v1/watchlist/{orgnr}` | DELETE | Ta bort bevakning |
| `/api/v1/announcements` | GET | Hämta kungörelser |
| `/api/v1/stats` | GET | Sync-statistik |
| `/api/v1/companies/search` | GET | Sök företag för bevakning |

## Kategorier

| Kategori | Beskrivning |
|----------|-------------|
| `konkurser` | Konkurser och konkursbeslut |
| `bolagsverkets_registreringar` | Bolagsregistreringar |
| `kallelser` | Kallelser på okända borgenärer |
| `skuldsaneringar` | Skuldsaneringsbeslut |
| `familjeratt` | Familjerättsliga kungörelser |

## Projektstruktur

```
├── .github/workflows/
│   └── poit-monitor.yml      # GitHub Actions
├── scripts/
│   └── poit_sync.py          # CLI för sync
├── src/
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── poit_scraper.py   # Huvudscraper (undetected-chromedriver)
│   ├── api.py                # FastAPI endpoints
│   ├── poit_monitor.py       # Sync service
│   └── poit_notifications.py # Email via Resend
├── requirements.txt
└── README.md
```

## Databas-schema (Supabase)

### user_watchlists
- `id` - UUID
- `user_id` - UUID (NULL = systembevakning)
- `orgnr` - TEXT
- `company_name` - TEXT
- `alert_categories` - TEXT[]
- `email_notifications` - BOOLEAN

### poit_announcements
- `id` - UUID
- `poit_id` - TEXT (UNIQUE, för deduplicering)
- `category` - TEXT
- `title` - TEXT
- `content` - TEXT
- `announcement_date` - DATE
- `extracted_orgnrs` - TEXT[]

### poit_notifications
- `id` - UUID
- `user_id` - UUID
- `announcement_id` - UUID (FK)
- `orgnr` - TEXT
- `status` - pending/sent/failed/skipped

### poit_sync_stats
- `id` - UUID
- `sync_date` - DATE
- `status` - running/completed/failed
- `announcements_found` - INTEGER
- `announcements_new` - INTEGER
- `notifications_sent` - INTEGER

## GitHub Actions Secrets

Lägg till följande secrets i ditt GitHub-repo:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `RESEND_API_KEY`

## Teknisk Arkitektur

```
GitHub Actions (3x/dag)
        │
        ▼
┌───────────────────┐
│ undetected-chrome │ → Scrapar poit.bolagsverket.se
│   + xvfb display  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ poit_announcements│ → Lagrar nya kungörelser
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  user_watchlists  │ → Matchar mot 1217 bevakade orgnr
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│poit_notifications │ → Skapar notifikationer
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│   Resend Email    │ → Skickar alerts till användare
└───────────────────┘
```

## CAPTCHA-hantering

POIT använder CAPTCHA/bot-protection. Lösningen:

1. **undetected-chromedriver** - Kringgår bot-detection
2. **headless=False** med **xvfb** - Virtual display i CI
3. **Klick-baserad navigation** - Angular-appen kräver riktig interaktion

## Licens

MIT
