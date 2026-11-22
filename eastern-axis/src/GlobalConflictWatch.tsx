import { useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, ArrowUpRight, BrainCircuit, ChevronDown, ChevronRight, Clock3, Database, Globe2, RefreshCw, ShieldCheck, TrendingDown, TrendingUp } from 'lucide-react';
import './globalConflictWatch.css';

type Direction = 'deteriorating'|'improving'|'stable'|'unassessed';
type Status = 'assessed'|'review'|'monitor'|'data-gap';
type Evidence = {id:string;title:string;date:string;publisher:string;url:string};
type Zone = {
  id:string;name:string;region:string;countryCodes:string[];kind:string;status:Status;
  direction:Direction;change:{status:string;history:number[];recent:number|null;median:number|null;robustZ:number|null;changePct:number|null;direction:Direction};
  observationEnd:string|null;measurementFresh:boolean;modelReviewed:boolean;promoted:boolean;sourceQuality:string;
  media:{status:string;articles:number;publishers:number;evidence:Evidence[];limitation:string};
  actors:string[];whoBenefits:string;globalRisks:string;potentialUpside:string;reason:string;
  evidence:{source:string;url:string;observedAt:string|null;kind:string}[];
};
type Report = {
  schemaVersion:number;generatedAt:string;status:string;category:string;
  analyst:{name:string;model:string|null;modelStatus:string;reviewed:number;gate:string;commandEligible:number;methodology:string};
  sources:{ucdp:{status:string;rows?:number;version:string;url:string};rss?:{status:string;publishers:number;feeds:{name:string;status:string;url:string;articles:number}[]};gdelt:{status:string;targets:number;url:string}};
  measurement:{latestCodedEvent:string|null;dataAgeDays:number|null;eventCount:number;eventFresh:boolean};
  summary:{hotspots:number;assessed:number;deteriorating:number;improving:number;awaitingReview:number;monitored:number;coverageGaps:number};
  zones:Zone[];limitations:string[];
};
const prettyDate = (s?:string|null) => s && Number.isFinite(Date.parse(s)) ?
  new Date(s).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Not available';
const statusLabel:Record<Status,string> = {assessed:'Reviewed exception',review:'Awaiting corroboration',monitor:'Monitoring', 'data-gap':'Evidence gap'};
const directionLabel:Record<Direction,string> = {deteriorating:'Deteriorating',improving:'Improving',stable:'Within historical variation',unassessed:'Not assessable'};
const number = (n:number|null) => n===null?'—':new Intl.NumberFormat('en-US').format(n);
const safeLink = (link:string) => {try{return new URL(link).protocol==='https:';}catch{return false;}};
const age = (s?:string|null) => s && Number.isFinite(Date.parse(s)) ? Math.max(0,(Date.now()-Date.parse(s))/86400000) : Infinity;

