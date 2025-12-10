# Nyemissioner Integration Plan

## 1. Dataanalys från nyemissioner.se

### Nyemission (från listNyemissioner)
```typescript
{
  company: string,        // "3 Prospect Invest AB"
  slug: string,           // "3-prospect-invest-ab-2"
  url: string,            // Full URL till nyemissioner.se
  industry: string,       // "Okänd" (behöver förbättras)
  exchange: string,       // "Onoterat", "NGM Nordic SME", etc.
  subscriptionStart: string | null,
  subscriptionEnd: string | null
}
```

### Börsnotering (från listBorsnoteringar)
```typescript
{
  company: string,        // "Tessin Nordic Holding AB"
  slug: string,           // "tessin-nordic-holding-ab"
  url: string,
  targetExchange: string, // "Spotlight", "Nasdaq Stockholm"
  listingType: string,    // "Notering", "Listbyte", "IPO"
  listingDate: string | null,
  status: string,         // "Kommande", "Genomförd", "Inställd"
  subscriptionStart: string | null,
  subscriptionEnd: string | null
}
```

### Detaljerad Nyemission (från getNyemission)
```typescript
{
  ...Nyemission,
  amount: string | null,           // Emissionsbelopp
  subscriptionPrice: string | null, // Teckningskurs
  valuation: string | null,         // Pre/post-money valuation
  prospectusUrl: string | null,     // Länk till prospekt/memorandum
  companyWebsite: string | null,
  offerType: string | null,         // Typ av erbjudande
  description: string | null,
  terms: string | null,
  recordDate: string | null,        // Avstämningsdag
  lastUpdated: string | null
}
```

---

## 2. Befintlig Supabase-struktur (relevant)

| Tabell | Relevans |
|--------|----------|
| `companies` | FK för orgnr, företagsdata |
| `company_registry` | 887k företag för namn→orgnr lookup |
| `announcements` | Liknande struktur för events |
| `financials` | Kan länkas för valuation-kontext |

---

## 3. Förslag: Nya tabeller

### 3.1 `equity_offerings` (Nyemissioner + Börsnoteringar)

```sql
CREATE TABLE equity_offerings (
  id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),

  -- Identifiering
  company_orgnr TEXT REFERENCES companies(orgnr),  -- NULL om ej matchat
  company_name TEXT NOT NULL,                       -- Från scrape
  slug TEXT NOT NULL UNIQUE,                        -- "3-prospect-invest-ab-2"
  source_url TEXT,                                  -- nyemissioner.se URL

  -- Typ av erbjudande
  offering_type TEXT NOT NULL CHECK (offering_type IN (
    'nyemission',           -- Vanlig nyemission
    'foretradesemission',   -- Företrädesemission
    'riktad_emission',      -- Riktad emission
    'ipo',                  -- Börsintroduktion
    'listbyte',             -- Byte av lista
    'spridningsemission'    -- Spridning av aktier
  )),

  -- Marknadsplats
  exchange TEXT,            -- "NGM Nordic SME", "Spotlight", etc.
  listing_status TEXT,      -- "Onoterat", "Noterat"

  -- Tidsperiod
  subscription_start DATE,
  subscription_end DATE,
  record_date DATE,         -- Avstämningsdag
  listing_date DATE,        -- För IPO:er

  -- Belopp och villkor
  amount_sek BIGINT,                    -- Emissionsbelopp i SEK
  subscription_price_sek NUMERIC(12,4), -- Teckningskurs
  pre_money_valuation BIGINT,           -- Pre-money i SEK
  post_money_valuation BIGINT,          -- Post-money i SEK

  -- Aktieinfo (viktigt för valuation!)
  shares_before BIGINT,     -- Antal aktier före
  shares_offered BIGINT,    -- Antal nya aktier
  shares_after BIGINT,      -- Antal aktier efter
  quota_value NUMERIC(12,4), -- Kvotvärde

  -- Dokument
  prospectus_url TEXT,
  memorandum_url TEXT,
  company_website TEXT,

  -- Beskrivning
  description TEXT,
  terms TEXT,

  -- Status
  status TEXT DEFAULT 'active' CHECK (status IN (
    'upcoming',    -- Kommande
    'active',      -- Pågående teckningsperiod
    'completed',   -- Genomförd
    'cancelled'    -- Inställd
  )),

  -- Metadata
  source TEXT DEFAULT 'nyemissioner.se',
  scraped_at TIMESTAMPTZ DEFAULT now(),
  last_updated TIMESTAMPTZ,
  raw_data JSONB,           -- Spara all rådata

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index för snabb sökning
CREATE INDEX idx_equity_offerings_company ON equity_offerings(company_orgnr);
CREATE INDEX idx_equity_offerings_type ON equity_offerings(offering_type);
CREATE INDEX idx_equity_offerings_status ON equity_offerings(status);
CREATE INDEX idx_equity_offerings_dates ON equity_offerings(subscription_start, subscription_end);
CREATE INDEX idx_equity_offerings_slug ON equity_offerings(slug);
```

