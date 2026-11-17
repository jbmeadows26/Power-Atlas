import { ai, db } from '@appdeploy/sdk';
import { readDefenseIntelligence } from './defenseIntel';

/**
 * Free-first metadata monitoring: official public feeds, one bounded page each.
 * Not a tactical asset tracker. Feed items are unreviewed research leads.
 * No AI call occurs on the daily cron: AI is opt-in and cached.
 */
type FeedId = 'us-defense' | 'uk-mod' | 'un-security';
type FeedConfig = { id: FeedId; name: string; url: string; domains: string[] };
const FEEDS: FeedConfig[] = [
  {
    id: 'us-defense',
    name: 'U.S. Department of Defense news',
    url: 'https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=20&ContentType=1&Site=945',
    domains: ['defense.gov', 'war.gov']
  },
  {
    id: 'uk-mod',
    name: 'UK Ministry of Defence publications',
    url: 'https://www.gov.uk/government/organisations/ministry-of-defence.atom',
    domains: ['gov.uk']
  },
  {
    id: 'un-security',
    name: 'UN News: Peace and Security',
    url: 'https://news.un.org/feed/subscribe/en/news/topic/peace-and-security/feed/rss.xml',
    domains: ['un.org']
  }
];
type FeedHealth = {
  sourceId: FeedId; status: 'ok' | 'error'; lastAttemptAt: string;
  lastSuccessAt?: string; lastError?: string; examined: number;
  changed: number; baselined: number;
};
export type WatchRecord = {
  id: string; sourceId: FeedId; publisher: string; url: string; title: string;
  excerpt: string; published: string; firstSeenAt: string; changedAt: string;
  countryMentions: string[]; fingerprint: string;
  changeType: 'baseline' | 'new-publication' | 'source-revised';
  reviewState: 'unreviewed';
};
const COUNTRIES: { code: string; words: RegExp }[] = [
  { code: 'RU', words: /\b(russia|russian|moscow)\b/i },
  { code: 'UA', words: /\b(ukraine|ukrainian|kyiv)\b/i },
  { code: 'CN', words: /\b(china|chinese|beijing|prc)\b/i },
  { code: 'IR', words: /\b(iran|iranian|tehran)\b/i },
  { code: 'KP', words: /\b(north korea|north korean|dprk|pyongyang)\b/i },
  { code: 'KR', words: /\b(south korea|south korean|seoul)\b/i },
  { code: 'YE', words: /\b(yemen|yemeni|houthi)\b/i },
  { code: 'SD', words: /\b(sudan|sudanese|darfur)\b/i },
  { code: 'IL', words: /\b(israel|israeli|gaza)\b/i },
  { code: 'PS', words: /\b(palestine|palestinian|gaza)\b/i },
  { code: 'MM', words: /\b(myanmar|burma|burmese)\b/i },
  { code: 'SO', words: /\b(somalia|somali|al-shabaab)\b/i },
  { code: 'BY', words: /\b(belarus|belarusian)\b/i },
  { code: 'VE', words: /\b(venezuela|venezuelan)\b/i },
  { code: 'CU', words: /\b(cuba|cuban)\b/i },
  { code: 'TW', words: /\b(taiwan|taiwanese|taipei)\b/i },
  { code: 'JP', words: /\b(japan|japanese|tokyo)\b/i },
  { code: 'IN', words: /\b(india|indian|new delhi)\b/i },
  { code: 'PK', words: /\b(pakistan|pakistani)\b/i }
];
const TOPICS = /\b(defen[cs]e|military|armed forces|troops|missiles?|aircraft|warships?|navy|naval|submarines?|fighter|battle|armed conflict|security council|ceasefire|peacekeeping|strike|drone|weapons?|sanctions?|invasion|warfare|geopolitic|geostrategic|allied|allies|espionage|cyberattack|cybersecurity|security operations|joint exercise|deterrence|command|intelligence|conflict|gaza|ukraine|sudan|yemen)\b/i;
const deEnt = (value: string) => value
  .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/gi, '$1')
  .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
  .replace(/&#(\d+);/g, (_, n: string) => {
    const code = Number(n);
    return code > 31 && code < 0x110000 ? String.fromCodePoint(code) : '';
  })
  .replace(/<[^>]+>/g, ' ')
  .replace(/\s+/g, ' ')
  .trim();
