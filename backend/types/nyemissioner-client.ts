/**
 * Nyemissioner.se API Client
 * 
 * En TypeScript-klient för att hämta data om svenska nyemissioner och börsnoteringar
 * från nyemissioner.se via web scraping (ingen officiell API finns).
 * 
 * @author Isak Skogstad
 * @license MIT
 */

import * as cheerio from 'cheerio';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface Nyemission {
  /** Företagsnamn */
  company: string;
  /** URL-slug för detaljsidan */
  slug: string;
  /** Full URL till detaljsidan */
  url: string;
  /** Bransch (t.ex. "Läkemedel/Medicin") */
  industry: string;
  /** Lista (t.ex. "First North", "Nasdaq Stockholm") */
  exchange: string;
  /** Teckningsperiod startdatum (ISO-format) */
  subscriptionStart: string | null;
  /** Teckningsperiod slutdatum (ISO-format) */
  subscriptionEnd: string | null;
}

export interface NyemissionDetails extends Nyemission {
  /** Typ av erbjudande (t.ex. "Nyemission", "Företrädesemission", "IPO") */
  offerType: string;
  /** Emissionsbelopp som sträng (t.ex. "15,1 Mkr") */
  amount: string | null;
  /** Teckningskurs som sträng (t.ex. "0,42 kr per aktie") */
  subscriptionPrice: string | null;
  /** Värdering pre-money (t.ex. "50,33 Mkr pre-money") */
  valuation: string | null;
  /** URL till prospekt (PDF) */
  prospectusUrl: string | null;
  /** Avstämningsdag (ISO-format) */
  recordDate: string | null;
  /** Beskrivning av företaget */
  description: string;
  /** Emissionsvillkor */
  terms: string | null;
  /** Ytterligare information */
  additionalInfo: string | null;
  /** Företagets hemsida */
  companyWebsite: string | null;
  /** Senast uppdaterad */
  lastUpdated: string | null;
}

// ============================================================================
// Börsnotering Types
// ============================================================================

export interface Borsnotering {
  /** Företagsnamn */
  company: string;
  /** URL-slug för detaljsidan */
  slug: string;
  /** Full URL till detaljsidan */
  url: string;
  /** Målbörs (t.ex. "Nasdaq Stockholm", "First North") */
  targetExchange: string;
  /** Typ av notering (t.ex. "IPO", "Listbyte", "Notering") */
  listingType: string;
  /** Noteringsdatum (ISO-format) */
  listingDate: string | null;
  /** Status (t.ex. "Kommande", "Genomförd", "Inställd") */
  status: string;
  /** Teckningsperiod start (för IPO med emission) */
  subscriptionStart: string | null;
  /** Teckningsperiod slut */
  subscriptionEnd: string | null;
}

export interface Owner {
  /** Ägarens namn */
  name: string;
  /** Ägarandel i procent */
  percentage: number;
}

export interface BorsnoteringDetails extends Borsnotering {
  /** Beskrivning av företaget */
  description: string;
  /** Flyttar från (för listbyten) */
  movingFrom: string | null;
  /** Värdering/Market cap */
  valuation: string | null;
  /** URL till listingsdokument/prospekt */
  listingDocumentUrl: string | null;
  /** Ägare vid notering */
  owners: Owner[];
  /** Historisk ägarinfo (fritext) */
  historicalOwners: string | null;
  /** Ytterligare information */
  additionalInfo: string | null;
  /** Företagets hemsida */
  companyWebsite: string | null;
  /** Senast uppdaterad */
  lastUpdated: string | null;
  /** Pris per aktie */
  pricePerShare: string | null;
  /** Emissionsbelopp (om IPO med emission) */
  amount: string | null;
}

export interface SearchFilters {
  /** Filtrera på lista/börs */
  exchange?: string;
  /** Filtrera på bransch */
  industry?: string;
  /** Typ av emission */
  type?: 'nyemission' | 'ipo' | 'foretradesemission' | 'riktad' | 'konvertering' | 'kvittning' | 'apport';
  /** Sortering */
  sort?: 'newest' | 'oldest' | 'latest_published';
}

