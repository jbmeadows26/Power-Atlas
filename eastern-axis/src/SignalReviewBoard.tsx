import {useEffect,useMemo,useState} from 'react';
import {Activity,ArrowRight,ArrowUpRight,BrainCircuit,Database,Eye,Radio,ShieldAlert,ShieldCheck,TriangleAlert} from 'lucide-react';
import './signalReviewBoard.css';

type Baseline={status:string;sampleSize:number;robustZ:number|null;medianChange?:number};
type Review={
  id:string;kind:string;title:string;group:string;source:string;sourceUrl:string;
  observedAt?:string;screened:boolean;fresh:boolean;anomalous:boolean;needsReview:boolean;
  baseline:Baseline;status:string;reason:string;confidence:string;modelReviewed:boolean;
  evidence:string[];officialAlert?:boolean;severity?:string;
};
type Triage={schemaVersion:number;generatedAt:string;sourceCheckedAt:string;
  model:{status:string;name:string|null;role:string};policy:string;
  summary:{observed:number;screened:number;reviewed:number;monitoring:number;elevated:number;historyReady:number};
  reviews:Review[];alerts:unknown[]};
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
  if(code==='all')return true;
  if(group==='global')return true; // Explicit worldwide context, never country attribution.
  if(group===code)return true;
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
const sourceScope=(s:string)=>s==='global'?'WORLDWIDE SOURCE':s.startsWith('regional:')?'REGIONAL CONTEXT':s;
export default function SignalReviewBoard({mode,countryCode,onOpenEarly}:{
  mode:'early'|'command';countryCode:string;onOpenEarly?:()=>void
}){
  const [snapshot,setSnapshot]=useState<Triage|null>(null);
  const [error,setError]=useState<string|null>(null);
  const [refresh,setRefresh]=useState(0);
  const [filter,setFilter]=useState<'all'|'screened'|'events'>('screened');
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
  const countReviewed=reviews.filter(r=>r.modelReviewed).length;
  const rows=mode==='command'?elevated:
    (filter==='screened'?screened:filter==='events'?reviews.filter(r=>r.kind!=='metric'):reviews)
      .slice().sort((a,b)=>Number(b.status==='elevated')-Number(a.status==='elevated')||Number(b.needsReview)-Number(a.needsReview)||String(b.observedAt).localeCompare(String(a.observedAt)));
  return <section className={'sr-root sr-'+mode} aria-label={mode==='command'?'Evidence-gated command alerts':'AI analyst signal review'}>
    <header className="sr-head">
      <div><span className="sr-kicker"><BrainCircuit size={15}/> {mode==='command'?'COMMAND CENTER / ANALYST-VALIDATED':'AUTOMATED TRIAGE / EARLY WARNING'}</span>
        <h2>{mode==='command'?'Elevated intelligence findings':'Analyst review center'}</h2>
        <p>{mode==='command'?'Only evidence-gated findings appear here. Movement screens remain in Early Warning.':
          'Every published measurement is screened. The local AI analyst examines review candidates; unsupported elevations are withheld.'}</p>
      </div><button type="button" onClick={()=>setRefresh(v=>v+1)} aria-label="Reload analyst snapshot"><Activity size={14}/> Refresh</button>
    </header>
    {!snapshot&&<div className="sr-status sr-unavailable"><TriangleAlert size={17}/> {error||'Loading analyst review…'} · No automatic escalation is claimed. Existing measured readings remain available.</div>}
    {snapshot&&<>
      <div className="sr-stats">
        {mode==='early'?<>
          <div><small>IN SCOPE</small><strong>{reviews.length}</strong><span>Source-linked observations</span></div>
          <div><small>REVIEW SCREENS</small><strong>{screened.length}</strong><span>Candidate abnormalities</span></div>
          <div><small>AI REVIEWED</small><strong>{countReviewed}</strong><span>Model: {snapshot.model.status}</span></div>
          <div><small>ELEVATED</small><strong>{elevated.length}</strong><span>Sent to Command</span></div>
        </>:<>
          <div><small>CONFIRMED ELEVATIONS</small><strong>{elevated.length}</strong><span>Evidence-gated</span></div>
          <div><small>MONITORED ELSEWHERE</small><strong>{reviews.length-elevated.length}</strong><span>Early Warning lane</span></div>
          <div><small>ANALYST STATUS</small><strong className="sr-word">{snapshot.model.status==='available'?'ONLINE':snapshot.model.status==='partial'?'PARTIAL':snapshot.model.status==='not-needed'?'NO QUEUE':'UNAVAILABLE'}</strong><span>{countReviewed} model-reviewed records</span></div>
          <div><small>REVIEW DATE</small><strong className="sr-word">{stamp(snapshot.generatedAt)}</strong><span>Published snapshot</span></div>
        </>}
      </div>
      <div className={'sr-status '+(stale?'sr-unavailable':'')}>
        {stale?<TriangleAlert size={17}/>:<ShieldCheck size={17}/>}
        <span>{stale?'The analyst report is stale. Historical elevations are suppressed from current Command alerts.':
          snapshot.model.status==='unavailable'?'AI reasoning unavailable; automated screening continues without promoting unsupported findings.':
          snapshot.model.status==='not-needed'?'No fresh candidates require an AI model call in this snapshot.':
          snapshot.model.status==='partial'?'Some records received valid AI review; other candidates remain monitored and unreviewed.':
          'The constrained AI analyst ran on review candidates. Its proposed elevations remain subject to source-evidence gates.'}
          <small> Source collection: {stamp(snapshot.sourceCheckedAt)} · Triage: {stamp(snapshot.generatedAt)}</small></span>
      </div>
      {mode==='early'?<div className="sr-tabs" aria-label="Analyst record views">
        {([['screened','Needs analysis'],['all','All monitored'],['events','New source leads']] as const).map(([key,label])=>
          <button key={key} type="button" className={filter===key?'active':''} aria-pressed={filter===key} onClick={()=>setFilter(key)}>{label}</button>)}
      </div>:null}
      {mode==='command'&&elevated.length===0?<div className="sr-empty"><ShieldCheck size={23}/><div><strong>No substantiated elevated findings in this snapshot</strong><p>{stale?'The latest triage is out of date.':'The absence of a promoted finding does not prove there are no risks; monitoring and incomplete evidence stay in Early Warning.'}</p></div>{onOpenEarly&&<button type="button" onClick={onOpenEarly}>Open Early Warning <ArrowRight size={14}/></button>}</div>:null}
      {rows.length===0&&mode==='early'&&<div className="sr-empty"><Radio size={22}/><div><strong>No records match this analyst lane</strong><p>Change the filter to view all monitored observations and original sources.</p></div></div>}
      <div className="sr-rows">{rows.map(r=><details key={r.id} className={'sr-item '+(r.status==='elevated'?'sr-elevated':'')}>
        <summary><span className="sr-icon">{r.status==='elevated'?<ShieldAlert size={17}/>:r.needsReview?<Eye size={17}/>:<Database size={17}/>}</span>
          <span className="sr-main"><strong>{r.title}</strong><small>{sourceScope(r.group)} · {r.source} · {stamp(r.observedAt||'')}</small></span>
          <span className={'sr-pill '+(r.status==='elevated'?'sr-hot':r.modelReviewed?'sr-reviewed':r.needsReview?'sr-review':'')}>{r.status==='elevated'?'ELEVATED':r.modelReviewed?'MONITORED · AI':r.needsReview?'AWAITING AI':'MONITORED'}</span>
        </summary>
        <div className="sr-detail">
          <p>{r.reason}</p>
          <div className="sr-metadata">
            <span><b>Analyst:</b> {r.modelReviewed?'AI reviewed':'Automated screening'}</span>
            <span><b>Confidence:</b> {r.confidence}</span>
            <span><b>Baseline:</b> {r.baseline?.status||'not available'}{typeof r.baseline?.robustZ==='number'?' · robust z '+r.baseline.robustZ:''}</span>
            <span><b>History:</b> {r.baseline?.sampleSize||0} comparison intervals</span>
            <span><b>Freshness:</b> {r.fresh?'within source window':'historical or stale'}</span>
            <span><b>Scope:</b> {sourceScope(r.group)}</span>
          </div>
          <a href={r.sourceUrl} rel="noopener noreferrer" target="_blank">Open original evidence <ArrowUpRight size={14}/></a>
          <small>Country and regional context does not establish responsibility or impact; this is not a prediction.</small>
        </div>
      </details>)}</div>
      {mode==='early'&&rows.length>0&&<p className="sr-footnote">Review thresholds are screening prompts, not calibrated threat probabilities. Model recommendations cannot override missing historical comparisons, publisher attribution or official-advisory verification. New feed leads never become command alerts solely because they were collected.</p>}
    </>}
  </section>;
}
