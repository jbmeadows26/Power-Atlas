import { useEffect, useMemo, useRef, useState } from 'react';
import { Activity, AlertTriangle, ExternalLink, Radar, ShieldCheck } from 'lucide-react';
import './signal-pulse.css';

type Health = { status?: 'ok' | 'error'; lastAttemptAt?: string; lastSuccessAt?: string; lastError?: string };
type Feed = { id: string; name: string; health: Health | null };
type RecordItem = { id: string; sourceId: string; title: string; date: string; sourceUrl: string; countryMention?: string };
type Intel = { sources: Feed[]; records: RecordItem[] };
type AlliedEvidence = { id: string; sourceId?: string; countries?: string[]; title: string; date: string; url: string; publisher: string; sourceGroup?: string };
type AlliedPortal = { name: string; group: string; url: string; mode: string };
type AnalystManifest = { schemaVersion: number; generatedAt?: string | null; sourceHealth?: Record<string,string>; records: AlliedEvidence[]; alliedSources?: AlliedPortal[] };

const label = (id: string) => ({doj:'DOJ',fara:'FARA',cisa:'CISA',ofac:'OFAC'} as Record<string,string>)[id] || id.replace(/[-_]/g,' ');
const url = (input: string) => {
  try { const u = new URL(input); return u.protocol === 'https:' && !u.username && !u.password ? u.href : null; }
  catch { return null; }
};
const dateTime = (value?: string) => value && Number.isFinite(Date.parse(value))
  ? new Date(value).toLocaleString('en-US', {month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}) + ' UTC' : 'Unreported';