export interface ListResponse {
  /** Lista med nyemissioner */
  items: Nyemission[];
  /** Om det finns fler sidor */
  hasMore: boolean;
  /** Total antal (om tillgängligt) */
  total?: number;
}

export interface ClientConfig {
  /** Base URL för nyemissioner.se */
  baseUrl?: string;
  /** User-Agent header */
  userAgent?: string;
  /** Rate limit (millisekunder mellan requests) */
  rateLimitMs?: number;
  /** Timeout i millisekunder */
  timeoutMs?: number;
}

// ============================================================================
// Client Implementation
// ============================================================================

export class NyemissionerClient {
  private baseUrl: string;
  private userAgent: string;
  private rateLimitMs: number;
  private timeoutMs: number;
  private lastRequestTime: number = 0;

  constructor(config: ClientConfig = {}) {
    this.baseUrl = config.baseUrl || 'https://nyemissioner.se';
    this.userAgent = config.userAgent || 'NyemissionerClient/1.0';
    this.rateLimitMs = config.rateLimitMs || 1000; // 1 request per sekund
    this.timeoutMs = config.timeoutMs || 30000;
  }

  // --------------------------------------------------------------------------
  // Private helpers
  // --------------------------------------------------------------------------

  private async rateLimit(): Promise<void> {
    const now = Date.now();
    const elapsed = now - this.lastRequestTime;
    if (elapsed < this.rateLimitMs) {
      await new Promise(resolve => setTimeout(resolve, this.rateLimitMs - elapsed));
    }
    this.lastRequestTime = Date.now();
  }

