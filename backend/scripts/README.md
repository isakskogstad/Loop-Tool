# Scripts

## daily_sync.py

Fullständig daglig synkronisering som fungerar precis som vanlig API-berikning.

### Funktioner

- **Full berikning**: Hämtar komplett data från officiella källor
- **Historikspårning**: Skapar snapshots före uppdateringar (styrelseändringar etc. kan spåras)
- **Komplett data**: Lagrar roller, ekonomi, branscher, varumärken, koncernstruktur
- **Smart ändringsdetektering**: Loggar vad som ändrats (namn, status, antal roller, etc.)

### Hur det fungerar

1. Hämtar alla `orgnr` från Supabase `companies`-tabellen
2. För varje företag:
   - Hämtar nuvarande data (för jämförelse)
   - Anropar `orchestrator.get_company_async(force_refresh=True)`
   - Hämtar färsk data parallellt från datakällorna
   - Skapar historik-snapshot före uppdatering
   - Lagrar all data: företag, roller, ekonomi, branscher, etc.
3. Loggar ändringar med före/efter-värden

### Tidsuppskattningar

| Antal företag | Uppskattad tid |
|---------------|----------------|
| 50 | ~2 minuter |
| 100 | ~4 minuter |
| 176 | ~6 minuter |
| 500 | ~17 minuter |

### Rate Limiting

| Gräns | Värde |
|-------|-------|
| Mellan företag | 2 sekunder |
| Per minut | ~30 företag |

### Köra lokalt

```bash
# Sätt miljövariabler
export SUPABASE_URL="https://ditt-projekt.supabase.co"
export SUPABASE_KEY="din-service-role-key"

# Eller använd .env fil
cp .env.example .env
# Redigera .env med dina uppgifter

# Kör från projektroten
python scripts/daily_sync.py
```

### GitHub Actions (Automatiskt)

Synken körs automatiskt via GitHub Actions:

- **Schema:** Dagligen kl 06:00 CET / 07:00 CEST
- **Manuell trigger:** Gå till Actions-fliken → "Daily Company Sync" → "Run workflow"
- **Timeout:** 60 minuter

### GitHub Secrets

Sätt dessa i: Settings → Secrets and variables → Actions → New repository secret

| Secret-namn | Beskrivning |
|-------------|-------------|
| `SUPABASE_URL` | Supabase projekt-URL |
| `SUPABASE_KEY` | Supabase service role key |

### Exempelutdata

```
2025-12-09 06:00:01 - INFO - ============================================================
2025-12-09 06:00:01 - INFO - DAILY SYNC STARTED (Full Enrichment Mode)
2025-12-09 06:00:01 - INFO - Found 176 companies in database
2025-12-09 06:00:01 - INFO - Estimated time: ~5.9 minutes
2025-12-09 06:00:02 - INFO - Progress: 1/176 (0.6%) - Elapsed: 0.0m - Remaining: ~5.8m
2025-12-09 06:00:52 - INFO - Progress: 25/176 (14.2%) - Elapsed: 0.8m - Remaining: ~5.0m
2025-12-09 06:01:15 - INFO -   5567037485: UPDATED - Spotify AB
2025-12-09 06:01:15 - INFO -     roles: 12 -> 14
2025-12-09 06:01:15 - INFO -     financials: 5 -> 6
...
2025-12-09 06:06:15 - INFO - ============================================================
2025-12-09 06:06:15 - INFO - DAILY SYNC COMPLETED
2025-12-09 06:06:15 - INFO - Duration: 6.2 minutes (374 seconds)
2025-12-09 06:06:15 - INFO - Total companies: 176
2025-12-09 06:06:15 - INFO - Processed: 176
2025-12-09 06:06:15 - INFO - Updated: 12
2025-12-09 06:06:15 - INFO - Unchanged: 162
2025-12-09 06:06:15 - INFO - Not found: 2
2025-12-09 06:06:15 - INFO - Errors: 0
```

### Felnotifieringar

Om synken misslyckas:
1. GitHub Action skapar/uppdaterar en issue med label `sync-failure`
2. Kolla Actions-fliken för detaljerade loggar
3. Vanliga problem:
   - Utgångna credentials
   - Supabase-anslutningsproblem
   - Tillfällig blockering (för många anrop)

### Vad som uppdateras

| Datatyp | Historik spåras |
|---------|-----------------|
| Grundinfo (namn, status) | ✅ |
| Adress | ✅ |
| SNI-koder (branscher) | ✅ |
| Styrelsemedlemmar (roller) | ✅ |
| Ekonomisk data | ✅ |
| Koncernstruktur | ✅ |
| Varumärken | ✅ |
