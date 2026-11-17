import { useEffect, useMemo, useState } from 'react';
import { api } from './apiClient';
import { Activity, AlertCircle, ArrowUpRight, CheckCircle2, ChevronDown, Clock3, Database, ExternalLink, FileSearch, Filter, LoaderCircle, Radio, RefreshCcw, Search, ShieldCheck } from 'lucide-react';
import './intake.css';

type FeedHealth = {
  sourceId: 'doj' | 'fara' | 'cisa' | 'ofac';
  status:'ok'|'error';
  lastAttemptAt:string;
  lastSuccessAt?:string;
  lastError?:string;
  examined:number;
  inserted:number;
  duplicates:number;
};
type Feed = { id:'doj'|'fara'|'cisa'; name:string; agency:string; documentation:string; category:string; caveat:string; health:FeedHealth|null };
type Intake = {
  id:string; sourceId:'doj'|'fara'|'cisa'; sourceRecordId:string;
  title:string; summary:string; date:string; sourceUrl:string;
  countryMention?:string; countryRule?:string;
  recordType:string; reviewState:string; evidenceTier:string; collectedAt:string;
};
type Intelligence = { sources:Feed[]; records:Intake[]; sampled:number; resultsNote:string; reviewPolicy:string };
const SOURCE_NAMES:Record<string,string> = {doj:'DOJ',fara:'FARA',cisa:'CISA',ofac:'OFAC'};
const d=(value?:string)=>value?new Date(value.length===10?value+'T12:00:00Z':value).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}):'Not yet';
export default function IntakeDesk({countryCode='all'}:{countryCode?:string}) {
  const [data,setData]=useState<Intelligence|null>(null);
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(true);
  const [source,setSource]=useState('all');
  const [search,setSearch]=useState('');
  const [chosen,setChosen]=useState<Intake|null>(null);
  const refresh=()=>{
    setLoading(true);setError('');
    api.get('/api/intelligence').then(response=>{setData(response.data as Intelligence);setChosen(null);}).catch(()=>setError('Collector status could not be read. Previous source data has not been altered.')).finally(()=>setLoading(false));
  };
  useEffect(refresh,[]);
  const visible=useMemo(()=>((data?.records||[]).filter(record=>(countryCode==='all'||record.countryMention===countryCode) && (source==='all'||record.sourceId===source) && (record.title+' '+record.sourceRecordId+' '+record.summary).toLowerCase().includes(search.toLowerCase()))),[data,source,search,countryCode]);
  const ok=data?.sources.filter(s=>s.health?.status==='ok').length||0;
  const fail=data?.sources.filter(s=>s.health?.status==='error').length||0;
  const never=data?.sources.filter(s=>!s.health).length||0;
  return <div className="intake-root">
    <div className="eyebrow"><span className="eyebrow-line"/> RESEARCH OPERATIONS / COLLECTION DESK</div>
    <div className="page-heading"><div><h1>Collection desk<span className="period">.</span></h1><p>Public-source intake, duplicate prevention and a review queue. This is not a list of verified offenders.</p></div><button className="intake-refresh" onClick={refresh} disabled={loading}><RefreshCcw size={15}/> Check latest status</button></div>
    <div className="intake-disclosure"><ShieldCheck size={20}/><p><strong>Evidence firewall:</strong> incoming records are unreviewed source references. A nationality mentioned in a headline is not proof of government direction. FARA registration is lawful disclosure, and CISA vulnerabilities are not attributed to any country.</p></div>
    {loading&&!data?<div className="intake-loading"><LoaderCircle size={21} className="spinning"/> Reading collection status…</div>:null}
    {error?<div className="intake-warning"><AlertCircle size={17}/>{error}<button onClick={refresh}>Retry</button></div>:null}
    {data&&<>
      <div className="intake-summary">
        <div className="intake-stat"><span>HEALTHY CONNECTORS</span><strong>{ok} <small>/ {data.sources.length}</small></strong><p>Last check completed successfully</p></div>
        <div className="intake-stat"><span>NEEDS ATTENTION</span><strong>{fail}</strong><p>Failures shown individually below</p></div>
        <div className="intake-stat"><span>AWAITING FIRST RUN</span><strong>{never}</strong><p>Scheduled, not yet proven active</p></div>
        <div className="intake-stat"><span>REVIEW QUEUE SAMPLE</span><strong>{data.sampled}</strong><p>Unreviewed records in bounded display</p></div>
      </div>
      <div className="intake-h2"><div><div className="eyebrow smaller">AUTOMATED SOURCE CHECKS</div><h2>Connector health</h2></div><span>READ-ONLY STATUS · NO MANUAL SCRAPING</span></div>
      <div className="intake-sources">{data.sources.map(s=><article className="intake-source" key={s.id}>
        <div className="intake-source-top"><span className="intake-agency">{s.category.toUpperCase()}</span><span className={'intake-state '+(s.health?.status||'pending')}>{s.health?.status==='ok'?'CHECK SUCCESSFUL':s.health?.status==='error'?'CHECK FAILED':'NOT CHECKED YET'}</span></div>
        <h3>{s.name}</h3><span className="intake-sub">Source: {s.agency}</span>
        <div className="intake-health-grid"><div><span>LAST ATTEMPT</span><strong>{d(s.health?.lastAttemptAt)}</strong></div><div><span>LAST SUCCESS</span><strong>{d(s.health?.lastSuccessAt)}</strong></div><div><span>EXAMINED LAST RUN</span><strong>{s.health?.status==='ok'?s.health.examined.toLocaleString():'—'}</strong></div><div><span>NEW / DUPLICATES</span><strong>{s.health?.status==='ok'?s.health.inserted+' / '+s.health.duplicates:'—'}</strong></div></div>
        {s.health?.lastError&&<div className="intake-feed-error"><AlertCircle size={14}/>{s.health.lastError}</div>}
        <p>{s.caveat}</p>
        <a href={s.documentation} target="_blank" rel="noopener noreferrer">Documentation <ExternalLink size={13}/></a>
      </article>)}</div>
      <div className="intake-h2"><div><div className="eyebrow smaller">SOURCE REFERENCES / UNREVIEWED</div><h2>Research intake</h2></div><span>{data.sampled} RECORDS SHOWN · NOT A GLOBAL TOTAL</span></div>
      <div className="intake-toolbar"><div className="intake-search"><Search size={17}/><input aria-label="Search imported source records" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search titles, CVEs or registration numbers…"/></div><div className="intake-filter"><Filter size={15}/><select aria-label="Filter imported source" value={source} onChange={e=>{setSource(e.target.value);setChosen(null);}}><option value="all">All sources</option>{data.sources.map(s=><option value={s.id} key={s.id}>{s.name}</option>)}</select><ChevronDown size={14}/></div></div>
      {countryCode!=='all'&&<p className="intake-disclosure">Country scope {countryCode}: only explicitly tagged source references are displayed. Untagged OFAC, FARA and CISA records remain accessible in Global; collector health is always global.</p>}
      <div className="intake-list-layout"><div className="intake-records">{visible.length===0?<div className="intake-empty"><Database size={21}/><h3>No matching intake records yet</h3><p>{data.sources.some(s=>!s.health)?'The first scheduled collection has not completed for every source.':'Try another source or keyword. A successful collection with no matches is not proof of inactivity.'}</p></div>:visible.map(r=><button key={r.id} className={'intake-record '+(chosen?.id===r.id?'active':'')} onClick={()=>setChosen(r)}><div className="intake-record-meta"><span>{SOURCE_NAMES[r.sourceId]} · {r.recordType}</span><span>{d(r.date)}</span></div><h3>{r.title}</h3><div className="intake-record-foot"><span><span className="intake-amber-dot"/> AWAITING HUMAN REVIEW</span><span>DETAILS <ArrowUpRight size={14}/></span></div></button>)}</div><aside className="intake-detail">{chosen?<><span className="eyebrow smaller">RAW SOURCE INDEX · UNREVIEWED</span><h3>{chosen.title}</h3><div className="intake-detail-line"><span>AGENCY</span><strong>{SOURCE_NAMES[chosen.sourceId]}</strong></div><div className="intake-detail-line"><span>RECORD ID</span><strong>{chosen.sourceRecordId}</strong></div><div className="intake-detail-line"><span>RECORD DATE</span><strong>{d(chosen.date)}</strong></div><div className="intake-detail-line"><span>COLLECTED</span><strong>{d(chosen.collectedAt)}</strong></div><div className="intake-detail-line"><span>REVIEW STATE</span><strong>Unreviewed</strong></div>{chosen.countryMention&&<div className="intake-detail-line"><span>HEADLINE MENTIONS</span><strong>{chosen.countryMention} · not attribution</strong></div>}<p className="intake-description">{chosen.summary}</p><div className="intake-review-caveat"><ShieldCheck size={18}/><p>Original-source identity is recorded; the factual allegations and subsequent legal outcomes have not been independently adjudicated by this platform.</p></div><a href={chosen.sourceUrl} target="_blank" rel="noopener noreferrer" className="intake-record-link">Open public source <ExternalLink size={14}/></a></>:<div className="intake-select"><FileSearch size={29}/><h3>Inspect a record</h3><p>Select a source reference to review its collection date, original evidence link and publication status.</p></div>}</aside></div>
      <div className="intake-footnote"><Activity size={15}/><span>{data.resultsNote} Source checks execute on the published schedule; refreshing this screen only re-reads stored results.</span></div>
    </>}
  </div>;
}