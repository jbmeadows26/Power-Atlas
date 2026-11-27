import {useEffect,useId,useMemo,useState} from 'react';
import {Activity,ArrowUpRight,BarChart3,BookOpenCheck,ChevronDown,Clock3,ShieldCheck,TriangleAlert} from 'lucide-react';
import {api} from './lib/api';
import {buildDomainBrief, needsGlobalSystems, SNAPSHOT_PATHS, type BriefInput, type EvidenceBrief} from './lib/domainAnalysts';
import './analystEvidence.css';

type Case={code?:string;topic?:string;source?:string;title?:string};
type HookArgs={view:string;focus:string;country:string;countryName?:string;horizon?:string;severity?:string;cases:Case[]};
const keys=Object.entries(SNAPSHOT_PATHS) as Array<[string,string]>;
/** Keep original source dates intact; only the visible label is human-readable. */
const readableDate=(value:string|undefined)=>{
  const original=(value||'').trim();
  if(/^\d{4}-\d{2}$/.test(original)){
    const time=Date.parse(original+'-15T12:00:00Z');
    return Number.isFinite(time)?new Date(time).toLocaleDateString('en-US',{month:'short',year:'numeric',timeZone:'UTC'}):original;
  }
  if(/^\d{4}-\d{2}-\d{2}(?:T.*)?$/.test(original)){
    const time=Date.parse(original.length===10?original+'T12:00:00Z':original);
    return Number.isFinite(time)?new Date(time).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):original;
  }
  return original||'Date not reported';
};
const asObject=(value:unknown):Record<string,unknown>|null=>
  value&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,unknown>:null;

/** One memoized view of published snapshots feeds both desktop side rail and mobile inline analysis. */
export function useAnalystEvidence({view,focus,country,countryName,horizon,severity,cases}:HookArgs):EvidenceBrief{
  const [snapshots,setSnapshots]=useState<Record<string,unknown>>({});
  const [failures,setFailures]=useState<string[]>([]);
  const [systems,setSystems]=useState<{country:string;data:unknown}|undefined>(undefined);
  const [tick,setTick]=useState(0);
  useEffect(()=>{
    const interval=window.setInterval(()=>setTick(x=>x+1),10*60_000);
    return()=>window.clearInterval(interval);
  },[]);
  useEffect(()=>{
    let live=true;
    const controllers:AbortController[]=[];
    const load=async(key:string,path:string)=>{
      const controller=new AbortController();controllers.push(controller);
      const timer=window.setTimeout(()=>controller.abort(),12000);
      try{
        const base=String(import.meta.env.BASE_URL||'/');
        // The static Pages telemetry is only a bootstrap placeholder.
        const url=key==='resilience'?'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json':base+path;
        const response=await fetch(url,{cache:'no-store',signal:controller.signal});
        if(!response.ok)throw Error(key+' HTTP '+response.status);
        const value:unknown=await response.json();
        const record=asObject(value);
        const primary:Record<string,string>={source:'records',triage:'reviews',markets:'metrics',transmission:'householdMetrics',conflict:'zones',inventory:'assets',changes:'assessments',shortage:'forecasts',early:'metrics',resilience:'observations'};
        if(!record||typeof record.schemaVersion!=='number'||!Array.isArray(record[primary[key]]))throw Error(key+' invalid schema');
        if(!live)return;
        setSnapshots(previous=>({...previous,[key]:value}));
        setFailures(previous=>previous.filter(x=>x!==key));
      }catch{
        if(!live)return;
        // Preserve the last dated valid snapshot; downstream cards mark refresh failures.
        setFailures(previous=>previous.includes(key)?previous:[...previous,key]);
      }finally{window.clearTimeout(timer);}
    };
    // Publish successful channels independently; slow or failed feeds cannot block other cards.
    keys.forEach(([key,path])=>{void load(key,path);});
    return()=>{live=false;controllers.forEach(c=>c.abort());};
  },[tick]);
  const needsSystems=needsGlobalSystems(view,focus);
  useEffect(()=>{
    let live=true;
    setSystems(undefined);
    if(!needsSystems)return;
    // WLD is the World Bank's global aggregate; never substitute a country value.
    const queryCountry=country==='all'?'WLD':country;
    api.get('/api/global-systems/'+encodeURIComponent(queryCountry)).then(response=>{
      const value:unknown=response.data;
      if(live&&asObject(value)&&Array.isArray(asObject(value)?.indicators))setSystems({country,data:value});
    }).catch(()=>{if(live)setSystems(undefined);});
    return()=>{live=false;};
  },[country,tick,needsSystems]);
  return useMemo(()=>buildDomainBrief({view,focus,country,countryName,horizon,severity,cases,snapshots,systems:needsSystems&&systems?.country===country?systems.data:undefined,failures} as BriefInput),
    [view,focus,country,countryName,horizon,severity,cases,snapshots,systems,failures,needsSystems]);
}

