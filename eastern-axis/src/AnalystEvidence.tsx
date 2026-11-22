import {useEffect,useMemo,useState} from 'react';
import {Activity,ArrowUpRight,BarChart3,BookOpenCheck,Clock3,ShieldCheck,TriangleAlert} from 'lucide-react';
import {api} from './lib/api';
import {buildDomainBrief, SNAPSHOT_PATHS, type BriefInput, type EvidenceBrief} from './lib/domainAnalysts';
import './analystEvidence.css';

type Case={code?:string;topic?:string;source?:string;title?:string};
type HookArgs={view:string;focus:string;country:string;countryName?:string;cases:Case[]};
const keys=Object.entries(SNAPSHOT_PATHS) as Array<[string,string]>;
const asObject=(value:unknown):Record<string,unknown>|null=>
  value&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,unknown>:null;

/** One memoized view of published snapshots feeds both desktop side rail and mobile inline analysis. */
export function useAnalystEvidence({view,focus,country,countryName,cases}:HookArgs):EvidenceBrief{
  const [snapshots,setSnapshots]=useState<Record<string,unknown>>({});
  const [failures,setFailures]=useState<string[]>([]);
  const [systems,setSystems]=useState<unknown>(undefined);
  const [tick,setTick]=useState(0);
  useEffect(()=>{
    const interval=window.setInterval(()=>setTick(x=>x+1),10*60_000);
    return()=>window.clearInterval(interval);
  },[]);
  useEffect(()=>{
    let live=true;
    Promise.allSettled(keys.map(async ([key,path])=>{
      const response=await fetch(String(import.meta.env.BASE_URL||'/')+path,{cache:'no-store'});
      if(!response.ok)throw Error(key+' HTTP '+response.status);
      const value:unknown=await response.json();
      if(!asObject(value)||typeof asObject(value)?.schemaVersion!=='number')throw Error(key+' invalid schema');
      return [key,value] as const;
    })).then(results=>{
      if(!live)return;
      const available:Record<string,unknown>={},missing:string[]=[];
      for(let i=0;i<results.length;i++){
        const result=results[i];
        if(result.status==='fulfilled')available[result.value[0]]=result.value[1];
        else missing.push(keys[i][0]);
      }
      setSnapshots(available);setFailures(missing);
    });
    return()=>{live=false;};
  },[tick]);
  useEffect(()=>{
    let live=true;
    setSystems(undefined);
    // WLD is the World Bank's global aggregate; never substitute a country value.
    const queryCountry=country==='all'?'WLD':country;
    api.get('/api/global-systems/'+encodeURIComponent(queryCountry)).then(response=>{
      const value:unknown=response.data;
      if(live&&asObject(value)&&Array.isArray(asObject(value)?.indicators))setSystems(value);
    }).catch(()=>{if(live)setSystems(undefined);});
    return()=>{live=false;};
  },[country,tick]);
  return useMemo(()=>buildDomainBrief({view,focus,country,countryName,cases,snapshots,systems,failures} as BriefInput),
    [view,focus,country,countryName,cases,snapshots,systems,failures]);
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
export default function AnalystEvidence({reading,placement='rail'}:{reading:EvidenceBrief;placement?:'rail'|'inline'}){
  const [details,setDetails]=useState(false);
  useEffect(()=>setDetails(false),[reading.title,reading.scope]);
  return <section className={'eai-readout eai-'+placement} aria-label={'Source-backed analyst interpretation: '+reading.title}>
    <div className="eai-head">
      <span className="eai-eyebrow"><BookOpenCheck size={14}/> ACTIVE CATEGORY ANALYST</span>
      <div className="eai-title">{reading.title}</div>
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
      <div><strong>ORIGINAL EVIDENCE</strong><span><Clock3 size={12}/> {reading.asOf}</span></div>
      {reading.sources.length?reading.sources.slice(0,4).map(link=><a key={link.url} href={link.url} target="_blank" rel="noopener noreferrer" title={'Open '+link.title}>
        {link.title}<ArrowUpRight size={12}/>{link.date&&<small>{link.date}</small>}
      </a>):<p>No original records available in this scope. Do not interpret missing as zero.</p>}
      <small>{reading.coverage}</small>
    </div>
  </section>;
}
