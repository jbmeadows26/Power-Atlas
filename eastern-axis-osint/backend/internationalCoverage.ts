import { createHash } from 'node:crypto';
import { db } from './runtime';

const UK_URL = 'https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv';
const CA_URL = 'https://www.international.gc.ca/world-monde/assets/office_docs/international_relations-relations_internationales/sanctions/sema-lmes.xml';

type Sample = {
  identifier: string;
  name: string;
  kind: string;
  regime: string;
  reportedParent?: string;
};
type CountrySummary = { count: number; samples: Sample[] };
type Snapshot = {
  id: string;
  checkedAt: string;
  publicationDate: string | null;
  fileSha256: string;
  sourceUrl: string;
  source: string;
  status: 'ok';
  totalUniqueDesignations: number;
  recordsParsed: number;
  regimeCounts: Record<string, number>;
  countryRegimes: Record<string, CountrySummary>;
  unidentifiedCountryRegimes: number;
  sampleLimit: number;
};
type SourceHealth = {
  id: string;
  status: 'ok' | 'failed';
  attemptedAt: string;
  lastSuccessAt?: string;
  error?: string;
};
const regimes: Array<[RegExp, string]> = [
  [/\brussia|russian\b/i, 'RU'],
  [/\bbelarus/i, 'BY'],
  [/\biran|iranian\b/i, 'IR'],
  [/\bnorth korea|dprk\b/i, 'KP'],
  [/\bchina|chinese\b/i, 'CN'],
  [/\bvenezuela/i, 'VE'],
  [/\bcuba\b/i, 'CU'],
  [/\bafghan/i, 'AF'],
  [/\bmyanmar|burma\b/i, 'MM'],
  [/\bsyria/i, 'SY'],
  [/\blibya/i, 'LY'],
  [/\bsudan/i, 'SD'],
  [/\bsouth sudan/i, 'SS'],
  [/\bsomalia/i, 'SO'],
  [/\byemen/i, 'YE'],
  [/\biraq/i, 'IQ'],
  [/\bethiopia/i, 'ET'],
  [/\bcentral african republic/i, 'CF'],
  [/\bcongo/i, 'CD'],
  [/\bnicaragua/i, 'NI'],
  [/\bmali\b/i, 'ML'],
  [/\bburundi/i, 'BI'],
  [/\bguinea/i, 'GN'],
  [/\bhaiti/i, 'HT'],
  [/\bzimbabwe/i, 'ZW'],
  [/\blebanon/i, 'LB']
];
const sha = (input: string) => createHash('sha256').update(input, 'utf8').digest('hex');