export default function GlobalConflictWatch({countryCode='all',countryName}:{countryCode?:string;countryName?:string}) {
  const [data,setData] = useState<Report|null>(null);
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(true);
  const [refresh,setRefresh] = useState(0);
  const [filter,setFilter] = useState('All assessments');
  const [region,setRegion] = useState('All regions');
  const [query,setQuery] = useState('');
  const [expanded,setExpanded] = useState<string|null>(null);

  useEffect(()=>{
    let current=true;
    setLoading(true);
    setError('');
    const root=String(import.meta.env.BASE_URL||'/');
    fetch(root+'analysis/global-conflict-watch.json',{cache:'no-store'})
      .then(async res=>{if(!res.ok)throw new Error('The conflict analyst has not published a verified snapshot');return res.json();})
      .then((report:Report)=>{
        if(!current)return;
        if(report.schemaVersion!==1||report.category!=='Defense, Security & Cyber'||!Array.isArray(report.zones)||!report.summary||!report.measurement)throw new Error('Conflict report did not pass schema validation');
        setData(report);
      })
      .catch(e=>{if(current){setData(null);setError(String(e?.message||'Conflict feed unavailable'));}})
      .finally(()=>{if(current)setLoading(false);});
    return()=>{current=false;};
  },[refresh]);

  const selected = useMemo(()=>data?.zones.filter(z=>countryCode==='all'||z.countryCodes.includes(countryCode))||[],[data,countryCode]);
  const regions = useMemo(()=>['All regions',...new Set(selected.map(z=>z.region))],[selected]);
  const shown = useMemo(()=>selected.filter(z=>
    (region==='All regions'||z.region===region)&&
    (filter==='All assessments'||(filter==='Reviewed exceptions'&&z.promoted)||(filter==='Awaiting verification'&&z.status==='review')||
     (filter==='Monitored'&&z.status==='monitor')||(filter==='Coverage gaps'&&z.status==='data-gap'))&&
    (!query||[z.name,z.region,z.countryCodes.join(' '),z.reason].join(' ').toLowerCase().includes(query.toLowerCase()))
  ),[selected,region,filter,query]);
  const counts={promoted:selected.filter(z=>z.promoted).length,
    worsening:selected.filter(z=>z.promoted&&z.direction==='deteriorating').length,
    improving:selected.filter(z=>z.promoted&&z.direction==='improving').length,
    review:selected.filter(z=>z.status==='review').length,
    gaps:selected.filter(z=>z.status==='data-gap').length};
  const stale = !data || age(data.generatedAt)>2.5;
  const scope = countryCode==='all'?'Global hotspots':countryName||countryCode;

  return <section className="gc-root" aria-label="Global conflict and hotspot analyst">
    <header className="gc-header">
      <div>
        <div className="gc-kicker"><Globe2 size={15}/> DEFENSE, SECURITY & CYBER / AI CONFLICT ANALYST</div>
        <h2>Global conflict <em>watch.</em></h2>
        <p>Which hotspots are departing from their own historic norms? Where is recorded violence rising or falling, who might gain, and how could the wider world be affected?</p>
      </div>
      <button className="gc-refresh" type="button" disabled={loading} onClick={()=>setRefresh(x=>x+1)}><RefreshCw size={15}/>{loading?'Checking…':'Reload data'}</button>
    </header>

    <div className="gc-metrics">
      <div><small>WATCH AREAS</small><strong>{data?selected.length:'—'}</strong><span>{scope}</span></div>
      <div><small>REVIEWED EXCEPTIONS</small><strong>{data?counts.promoted:'—'}</strong><span>Evidence-gated analyst outputs</span></div>
      <div><small>DETERIORATING</small><strong>{data?counts.worsening:'—'}</strong><span>Reviewed historical event increase</span></div>
      <div><small>IMPROVING</small><strong>{data?counts.improving:'—'}</strong><span>Reviewed historical event decrease</span></div>
      <div><small>REVIEW QUEUE</small><strong>{data?counts.review:'—'}</strong><span>Historical outliers pending corroboration</span></div>
      <div><small>DATA GAPS</small><strong>{data?counts.gaps:'—'}</strong><span>Missing / insufficient measurement</span></div>
    </div>

    <div className="gc-sourcebar">
      <span><Clock3 size={14}/> Analyst run: {prettyDate(data?.generatedAt)}</span>
      <span><Database size={14}/> Latest dated UCDP event: {prettyDate(data?.measurement.latestCodedEvent)}</span>
      <span><BrainCircuit size={14}/> AI: {data?.analyst.modelStatus||'unavailable'}</span>
      <span><ShieldCheck size={14}/> Automatic Command alerts: 0</span>
    </div>
    {countryCode!=='all'&&<div className="gc-note"><AlertTriangle size={16}/> {scope} may appear in multinational watch areas; counts are not exclusively attributable to this country.</div>}
    {data&&(!data.measurement.eventFresh||stale||data.status!=='ok')&&
      <div className="gc-note"><AlertTriangle size={16}/> {data.status!=='ok'?'The conflict-event collector is unavailable. ':''}
        {!data.measurement.eventFresh?'The latest coded event is outside the freshness window. ':''}
        {stale?'The published snapshot is older than 60 hours. ':''}
        No current escalation is inferred from missing or lagged data.</div>}
    {error&&<div className="gc-note"><AlertTriangle size={16}/> {error}. An empty report does not mean no conflict is occurring.</div>}
    {loading&&<p className="gc-loading">Loading source-attributed conflict assessments…</p>}
    <div className="gc-legend">
      <strong>CONFIRMED EVENT COUNT ≠ REAL-TIME BATTLEFIELD STATUS</strong>
      <span>UCDP candidate coding can lag events. Public editorial RSS monitors reporting only. “Who benefits” is an analyst hypothesis, never a declared winner. Dated and linked evidence appears in each briefing.</span>
    </div>

    <div className="gc-controls">
      <label>Assessment <select value={filter} onChange={e=>setFilter(e.target.value)}>{['All assessments','Reviewed exceptions','Awaiting verification','Monitored','Coverage gaps'].map(v=><option key={v}>{v}</option>)}</select></label>
      <label>Region <select value={region} onChange={e=>setRegion(e.target.value)}>{regions.map(v=><option key={v}>{v}</option>)}</select></label>
      <label className="gc-search">Find a hotspot <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Theater, country or concern…"/></label>
      <span className="gc-count">{shown.length} areas</span>
    </div>

    <div className="gc-list">
      {shown.map(z=><article className={'gc-zone gc-'+z.status} key={z.id}>
        <button type="button" className="gc-zone-top" aria-expanded={expanded===z.id} onClick={()=>setExpanded(expanded===z.id?null:z.id)}>
          <div className="gc-zone-name"><small>{z.region} / {z.kind==='strategic-flashpoint'?'STRATEGIC FLASHPOINT':'ARMED-CONFLICT WATCH'}</small>
            <strong>{z.name}</strong><span className={'gc-status gc-state-'+z.status}>{statusLabel[z.status]}</span></div>
          <div className="gc-zone-stat"><small>RECORDED EVENTS / 28 DAYS</small><strong>{number(z.change.recent)}</strong><span>Historical median {number(z.change.median)}</span></div>
          <div className="gc-zone-direction"><small>DIRECTION</small>
            <strong className={'gc-direction-'+z.direction}>{z.direction==='deteriorating'?<TrendingUp size={18}/>:z.direction==='improving'?<TrendingDown size={18}/>:<Activity size={18}/>}
              {directionLabel[z.direction]}</strong>
            <span>{z.change.changePct===null?'Insufficient baseline':(z.change.changePct>0?'+':'')+z.change.changePct.toFixed(1)+'% against median'}</span>
          </div>
          {expanded===z.id?<ChevronDown size={20}/>:<ChevronRight size={20}/>}
        </button>
        {expanded===z.id&&<div className="gc-details">
          <div className="gc-detail-lead">
            <p><strong>Analyst judgment</strong>{z.reason}</p>
            <span>Event observation through {prettyDate(z.observationEnd)} · {z.modelReviewed?'AI reviewed':'AI review not completed'} · {z.sourceQuality}</span>
          </div>
          <div className="gc-chart-wrap">
            <div><strong>Historical volatility</strong><span>Eight prior 28-day windows vs. most recent coded window · event counts, not casualties</span></div>
            {z.change.status==='assessable'&&z.change.recent!==null?
              <div className="gc-bars" role="img" aria-label={'Historical counts '+z.change.history.join(', ')+' and recent count '+z.change.recent}>
                {[...z.change.history,z.change.recent].map((n,i)=>{
                  const top=Math.max(1,...z.change.history,z.change.recent||0);
                  return <div key={i} className="gc-bar-col"><span>{n}</span><i className={i===8?'gc-bar-current':''} style={{height:Math.max(4,Math.round(100*n/top))+'%'}}/><small>{i===8?'Latest':String(i+1)}</small></div>;
                })}
              </div>:<p className="gc-chart-empty">No statistically assessable event history. No zero is assumed.</p>}
            <small>Robust Z: {z.change.robustZ===null?'not assessed':z.change.robustZ} · minimum 8 complete baseline windows · no probability claims</small>
          </div>
          <div className="gc-impact-grid">
            <div><small>WHO MAY BENEFIT?</small><p>{z.whoBenefits}</p><span>Interpretation / hypothesis — not verified advantage</span></div>
            <div><small>RISKS TO THE WORLD</small><p>{z.globalRisks}</p><span>Scenario pathways, not confirmed downstream impacts</span></div>
            <div><small>POTENTIAL UPSIDE</small><p>{z.potentialUpside}</p><span>Conditional outcomes, not promises or predictions</span></div>
          </div>
          <div className="gc-evidence">
            <div><strong>Source trail</strong><small>UCDP coded record + editorial media discovery are different kinds of evidence</small></div>
            <div className="gc-source-links">
              {z.evidence.filter(e=>safeLink(e.url)).map(e=><a key={e.url} href={e.url} target="_blank" rel="noopener noreferrer">{e.source} · {prettyDate(e.observedAt)} <ArrowUpRight size={13}/></a>)}
              {z.media.evidence.filter(e=>safeLink(e.url)).slice(0,5).map(e=><a key={e.url} href={e.url} target="_blank" rel="noopener noreferrer">{e.publisher} · {prettyDate(e.date)} <ArrowUpRight size={13}/></a>)}
            </div>
            <p>Independent media publishers: {z.media.status==='ok'?z.media.publishers:'unavailable'} · Articles sampled: {z.media.status==='ok'?z.media.articles:'unavailable'}. News coverage does not certify violence or casualties.</p>
          </div>
        </div>}
      </article>)}
      {!loading&&data&&shown.length===0&&<div className="gc-empty">No watch area matches these filters. This is not a finding that the location is conflict-free.</div>}
    </div>
    {data&&<footer className="gc-footer">Coverage: <a href={data.sources.ucdp.url} target="_blank" rel="noopener noreferrer">UCDP event-data method <ArrowUpRight size={12}/></a> ·
      <a href={data.sources.rss?.feeds?.find(x=>x.status==='ok')?.url||data.sources.gdelt.url} target="_blank" rel="noopener noreferrer">Public editorial media feeds <ArrowUpRight size={12}/></a>.
      An exception is a screening judgment, not proof of an imminent attack or a named beneficiary. No live unit locations or tactical targeting.</footer>}
  </section>;
}
