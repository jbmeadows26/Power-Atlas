import {useEffect,useMemo,useState} from 'react';
import {Activity,ArrowRight,ArrowUpRight,BrainCircuit,Database,Eye,Radio,ShieldAlert,ShieldCheck,TriangleAlert} from 'lucide-react';
import './signalReviewBoard.css';

type Baseline={status:string;sampleSize:number;robustZ:number|null;medianChange?:number};
type Review={
  id:string;kind:string;title:string;group:string;source:string;sourceUrl:string;
  observedAt?:string;screened:boolean;fresh:boolean;anomalous:boolean;needsReview:boolean;
  baseline:Baseline;status:string;reason:string;confidence:string;modelReviewed:boolean;
  evidence:string[];officialAlert?:boolean;severity?:string;changePct?:number;
};
type Triage={schemaVersion:number;generatedAt:string;sourceCheckedAt:string;
  model:{status:string;name:string|null;role:string};policy:string;
  summary:{observed:number;screened:number;reviewed:number;monitoring:number;elevated:number;historyReady:number};
  reviews:Review[];alerts:unknown[]};
type Lane='signals'|'queue'|'weather'|'sources'|'all';
function valid(v:unknown):v is Triage {
  if(!v||typeof v!=='object')return false;
  const t=v as Partial<Triage>;
  return t.schemaVersion===1&&typeof t.generatedAt==='string'&&Array.isArray(t.reviews)&&
    t.reviews.every(r=>r&&typeof r.id==='string'&&typeof r.title==='string'&&typeof r.reason==='string'&&
      typeof r.group==='string'&&typeof r.sourceUrl==='string'&&r.sourceUrl.startsWith('https://')&&
      typeof r.status==='string'&&typeof r.modelReviewed==='boolean')&&
    !!t.summary&&Number.isFinite(t.summary.observed)&&!!t.model&&typeof t.model.status==='string';
}
function scopeMatch(group:string,code:string) {
  if(code==='all'||group==='global'||group===code)return true;
  const proximity:Record<string,string[]>={
    CN:['regional:taiwan-strait','regional:east-asia'],TW:['regional:taiwan-strait','regional:east-asia'],
    JP:['regional:east-asia'],KR:['regional:east-asia'],
    IR:['regional:persian-gulf','regional:strait-of-hormuz'],
    OM:['regional:persian-gulf','regional:strait-of-hormuz'],AE:['regional:persian-gulf','regional:strait-of-hormuz'],
    EE:['regional:baltic-sea'],LV:['regional:baltic-sea'],LT:['regional:baltic-sea'],
    FI:['regional:baltic-sea'],SE:['regional:baltic-sea'],PL:['regional:baltic-sea'],
    EG:['regional:eastern-mediterranean'],IL:['regional:eastern-mediterranean'],TR:['regional:eastern-mediterranean']
  };
  return (proximity[code]||[]).includes(group);
}
const stamp=(d:string)=>{const time=Date.parse(d);return Number.isFinite(time)?new Date(time).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Unverified date';};
const sourceScope=(s:string)=>s==='global'?'WORLDWIDE CONTEXT':s.startsWith('regional:')?'REGIONAL CONTEXT':s;
const weather=(r:Review)=>r.kind==='advisory'&&/National Weather Service/i.test(r.source);
const cyber=(r:Review)=>/CISA|cybersecurity/i.test(r.source);
const magnitude=(r:Review)=>Math.abs(typeof r.baseline?.robustZ==='number'?r.baseline.robustZ:0);
export default function SignalReviewBoard({mode,countryCode,onOpenEarly}:{
  mode:'early'|'command';countryCode:string;onOpenEarly?:()=>void
}){
  const [snapshot,setSnapshot]=useState<Triage|null>(null);
  const [error,setError]=useState<string|null>(null);
  const [refresh,setRefresh]=useState(0);
  const [filter,setFilter]=useState<Lane>('signals');
  useEffect(()=>{const timer=window.setInterval(()=>setRefresh(v=>v+1),5*60*1000);return()=>window.clearInterval(timer);},[]);
  useEffect(()=>{
    let alive=true;
    fetch(String(import.meta.env.BASE_URL||'/')+'analysis/early-warning-triage.json',{cache:'no-store'})
      .then(async r=>{if(!r.ok)throw Error('Analyst review has not been published');const value=await r.json();if(!valid(value))throw Error('Analyst report schema not verified');return value;})
      .then(value=>{if(alive){setSnapshot(value);setError(null);}})
      .catch((e:unknown)=>{if(alive){setSnapshot(null);setError(e instanceof Error?e.message:'Review report unavailable');}});
    return()=>{alive=false};
  },[refresh]);
  const age=snapshot?Date.now()-Date.parse(snapshot.generatedAt):NaN;
  const stale=snapshot!==null&&(!Number.isFinite(age)||age<0||age>72*3600000);
  const reviews=useMemo(()=>(snapshot?.reviews||[]).filter(r=>scopeMatch(r.group,countryCode)),[snapshot,countryCode]);
  const elevated=reviews.filter(r=>r.status==='elevated'&&!stale);
  const screened=reviews.filter(r=>r.screened);
  const pending=screened.filter(r=>r.needsReview&&!r.modelReviewed);
  const countReviewed=screened.filter(r=>r.modelReviewed).length;
  const metrics=reviews.filter(r=>r.kind==='metric');
  const advisories=reviews.filter(weather);
  const leads=reviews.filter(r=>r.kind!=='metric'&&!weather(r));
  const local=reviews.filter(r=>countryCode==='all'?r.group!=='global':r.group===countryCode).length;
  const worldwide=reviews.filter(r=>r.group==='global').length;
  const selected=filter==='signals'?metrics:filter==='queue'?pending:filter==='weather'?advisories:filter==='sources'?leads:reviews;
  const rows=(mode==='command'?elevated:selected).slice().sort((a,b)=>{
    if(filter==='signals'&&mode==='early')return Number(b.group===countryCode)-Number(a.group===countryCode)||
      Number(b.screened)-Number(a.screened)||magnitude(b)-magnitude(a)||Math.abs(b.changePct||0)-Math.abs(a.changePct||0);
    return Number(b.status==='elevated')-Number(a.status==='elevated')||
      Number(b.needsReview&&!b.modelReviewed)-Number(a.needsReview&&!a.modelReviewed)||
      String(b.observedAt).localeCompare(String(a.observedAt));
  });
  const displayRows=mode==='early'&&filter==='signals'?rows.slice(0,8):rows;
  const mixes=[{label:'Markets & GNSS',count:metrics.length},
    {label:'Weather advisories',count:advisories.length},
    {label:'Cyber advisories',count:leads.filter(cyber).length},
    {label:'Other source leads',count:leads.filter(r=>!cyber(r)).length}];
  const largest=Math.max(1,...mixes.map(m=>m.count));
  return <section className={'sr-root sr-'+mode} aria-label={mode==='command'?'Evidence-gated command alerts':'AI analyst signal review'}>
    <header className="sr-head">
      <div><span className="sr-kicker"><BrainCircuit size={15}/> {mode==='command'?'COMMAND / VERIFIED FINDINGS':'EARLY WARNING / SOURCE-BASED MONITORING'}</span>
        <h2>{mode==='command'?'Intelligence pulse':'Signals and source movements'}</h2>
        <p>{mode==='command'?'Only independently evidence-gated findings are promoted. Other observations remain in Early Warning.':
          'Measured changes come first. Official weather advisories and raw collection leads have separate views.'}</p>
      </div><button type="button" onClick={()=>setRefresh(v=>v+1)} aria-label="Reload analyst snapshot"><Activity size={14}/> Refresh</button>
    </header>
    {!snapshot&&<div className="sr-status sr-unavailable"><TriangleAlert size={17}/> {error||'Loading analyst review…'} · No automatic escalation is claimed.</div>}
    {snapshot&&<>
      <div className="sr-stats">
        <div><small>{mode==='command'?'EVIDENCE-GATED':'MONITORED SIGNALS'}</small><strong>{mode==='command'?elevated.length:metrics.length}</strong><span>{mode==='command'?'Confirmed alerts':'Measured series · market / GNSS'}</span></div>
        <div><small>{mode==='command'?'REVIEW CANDIDATES':'REVIEW CANDIDATES'}</small><strong>{screened.length}</strong><span>Require closer examination</span></div>
        <div><small>AWAITING AI</small><strong>{pending.length}</strong><span>{countReviewed}/{screened.length} candidates reviewed</span></div>
        <div><small>{countryCode==='all'?'NON-GLOBAL':'COUNTRY-MATCHED'}</small><strong>{local}</strong><span>{worldwide} worldwide context records</span></div>
      </div>
      <div className="sr-coverage" aria-label="Observation counts by source category, not threat severity">
        <span className="sr-coverage-label">SOURCE COVERAGE · {reviews.length} VISIBLE RECORDS</span>
        <div className="sr-coverage-bars">{mixes.map(m=><div className="sr-cover-row" key={m.label}>
          <span>{m.label}</span><div className="sr-cover-track"><i style={{width:(100*m.count/largest)+'%'}}/></div><b>{m.count}</b>
        </div>)}</div>
      </div>
      <div className={'sr-status sr-slim '+(stale?'sr-unavailable':'')}>
        {stale?<TriangleAlert size={16}/>:<ShieldCheck size={16}/>}
        <span>{stale?'Report out of date; prior elevations are suppressed.':
          pending.length>0?countReviewed+' of '+screened.length+' candidates AI-reviewed; '+pending.length+' remain pending and unpromoted.':
          snapshot.model.status==='unavailable'?'AI unavailable; automated screens still run, with no unsupported promotions.':
          'Latest review complete for visible candidates; elevation still requires independent evidence.'}
          <small>Sources {stamp(snapshot.sourceCheckedAt)} · Reviewed {stamp(snapshot.generatedAt)} · Worldwide context is not country attribution</small></span>
      </div>
      {mode==='early'&&<div className="sr-tabs" aria-label="Analyst record views">
        {([['signals','Market & GNSS'],['queue','Unreviewed'],['weather','Weather alerts'],['sources','Source leads'],['all','All records']] as const).map(([key,label])=>
          <button key={key} type="button" className={filter===key?'active':''} aria-pressed={filter===key} onClick={()=>setFilter(key)}>
            {label}{key==='queue'?' ('+pending.length+')':key==='weather'?' ('+advisories.length+')':''}
          </button>)}
      </div>}
      {mode==='command'&&elevated.length===0&&<div className="sr-empty sr-compact-empty">
        <ShieldCheck size={21}/><div><strong>0 findings passed the evidence gate</strong><p>This is not a zero-risk assessment. {pending.length>0?pending.length+' reviews are incomplete. ':''}See measured movements and original advisories in Early Warning.</p></div>
        {onOpenEarly&&<button type="button" onClick={onOpenEarly}>Inspect signals <ArrowRight size={14}/></button>}
      </div>}
      {mode==='early'&&<div className="sr-list-caption">
        <strong>{filter==='signals'?'Largest measured movements':filter==='queue'?'Unreviewed candidates':filter==='weather'?'Official weather advisories':filter==='sources'?'New source records':'All monitored records'}</strong>
        <span>{filter==='signals'?'Showing up to 8 measured changes · not verified threats':displayRows.length+' records · original source links in each detail'}</span>
      </div>}
      {mode==='early'&&displayRows.length===0&&<div className="sr-empty"><Radio size={22}/><div><strong>No records in this view</strong><p>Other monitoring views and original source readings remain accessible.</p></div></div>}
      <div className="sr-rows">{displayRows.map(r=><details key={r.id} className={'sr-item '+(r.status==='elevated'?'sr-elevated':'')}>
        <summary><span className="sr-icon">{r.status==='elevated'?<ShieldAlert size={17}/>:r.needsReview?<Eye size={17}/>:<Database size={17}/>}</span>
          <span className="sr-main"><strong>{r.title}</strong><small>{sourceScope(r.group)} · {r.source} · {stamp(r.observedAt||'')}</small></span>
          {r.kind==='metric'&&typeof r.changePct==='number'?<span className="sr-delta">{r.changePct>0?'+':''}{r.changePct.toFixed(1)}%</span>:
          <span className={'sr-pill '+(r.status==='elevated'?'sr-hot':r.modelReviewed?'sr-reviewed':r.needsReview?'sr-review':'')}>{r.status==='elevated'?'ELEVATED':r.modelReviewed?'REVIEWED':r.needsReview?'PENDING':'SOURCE'}</span>}
        </summary>
        <div className="sr-detail">
          <p>{r.reason}</p>
          <div className="sr-metadata">
            <span><b>Review:</b> {r.modelReviewed?'AI reviewed':r.needsReview?'Pending AI':'Automated screen'}</span>
            <span><b>Confidence:</b> {r.confidence}</span>
            <span><b>Baseline:</b> {r.baseline?.status||'not available'}{typeof r.baseline?.robustZ==='number'?' · robust z '+r.baseline.robustZ:''}</span>
            <span><b>History:</b> {r.baseline?.sampleSize||0} intervals</span>
            <span><b>Freshness:</b> {r.fresh?'within source window':'historical or stale'}</span>
            <span><b>Scope:</b> {sourceScope(r.group)}</span>
          </div>
          <a href={r.sourceUrl} rel="noopener noreferrer" target="_blank">Open original evidence <ArrowUpRight size={14}/></a>
          <small>Geographic association alone does not imply cause, responsibility or impact.</small>
        </div>
      </details>)}</div>
      {mode==='early'&&filter==='signals'&&rows.length>displayRows.length&&<button className="sr-show-all" type="button" onClick={()=>setFilter('all')}>Explore all {reviews.length} source records <ArrowRight size={14}/></button>}
      {mode==='early'&&<p className="sr-footnote">Bars represent source counts, not risk probabilities. Review prompts are not calibrated threat forecasts. AI decisions cannot override evidence, expiry, corroboration or publisher attribution checks.</p>}
    </>}
  </section>;
}