function Sparkline({chart}:{chart:NonNullable<EvidenceBrief['chart']>}){
  const vals=chart.values.filter(Number.isFinite);
  if(vals.length<3)return null;
  const low=Math.min(...vals),high=Math.max(...vals),span=high-low||1;
  const points=vals.map((v,i)=>[8+i*288/(vals.length-1),69-57*(v-low)/span]);
  const polyline=points.map(([x,y])=>x.toFixed(1)+','+y.toFixed(1)).join(' ');
  const last=points.at(-1)!;
  return <div className="eai-spark" role="img" aria-label={chart.label}>
    <div><BarChart3 size={13}/>{chart.label}</div>
    <svg viewBox="0 0 304 82" preserveAspectRatio="none" aria-hidden="true">
      <line x1="7" x2="297" y1="70" y2="70" stroke="#557780" strokeWidth="1" strokeDasharray="3 4"/>
      <polyline fill="none" stroke="#d6ed93" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" points={polyline}/>
      <circle cx={last[0]} cy={last[1]} r="3.7" fill="#d6ed93"/>
    </svg>
    <span>{chart.dates[0]||'Earlier observation'} · {chart.dates.at(-1)||'Latest observation'} · source-dated, not live</span>
  </div>;
}
export default function AnalystEvidence({reading,placement='rail'}:{reading:EvidenceBrief;placement?:'rail'|'inline'|'details'}){
  const [details,setDetails]=useState(false);
  useEffect(()=>setDetails(false),[reading.title,reading.scope]);
  return <section className={'eai-readout eai-'+placement} aria-label={'Source-backed analyst interpretation: '+reading.title}>
    <div className="eai-head">
      <span className="eai-eyebrow"><BookOpenCheck size={14}/> ACTIVE CATEGORY ANALYST</span>
      <div className="eai-title">{reading.title}</div>
      <p className="eai-author">{reading.analyst} · automated, source-bounded assessment</p>
      <div className="eai-meta"><span className={'eai-state '+reading.status}>{reading.status==='coverage-gap'?'COVERAGE GAP':reading.status==='monitoring'?'MONITORED':'SOURCE-DATED'}</span><span>{reading.scope}</span></div>
    </div>
    <div className="eai-kpis">
      {reading.metrics.length?reading.metrics.slice(0,3).map(m=><div className="eai-kpi" key={m.label}>
        <strong>{m.value}</strong><span>{m.label}</span>{m.detail&&<small>{m.detail}</small>}
      </div>):<div className="eai-unavailable"><TriangleAlert size={15}/> No source-verified metrics in this scope</div>}
    </div>
    {reading.chart&&<Sparkline chart={reading.chart}/>}
    <div className="eai-finding">
      <span><Activity size={13}/> EVIDENCE SUMMARY</span>
      <p>{reading.finding}</p>
    </div>
    <div className="eai-interpretation">
      <strong>Beyond the norm? Improving or deteriorating?</strong>
      <p>{reading.direction}</p>
    </div>
    <div className="eai-interpretation">
      <strong>Why it matters</strong>
      <p>{reading.implication}</p>
    </div>
    <button type="button" className="eai-detail-toggle" aria-expanded={details} onClick={()=>setDetails(v=>!v)}>
      <ShieldCheck size={13}/>{details?'Hide deep assessment':'Beneficiaries, next evidence & limitations'} <span aria-hidden="true">{details?'−':'+'}</span>
    </button>
    {details&&<div className="eai-expanded">
      <strong>Who benefits?</strong><p>{reading.beneficiaries}</p>
      <strong>What to watch</strong><p>{reading.watch}</p>
      <strong>Evidence limit</strong><p>{reading.limitation}</p>
    </div>}
    <div className="eai-sources">
      <div><strong>ORIGINAL EVIDENCE</strong><span title={reading.asOf}><Clock3 size={12}/> {readableDate(reading.asOf)}</span></div>
      {reading.sources.length?reading.sources.slice(0,4).map(link=><a key={link.url} href={link.url} target="_blank" rel="noopener noreferrer" title={'Open '+link.title+(link.date?' · '+link.date:'')}>
        <span className="eai-source-label">{link.title}{link.date&&<small title={link.date}>{readableDate(link.date)}</small>}</span>
        <ArrowUpRight size={13}/>
      </a>):<p>No original records available in this scope. Do not interpret missing as zero.</p>}
      <small>{reading.coverage}</small>
    </div>
  </section>;
}

/**
 * Mobile-first progressive disclosure: do not bury monitoring charts or
 * duplicate the Command Room's visible signal counters. The original sourced
 * analysis is preserved in full on demand, and the desktop rail is unchanged.
 */
export function AnalystEvidenceCompact({reading}:{reading:EvidenceBrief}){
  const [open,setOpen]=useState(false);
  const detailsId=useId();
  useEffect(()=>setOpen(false),[reading.title,reading.scope]);
  return <section className="eai-inline eai-compact" aria-label={'Analyst interpretation: '+reading.title}>
    <button type="button" className="eai-compact-trigger" aria-expanded={open} aria-controls={detailsId}
      onClick={()=>setOpen(previous=>!previous)}>
      <span className="eai-compact-identity"><BookOpenCheck size={16}/><span><small>ANALYST INTERPRETATION</small><strong>{reading.title}</strong></span></span>
      <span className={'eai-state '+reading.status}>{reading.status==='coverage-gap'?'DATA GAP':reading.status==='monitoring'?'MONITORING':'DATED'}</span>
      <ChevronDown className={open?'eai-compact-chevron open':'eai-compact-chevron'} size={18}/>
    </button>
    {!open&&<div className="eai-compact-action">
      <div className="eai-compact-metrics">{reading.metrics.slice(0,2).map(m=><div className="eai-compact-metric" key={m.label}><strong>{m.value}</strong><span>{m.label}</span></div>)}</div>
      <p className="eai-compact-preview">{reading.status==='coverage-gap'?'Evidence coverage is incomplete.':reading.status==='monitoring'?'Monitoring; abnormal change not necessarily confirmed.':'Source-dated evidence; open for assessment.'}</p>
    </div>}
    <div id={detailsId} className="eai-compact-body" hidden={!open}>
      {open&&<AnalystEvidence reading={reading} placement="details"/>}
    </div>
  </section>;
}
