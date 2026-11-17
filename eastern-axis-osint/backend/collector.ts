import { db } from '@appdeploy/sdk';
import { readOFACMetadata, syncOFAC } from './ofac';
import { recordCollectionAttempt, recordHttpDigest } from './evidence';

export type FeedId = 'doj' | 'fara' | 'cisa' | 'ofac';
type FeedState = {
  sourceId: FeedId;
  status: 'ok' | 'error';
  lastAttemptAt: string;
  lastSuccessAt?: string;
  lastError?: string;
  examined: number;
  inserted: number;
  duplicates: number;
};
export type IntakeRecord = {
  id: string;
  sourceId: FeedId;
  sourceRecordId: string;
  title: string;
  summary: string;
  date: string;
  sourceUrl: string;
  countryMention?: string;
  countryRule?: string;
  recordType: string;
  reviewState: 'unreviewed';
  evidenceTier: 'original-source-index';
  collectedAt: string;
};
const FEEDS: { id: FeedId; name: string; agency: string; documentation: string; category: string; caveat: string }[] = [
  {id:'ofac',name:'Treasury OFAC SDN Register',agency:'U.S. Treasury / OFAC',
    documentation:'https://ofac.treasury.gov/sanctions-list-service',category:'Sanctions',
    caveat:'SDN list only. Names and program codes do not establish physical location, citizenship or state direction; aliases and the non-SDN lists are not yet resolved.'},
  {
    id: 'doj', name: 'DOJ Press Releases', agency: 'U.S. Department of Justice',
    documentation: 'https://www.justice.gov/developer/api-documentation/api_v1',
    category: 'Legal records',
    caveat: 'A DOJ release can contain allegations, settlements or convictions. A headline is not evidence of final liability.'
  },
  {
    id: 'fara', name: 'FARA Active Registrants', agency: 'U.S. Department of Justice',
    documentation: 'https://efile.fara.gov/ords/fara/f?p=API:ENDPOINTS',
    category: 'Foreign-agent disclosures',
    caveat: 'FARA registration is a legal disclosure, NOT evidence of crime or hostile foreign activity.'
  },
  {
    id: 'cisa', name: 'CISA Known Exploited Vulnerabilities', agency: 'Cybersecurity and Infrastructure Security Agency',
    documentation: 'https://github.com/cisagov/kev-data',
    category: 'Defensive cyber risk',
    caveat: 'An exploited software vulnerability does NOT establish an attacker, country or state sponsorship.'
  }
];
const MENTIONS = [
  { code:'RU', re:/\b(russia|russian)\b/i },
  { code:'CN', re:/\b(china|chinese|prc)\b/i },
  { code:'IR', re:/\b(iran|iranian)\b/i },
  { code:'KP', re:/\b(north korea|north korean|dprk)\b/i },
  { code:'CU', re:/\b(cuba|cuban)\b/i },
  { code:'BY', re:/\b(belarus|belarusian)\b/i },
  { code:'VE', re:/\b(venezuela|venezuelan)\b/i }
];
const DOJ_RE = /\b(russia|russian|china|chinese|iran|iranian|north korea|north korean|dprk|belarus|belarusian|cuba|cuban|venezuela|venezuelan|espionage|foreign agent|trade secret|export control|sanctions evasion|state-sponsored|foreign interference)\b/i;
const clean = (text: unknown) => String(text ?? '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
const isoDate = (d: unknown) => {
  const x = String(d ?? '');
  if (/^\d{10}$/.test(x)) return new Date(Number(x) * 1000).toISOString().slice(0, 10);
  if (/^\d{4}-\d{2}-\d{2}/.test(x)) return x.slice(0, 10);
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(x)) {
    const [month, day, year] = x.split('/');
    return year + '-' + month + '-' + day;
  }
  return '';
};
async function jsonGet(url: string, timeoutMs = 9000): Promise<unknown> {
  const response = await fetch(url, {
    headers: { Accept: 'application/json', 'User-Agent': 'EasternAxisOpenResearch/1.0' },
    signal: AbortSignal.timeout(timeoutMs)
  });
  if (!response.ok) throw new Error('Upstream HTTP ' + response.status);
  const raw = await response.text();
  await recordHttpDigest(url, raw, response);
  return JSON.parse(raw);
}
function safeDoJUrl(input: unknown): string | null {
  try {
    const url = new URL(String(input));
    if (url.protocol !== 'https:' || (url.hostname !== 'justice.gov' && !url.hostname.endsWith('.justice.gov'))) return null;
    return url.href;
  } catch { return null; }
}
function countryMention(title: string): string | undefined {
  return MENTIONS.find(m => m.re.test(title))?.code;
}
type DOJItem = { uuid?: string; title?: string; date?: string; url?: string };
async function readDOJ(): Promise<{ rows: IntakeRecord[]; examined: number }> {
  const params = new URLSearchParams({ sort:'date', direction:'DESC', pagesize:'50', fields:'uuid,title,date,url' });
  const body = await jsonGet('https://www.justice.gov/api/v1/press_releases.json?' + params.toString()) as { results?: DOJItem[] };
  if (!Array.isArray(body.results)) throw new Error('Invalid DOJ response schema');
  const collectedAt = new Date().toISOString();
  const items = body.results;
  const rows: IntakeRecord[] = [];
  for (const item of items) {
    const title = clean(item.title);
    const url = safeDoJUrl(item.url);
    const id = String(item.uuid || '').toLowerCase();
    if (!/^[a-f\d-]{20,48}$/.test(id) || !title || !url || !DOJ_RE.test(title)) continue;
    const mention = countryMention(title);
    rows.push({
      id:'doj-' + id, sourceId:'doj', sourceRecordId:id, title, date:isoDate(item.date),
      summary:'DOJ news release matched a topic keyword. Review the original text for the applicable allegations, evidence and subsequent case outcomes.',
      sourceUrl:url, recordType:'DOJ news release', reviewState:'unreviewed',
      evidenceTier:'original-source-index', collectedAt,
      ...(mention ? { countryMention:mention, countryRule:'Headline word match only; NOT a government-attribution finding' } : {})
    });
  }
  return { rows:rows.slice(0, 20), examined:items.length };
}
type FARARow = { Registration_Number?: number | string; Name?: string; Registration_Date?: string };
async function readFARA(): Promise<{ rows: IntakeRecord[]; examined: number }> {
  const body = await jsonGet('https://efile.fara.gov/api/v1/Registrants/json/Active', 10000) as { REGISTRANTS_ACTIVE?: { ROW?: FARARow[] | FARARow } };
  const raw = body.REGISTRANTS_ACTIVE?.ROW;
  const items = Array.isArray(raw) ? raw : raw ? [raw] : [];
  if (!items.length) throw new Error('Invalid or empty FARA active-register schema');
  const collectedAt = new Date().toISOString();
  const rows: IntakeRecord[] = items
    .filter(item=>/^\d{1,8}$/.test(String(item.Registration_Number || '')) && clean(item.Name).length>0)
    .sort((a,b)=>Number(b.Registration_Number)-Number(a.Registration_Number))
    .slice(0,18)
    .map(item=>({
      id:'fara-' + String(item.Registration_Number),
      sourceId:'fara' as const, sourceRecordId:String(item.Registration_Number),
      title:clean(item.Name), date:isoDate(item.Registration_Date),
      summary:'Active foreign-agent registration as listed by DOJ FARA. Registration is a disclosure requirement; it does not imply misconduct. Foreign principal, country and filings must be checked separately.',
      sourceUrl:'https://efile.fara.gov/api/v1/Registrants/json/Active',
      recordType:'FARA active registration', reviewState:'unreviewed' as const,
      evidenceTier:'original-source-index' as const, collectedAt
    }));
  return {rows,examined:items.length};
}
type KEVItem = { cveID?:string; vendorProject?:string; product?:string; vulnerabilityName?:string; shortDescription?:string; dateAdded?:string };
async function readCISA(): Promise<{rows:IntakeRecord[];examined:number}> {
  // CISA-managed GitHub mirror avoids the primary website's occasional anti-bot rejection.
  const body = await jsonGet('https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json', 13000) as { vulnerabilities?:KEVItem[]; count?:number };
  if (!Array.isArray(body.vulnerabilities) || !body.vulnerabilities.length || body.vulnerabilities.length !== body.count)
    throw new Error('CISA catalog completeness check failed');
  const collectedAt = new Date().toISOString();
  const rows:IntakeRecord[] = [...body.vulnerabilities]
    .filter(v=>/^CVE-\d{4}-\d{4,}$/.test(String(v.cveID || '')))
    .sort((a,b)=>String(b.dateAdded || '').localeCompare(String(a.dateAdded || '')))
    .slice(0,18)
    .map(v=>({
      id:'cisa-' + String(v.cveID), sourceId:'cisa' as const, sourceRecordId:String(v.cveID),
      title:clean(v.vulnerabilityName || (v.vendorProject + ' ' + v.product)),
      summary:clean(v.shortDescription).slice(0,420),
      date:isoDate(v.dateAdded),
      sourceUrl:'https://nvd.nist.gov/vuln/detail/' + String(v.cveID),
      recordType:'CISA KEV catalog entry', reviewState:'unreviewed' as const,
      evidenceTier:'original-source-index' as const, collectedAt
    }));
  return {rows,examined:body.vulnerabilities.length};
}
const SOURCE_IDS: FeedId[] = ['doj','fara','cisa','ofac'];
export async function readIntelligenceDesk() {
  const [stateRead,recordRead,ofacRead] = await Promise.allSettled([
    db.get<FeedState>('intel_source_health', SOURCE_IDS, {consistent:true}),
    db.list<IntakeRecord>('intel_records', { limit:240 }),
    readOFACMetadata()
  ]);
  const states = stateRead.status==='fulfilled'?stateRead.value:SOURCE_IDS.map(()=>null);
  const entries = recordRead.status==='fulfilled'?recordRead.value:{items:[] as IntakeRecord[]};
  const ofac = ofacRead.status==='fulfilled'?ofacRead.value:null;
  const records = entries.items
    .filter(r=>SOURCE_IDS.includes(r.sourceId) && r.reviewState==='unreviewed')
    .sort((a,b)=>((b.date || '').localeCompare(a.date || '') || (b.collectedAt || '').localeCompare(a.collectedAt || '')))
    .slice(0, 60);
  return {
    sources:FEEDS.map(s=>({...s,health:states[SOURCE_IDS.indexOf(s.id)] || null})),
    ofac, records, sampled:records.length,
    resultsNote:'This is a bounded recent intake sample, not a complete database search or a count of global incidents.',
    reviewPolicy:'Records are automatically imported source references. None are published as validated accusations; no government or person is assigned responsibility from a name or headline.'
  };
}
export async function syncFeed(sourceId: FeedId) {
  const attemptedAt = new Date().toISOString();
  let previous:FeedState | null = null;
  try {
    if(sourceId==='ofac') {
      const outcome = await syncOFAC();
      await recordCollectionAttempt({sourceId,attemptedAt,finishedAt:new Date().toISOString(),
        status:outcome.status==='ok'?'ok':'failed',examined:outcome.examined||0,
        matched:outcome.examined||0,inserted:outcome.inserted||0,
        zeroMatches:outcome.status==='ok' && (outcome.examined||0)===0,
        ...(outcome.status==='error'?{failureReason:String(outcome.error||'OFAC collection failed').slice(0,220)}:{}),
        collectionScope:'bounded-scheduled-official-public'});
      return outcome;
    }
    [previous] = await db.get<FeedState>('intel_source_health', [sourceId], {consistent:true});
    const feed = sourceId==='doj' ? await readDOJ() : sourceId==='fara' ? await readFARA() : await readCISA();
    if (feed.rows.length === 0 && sourceId !== 'doj') throw new Error('No valid source rows after normalization');    // Stable chosen IDs guarantee duplicate prevention across daily runs.
    // Only a small change-detection window is processed; never scan historical tables.
    const added = feed.rows.length ? await db.tx.add('intel_records', feed.rows) : [];
    const inserted = added.filter(Boolean).length;
    const state: FeedState = {
      sourceId, status:'ok', lastAttemptAt:attemptedAt, lastSuccessAt:attemptedAt,
      examined:feed.examined, inserted, duplicates:feed.rows.length-inserted
    };
    const [saved] = await db.tx.update('intel_source_health', [{id:sourceId,record:state}]);
    if (!saved) throw new Error('Source health status write not confirmed');
    await recordCollectionAttempt({sourceId,attemptedAt,finishedAt:new Date().toISOString(),status:'ok',
      examined:feed.examined,matched:feed.rows.length,inserted,zeroMatches:feed.rows.length===0,
      collectionScope:'bounded-scheduled-official-public'});
    return { sourceId, status:'ok', inserted, duplicates:state.duplicates, examined:feed.examined };
  } catch (err) {
    const failure = err instanceof Error ? err.name + ': ' + err.message : 'Unexpected ingestion failure';
    const state: FeedState = {
      sourceId, status:'error', lastAttemptAt:attemptedAt, lastSuccessAt:previous?.lastSuccessAt,
      lastError:failure.slice(0,220), examined:previous?.examined||0,
      inserted:0, duplicates:0
    };
    try { await db.tx.update('intel_source_health', [{id:sourceId,record:state}]); }
    catch (stateErr) { console.error('Failed to retain source health status', sourceId, stateErr); }
    await recordCollectionAttempt({sourceId,attemptedAt,finishedAt:new Date().toISOString(),status:'failed',
      examined:0,matched:0,inserted:0,zeroMatches:false,failureReason:failure.slice(0,220),
      collectionScope:'bounded-scheduled-official-public'});
    console.error('Official source intake failed',sourceId,failure);
    return {sourceId,status:'error',error:failure};
  }
}
export async function runCollectorCron(event: { payload?: { sourceId?: string } }) {
  const sourceId = event.payload?.sourceId;
  if (!SOURCE_IDS.includes(sourceId as FeedId)) {
    console.error('Ignored unknown collector source', sourceId);
    return { statusCode:200 };
  }
  await syncFeed(sourceId as FeedId);
  return { statusCode:200 };
}