/**
 * Sync Equity Offerings from nyemissioner.se to Supabase
 *
 * Usage: npx tsx sync-offerings.mts
 */

import { NyemissionerClient, type Nyemission, type Borsnotering } from './dist/index.js';

const SUPABASE_URL = 'https://wzkohritxdrstsmwopco.supabase.co';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  console.error('❌ Missing SUPABASE_SERVICE_KEY environment variable');
  process.exit(1);
}

interface EquityOffering {
  company_name: string;
  company_orgnr?: string | null;
  slug: string;
  source_url: string;
  offering_type: string;
  exchange?: string | null;
  listing_status?: string | null;
  subscription_start?: string | null;
  subscription_end?: string | null;
  listing_date?: string | null;
  status: string;
  source: string;
  raw_data: Record<string, unknown>;
}

async function supabaseQuery(query: string): Promise<unknown[]> {
  const response = await fetch(`${SUPABASE_URL}/rest/v1/rpc/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_SERVICE_KEY!,
      'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
    },
    body: JSON.stringify({ query }),
  });
  return response.json();
}

async function matchOrgnr(companyName: string): Promise<string | null> {
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/rpc/match_company_orgnr`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_SERVICE_KEY!,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
      },
      body: JSON.stringify({ search_name: companyName }),
    }
  );
  const result = await response.text();
  // Result is just the orgnr string or null
  return result && result !== 'null' ? result.replace(/"/g, '') : null;
}

async function upsertOffering(offering: EquityOffering): Promise<void> {
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/equity_offerings`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_SERVICE_KEY!,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
        'Prefer': 'resolution=merge-duplicates',
      },
      body: JSON.stringify(offering),
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Upsert failed: ${error}`);
  }
}

function determineStatus(item: Nyemission | Borsnotering): string {
  const now = new Date();
  const start = item.subscriptionStart ? new Date(item.subscriptionStart) : null;
  const end = item.subscriptionEnd ? new Date(item.subscriptionEnd) : null;

  if (end && end < now) return 'completed';
  if (start && start > now) return 'upcoming';
  if (start && end && start <= now && end >= now) return 'active';
  return 'upcoming'; // Default
}

async function syncNyemissioner(): Promise<number> {
  console.log('\n📋 Syncing nyemissioner...');
  const client = new NyemissionerClient({ rateLimitMs: 1500 });

  const result = await client.listNyemissioner();
  console.log(`   Found ${result.items.length} nyemissioner`);

  // Deduplicate by slug
  const uniqueItems = new Map<string, Nyemission>();
  for (const item of result.items) {
    if (!uniqueItems.has(item.slug)) {
      uniqueItems.set(item.slug, item);
    }
  }

  let synced = 0;
  for (const [slug, item] of uniqueItems) {
    try {
      // Match orgnr
      const orgnr = await matchOrgnr(item.company);

      const offering: EquityOffering = {
        company_name: item.company,
        company_orgnr: orgnr,
        slug: item.slug,
        source_url: item.url,
        offering_type: 'nyemission',
        exchange: item.exchange !== 'Okänd' ? item.exchange : null,
        listing_status: item.exchange === 'Onoterat' ? 'Onoterat' : 'Noterat',
        subscription_start: item.subscriptionStart,
        subscription_end: item.subscriptionEnd,
        status: determineStatus(item),
        source: 'nyemissioner.se',
        raw_data: item as unknown as Record<string, unknown>,
      };

      await upsertOffering(offering);
      synced++;
      console.log(`   ✓ ${item.company} (${orgnr || 'no orgnr'})`);
    } catch (error) {
      console.log(`   ✗ ${item.company}: ${error}`);
    }
  }

  return synced;
}

async function syncBorsnoteringar(): Promise<number> {
  console.log('\n📊 Syncing börsnoteringar...');
  const client = new NyemissionerClient({ rateLimitMs: 1500 });

  const result = await client.listBorsnoteringar();
  console.log(`   Found ${result.items.length} börsnoteringar`);

  // Deduplicate by slug
  const uniqueItems = new Map<string, Borsnotering>();
  for (const item of result.items) {
    if (!uniqueItems.has(item.slug)) {
      uniqueItems.set(item.slug, item);
    }
  }

  let synced = 0;
  for (const [slug, item] of uniqueItems) {
    try {
      // Match orgnr
      const orgnr = await matchOrgnr(item.company);

      // Determine offering type
      let offeringType = 'ipo';
      if (item.listingType === 'Listbyte') offeringType = 'listbyte';
      else if (item.listingType === 'Spridningsemission') offeringType = 'spridningsemission';

      const offering: EquityOffering = {
        company_name: item.company,
        company_orgnr: orgnr,
        slug: item.slug,
        source_url: item.url,
        offering_type: offeringType,
        exchange: item.targetExchange !== 'Okänd' ? item.targetExchange : null,
        listing_status: 'Noterat',
        subscription_start: item.subscriptionStart,
        subscription_end: item.subscriptionEnd,
        listing_date: item.listingDate,
        status: item.status === 'Genomförd' ? 'completed' :
                item.status === 'Inställd' ? 'cancelled' : 'upcoming',
        source: 'nyemissioner.se',
        raw_data: item as unknown as Record<string, unknown>,
      };

      await upsertOffering(offering);
      synced++;
      console.log(`   ✓ ${item.company} (${orgnr || 'no orgnr'})`);
    } catch (error) {
      console.log(`   ✗ ${item.company}: ${error}`);
    }
  }

  return synced;
}

async function main() {
  console.log('='.repeat(50));
  console.log('EQUITY OFFERINGS SYNC');
  console.log('='.repeat(50));
  console.log(`Time: ${new Date().toISOString()}`);

  const nyemissionerCount = await syncNyemissioner();
  const borsnoteringarCount = await syncBorsnoteringar();

  console.log('\n' + '='.repeat(50));
  console.log('SUMMARY');
  console.log('='.repeat(50));
  console.log(`Nyemissioner synced: ${nyemissionerCount}`);
  console.log(`Börsnoteringar synced: ${borsnoteringarCount}`);
  console.log(`Total: ${nyemissionerCount + borsnoteringarCount}`);
}

main().catch(console.error);
