import { useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Clock3, ExternalLink, Network, RefreshCcw, ShieldAlert, ShieldCheck } from 'lucide-react';
import './resilienceWatch.css';

type Observation = {
  id:string; title:string; category:string; provider?:string; checkedAt:string;
  source:string; sourceUrl?:string|null; status:string; scope:string;
  dnsMs?:number; handshakeMs?:number; certDaysRemaining?:number;
  prefix?:string; expectedOrigin?:string; rpkiState?:string; regions?:Array<{country:string;httpStatus:number|null;state:string;latencyMs?:number|null}>;
  failedRegions?:number; detail?:string; metric?:string; value?:number; unit?:string; baseline?:number|null; note?:string; bgpUpdateCount?:number; bgpWindowHours?:number;
  frequencyHz?:number; deviationHz?:number; sourceTime?:string; sampleAgeSeconds?:number; sampleCount?:number; expectedHz?:number;
  exchange?:string; exchangeId?:number; latencyMs?:number; requestMethod?:string; httpStatus?:number;
};
type Snapshot = {
  schemaVersion:number; checkedAt:string; status:string; summary:string; sampledCount:number;
  incidents:Array<{id:string;severity:string;title:string;explanation:string;evidenceIds:string[];confidence:string}>;
  screeningSignals?:Array<{id:string;title:string;kind:string;detail:string;evidenceIds:string[];observed?:number;baselineMedian?:number}>;
  observations:Observation[]; capabilities:Array<{id:string;title:string;source:string;status:string}>;
  limitations:string[]; history:Array<{checkedAt:string;observed:number;alerts:number;errors:number}>;
};
const RAW_SNAPSHOT = 'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json';
const categories:Record<string,string> = {
  regional_http:'Independent regional HTTP',dns_tls:'TLS, DNS and certificate health',
  bgp_rpki:'Routing integrity',traffic:'Independent traffic reports',
  grid_frequency:'Official GB power-grid telemetry',ixp_directory:'Public IXP directory (not congestion)',pki_transport:'Certificate-authority CRL transport',
  automation:'Autonomous remediation', 'control-plane':'Cloud control-plane synchronization',
  deployment:'Deployments and validation', capacity:'Hard limits and capacity',
  routing:'IXP and transport',physical:'Grid, UPS, fiber and DAS',
  endpoint:'Out-of-band endpoint security',tracing:'MELT and tracing',pki:'Certificate revocation'
};
function age(iso?:string) {
  const stamp=Date.parse(iso||'');
  if (!Number.isFinite(stamp)) return 'unknown age';
  const m=Math.max(0,Math.floor((Date.now()-stamp)/60000));
  return m<60 ? m+'m ago' : m<1440 ? Math.floor(m/60)+'h ago' : Math.floor(m/1440)+'d ago';
}
function date(iso?:string) {
  if(!iso || !Number.isFinite(Date.parse(iso))) return 'Not yet observed';
  return new Date(iso).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZone:'UTC'})+' UTC';
}
export default function ResilienceWatch(){
  const [snapshot,setSnapshot]=useState<Snapshot|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [revision,setRevision]=useState(0);
  const [filter,setFilter]=useState('all');
  const [showAll,setShowAll]=useState(false);
  useEffect(()=>{
    let alive=true;setLoading(true);setError('');
    fetch(RAW_SNAPSHOT+'?v='+Date.now(),{cache:'no-store',headers:{Accept:'application/json'}})
      .then(async response=>{if(!response.ok)throw new Error('Published snapshot is unavailable ('+response.status+')');return response.json();})
      .then((data:Snapshot)=>{
        if(!data || data.schemaVersion!==1 || !Array.isArray(data.observations) || !Array.isArray(data.capabilities) || typeof data.checkedAt!=='string')throw new Error('Unexpected monitoring snapshot schema');
        if(alive)setSnapshot(data);
      })
      .catch(e=>{if(alive){setSnapshot(null);setError(e instanceof Error?e.message:'Monitoring snapshot unavailable');}})
      .finally(()=>{if(alive)setLoading(false);});
    return()=>{alive=false;};
  },[revision]);
  const stale=snapshot ? Date.now()-Date.parse(snapshot.checkedAt)>120*60000 : false;
  const groups=useMemo(()=>snapshot ? [...new Set(snapshot.observations.map(o=>o.category))] : [],[snapshot]);
  const observations=useMemo(()=>!snapshot?[]:snapshot.observations.filter(o=>filter==='all'||o.category===filter),[snapshot,filter]);
  const supported=snapshot?.capabilities.filter(c=>c.status==='sampled').length||0;
  const notConnected=snapshot?.capabilities.filter(c=>c.status!=='sampled').length||0;
  return <section className="rw-root" aria-label="Independent systemic resilience monitoring">
    <div className="rw-header"><div>
      <div className="rw-eyebrow"><Network size={16}/> INDEPENDENT RESILIENCE INTELLIGENCE</div>
      <h1>Early signs of cascading failure</h1>
      <p>Sample the internet from outside shared vendor control planes. Cross-check network, identity, routing and physical constraints—without equating service disruption with a cyberattack.</p>
    </div><button type="button" className="rw-refresh" onClick={()=>setRevision(v=>v+1)} disabled={loading}><RefreshCcw size={15}/> Refresh snapshot</button></div>
    {loading && !snapshot && <p className="rw-notice"><Activity size={17}/> Retrieving most recent public monitoring snapshot…</p>}
    {error && <p role="status" className="rw-notice rw-warning"><AlertTriangle size={17}/> {error}. No artificial normal status has been substituted.</p>}
    {snapshot && <>
      <div className={'rw-overall '+(snapshot.status==='watch'?'rw-alert':'')}>
        <div className="rw-overall-main">{snapshot.status==='watch'?<ShieldAlert size={22}/>:<Clock3 size={22}/>}<div>
          <strong>{stale?'STALE SNAPSHOT':snapshot.status==='watch'?'CORRELATED WATCH':snapshot.status==='screening'?'SCREENING SIGNALS — UNCONFIRMED':snapshot.status==='unavailable'?'DATA UNAVAILABLE':'NO CORRELATED ALERT IN SAMPLE'}</strong>
          <p>{snapshot.summary}. {stale?'The latest published snapshot is over two hours old; do not use it to infer present conditions.':''}</p>
        </div></div><span>{date(snapshot.checkedAt)} · {age(snapshot.checkedAt)}</span>
      </div>
      <div className="rw-metrics"><div><span>Source observations</span><strong>{snapshot.sampledCount}</strong><small>Scope-specific checks, not services certified healthy</small></div>
        <div><span>Correlated watches</span><strong>{snapshot.incidents.length}</strong><small>Screening signals, not attributed events</small></div>
        <div><span>Connected capabilities</span><strong>{supported} / {snapshot.capabilities.length}</strong><small>{notConnected} not sampled or require access</small></div></div>
      {(snapshot.screeningSignals?.length||0)>0 && <div className="rw-incident-list" aria-label="Unconfirmed screening signals">
        {snapshot.screeningSignals?.map(s=><article className="rw-incident" key={s.id}>
          <div><AlertTriangle size={17}/><strong>{s.title}</strong><span>REVIEW</span></div>
          <p>{s.detail}</p><small>{typeof s.observed==='number'?'Observed '+s.observed+' · baseline '+s.baselineMedian+' · ':''}Evidence: {s.evidenceIds.join(' · ')} · not corroborated</small>
        </article>)}
      </div>}
      {snapshot.incidents.length>0 && <div className="rw-incident-list" aria-label="Correlated alerts">
        {snapshot.incidents.map(x=><div className="rw-incident" key={x.id}><div><AlertTriangle size={18}/><strong>{x.title}</strong><span>{x.severity.toUpperCase()}</span></div>
        <p>{x.explanation}</p><small>Evidence: {x.evidenceIds.join(' · ')} · confidence: {x.confidence}</small></div>)}</div>}
      <div className="rw-toolbar"><h2>Independent observations</h2><label>Signal family <select aria-label="Filter resilience signal family" value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All signals</option>
        {groups.map(g=><option value={g} key={g}>{categories[g]||g}</option>)}</select></label></div>
      <div className="rw-probes">{observations.map(o=><article className="rw-probe" key={o.id}>
        <div className="rw-probe-top"><div><span className="rw-category">{categories[o.category]||o.category}</span><h3>{o.title}</h3></div>
          <span className={'rw-pill '+(o.status==='observed'?'rw-ok':o.status==='warning'?'rw-warning-pill':'rw-na')}>{o.status==='observed'?'SAMPLED':o.status==='warning'?'FLAGGED':o.status==='not_configured'?'NO TOKEN':o.status==='stale'?'STALE':o.status.toUpperCase().replaceAll('_',' ')}</span></div>
        <div className="rw-detail-grid">
          {o.dnsMs!==undefined && <span>DNS <b>{o.dnsMs} ms</b></span>}
          {o.handshakeMs!==undefined && <span>TLS handshake <b>{o.handshakeMs} ms</b></span>}
          {o.certDaysRemaining!==undefined && <span>Certificate expiry <b>{o.certDaysRemaining} days</b></span>}
          {o.rpkiState && <span>RPKI origin <b>{o.rpkiState}</b></span>}
          {typeof o.frequencyHz==='number' && <span>Grid frequency <b>{o.frequencyHz.toFixed(3)} Hz</b></span>}
          {typeof o.deviationHz==='number' && <span>Deviation from 50 Hz <b>{o.deviationHz.toFixed(3)} Hz</b></span>}
          {o.sourceTime && <span>Source observed <b>{date(o.sourceTime)}</b></span>}
          {typeof o.sampleAgeSeconds==='number' && <span>Reading delay <b>{Math.max(0,Math.round(o.sampleAgeSeconds/60))}m</b></span>}
          {o.exchange && <span>Exchange listing <b>{o.exchange}</b></span>}
          {o.requestMethod && <span>CRL request <b>{o.requestMethod}</b></span>}
          {typeof o.httpStatus==='number' && <span>HTTP status <b>{o.httpStatus}</b></span>}
          {typeof o.latencyMs==='number' && <span>Endpoint latency <b>{o.latencyMs.toFixed(1)} ms</b></span>}
          {typeof o.bgpUpdateCount==='number' && <span>Sampled BGP updates <b>{o.bgpUpdateCount} / {o.bgpWindowHours||1}h</b></span>}
          {o.metric && o.value!==undefined && <span>Operator metric <b>{o.value} {o.unit||''}{typeof o.baseline==='number'?' · baseline '+o.baseline:''}</b></span>}
          {o.regions?.map((r,i)=><span key={r.country+i}>{r.country||'Unknown region'} <b>{r.httpStatus??'No HTTP status'} · {r.state}{typeof r.latencyMs==='number'?' · '+r.latencyMs+'ms':''}</b></span>)}
        </div>
        {o.detail && <p className="rw-detail-error">{o.detail}</p>}
        {o.note && <p className="rw-scope">{o.note}</p>}
        <p className="rw-scope">{o.scope}</p>
        <div className="rw-source">{o.sourceUrl?<a href={o.sourceUrl} target="_blank" rel="noopener noreferrer">{o.source}<ExternalLink size={12}/></a>:<span>{o.source}</span>}<span>{age(o.checkedAt)}</span></div>
      </article>)}</div>
      <div className="rw-toolbar"><h2>Collection coverage & private-access gaps</h2><button type="button" onClick={()=>setShowAll(v=>!v)}>{showAll?'Show fewer':'Show all '+snapshot.capabilities.length+' capabilities'}</button></div>
      <div className="rw-capabilities">{snapshot.capabilities.slice(0,showAll?undefined:9).map(c=><div className="rw-capability" key={c.id}>
        <div>{c.status==='sampled'?<CheckCircle2 size={16}/>:<Clock3 size={16}/>}<strong>{c.title}</strong><small>{c.source}</small></div>
        <span className={c.status==='sampled'?'rw-live':'rw-missing'}>{c.status}</span>
      </div>)}</div>
      <details className="rw-method"><summary>Limitations and escalation rules</summary>
        <p>A sampled endpoint cannot establish worldwide system health. Alerts require independent providers and more than one affected region; no cause, actor, or attack is inferred. Public reachability probes do not verify authenticated business transactions.</p>
        <ul>{snapshot.limitations.map(v=><li key={v}>{v}</li>)}</ul>
        <p>Enable private telemetry only through authorized, aggregate-only connectors. Never publish endpoint traces, authentication tokens, security logs or private infrastructure maps.</p>
      </details>
    </>}
  </section>;
}
