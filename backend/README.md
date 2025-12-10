# Loop API

**Loop API är en datakälla för att hitta och följa data om företag och andra bolag.**

## Statistik

| Data | Antal |
|------|-------|
| Sökbara företag | 887 000+ |
| Cachade företag | ~200 |
| Årsredovisningar | XBRL-data |

## API-dokumentation

- **Swagger UI:** https://loop-auto-api.onrender.com/docs
- **ReDoc:** https://loop-auto-api.onrender.com/redoc

## Snabbstart

```bash
# Sök företag
curl "https://loop-auto-api.onrender.com/api/v1/lookup?name=spotify" \
  -H "X-API-Key: DIN_API_NYCKEL"

# Hämta företagsdata
curl "https://loop-auto-api.onrender.com/api/v1/companies/5567037485" \
  -H "X-API-Key: DIN_API_NYCKEL"
```

## API-nyckel

För att använda Loop API behöver du en API-nyckel.

**Ansök om API-nyckel:**
```bash
curl -X POST "https://loop-auto-api.onrender.com/api/v1/request-key" \
  -H "Content-Type: application/json" \
  -d '{"email": "din@email.se", "name": "Ditt Namn", "use_case": "Beskriv användning"}'
```

Inkludera API-nyckeln i varje anrop via headern `X-API-Key`.

## Endpoints

### Sök & Lookup

| Endpoint | Beskrivning |
|----------|-------------|
| `GET /api/v1/lookup?name={sökord}` | Sök företag på namn |
| `GET /api/v1/search/companies` | Avancerad sökning med filter |

### Företagsdata

| Endpoint | Beskrivning |
|----------|-------------|
| `GET /api/v1/companies/{orgnr}` | Komplett företagsdata |
| `GET /api/v1/companies/{orgnr}/summary` | Snabb sammanfattning |
| `GET /api/v1/companies/{orgnr}/board` | Styrelse & ledning |
| `GET /api/v1/companies/{orgnr}/financials` | Finansiell historik |
| `GET /api/v1/companies/{orgnr}/structure` | Koncernstruktur |
| `GET /api/v1/companies/{orgnr}/announcements` | Kungörelser |

### Årsredovisningar (XBRL)

| Endpoint | Beskrivning |
|----------|-------------|
| `GET /api/v1/companies/{orgnr}/annual-reports` | Lista årsredovisningar |
| `GET /api/v1/companies/{orgnr}/annual-reports/{year}` | Specifik årsredovisning |
| `GET /api/v1/companies/{orgnr}/xbrl-facts` | XBRL-data (finansiella fakta) |
| `GET /api/v1/companies/{orgnr}/audit-history` | Revisionshistorik |
| `POST /api/v1/companies/{orgnr}/sync-annual-reports` | Synka årsredovisningar |

### Historik

| Endpoint | Beskrivning |
|----------|-------------|
| `GET /api/v1/companies/{orgnr}/history` | Alla historiska snapshots |
| `GET /api/v1/companies/{orgnr}/history/board` | Styrelsehistorik |

### Berikning

| Endpoint | Beskrivning |
|----------|-------------|
| `POST /api/v1/enrich` | Berika ett företag |
| `POST /api/v1/enrich/batch` | Berika flera företag (max 10) |

## Rate Limits

- Generellt: 100 anrop/minut
- Berikning: 10 anrop/minut
- Årsredovisningssynk: 10 anrop/minut

## Licens

MIT - Se [LICENSE](LICENSE)

---

**Version 3.3.0** | [API Status](https://loop-auto-api.onrender.com/health)
