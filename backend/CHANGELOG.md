# Ändringslogg

Alla viktiga ändringar i Loop API dokumenteras i denna fil.

Formatet är baserat på [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
och projektet följer [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.3.0] - 2025-12-09

### Tillagt
- **Svenska API-kategorier** - Alla endpoint-kategorier nu på svenska
- **Daglig synkronisering** - Automatisk daglig uppdatering av företagsdata
- GitHub Actions workflow (`daily-sync.yml`) som körs kl 06:00 CET
- `scripts/daily_sync.py` - Fristående synkskript med rate limiting
- Synkdokumentation i `scripts/README.md`
- Automatiska felnotifieringar via GitHub Issues

### Ändrat
- API-titel ändrad till "Loop Company Data API"
- Datakällor dolda från externa användare
- Alla endpoint-beskrivningar översatta till svenska

### Tekniskt
- Rate limiting: Respekterar officiella API-gränser
- Ändringsdetektering via datahashing (uppdaterar endast om data ändrats)
- OAuth2 token-hantering med automatisk förnyelse
- Omfattande loggning med progress-tracking

## [3.2.0] - 2025-12-09

### Tillagt
- `related_companies` lagring - Koncernstruktur sparas nu i databasen
- `announcements` lagring - Kungörelser sparas nu i databasen
- Nya databasmetoder: `add_related_companies()`, `add_announcements()`
- Omfattande API-dokumentation i README
- LICENSE-fil (MIT)
- Denna CHANGELOG-fil

### Fixat
- **Batch enrich-bugg** - Lade till saknad `force_refresh` parameter
- **Datapipeline** - `related_companies` och `announcements` skickas nu korrekt till `store_company_complete()`

### Borttaget
- Föråldrade tabeller (via SQL migration):
  - `merinfo_hashes`
  - `vehicles` och `vehicles_history`
  - `beneficial_owners` och `beneficial_owners_history`
  - `signatories`

### Ändrat
- Uppdaterat `store_company_complete()` signatur för att acceptera `related_companies` och `announcements`
- Uppdaterat `setup_supabase_tables.sql` för att ta bort föråldrade tabelldefinitioner

## [3.1.0] - 2025-12-09

### Tillagt
- API-nyckel autentisering (`X-API-Key` header)
- Rate limiting (100 anrop/min generellt, 10 anrop/min berikning)
- SQL-injektionsskydd med input-sanering
- Circuit breaker-integration för resiliens
- Request ID-tracking för feldebugning
- RLS-policyer på alla huvudtabeller
- Prestandaindex för vanliga sökningar

### Ändrat
- CORS-konfiguration använder nu `Config.CORS_ORIGINS` istället för wildcard
- Krävda miljövariabler valideras vid uppstart

## [3.0.0] - 2025-12-09

### Tillagt
- Supabase PostgreSQL-backend (ersätter SQLite)
- Asynkron parallell datahämtning med `asyncio`
- Företagsregister med 887 000+ sökbara företag
- Historiktabeller för ändringsloggning
- Strukturerad loggning med `logging_config.py`

### Ändrat
- Fullständig omskrivning av databaslagret (`supabase_client.py`)
- Data-orkestrator med async-stöd (`orchestrator.py`)
- Ny API-struktur med `/api/v1/` prefix

### Borttaget
- SQLite-databasstöd
- Föråldrade scrapers
- Gammalt `database.py` modul

## [2.0.0] - 2025-12-08

### Tillagt
- Integration med officiella svenska företagsregister
- Finansiell data och styrelsedata
- Grundläggande företagsberiknings-endpoints

### Ändrat
- API-redesign med FastAPI
- Ny datamodell för svenska företagsdata

## [1.0.0] - 2025-12-01

### Tillagt
- Initial release
- Grundläggande företagsuppslagsfunktionalitet
- SQLite-databas för caching