  private async fetch(url: string): Promise<string> {
    await this.rateLimit();
    
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    
    try {
      const response = await fetch(url, {
        headers: {
          'User-Agent': this.userAgent,
          'Accept': 'text/html,application/xhtml+xml',
          'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
        },
        signal: controller.signal,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.text();
    } finally {
      clearTimeout(timeout);
    }
  }

  private parseSwedishDate(dateStr: string): string | null {
    if (!dateStr) return null;
    
    // Format: "2024-04-23" eller "19 april 2024"
    const isoMatch = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/);
    if (isoMatch) {
      return dateStr;
    }
    
    const swedishMonths: Record<string, string> = {
      'januari': '01', 'februari': '02', 'mars': '03', 'april': '04',
      'maj': '05', 'juni': '06', 'juli': '07', 'augusti': '08',
      'september': '09', 'oktober': '10', 'november': '11', 'december': '12'
    };
    
    const match = dateStr.match(/(\d{1,2})\s+(\w+)\s+(\d{4})/);
    if (match) {
      const [, day, month, year] = match;
      const monthNum = swedishMonths[month.toLowerCase()];
      if (monthNum) {
        return `${year}-${monthNum}-${day.padStart(2, '0')}`;
      }
    }
    
    return null;
  }

  private extractSlug(url: string): string {
    const match = url.match(/\/nyemissioner\/([^\/]+)\/?$/);
    return match ? match[1] : url;
  }

  private extractBorsnoteringSlug(url: string): string {
    // Matcha /borsnotering/slug/ eller /planerad-notering/slug/
    const match = url.match(/\/(borsnotering|planerad-notering)\/([^\/]+)\/?$/);
    if (match) return match[2];
    
    // Fallback: ta sista segmentet
    const segments = url.split('/').filter(s => s.length > 0);
    return segments[segments.length - 1] || url;
  }

  // --------------------------------------------------------------------------
  // Public API
  // --------------------------------------------------------------------------

  /**
   * Hämtar lista med aktuella och historiska nyemissioner
   * 
   * @param filters - Filtreringsalternativ
   * @returns Lista med nyemissioner
   * 
   * @example
   * ```typescript
   * const client = new NyemissionerClient();
   * const result = await client.listNyemissioner({ industry: 'Data/IT' });
   * console.log(result.items);
   * ```
   */
  async listNyemissioner(filters: SearchFilters = {}): Promise<ListResponse> {
    // Hämta startsidan istället för sök-sidan för att få aktuella nyemissioner
    const url = `${this.baseUrl}/`;
    const html = await this.fetch(url);
    const $ = cheerio.load(html);

    const items: Nyemission[] = [];

    // Jet Engine-struktur: .jet-listing-grid__item med data-url i .jet-engine-listing-overlay-wrap
    // Filtrera endast på nyemissioner (inte börsnoteringar eller nyheter)
    $('.jet-listing-grid__item').each((_, element) => {
      const $el = $(element);

      // Hämta URL från data-url attribut eller overlay-länk
      const $overlay = $el.find('.jet-engine-listing-overlay-wrap');
      const href = $overlay.attr('data-url') ||
                   $el.find('.jet-engine-listing-overlay-link').attr('href') || '';

      // Filtrera: endast /nyemissioner/ URLs
      if (!href.includes('/nyemissioner/')) return;

      // Företagsnamn finns i h2.elementor-heading-title
      const company = $el.find('h2.elementor-heading-title').first().text().trim();

      if (!company || !href) return;

      // Övrig info finns i andra heading-element
      const headings = $el.find('.elementor-heading-title').map((_, h) => $(h).text().trim()).get();

      // Första heading är företagsnamn, resten kan vara bransch, lista etc.
      const otherInfo = headings.slice(1);

      // Försök identifiera bransch och exchange från övrig info
      let industry = 'Okänd';
      let exchange = 'Okänd';

      otherInfo.forEach(info => {
        const lower = info.toLowerCase();
        // Kända listor/börser
        if (lower.includes('spotlight') || lower.includes('ngm') ||
            lower.includes('first north') || lower.includes('onoterat') ||
            lower.includes('nasdaq') || lower.includes('aktietorget')) {
          exchange = info;
        } else if (info.length > 2 && info.length < 50) {
          // Annan info är troligen bransch
          if (industry === 'Okänd') industry = info;
        }
      });

      const item: Nyemission = {
        company,
        slug: this.extractSlug(href),
        url: href.startsWith('http') ? href : `${this.baseUrl}${href}`,
        industry,
        exchange,
        subscriptionStart: null,
        subscriptionEnd: null,
      };

      // Applicera filter
      if (filters.industry && !item.industry.toLowerCase().includes(filters.industry.toLowerCase())) {
        return;
      }
      if (filters.exchange && !item.exchange.toLowerCase().includes(filters.exchange.toLowerCase())) {
        return;
      }

      items.push(item);
    });

    return {
      items,
      hasMore: items.length >= 10,
    };
  }

  /**
   * Hämtar detaljerad information om en specifik nyemission
   * 
   * @param slugOrUrl - URL-slug (t.ex. "scibase-ab-6") eller full URL
   * @returns Detaljerad nyemissionsinformation
   * 
   * @example
   * ```typescript
   * const client = new NyemissionerClient();
   * const details = await client.getNyemission('scibase-ab-6');
   * console.log(details.amount, details.subscriptionPrice);
   * ```
   */
  async getNyemission(slugOrUrl: string): Promise<NyemissionDetails> {
    const slug = this.extractSlug(slugOrUrl);
    const url = `${this.baseUrl}/nyemissioner/${slug}/`;
    const html = await this.fetch(url);
    const $ = cheerio.load(html);
    
    // Extrahera grundläggande info
    const company = $('h1').first().text().replace('Nyemission i', '').trim();
    
    // Extrahera emissionsfakta
    const getFactValue = (label: string): string | null => {
      const $section = $(`*:contains("${label}")`).filter((_, el) => 
        $(el).text().trim().startsWith(label)
      ).first();
      
      if ($section.length) {
        const $value = $section.next();
        return $value.text().trim() || null;
      }
      
      // Alternativ: leta i list-items
      const $li = $(`li:contains("${label}"), *:contains("${label}")`).first();
      return $li.length ? $li.text().replace(label, '').trim() : null;
    };
    
    // Hitta typ av erbjudande
    const offerType = $('*:contains("Typ av erbjudande")').next().text().trim() ||
                      $('*:contains("Nyemission"), *:contains("IPO"), *:contains("Företrädesemission")')
                        .filter((_, el) => $(el).text().trim().length < 30)
                        .first().text().trim() || 'Okänd';
    
    // Hitta belopp
    const amountText = $('*:contains("Emissionsbelopp")').parent().text() ||
                       $('*:contains("Mkr")').first().text();
    const amountMatch = amountText.match(/([\d,\.]+)\s*Mkr/);
    const amount = amountMatch ? `${amountMatch[1]} Mkr` : null;
    
    // Hitta teckningskurs
    const priceText = $('*:contains("Teckningskurs")').parent().text();
    const priceMatch = priceText.match(/([\d,\.]+)\s*kr/);
    const subscriptionPrice = priceMatch ? priceText.trim() : null;
    
    // Hitta värdering
    const valuationText = $('*:contains("Värdering")').parent().text();
    const valuation = valuationText.includes('Mkr') ? valuationText.trim() : null;
    
    // Hitta prospekt-länk
    const prospectusUrl = $('a[href*="prospekt"]').attr('href') ||
                          $('a:contains("Visa prospekt")').attr('href') ||
                          null;
    
    // Hitta teckningsperiod
    const dates = html.match(/\d{4}-\d{2}-\d{2}/g) || [];
    const subscriptionStart = dates[0] || null;
    const subscriptionEnd = dates[1] || null;
    
    // Hitta avstämningsdag
    const recordDateText = $('*:contains("Avstämningsdag")').parent().text();
    const recordDate = this.parseSwedishDate(recordDateText);
    
    // Hitta bransch och lista
    const industry = $('a[href*="/branscher/"]').first().text().trim() || 'Okänd';
    const exchange = $('a[href*="/listor/"]').first().text().trim() ||
                     $('*:contains("Lista")').next().text().trim() || 'Okänd';
    
    // Hitta beskrivning (första längre textstycket)
    const description = $('p').filter((_, el) => {
      const text = $(el).text().trim();
      return text.length > 100 && !text.includes('Håll dig uppdaterad');
    }).first().text().trim() || '';
    
    // Hitta villkor
    const termsSection = $('*:contains("Villkor")').filter((_, el) => 
      $(el).text().trim() === 'Villkor'
    ).first();
    const terms = termsSection.length ? termsSection.next().text().trim() : null;
    
    // Hitta mer information
    const moreInfoSection = $('*:contains("Mer information")').filter((_, el) =>
      $(el).text().trim() === 'Mer information'
    ).first();
    const additionalInfo = moreInfoSection.length ? moreInfoSection.next().text().trim() : null;
    
    // Hitta företagets hemsida
    const companyWebsite = $('a[href^="http"]:not([href*="nyemissioner.se"])')
                            .filter((_, el) => !$(el).attr('href')?.includes('wp-content'))
                            .first().attr('href') || null;
    
    // Hitta uppdateringsdatum
    const updateMatch = html.match(/Uppdaterat:\s*(\d{1,2}\s+\w+\s+\d{4})/);
    const lastUpdated = updateMatch ? this.parseSwedishDate(updateMatch[1]) : null;
    
    return {
      company,
      slug,
      url,
      industry,
      exchange,
      subscriptionStart,
      subscriptionEnd,
      offerType,
      amount,
      subscriptionPrice,
      valuation,
      prospectusUrl: prospectusUrl ? 
        (prospectusUrl.startsWith('http') ? prospectusUrl : `${this.baseUrl}${prospectusUrl}`) : null,
      recordDate,
      description,
      terms,
      additionalInfo,
      companyWebsite,
      lastUpdated,
    };
  }

  /**
   * Hämtar alla planerade börsnoteringar (IPOs/listbyten)
   * 
   * @returns Lista med planerade noteringar
   * 
   * @example
   * ```typescript
   * const client = new NyemissionerClient();
   * const ipos = await client.listBorsnoteringar();
   * ipos.items.forEach(ipo => {
   *   console.log(`${ipo.company} - ${ipo.listingType} på ${ipo.targetExchange}`);
   * });
   * ```
   */
  async listBorsnoteringar(): Promise<{ items: Borsnotering[]; hasMore: boolean }> {
    // Hämta startsidan för att få börsnoteringar
    const url = `${this.baseUrl}/`;
    const html = await this.fetch(url);
    const $ = cheerio.load(html);

    const items: Borsnotering[] = [];

    // Jet Engine-struktur: .jet-listing-grid__item med data-url
    // Filtrera endast på börsnoteringar (inte nyemissioner eller nyheter)
    $('.jet-listing-grid__item').each((_, element) => {
      const $el = $(element);

      // Hämta URL från data-url attribut
      const $overlay = $el.find('.jet-engine-listing-overlay-wrap');
      const href = $overlay.attr('data-url') ||
                   $el.find('.jet-engine-listing-overlay-link').attr('href') || '';

      // Filtrera: endast /borsnotering/ URLs
      if (!href.includes('/borsnotering/')) return;

      // Företagsnamn finns i h2.elementor-heading-title
      const company = $el.find('h2.elementor-heading-title').first().text().trim();

      if (!company || company.length < 2) return;

      // Övrig info finns i andra heading-element
      const headings = $el.find('.elementor-heading-title').map((_, h) => $(h).text().trim()).get();
      const otherInfo = headings.slice(1);

      // Försök identifiera exchange och andra detaljer
      let targetExchange = 'Okänd';

      otherInfo.forEach(info => {
        const lower = info.toLowerCase();
        if (lower.includes('spotlight') || lower.includes('ngm') ||
            lower.includes('first north') || lower.includes('nasdaq') ||
            lower.includes('aktietorget')) {
          targetExchange = info;
        }
      });

      const slug = this.extractBorsnoteringSlug(href);

      items.push({
        company,
        slug,
        url: href.startsWith('http') ? href : `${this.baseUrl}${href}`,
        targetExchange,
        listingType: 'Notering',
        listingDate: null,
        status: 'Kommande',
        subscriptionStart: null,
        subscriptionEnd: null,
      });
    });

    return { items, hasMore: items.length >= 10 };
  }

  /**
   * Hämtar detaljerad information om en specifik börsnotering
   * 
   * @param slugOrUrl - URL-slug (t.ex. "viva-wine-group-ab") eller full URL
   * @returns Detaljerad börsnoteringsinformation
   * 
   * @example
   * ```typescript
   * const client = new NyemissionerClient();
   * const details = await client.getBorsnotering('viva-wine-group-ab');
   * console.log(details.valuation);     // "3 340 Mkr i market cap..."
   * console.log(details.listingType);   // "Listbyte"
   * console.log(details.owners);        // [{name: "Late Harvest...", percentage: 26.05}, ...]
   * ```
   */
  async getBorsnotering(slugOrUrl: string): Promise<BorsnoteringDetails> {
    const slug = this.extractBorsnoteringSlug(slugOrUrl);
    const url = `${this.baseUrl}/borsnotering/${slug}/`;
    const html = await this.fetch(url);
    const $ = cheerio.load(html);
    
    // Extrahera företagsnamn
    const headerText = $('h1, h2').first().text().trim();
    const company = headerText.replace(/Börsnotering\s*(av|i)?/i, '').trim();
    
    // Extrahera beskrivning (första längre textstycket)
    const description = $('p, [class*="description"], [class*="intro"]').filter((_, el) => {
      const text = $(el).text().trim();
      return text.length > 50 && 
             !text.includes('Håll dig uppdaterad') &&
             !text.includes('Prenumerera') &&
             !text.includes('Uppdaterat:');
    }).first().text().trim() || '';
    
    // Hjälpfunktion för att hitta värden i fakta-sektionen
    const getFactValue = (label: string): string | null => {
      // Sök efter label följt av värde
      const regex = new RegExp(`${label}[:\\s]*([^\\n]+)`, 'i');
      const match = html.match(regex);
      if (match) return match[1].trim();
      
      // Alternativt: hitta i struktur
      let value: string | null = null;
      $('*').each((_, el) => {
        const $el = $(el);
        if ($el.text().trim().toLowerCase() === label.toLowerCase()) {
          const $next = $el.next();
          if ($next.length) {
            value = $next.text().trim();
            return false; // break
          }
        }
      });
      return value;
    };
    
    // Noteringsfakta
    const targetExchange = getFactValue('Lista') || 
                          $('a[href*="/listor/"]').first().text().trim() || 'Okänd';
    
    const movingFrom = getFactValue('Flyttar från') || null;
    
    const listingTypeText = getFactValue('Typ av notering') || '';
    let listingType = 'Notering';
    if (listingTypeText.toLowerCase().includes('listbyte')) listingType = 'Listbyte';
    else if (listingTypeText.toLowerCase().includes('ipo')) listingType = 'IPO';
    else if (listingTypeText.toLowerCase().includes('spridning')) listingType = 'Spridningsemission';
    else if (listingTypeText) listingType = listingTypeText;
    
    // Noteringsdatum
    const listingDateText = getFactValue('Noteringsdatum') || getFactValue('Första handelsdag') || '';
    const listingDate = this.parseSwedishDate(listingDateText);
    
    // Status
    const statusText = getFactValue('Status') || '';
    let status = 'Kommande';
    if (statusText.toLowerCase().includes('genomförd') || statusText.toLowerCase().includes('noterad')) {
      status = 'Genomförd';
    } else if (statusText.toLowerCase().includes('kommande')) {
      status = 'Kommande';
    } else if (statusText.toLowerCase().includes('inställd')) {
      status = 'Inställd';
    } else if (statusText) {
      status = statusText;
    }
    
    // Värdering
    const valuationSection = $('*:contains("Värdering")').filter((_, el) => 
      $(el).text().trim() === 'Värdering'
    ).first();
    let valuation = valuationSection.length ? valuationSection.next().text().trim() : null;
    if (!valuation) {
      const valuationMatch = html.match(/(\d[\d\s,\.]*)\s*Mkr\s*(i\s*market\s*cap|pre-money)?/i);
      if (valuationMatch) {
        valuation = valuationMatch[0].trim();
      }
    }
    
    // Listingsdokument/Prospekt
    const listingDocumentUrl = $('a[href*="prospekt"], a[href*="listnings"], a[href*="memorandum"]')
      .filter((_, el) => !$(el).attr('href')?.includes('annons'))
      .first().attr('href') || null;
    
    // Parsa ägare
    const owners: Owner[] = [];
    const ownerSection = $('*:contains("Ägare vid notering")').first().parent();
    
    // Försök hitta ägare i olika format
    // Format 1: Tabell eller lista med namn och procent
    $('*').each((_, el) => {
      const text = $(el).text().trim();
      // Matcha "Företagsnamn    26,05%" eller "Företagsnamn 26.05%"
      const ownerMatch = text.match(/^([A-Za-zÅÄÖåäö\s&\(\)]+?)\s+([\d,\.]+)\s*%$/);
      if (ownerMatch && ownerMatch[1].length > 2 && ownerMatch[1].length < 100) {
        const name = ownerMatch[1].trim();
        const pct = parseFloat(ownerMatch[2].replace(',', '.'));
        // Undvik dubletter
        if (!owners.find(o => o.name === name) && pct > 0 && pct <= 100) {
          owners.push({ name, percentage: pct });
        }
      }
    });
    
    // Om inga ägare hittades, försök alternativ parsing
    if (owners.length === 0) {
      const ownerText = html.match(/Ägare vid notering[\s\S]*?(?=Ägare\s*\d|Mer information|$)/i)?.[0] || '';
      const ownerMatches = ownerText.matchAll(/([A-Za-zÅÄÖåäö\s&\(\)]+?)\s+([\d,\.]+)\s*%/g);
      for (const match of ownerMatches) {
        const name = match[1].trim();
        const pct = parseFloat(match[2].replace(',', '.'));
        if (name.length > 2 && name.length < 100 && pct > 0 && pct <= 100) {
          if (!owners.find(o => o.name === name)) {
            owners.push({ name, percentage: pct });
          }
        }
      }
    }
    
    // Historiska ägare
    const historicalMatch = html.match(/Ägare\s*\d{1,2}\s+(januari|februari|mars|april|maj|juni|juli|augusti|september|oktober|november|december)\s+\d{4}:?\s*([^<]+)/i);
    const historicalOwners = historicalMatch ? historicalMatch[0].trim() : null;
    
    // Mer information
    const moreInfoSection = $('*:contains("Mer information")').filter((_, el) =>
      $(el).text().trim() === 'Mer information'
    ).first();
    const additionalInfo = moreInfoSection.length ? moreInfoSection.next().text().trim() : null;
    
    // Företagets hemsida
    const companyWebsite = $('a[href^="http"]:not([href*="nyemissioner.se"])')
      .filter((_, el) => !$(el).attr('href')?.includes('wp-content'))
      .first().attr('href') || null;
    
    // Uppdateringsdatum
    const updateMatch = html.match(/Uppdaterat:\s*(\d{1,2}\s+\w+\s+\d{4})/);
    const lastUpdated = updateMatch ? this.parseSwedishDate(updateMatch[1]) : null;
    
    // Teckningsperiod (för IPO med emission)
    const dates = html.match(/\d{4}-\d{2}-\d{2}/g) || [];
    const subscriptionStart = dates.find(d => d !== listingDate) || null;
    const subscriptionEnd = dates.length > 1 ? dates[dates.length - 1] : null;
    
    // Pris per aktie
    const priceMatch = html.match(/([\d,\.]+)\s*kr\s*(per\s*aktie)?/i);
    const pricePerShare = priceMatch ? priceMatch[0].trim() : null;
    
    // Emissionsbelopp
    const amountMatch = html.match(/([\d,\.]+)\s*Mkr\s*(i\s*emission|emissionsbelopp)?/i);
    const amount = amountMatch ? `${amountMatch[1]} Mkr` : null;
    
    return {
      company,
      slug,
      url,
      targetExchange,
      listingType,
      listingDate,
      status,
      subscriptionStart,
      subscriptionEnd,
      description,
      movingFrom,
      valuation,
      listingDocumentUrl: listingDocumentUrl ? 
        (listingDocumentUrl.startsWith('http') ? listingDocumentUrl : `${this.baseUrl}${listingDocumentUrl}`) : null,
      owners,
      historicalOwners,
      additionalInfo,
      companyWebsite,
      lastUpdated,
      pricePerShare,
      amount,
    };
  }

  /**
   * Söker efter nyemissioner med fritext
   * 
   * @param query - Sökfråga (företagsnamn etc.)
   * @returns Matchande nyemissioner
   */
  async search(query: string): Promise<ListResponse> {
    // Nyemissioner.se verkar inte ha ett publikt sök-API
    // Vi hämtar alla och filtrerar lokalt
    const all = await this.listNyemissioner();
    const normalizedQuery = query.toLowerCase();
    
    const filtered = all.items.filter(item => 
      item.company.toLowerCase().includes(normalizedQuery) ||
      item.industry.toLowerCase().includes(normalizedQuery)
    );
    
    return {
      items: filtered,
      hasMore: false,
    };
  }

  /**
   * Hämtar senaste nyheterna om nyemissioner
   * 
   * @param limit - Max antal nyheter att hämta
   * @returns Lista med nyheter
   */
  async listNews(limit: number = 10): Promise<Array<{
    title: string;
    url: string;
    date: string | null;
    excerpt: string;
  }>> {
    const url = `${this.baseUrl}/nyheter/`;
    const html = await this.fetch(url);
    const $ = cheerio.load(html);
    
    const news: Array<{
      title: string;
      url: string;
      date: string | null;
      excerpt: string;
    }> = [];
    
    $('article, [class*="news"], [class*="post"]').each((index, element) => {
      if (index >= limit) return false;
      
      const $el = $(element);
      const $link = $el.find('a[href*="/nyheter/"]').first();
      const title = $link.text().trim() || $el.find('h2, h3').first().text().trim();
      const href = $link.attr('href');
      
      if (!title || !href) return;
      
      // Hitta datum
      const dateText = $el.find('time, [class*="date"]').text().trim() ||
                       $el.text().match(/(\d{1,2}\s+\w+\s+\d{4})/)?.[1] || null;
      
      // Hitta excerpt
      const excerpt = $el.find('p').first().text().trim().substring(0, 200);
      
      news.push({
        title,
        url: href.startsWith('http') ? href : `${this.baseUrl}${href}`,
        date: dateText ? this.parseSwedishDate(dateText) : null,
        excerpt,
      });
    });
    
    return news;
  }
}

// ============================================================================
// Export default instance
// ============================================================================

export default NyemissionerClient;
