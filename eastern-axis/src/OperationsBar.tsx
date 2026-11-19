import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { Activity, ArrowUpRight, Database, Globe2, Radio, RefreshCcw, ShieldAlert } from 'lucide-react';
import './operations-bar.css';

type Country = { code: string; name: string; region: string; relationship?: string; isTreatyAlly?: boolean };
type CaseFile = { code: string; id: string; date: string };
type SourceHealth = { status?: 'ok' | 'error'; lastAttemptAt?: string; lastSuccessAt?: string };
type Intel = {
  sources?: Array<{ id: string; name: string; health: SourceHealth | null }>;
  records?: Array<{ id: string }>;
  ofac?: { checkedAt?: string; records: number } | null;
};
type Signals = { checkedAt?: string; generatedAt?: string; events?: Array<{ id: string }>; naturalEvents?: Array<{ id: string }> };
type Metric = { value: number; year: string; source: string };
type Brief = { metrics?: Record<string,Metric>; updatedAt?: string };
type Props = {
  countryCode: string;
  countries: Country[];
  cases: CaseFile[];
  sourceDirectoryCount: number;
  onNavigate: (target: 'Overview' | 'Countries' | 'Collection desk' | 'Risk watch') => void;
};
const format = (value: number) => new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1}).format(value);
const validTime = (value?: string) => value && Number.isFinite(Date.parse(value)) ? Date.parse(value) : null;
function age(value: string | undefined, now: number) {
  const date = validTime(value);
  if (date === null) return 'Timestamp unavailable';
  const hours = (now - date) / 3600000;
  if (hours < -1) return 'Time mismatch';
  if (hours < 1) return 'Updated within 1h';
  if (hours < 24) return Math.floor(hours) + 'h since update';
  return Math.floor(hours / 24) + 'd since update';
}
export default function OperationsBar({countryCode,countries,cases,sourceDirectoryCount,onNavigate}:Props){
  const [intel,setIntel]=useState<Intel|null>(null);
  const [signals,setSignals]=useState<Signals|null>(null);
  const [brief,setBrief]=useState<Brief|null>(null);
  const [intelError,setIntelError]=useState(false);
  const [signalError,setSignalError]=useState(false);
  const [now,setNow]=useState(()=>Date.now());
  const [refreshId,setRefreshId]=useState(0);
  useEffect(()=>{
    const clock=window.setInterval(()=>setNow(Date.now()),60000);
    const check=window.setInterval(()=>setRefreshId(v=>v+1),5*60*1000);
    return()=>{window.clearInterval(clock);window.clearInterval(check);};
  },[]);
  useEffect(()=>{
    let active=true;
    api.get('/api/intelligence').then(result=>{if(active){setIntel(result.data as Intel);setIntelError(false);}})
      .catch(()=>{if(active){setIntel(null);setIntelError(true);}});
    api.get('/api/world-signals').then(result=>{if(active){setSignals(result.data as Signals);setSignalError(false);}})
      .catch(()=>{if(active){setSignals(null);setSignalError(true);}});
    return()=>{active=false;};
  },[refreshId]);
  useEffect(()=>{
    if(countryCode==='all'){setBrief(null);return;}
    let active=true;
    setBrief(null);
    api.get('/api/brief/'+encodeURIComponent(countryCode))
      .then(result=>{if(active)setBrief(result.data as Brief);})
      .catch(()=>{if(active)setBrief(null);});
    return()=>{active=false;};
  },[countryCode,refreshId]);
  const country = countries.find(item=>item.code===countryCode);
  const checked=useMemo(()=>(intel?.sources||[]).filter(feed=>feed.health?.status==='ok'),[intel]);
  const failed=useMemo(()=>(intel?.sources||[]).filter(feed=>feed.health?.status==='error'),[intel]);
  const notChecked=useMemo(()=>(intel?.sources||[]).filter(feed=>!feed.health?.status),[intel]);
  const stale=useMemo(()=>(intel?.sources||[]).filter(feed=>feed.health?.status==='ok'
    && (!validTime(feed.health?.lastSuccessAt)||now-(validTime(feed.health?.lastSuccessAt)||0)>48*3600000)),[intel,now]);
  const latest=(intel?.sources||[]).map(feed=>feed.health?.lastSuccessAt).filter((v):v is string=>!!validTime(v)).sort().reverse()[0];
  const sourceNeedsReview=failed.length+notChecked.length+stale.length;
  const focusedCases=cases.filter(c=>countryCode==='all'||c.code===countryCode).length;
  const hazardCount=signals ? (signals.events?.length||0)+(signals.naturalEvents?.length||0) : null;
  const focusMetric=countryCode==='all'?null:brief?.metrics?.gdp;
  const metrics=[
    {label:'CURATED CASE FILES',value:format(focusedCases),note:countryCode==='all'?'Indexed worldwide':'Explicitly tagged '+countryCode,kind:'neutral',action:'Countries' as const},
    {label:'INTAKE SAMPLE',value:intel && Array.isArray(intel.records)?format(intel.records.length):'—',note:intelError?'Source unavailable':'Global sample · not country attributed',kind:intelError?'error':'neutral',action:'Collection desk' as const},
    {label:'OFAC GLOBAL ENTRIES',value:intel?.ofac?format(intel.ofac.records):'—',note:intel?.ofac?'Global SDN snapshot':'Not verified',kind:'neutral',action:'Collection desk' as const},
    {label:'SOURCE HEALTH',value:intel ? checked.length+' / '+(intel.sources?.length||0) :'—',note:intelError?'Unable to check':sourceNeedsReview?'Review '+sourceNeedsReview+' failed/stale/unverified':'No reported problems in monitored feeds',kind:(sourceNeedsReview||intelError)?'error':'neutral',action:'Collection desk' as const},
    {label:'GLOBAL HAZARDS',value:hazardCount===null?'—':format(hazardCount),note:signalError?'Signal feed unavailable':'Sampled USGS + NASA · no country attribution',kind:signalError?'error':'neutral',action:'Risk watch' as const},
    {label:countryCode==='all'?'SOURCE DIRECTORY':'GDP · REPORTED',value:countryCode==='all'?format(sourceDirectoryCount):focusMetric&&Number.isFinite(focusMetric.value)?'$'+format(focusMetric.value):'—',note:countryCode==='all'?'Catalog entries · not ingested evidence':focusMetric?'World Bank · '+focusMetric.year:'No verified observation',kind:'neutral',action:countryCode==='all'?'Collection desk' as const:'Countries' as const},
  ];
  return <section className="ea-ops" aria-label="Persistent global intelligence data bar">
    <div className="ea-ops-identity">
      <div className="ea-ops-eyebrow"><Radio size={13}/> ACTIVE MONITORING CONTEXT <span className="ea-ops-pulse"/></div>
      <div className="ea-ops-country"><Globe2 size={21}/><strong>{country?.name || 'Worldwide'}</strong><button type="button" onClick={()=>onNavigate('Countries')} title="Open country records"><ArrowUpRight size={15}/></button></div>
      <div className="ea-ops-description">{country ? country.region+' · '+countryCode+' · '+(country.isTreatyAlly?'Treaty ally':'Relationship requires evidence review') : 'Global public-source coverage'}</div>
      <div className="ea-ops-freshness"><Database size={12}/>{intelError?'INTAKE OFFLINE':'INTAKE '+age(latest,now).toUpperCase()} <button type="button" onClick={()=>setRefreshId(v=>v+1)} aria-label="Refresh global statistics"><RefreshCcw size={13}/></button></div>
    </div>
    <div className="ea-ops-metrics">{metrics.map(metric=><button key={metric.label} className={'ea-ops-metric '+(metric.kind==='error'?'is-warning':'')} type="button" onClick={()=>onNavigate(metric.action)}>
      <span>{metric.label}<ArrowUpRight size={12}/></span>
      <strong>{metric.value}</strong>
      <small>{metric.note}</small>
    </button>)}</div>
    {sourceNeedsReview>0 && <div className="ea-ops-alert" role="status"><ShieldAlert size={13}/> {sourceNeedsReview} monitored checks require review · no unverified source is treated as healthy</div>}
    <div className="ea-ops-caption"><Activity size={12}/> DATA UPDATES WHILE OPEN · REPORTED COUNTS ≠ REAL-WORLD THREAT LEVEL</div>
  </section>;
}