function regimeCode(regime: string) {
  // A legal regime is NOT a sanctioned person's nationality or location.
  return regimes.find(([re]) => re.test(regime))?.[1] || '';
}
function tag(xml: string, name: string): string {
  const value = xml.match(new RegExp('<' + name + '(?:\\s[^>]*)?>([\\s\\S]*?)<\\/' + name + '>'));
  return (value?.[1] || '').replace(/&amp;/g, '&').replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").trim();
}
function* csvRows(text: string): Generator<string[]> {
  let row: string[] = [];
  let cell = '';
  let quote = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quote && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else {
        quote = !quote;
      }
    } else if (!quote && char === ',') {
      row.push(cell);
      cell = '';
    } else if (!quote && (char === '\r' || char === '\n')) {
      if (char === '\r' && text[i + 1] === '\n') i++;
      row.push(cell);
      cell = '';
      if (row.some(x => x.length > 0)) yield row;
      row = [];
    } else {
      cell += char;
    }
  }
  row.push(cell);
  if (row.some(x => x.length > 0)) yield row;
}
async function publicFile(url: string, maxBytes: number, timeout: number) {
  const response = await fetch(url, {
    headers: { Accept: 'text/csv, application/xml, text/xml, */*' },
    signal: AbortSignal.timeout(timeout)
  });
  if (!response.ok) throw new Error('Official source HTTP ' + response.status);
  const advertisedSize = Number(response.headers.get('content-length') || 0);
  if (advertisedSize > maxBytes) throw new Error('Official file exceeds configured size ceiling');
  const raw = await response.text();
  if (Buffer.byteLength(raw, 'utf8') > maxBytes) throw new Error('Official response exceeds configured size ceiling');
  return raw;
}
function accumulator(id: string, sourceUrl: string, name: string, publicationDate: string | null, fileSha256: string): Snapshot {
  return {
    id, sourceUrl, source: name, checkedAt: new Date().toISOString(), publicationDate, fileSha256,
    status: 'ok', totalUniqueDesignations: 0, recordsParsed: 0,
    regimeCounts: {}, countryRegimes: {}, unidentifiedCountryRegimes: 0, sampleLimit: 5
  };
}
function addRecord(snap: Snapshot, regime: string, sample: Sample | null) {
  const label = regime.slice(0, 180) || 'Unspecified legal regime';
  snap.regimeCounts[label] = (snap.regimeCounts[label] || 0) + 1;
  const country = regimeCode(label);
  if (!country) {
    snap.unidentifiedCountryRegimes++;
    return;
  }
  const countryRecord = snap.countryRegimes[country] || { count: 0, samples: [] };
  countryRecord.count++;
  if (sample && countryRecord.samples.length < 5) countryRecord.samples.push(sample);
  snap.countryRegimes[country] = countryRecord;
}
async function recordSnapshot(snap: Snapshot) {
  const serialized = JSON.stringify(snap);
  if (Buffer.byteLength(serialized, 'utf8') > 220_000) {
    throw new Error('Sanctions snapshot too large; refusing unbounded database write');
  }
  const [saved] = await db.tx.update('allied_sanctions_snapshots', [{ id: snap.id, record: snap }]);
  if (!saved) throw new Error('Sanctions snapshot write unconfirmed');
}
async function health(id: string, status: SourceHealth['status'], attemptedAt: string, reason?: string) {
  const [previous] = await db.get<SourceHealth>('allied_sanctions_health', [id]);
  const record: SourceHealth = {
    id, status, attemptedAt,
    lastSuccessAt: status === 'ok' ? attemptedAt : previous?.lastSuccessAt,
    ...(reason ? { error: reason.slice(0, 220) } : {})
  };
  await db.tx.update('allied_sanctions_health', [{ id, record }]);
}
export async function syncUK() {
  const started = new Date().toISOString();
  try {
    const data = await publicFile(UK_URL, 85_000_000, 28_000);
    const newline = data.indexOf('\n');
    if (newline < 0 || !data.slice(0, newline).includes('Report Date:')) throw new Error('UK CSV version header missing');
    const reportDate = data.slice(0, newline).split(':').slice(1).join(':').trim();
    const reader = csvRows(data.slice(newline + 1));
    const columns = reader.next().value;
    if (!columns || !columns.includes('Unique ID') || !columns.includes('Regime Name') || !columns.includes('Designation Type')) {
      throw new Error('UK Sanctions List column schema changed');
    }
    const get = (row: string[], key: string) => row[columns.indexOf(key)]?.trim() || '';
    const snap = accumulator('uk', UK_URL, 'United Kingdom FCDO UK Sanctions List', reportDate, sha(data));
    const seen = new Set<string>();
    for (const row of reader) {
      snap.recordsParsed++;
      const uid = get(row, 'Unique ID');
      if (!/^[A-Za-z0-9-]{4,48}$/.test(uid) || seen.has(uid)) continue;
      seen.add(uid);
      const regime = get(row, 'Regime Name');
      const kind = get(row, 'Designation Type');
      const name = get(row, 'Name 6') || [get(row,'Name 1'),get(row,'Name 2'),get(row,'Name 3')].filter(Boolean).join(' ');
      const parent = get(row, 'Parent company');
      const corporate = /entity|ship/i.test(kind) && name.length > 0;
      const sample: Sample | null = corporate ? {
        identifier: uid, name: name.slice(0, 160), kind: kind.slice(0, 50),
        regime: regime.slice(0, 130), ...(parent ? { reportedParent: parent.slice(0, 160) } : {})
      } : null;
      addRecord(snap, regime, sample);
    }
    snap.totalUniqueDesignations = seen.size;
    if (seen.size < 1500) throw new Error('UK CSV incomplete: insufficient unique designation IDs');
    await recordSnapshot(snap);
    await health('uk', 'ok', started);
    return { source: 'uk', status: 'ok', count: snap.totalUniqueDesignations, checkedAt: snap.checkedAt };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'UK ingestion unknown failure';
    await health('uk', 'failed', started, message);
    return { source: 'uk', status: 'failed', reason: message };
  }
}
export async function syncCanada() {
  const started = new Date().toISOString();
  try {
    const data = await publicFile(CA_URL, 10_000_000, 20_000);
    if (!data.includes('<data-set') || !data.includes('<record>')) throw new Error('Canadian XML schema changed');    const snap = accumulator('canada', CA_URL, 'Global Affairs Canada Autonomous Sanctions List', null, sha(data));
    const seen = new Set<string>();
    for (const match of data.matchAll(/<record>([\s\S]*?)<\/record>/g)) {
      snap.recordsParsed++;
      const record = match[1];
      const regime = tag(record, 'Country-Pays').split('/')[0].trim();
      const schedule = tag(record, 'Schedule-Annexe');
      const index = tag(record, 'Item-NumeroDarticle');
      const lastname = tag(record, 'LastName-NomDeFamille');
      const org = tag(record, 'Entity-Entite') || tag(record, 'Entity-Entité');
      const name = org || lastname;
      const signature = [regime, schedule, index, name].join('|');
      if (!name || seen.has(signature)) continue;
      seen.add(signature);
      const example: Sample | null = org ? {
        identifier: sha(signature).slice(0, 16), name: org.slice(0, 160),
        kind: 'Entity (as published)', regime: regime.slice(0, 130)
      } : null;
      addRecord(snap, regime, example);
    }
    snap.totalUniqueDesignations = seen.size;
    if (seen.size < 300) throw new Error('Canadian XML incomplete: fewer than 300 unique records');
    await recordSnapshot(snap);
    await health('canada', 'ok', started);
    return { source:'canada', status:'ok', count:snap.totalUniqueDesignations, checkedAt:snap.checkedAt };
  } catch (e) {
    const message = e instanceof Error ? e.message : 'Canada ingestion unknown failure';
    await health('canada', 'failed', started, message);
    return { source:'canada', status:'failed', reason:message };
  }
}
export async function readAlliedSanctions(code: string) {
  if (!/^[A-Z]{2}$/.test(code) && code !== 'all') return null;
  const keys = ['uk', 'canada'];
  let [snapshots, healths] = await Promise.all([
    db.get<Snapshot>('allied_sanctions_snapshots', keys, { consistent: true }),
    db.get<SourceHealth>('allied_sanctions_health', keys)
  ]);
  // The smaller Canadian register is safe to initialize from an official XML
  // query on first country visit. UK CSV is much larger: scheduled only.
  if (!snapshots[1]) {
    await syncCanada();
    [snapshots, healths] = await Promise.all([
      db.get<Snapshot>('allied_sanctions_snapshots', keys, { consistent: true }),
      db.get<SourceHealth>('allied_sanctions_health', keys)
    ]);
  }
  return {
    scope: code, checkedAt: new Date().toISOString(),
    sources: keys.map((id, i) => {
      const snap = snapshots[i];
      const report = code === 'all' ? null : snap?.countryRegimes[code] || null;
      return {
        id, name: id === 'uk' ? 'United Kingdom · UK Sanctions List' : 'Canada · Autonomous Sanctions List',
        sourceUrl: id === 'uk' ? UK_URL : CA_URL,
        status: snap ? 'snapshot' : healths[i]?.status === 'failed' ? 'failed' : 'awaiting-first-sync',
        lastAttemptAt: healths[i]?.attemptedAt || null,
        checkedAt: snap?.checkedAt || null, publicationDate: snap?.publicationDate || null,
        contentSha256: snap?.fileSha256 || null,
        listedUniqueDesignations: snap?.totalUniqueDesignations || null,
        parsedSourceRows: snap?.recordsParsed || null,
        regimeRecordCount: code === 'all' ? null : report?.count || 0,
        samples: code === 'all' ? [] : report?.samples || [],
        regimes: code === 'all' ? Object.entries(snap?.regimeCounts || {}).sort((a,b)=>b[1]-a[1]).slice(0,12).map(([name,count])=>({name,count})) : [],
        warning: 'Country filtering uses the named legal SANCTIONS REGIME, not the location or nationality of listed parties. Alias and address rows are collapsed by publisher ID. No identity, ownership, criminal liability or foreign-government direction is inferred.'
      };
    }),
    policy: 'These are source-index summaries for research, not legal screening. Legal scope, delisting, aliases and ownership-control tests require the current official regulations. The UK OFSI list ceased updates on 28 January 2026.',
    graphPolicy: 'Any parent-company label is an uncorroborated, source-reported field. It is not an analyst-validated beneficial-owner link.'
  };
}