const findTag = (xml: string, tag: string) => {
  const match = xml.match(new RegExp('<(?:[a-z0-9]+:)?' + tag + '(?:\\s[^>]*)?>([\\s\\S]*?)<\\/(?:[a-z0-9]+:)?' + tag + '>', 'i'));
  return match ? deEnt(match[1]) : '';
};
const checksum = (s: string) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  }
  return (h >>> 0).toString(16).padStart(8, '0');
};
const safeUrl = (raw: string, feed: FeedConfig): string | null => {
  try {
    const url = new URL(raw, feed.url);
    if (url.protocol !== 'https:') return null;
    if (!feed.domains.some(d => url.hostname === d || url.hostname.endsWith('.' + d))) return null;
    return url.href.split('#')[0];
  } catch { return null; }
};
const feedLink = (item: string, feed: FeedConfig) => {
  const alternate = [...item.matchAll(/<link\b([^>]*)\/?\s*>/gi)]
    .map(m => m[1])
    .find(attrs => /href\s*=/.test(attrs) && (!/rel\s*=/.test(attrs) || /rel\s*=\s*['"]alternate['"]/.test(attrs)));
  const href = alternate?.match(/href\s*=\s*['"]([^'"]+)['"]/i)?.[1] || findTag(item, 'link');
  return safeUrl(deEnt(href || ''), feed);
};
function parseItems(text: string, feed: FeedConfig) {
  const tags = /<(?:item|entry)\b[^>]*>([\s\S]*?)<\/(?:item|entry)>/gi;
  const output: Array<{title: string; excerpt: string; url: string; published: string}> = [];
  for (const m of text.matchAll(tags)) {
    const item = m[1];
    const title = findTag(item, 'title').slice(0, 260);
    const excerpt = (findTag(item, 'description') || findTag(item, 'summary') || '').slice(0, 600);
    const url = feedLink(item, feed);
    const publication = findTag(item, 'pubDate') || findTag(item, 'published') || findTag(item, 'updated');
    const iso = publication && !Number.isNaN(Date.parse(publication)) ? new Date(publication).toISOString().slice(0, 10) : '';
    if (url && title && TOPICS.test(title + ' ' + excerpt)) {
      output.push({title, excerpt, url, published: iso});
    }
    if (output.length >= 10) break;
  }
  return output;
}
async function fetchFeed(feed: FeedConfig) {
  const response = await fetch(feed.url, {
    headers: {Accept: 'application/rss+xml, application/atom+xml, application/xml, text/xml'},
    signal: AbortSignal.timeout(12000)
  });
  if (!response.ok) throw new Error('HTTP ' + response.status);
  const text = await response.text();
  if (text.length < 80 || text.length > 2000000) throw new Error('Invalid feed size');
  if (!/<(?:rss|feed|rdf:RDF)\b/i.test(text)) throw new Error('Unexpected XML document');
  const parsed = parseItems(text, feed);
  if (!parsed.length) throw new Error('No usable defense/security records in this feed window');
  return parsed;
}
export async function checkOfficialReportChanges() {
  for (const feed of FEEDS) {
    const now = new Date().toISOString();
    let health: FeedHealth;
    try {
      const items = await fetchFeed(feed);
      const [previousState] = await db.get<FeedHealth>('mil_watch_health', [feed.id], {consistent: true});
      const isBaseline = !previousState?.lastSuccessAt;
      const prepared = items.map(item => ({
        ...item,
        id: feed.id + '-' + checksum(item.url) + checksum(item.url.length + item.url),
        fingerprint: checksum([item.title, item.excerpt, item.published].join('|')),
        countryMentions: COUNTRIES.filter(c => c.words.test(item.title + ' ' + item.excerpt)).map(c => c.code)
      }));
      const old = await db.get<WatchRecord>('mil_watch_records', prepared.map(item => item.id), {consistent: true});
      let changed = 0;
      let baselined = 0;
      for (let i = 0; i < prepared.length; i++) {
        const item = prepared[i];
        const past = old[i];
        if (past?.fingerprint === item.fingerprint) continue;
        const changeType: WatchRecord['changeType'] = past ? 'source-revised' : isBaseline ? 'baseline' : 'new-publication';
        const record: WatchRecord = {
          id:item.id, sourceId:feed.id, publisher:feed.name, url:item.url,
          title:item.title, excerpt:item.excerpt, published:item.published,
          firstSeenAt:past?.firstSeenAt || now, changedAt:now,
          countryMentions:item.countryMentions, fingerprint:item.fingerprint,
          changeType, reviewState:'unreviewed'
        };
        if (past) {
          const [updated] = await db.tx.update('mil_watch_records', [{id:item.id,record}]);
          if (!updated) throw new Error('Record update not confirmed');
        } else {
          const [inserted] = await db.tx.add('mil_watch_records', [record]);
          if (!inserted) continue;
        }
        if (changeType === 'baseline') baselined++;
        else changed++;
      }
      health = {
        sourceId:feed.id,status:'ok',lastAttemptAt:now,lastSuccessAt:now,
        examined:items.length,changed,baselined
      };
    } catch (e) {
      const [past] = await db.get<FeedHealth>('mil_watch_health', [feed.id], {consistent: true});
      health = {
        sourceId:feed.id,status:'error',lastAttemptAt:now,lastSuccessAt:past?.lastSuccessAt,
        lastError:(e instanceof Error?e.message:'Unknown collection failure').slice(0,200),
        examined:0,changed:0,baselined:0
      };
    }
    const [saved] = await db.tx.update('mil_watch_health', [{id:feed.id,record:health}]);
    if (!saved) console.error('Could not store official feed state', feed.id);
  }
  return {statusCode:200};
}
export async function readOfficialReportChanges() {
  const [health, stored] = await Promise.all([
    db.get<FeedHealth>('mil_watch_health', FEEDS.map(f => f.id), {consistent: true}),
    db.list<WatchRecord>('mil_watch_records', {limit:120})
  ]);
  const records = stored.items
    .filter(x => x.reviewState === 'unreviewed' && FEEDS.some(f => f.id === x.sourceId))
    .sort((a,b) => (b.changedAt || '').localeCompare(a.changedAt || ''))
    .slice(0,48);
  return {
    feeds:FEEDS.map((f,i) => ({id:f.id,name:f.name,url:f.url,health:health[i] || null})),
    records,
    mode:'Official public-feed document metadata, not battlefield observation',    explanation:'Initial imports are baselines, not alerts. New and revised documents are unreviewed. Country mentions are headline matches only; capability changes are not established by metadata.',
    nextScan:'Scheduled daily at 11:05 UTC'
  };
}
const limitedCountry = (code: unknown) =>
  typeof code === 'string' && /^[A-Z]{2}$/.test(code.toUpperCase()) ? code.toUpperCase() : '';
const cacheFor = async (id: string) => {
  const [existing] = await db.get<{text:string;generatedAt:string}>('mil_ai_analysis', [id], {consistent: true});
  return existing;
};
async function makeAnalysis(id: string, prompt: string) {
  const saved = await cacheFor(id);
  if (saved) return {...saved, reused:true};
  const result = await ai.generate({
    system:'You are an evidence-constrained public-source research analyst. Use only the provided text, which is an editor-curated extract or an official-feed headline. Never claim to have read full reports. Distinguish official assessment from proven conduct, deployed strength from inventory, and headline leads from verified change. Do not infer agreement, disagreement or government attribution from missing evidence. Do not provide actionable tactical locations. Use plain language, concise headings, and source identifiers like [A1] or [M1].',
    prompt,maxTokens:950,temperature:0,thinkingMode:'FAST',cache:true
  });
  const text = result.text.trim().slice(0,7000);
  if (!text) throw new Error('AI model returned no analysis');
  const generatedAt = new Date().toISOString();
  await db.tx.add('mil_ai_analysis', [{id,text,generatedAt}]);
  return {text,generatedAt,reused:false};
}
export async function compareAlliedReports(input: unknown) {
  const code = limitedCountry(input);
  if (!code) return {error:'Invalid country code',status:'invalid'};
  const library = readDefenseIntelligence();
  const docs = library.assessments.filter(a => a.countries.includes(code));
  const distinct = new Set(docs.map(a => a.government));
  const sources = docs.map((a,i) => ({
    label:'A'+(i+1),title:a.title,agency:a.agency,government:a.government,
    date:a.published,excerpt:a.finding,url:a.url
  }));
  if (distinct.size < 2) return {
    status:'insufficient',code,sources,
    text:'At least two different issuing governments or alliance bodies are required for an allied-perspective comparison. No agreement or disagreement is inferred.',
    requiredSources:2
  };
  const fingerprint = checksum(JSON.stringify(sources));
  const prompt = 'Compare allied public assessments linked to country '+code+'. Sources are EDITOR SUMMARIES ONLY.\n'+
    sources.map(s => '['+s.label+'] '+s.government+' / '+s.agency+', '+s.date+': '+s.title+' — '+s.excerpt).join('\n')+
    '\n\nReturn sections: Shared themes; Meaningful differences in focus; Genuine contradictions (only if explicitly stated; otherwise NONE IDENTIFIED); Unresolved questions; Evidence limits. Name source labels in each finding. Do not conflate a different mandate or time period with contradiction.';
  return {status:'ready',code,sources,mode:'AI comparison of curated extracts, not full-document verification',
    ...(await makeAnalysis('allies-'+code+'-'+fingerprint,prompt))};
}
export async function analyzeSourceChanges(input: unknown) {
  const code = limitedCountry(input);
  const report = await readOfficialReportChanges();
  const leads = report.records.filter(x =>
    x.changeType !== 'baseline' && (!code || x.countryMentions.includes(code))
  ).slice(0,10);
  if (!leads.length) return {
    status:'no-changes',code,
    text:'No new or revised official-feed items are recorded for this filter yet. Source checks may be pending or incomplete; this does NOT mean there was no military activity or capability change.',
    sources:[],mode:'No AI call required'
  };
  const library = readDefenseIntelligence();
  const reference = library.assets.filter(x => !code || x.code === code).slice(0,9);
  const sources = leads.map((l,i) => ({
    label:'M'+(i+1),title:l.title,url:l.url,publisher:l.publisher,
    published:l.published,changeType:l.changeType,excerpt:l.excerpt
  }));
  const prompt = 'Assess possible changes in recent official military/public reporting'+(code?' mentioning '+code:'')+
    '. The entries below are HEADLINE/FEED EXCERPTS, NOT VERIFIED REPORT TEXT.\n'+
    sources.map(s => '['+s.label+'] '+s.publisher+' ('+(s.published||'date unknown')+') '+s.changeType+': '+s.title+'; '+s.excerpt).join('\n')+
    '\nOld curated asset reference points (not assumed authoritative inventory): '+reference.map(a => a.code+' '+a.name+' '+a.quantity+' ('+a.published+')').join('; ')+
    '\n\nReturn: Newly published official material; Possible capability or posture implications (unverified leads only); What changed in confirmed inventory (say NONE CONFIRMED absent comparable verified data); What needs manual verification. Cite [M#] and distinguish publication date from detection date. No invented quantities or real-time military tracking.';
  const fp = checksum(JSON.stringify(sources)+JSON.stringify(reference));
  return {status:'ready',code,sources,mode:'AI triage of unreviewed official-feed records',
    ...(await makeAnalysis('watch-'+(code||'all')+'-'+fp,prompt))};
}