### 3.2 `equity_offering_news` (Nyheter kopplade till emissioner)

```sql
CREATE TABLE equity_offering_news (
  id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
  offering_id UUID REFERENCES equity_offerings(id),
  title TEXT NOT NULL,
  url TEXT,
  published_at DATE,
  excerpt TEXT,
  source TEXT DEFAULT 'nyemissioner.se',
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. Koppling till befintliga data

### 4.1 Matcha företag via namn → orgnr

```sql
-- Funktion för fuzzy matching mot company_registry
CREATE OR REPLACE FUNCTION match_company_orgnr(company_name TEXT)
RETURNS TEXT AS $$
  SELECT orgnr
  FROM company_registry
  WHERE name_search @@ plainto_tsquery('swedish', company_name)
  ORDER BY ts_rank(name_search, plainto_tsquery('swedish', company_name)) DESC
  LIMIT 1;
$$ LANGUAGE sql STABLE;
```

### 4.2 Beräkna valuation från XBRL-data

Om vi har `shares_after` och `subscription_price_sek`:
```
post_money_valuation = shares_after * subscription_price_sek
```

Om vi har `aktiekapital` och `kvotvärde` från XBRL:
```
antal_aktier = aktiekapital / kvotvärde
```

---

## 5. API-harmonisering med LoopAutoClient

### 5.1 Utöka LoopAutoClient med nyemissioner-metoder

```typescript
// I api-client.ts - lägg till dessa metoder:

class LoopAutoClient {
  // ... befintliga metoder ...

  // NYA METODER FÖR EQUITY OFFERINGS

  async listEquityOfferings(filters?: {
    type?: 'nyemission' | 'ipo' | 'all';
    status?: 'upcoming' | 'active' | 'completed';
    exchange?: string;
    limit?: number;
  }): Promise<EquityOffering[]>

  async getEquityOffering(slug: string): Promise<EquityOfferingDetails>

  async getCompanyOfferings(orgnr: string): Promise<EquityOffering[]>

  // Kombinerad sökning
  async searchWithOfferings(query: string): Promise<{
    companies: Company[];
    offerings: EquityOffering[];
  }>
}
```

### 5.2 Nya endpoints i Loop API (backend)

```
GET /api/v1/offerings
GET /api/v1/offerings/:slug
GET /api/v1/companies/:orgnr/offerings
GET /api/v1/offerings/search?q=...
```

---

## 6. Synkroniseringsstrategi

### Cron-jobb för daglig uppdatering:

```typescript
async function syncNyemissioner() {
  const nyClient = new NyemissionerClient();

  // 1. Hämta alla aktuella nyemissioner
  const nyemissioner = await nyClient.listNyemissioner();
  const borsnoteringar = await nyClient.listBorsnoteringar();

  // 2. För varje: uppdatera eller skapa i Supabase
  for (const item of [...nyemissioner.items, ...borsnoteringar.items]) {
    // Matcha mot company_registry för orgnr
    const orgnr = await matchCompanyOrgnr(item.company);

    // Upsert i equity_offerings
    await supabase.from('equity_offerings').upsert({
      slug: item.slug,
      company_name: item.company,
      company_orgnr: orgnr,
      // ... resten av fälten
    }, { onConflict: 'slug' });
  }

  // 3. Uppdatera status för gamla (markera completed/cancelled)
}
```

---

## 7. Nästa steg

1. [ ] Skapa `equity_offerings` tabell via migration
2. [ ] Skapa `match_company_orgnr` funktion
3. [ ] Lägg till nya endpoints i Loop API backend
4. [ ] Utöka LoopAutoClient med offerings-metoder
5. [ ] Skapa sync-script för daglig uppdatering
6. [ ] Fixa getNyemission() selektorer för bättre detaljer