const age = (value: string | undefined, now: number) => {
  if (!value || !Number.isFinite(Date.parse(value))) return 'No successful run';
  const hours = (now - Date.parse(value)) / 3600000;
  if (hours < -1) return 'Clock discrepancy';
  if (hours < 1) return 'Within 1h';
  if (hours < 48) return Math.floor(hours) + 'h ago';
  return Math.floor(hours / 24) + 'd ago · stale';
};
const utcWeek = (ms: number) => {
  const d = new Date(ms), day = (d.getUTCDay()+6)%7;
  return Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate()-day);
};
type Props = { intel: Intel | null; error: boolean; activeCountry?: string };
export default function SignalPulse({ intel, error, activeCountry }: Props) {
  const [now, setNow] = useState(() => Date.now());
  const [newSinceVisit, setNewSinceVisit] = useState<number | null>(null);
  const [isFirstVisit, setIsFirstVisit] = useState(true);
  const [analyst, setAnalyst] = useState<AnalystManifest | null>(null);
  const [analystError, setAnalystError] = useState(false);
  const [analystRefresh, setAnalystRefresh] = useState(0);
  useEffect(() => { const timer=window.setInterval(()=>setAnalystRefresh(v=>v+1),5*60*1000); return ()=>window.clearInterval(timer); },[]);
  useEffect(() => {
    let active = true;
    fetch(import.meta.env.BASE_URL + 'analysis/manifest.json?t=' + Date.now(), {cache:'no-store'})
      .then(async response => { if (!response.ok) throw Error('Analyst index missing'); return response.json(); })
      .then((value: AnalystManifest) => {
        if (![1,2].includes(value.schemaVersion) || !Array.isArray(value.records) || !Array.isArray(value.alliedSources)) throw Error('Invalid source snapshot');
        if (active) { setAnalyst(value); setAnalystError(false); }
      })
      .catch(() => { if (active) { setAnalyst(null); setAnalystError(true); } });
    return () => { active = false; };
  }, [analystRefresh]);
  const initialized = useRef(false);
  const seenIds = useRef<string[] | null>(null);
  useEffect(() => { const interval = window.setInterval(() => setNow(Date.now()), 60000); return () => window.clearInterval(interval); },[]);
  const records = intel?.records || [];
  const recordIds = useMemo(() => JSON.stringify(records.map(record => record.id).filter(Boolean).sort()),[intel]);
  useEffect(() => {
    if (!intel) return;
    let ids: string[] = [];
    try { ids = JSON.parse(recordIds) as string[]; } catch { return; }
    // A previous snapshot of the same browser, not a global event or intelligence alert.
    const key = 'ea.intelligence.observed-ids.v1';
    let previous: string[] | null = null;
    try { const saved = window.localStorage.getItem(key);
      if (saved !== null) { const parsed = JSON.parse(saved); if (Array.isArray(parsed)) previous = parsed.filter((id): id is string => typeof id === 'string'); }
      if (!initialized.current) {
        setNewSinceVisit(previous === null ? null : ids.filter(id => !new Set(previous).has(id)).length);
        setIsFirstVisit(previous === null);
        initialized.current = true;
      } else if (seenIds.current) {
        const seen = new Set(seenIds.current);
        setNewSinceVisit(ids.filter(id => !seen.has(id)).length);
        setIsFirstVisit(false);
      }
      seenIds.current = ids;
      window.localStorage.setItem(key, JSON.stringify(ids.slice(0,500)));
    } catch { setNewSinceVisit(null); setIsFirstVisit(true); }
  },[intel,recordIds]);
  const start = utcWeek(now) - 7 * 7 * 86400000;
  const weeks = Array.from({length:8},(_,index)=>start+index*7*86400000);
  const counts = weeks.map(week => records.filter(record => {
    const t = Date.parse(record.date);
    return Number.isFinite(t) && t >= week && t < week + 7*86400000 && t <= now;
  }).length);
  const peak = Math.max(1,...counts);
  const dated = records.filter(record => Number.isFinite(Date.parse(record.date)) && Date.parse(record.date) <= now);
  const undatedCount = records.length - dated.length;
  const sourceMix = Object.entries(records.reduce<Record<string,number>>((acc,r) => {
    const key=r.sourceId || 'unspecified'; acc[key]=(acc[key]||0)+1; return acc;
  },{})).sort((a,b)=>b[1]-a[1]);
  const maxSource = Math.max(1,...sourceMix.map(([,count])=>count));
  const feeds = intel?.sources || [];
  const errors = feeds.filter(feed => feed.health?.status === 'error');
  const unknown = feeds.filter(feed => !feed.health?.status);
  const stale = feeds.filter(feed => feed.health?.status === 'ok'
    && (!feed.health.lastSuccessAt || !Number.isFinite(Date.parse(feed.health.lastSuccessAt)) || now-Date.parse(feed.health.lastSuccessAt)>48*3600000));
  const needsReview = errors.length+unknown.length+stale.length;
  const assessments = (analyst?.records || []).filter(record=>record.sourceId==='allied-assessment');
  const countryAssessments = assessments.filter(record=>!activeCountry||activeCountry==='all'||record.countries?.includes(activeCountry));
  const alliedStatus = analyst?.sourceHealth?.alliedAssessments || 'not assessed';
  const portals = analyst?.alliedSources || [];
  const recent = [...records].filter(record=>Number.isFinite(Date.parse(record.date)))
    .sort((a,b)=>Date.parse(b.date)-Date.parse(a.date)).slice(0,6);
  return <section className="sp-root" aria-label="Source-dated collection signal pulse">
    <header className="sp-head">
      <div><span><Radar size={15}/> OPERATIONS PULSE / BOUNDED SOURCE SAMPLE</span>
        <h2>What changed, what needs checking</h2></div>
      <div className="sp-head-counters">
        <span><b>{intel ? needsReview : '—'}</b> feed checks requiring review</span>
        <span><b>{error ? '—' : intel ? newSinceVisit === null ? '—' : newSinceVisit : '—'}</b> newly seen sample IDs</span>
      </div>
    </header>
    {error && <p className="sp-error" role="status"><AlertTriangle size={15}/> Intelligence API unavailable. Counts cannot be treated as zero.</p>}
    <div className="sp-grid">
      <section className="sp-panel">
        <div className="sp-panel-title"><span><Activity size={14}/> PUBLICATION HISTORY</span><small>8 UTC weeks · sampled records</small></div>
        <div className="sp-bars" role="img" aria-label={'Dated record publications by week: '+counts.join(', ')}>
          {weeks.map((week,index)=><div key={week} className="sp-week">
            <strong>{counts[index] || '·'}</strong>
            <div className="sp-bar-track"><span style={{height:(counts[index]?Math.max(4,100*counts[index]/peak):0)+'%'}}/></div>
            <small>{new Date(week).toLocaleDateString('en-US',{month:'numeric',day:'numeric',timeZone:'UTC'})}</small>
          </div>)}
        </div>
        <p className="sp-note">Publication dates in the returned sample, not observed incidents or a complete historical trend. {undatedCount} undated sample records. No publication in a week does not mean no activity.</p>
      </section>
      <section className="sp-panel">
        <div className="sp-panel-title"><span>INTAKE SOURCE MIX</span><small>{records.length} currently returned</small></div>
        <div className="sp-mix">
          {sourceMix.slice(0,7).map(([name,count])=><div key={name} className="sp-source">
            <div><span>{label(name)}</span><b>{count.toLocaleString()}</b></div>
            <div className="sp-meter"><i style={{width:count/maxSource*100+'%'}}/></div>
          </div>)}
          {!sourceMix.length && <p className="sp-note">No sample loaded. Do not infer zero intake.</p>}
        </div>
        <p className="sp-note">Mix reflects the API's bounded sample, not each government's total publications.</p>
      </section>
      <section className="sp-panel">
        <div className="sp-panel-title"><span>FEED FRESHNESS / SOURCE-BY-SOURCE</span><small>{feeds.length} reported</small></div>
        <div className="sp-health">
          {feeds.map(feed => {
            const condition=feed.health?.status === 'error'?'failed':!feed.health?.status?'unverified':!feed.health.lastSuccessAt||!Number.isFinite(Date.parse(feed.health.lastSuccessAt))||now-Date.parse(feed.health.lastSuccessAt)>48*3600000?'stale':'checked';
            return <div className="sp-feed" key={feed.id}>
              <span><i className={'sp-dot '+condition}/>{feed.name || label(feed.id)}</span>
              <strong>{condition.toUpperCase()}</strong>
              <small>Last successful: {age(feed.health?.lastSuccessAt,now)}</small>
            </div>;
          })}
          {!feeds.length && <p className="sp-note">Feed telemetry not returned. No connectors assumed healthy.</p>}
        </div>
        <p className="sp-note">{needsReview ? errors.length+' failed, '+stale.length+' stale, '+unknown.length+' unverified.' : 'No reported faults in monitored checks; unindexed sources remain unknown.'} Last-success time is more meaningful than a green connected badge.</p>
      </section>
      <section className="sp-panel">
        <div className="sp-panel-title"><span>RECENT SOURCE RECORDS</span><small>{activeCountry && activeCountry !== 'all' ? 'Global sample · not country attributed' : 'Global sample'}</small></div>
        <div className="sp-recent">
          {recent.map(record => {
            const href=url(record.sourceUrl);
            return <div key={record.id} className="sp-record">
              <span>{label(record.sourceId)} · {dateTime(record.date)}</span>
              {href ? <a href={href} target="_blank" rel="noopener noreferrer">{record.title}<ExternalLink size={12}/></a>
                : <strong>{record.title} · source link unavailable</strong>}
            </div>;
          })}
          {!recent.length && <p className="sp-note">No dated source records in the returned sample.</p>}
        </div>
        <p className="sp-note">{isFirstVisit?'A browser baseline is being saved; later visits can identify newly seen IDs.':'Newly seen means new to this browser snapshot, not a newly occurring event.'} {records.filter(record=>!url(record.sourceUrl)).length} sample records lack usable HTTPS source links.</p>
      </section>
    </div>
    <section className="sp-allied" aria-label="U.S. and allied government assessment coverage">
      <div className="sp-allied-head"><div><span>U.S. + ALLIED OFFICIAL ASSESSMENTS</span>
        <strong>{analystError ? 'Index unavailable' : analyst ? countryAssessments.length + ' indexed assessments in scope' : 'Checking assessment index…'}</strong>
        <small>Country tags reflect source indexing, not governmental responsibility or total national activity</small></div>
        <div><b>{analystError ? 'UNAVAILABLE' : alliedStatus.toUpperCase()}</b><small>Allied collector health</small>
          <small>Manifest: {dateTime(analyst?.generatedAt || undefined)}</small></div></div>
      {analystError && <p className="sp-error">Allied assessment snapshot unavailable. It must not be counted as zero.</p>}
      {analyst && <>
        <div className="sp-allied-kpis">
          <span><b>{assessments.length}</b> global indexed assessments</span>
          <span><b>{portals.length}</b> official source portals (references only)</span>
          <span><b>{countryAssessments.length}</b> indexed records {activeCountry && activeCountry !== 'all' ? 'explicitly tagged '+activeCountry : 'worldwide'}</span>
        </div>
        <div className="sp-allied-reports">
          {countryAssessments.slice(0,5).map(item=>{
            const href=url(item.url);
            return <article key={item.id}><span>{item.publisher} · {dateTime(item.date)} · {item.sourceGroup || 'Allied government'}</span>
              {href ? <a href={href} target="_blank" rel="noopener noreferrer">{item.title}<ExternalLink size={12}/></a> : <strong>{item.title} · original link unavailable</strong>}
            </article>;
          })}
          {countryAssessments.length===0&&<p className="sp-note">No explicitly country-tagged assessment in this bounded index. This does not establish that no allied government has published relevant information.</p>}
        </div>
        <details className="sp-allied-portals"><summary>Inspect all {portals.length} official allied source portals (discovery links, not ingested documents)</summary>
          <div>{portals.map((item,index)=>{const href=url(item.url);return href?<a href={href} target="_blank" rel="noopener noreferrer" key={item.name+index}>{item.name} · {item.group}<ExternalLink size={11}/></a>:<span key={item.name+index}>{item.name} · link missing</span>;})}</div>
        </details>
      </>}
    </section>
    <footer className="sp-foot"><ShieldCheck size={14}/> Triage source faults first. A source mention, sanction-program count, or new record does not establish threat severity, causation, or government responsibility.</footer>
  </section>;
}
