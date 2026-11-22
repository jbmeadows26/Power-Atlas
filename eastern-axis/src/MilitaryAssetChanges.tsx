import {useEffect,useMemo,useState} from 'react';
import {Activity,AlertTriangle,ArrowUpRight,BrainCircuit,ChevronDown,ChevronRight,Clock3,Database,Layers3,RefreshCw,Search,ShieldCheck,TrendingDown,TrendingUp} from 'lucide-react';
import './militaryAssetChanges.css';

type Status='review'|'monitor'|'historical'|'data-gap'|'assessed';
type Direction='expanding'|'contracting'|'within-baseline'|'unassessed';
type Row={id:string;code:string;country:string;metricId:string;metric:string;kind:'arms-transfer-volume'|'personnel-estimate'|'equipment-holdings';unit:string;
  observationYear:number;value:number;previousYear:number|null;previousValue:number|null;history:{year:number;value:number}[];
  baseline:{status:string;robustZ:number|null;median:number|null;changePct:number|null;direction:Direction};
  status:Status;anomalous:boolean;modelReviewed:boolean;modelDecision?:string|null;reviewedException:boolean;
  source:string;sourceUrl:string;sourceDate:string;evidenceClass:string;notInventoryChange:boolean;
  confidence:string;reason:string;analystRationale?:string;basis?:string;previousSourceUrl?:string|null};
type Report={schemaVersion:number;category:string;analystName:string;generatedAt:string;status:string;mode:string;method:string;
  summary:{countries:number;series:number;reviewCandidates:number;assessedExceptions:number;historical:number;monitoring:number;
    dataGaps:number;confirmedInventoryChanges:number;existingInventoryReferences:number;inventoryReferenceCountries:number};
  ai:{status:string;reviewed:number;model:string|null;role:string};
  sources:{id:string;status:string;countries:number;url:string;publisher:string;note?:string}[];
  assessments:Row[];limitations:string[]};
const labels:Record<Status,string>={review:'Needs analyst review',assessed:'Reviewed annual anomaly',monitor:'Within baseline',
  historical:'Historical only','data-gap':'Insufficient baseline'};
const directions:Record<Direction,string>={expanding:'Unusually higher',contracting:'Unusually lower',
  'within-baseline':'Within normal range',unassessed:'Not assessable'};
const category:Record<Row['kind'],string>={'arms-transfer-volume':'ARMS DELIVERIES / SIPRI TIV',
  'personnel-estimate':'HISTORICAL MILITARY PERSONNEL','equipment-holdings':'REPORTED EQUIPMENT HOLDINGS'};
const nice=(v:number|null,kind:Row['kind'])=>v===null?'—':kind==='arms-transfer-volume'?(v/1e6).toLocaleString('en-US',{maximumFractionDigits:1})+'M TIV':
  Math.round(v).toLocaleString('en-US')+(kind==='equipment-holdings'?' units':' people');
const num=(v:number|null)=>v===null?'—':(v>=0?'+':'')+v.toFixed(1)+'%';
const when=(value?:string)=>value&&Number.isFinite(Date.parse(value))?new Date(value).toLocaleString('en-US',{year:'numeric',month:'short',day:'numeric',timeZone:'UTC'}):'Not verified';
const safe=(url?:string|null)=>{try{return Boolean(url&&new URL(url).protocol==='https:');}catch{return false;}};
const compare:(a:Row,b:Row)=>number=(a,b)=>Number(b.status==='assessed')-Number(a.status==='assessed')||
  Number(b.status==='review')-Number(a.status==='review')||
  Math.abs(b.baseline.robustZ||0)-Math.abs(a.baseline.robustZ||0)||
  b.observationYear-a.observationYear;

export default function MilitaryAssetChanges({countryCode='all',countryName}:{countryCode?:string;countryName?:string}){
  const [report,setReport]=useState<Report|null>(null);
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(true);
  const [reload,setReload]=useState(0);
  const [scope,setScope]=useState('All measurements');
  const [status,setStatus]=useState('All assessments');
  const [text,setText]=useState('');
  const [open,setOpen]=useState<string|null>(null);
  const [limit,setLimit]=useState(48);

  useEffect(()=>{
    let mounted=true;
    setLoading(true);setError('');
    const base=String(import.meta.env.BASE_URL||'/');
    fetch(base+'analysis/military-asset-changes.json',{cache:'no-store'})
      .then(async response=>{if(!response.ok)throw Error('No verified asset-change snapshot is published');return response.json();})
      .then((data:Report)=>{
        if(!mounted)return;
        if(data.schemaVersion!==1||data.category!=='Defense, Security & Cyber'||!Array.isArray(data.assessments)||!data.summary||!data.ai)
          throw Error('The military asset change report failed its schema gate');
        setReport(data);
      })
      .catch(e=>{if(mounted){setError(String(e?.message||'Collection unavailable'));setReport(null);}})
      .finally(()=>{if(mounted)setLoading(false);});
    return()=>{mounted=false;};
  },[reload]);

  const scoped=useMemo(()=>report?.assessments.filter(x=>countryCode==='all'||x.code===countryCode)||[],
    [report,countryCode]);
  const shown=useMemo(()=>scoped.filter(x=>
    (scope==='All measurements'||x.kind===scope)&&
    (status==='All assessments'||x.status===status)&&
    (!text||[x.country,x.code,x.metric,x.reason].join(' ').toLowerCase().includes(text.toLowerCase()))
  ).sort(compare),[scoped,scope,status,text]);
  const summary={countries:new Set(scoped.map(x=>x.code)).size,
    reviewed:scoped.filter(x=>x.status==='assessed').length,
    queue:scoped.filter(x=>x.status==='review').length,
    higher:scoped.filter(x=>x.anomalous&&x.baseline.direction==='expanding').length,
    lower:scoped.filter(x=>x.anomalous&&x.baseline.direction==='contracting').length,
    holdings:scoped.filter(x=>x.kind==='equipment-holdings'&&x.status==='assessed').length,
    gaps:scoped.filter(x=>x.status==='data-gap').length};
  const stale=report&&Date.now()-Date.parse(report.generatedAt)>3*86400000;
  const country=countryCode==='all'?'Worldwide':countryName||countryCode;
  return <section className="mac-root" aria-label="Military asset change analyst">
    <header className="mac-head">
      <div><div className="mac-kicker"><Layers3 size={15}/> DEFENSE, SECURITY & CYBER / CHANGE ANALYST</div>
        <h2>Military asset <em>change watch.</em></h2>
        <p>Country-by-country screens for unusual changes in arms deliveries, personnel estimates and source-reviewed equipment inventories. Historical departures from normal do not establish operational strength or hostile intent.</p>
      </div>
      <button type="button" className="mac-refresh" disabled={loading} onClick={()=>setReload(x=>x+1)}><RefreshCw size={14}/>{loading?'Checking…':'Reload evidence'}</button>
    </header>
    <div className="mac-stats">
      <div><small>COUNTRIES TRACKED</small><strong>{report?summary.countries:'—'}</strong><span>{country}</span></div>
      <div><small>REVIEWED OUTLIERS</small><strong>{report?summary.reviewed:'—'}</strong><span>Historical changes, not threats</span></div>
      <div><small>REVIEW QUEUE</small><strong>{report?summary.queue:'—'}</strong><span>Unusual readings awaiting AI</span></div>
      <div><small>HIGHER THAN NORMAL</small><strong>{report?summary.higher:'—'}</strong><span>Annual volume or reported holdings</span></div>
      <div><small>LOWER THAN NORMAL</small><strong>{report?summary.lower:'—'}</strong><span>Annual volume or reported holdings</span></div>
      <div><small>VERIFIED HOLDINGS</small><strong>{report?summary.holdings:'—'}</strong><span>Reviewed reported equipment changes</span></div>
    </div>
    <div className="mac-meta">
      <span><Clock3 size={13}/> Snapshot {when(report?.generatedAt)}</span>
      <span><BrainCircuit size={13}/> AI: {report?.ai.status||'unavailable'} · {report?.ai.reviewed??0} reviewed</span>
      <span><Database size={13}/> Historical reference assets: {report?.summary.existingInventoryReferences??'—'}</span>
      <span><ShieldCheck size={13}/> Automatic Command alerts: none</span>
    </div>
    {countryCode!=='all'&&<div className="mac-note"><AlertTriangle size={15}/> Country scope: {country}. All displayed records use explicit country identifiers. Missing equipment types do not mean zero assets.</div>}
    {(error||stale)&&<div className="mac-note"><AlertTriangle size={15}/> {error||'The dataset has not been refreshed in three days. Historical records remain labeled with their observation year.'}</div>}
    <div className="mac-explainer"><strong>IMPORTANT: DELIVERIES ≠ INVENTORY</strong>
      <span>SIPRI trend-indicator values describe annual international arms-transfer volume, not aircraft/tank counts or purchasing cost. Personnel estimates may be years old. Real equipment inventory changes require comparable dated national or UNROCA holdings reports.</span>
    </div>
    <div className="mac-controls">
      <label>Signal class<select value={scope} onChange={v=>{setScope(v.target.value);setLimit(48);}}>
        <option>All measurements</option><option value="arms-transfer-volume">Arms-transfer volume</option>
        <option value="equipment-holdings">Reported equipment inventories</option>
        <option value="personnel-estimate">Historical personnel</option></select></label>
      <label>Review state<select value={status} onChange={v=>{setStatus(v.target.value);setLimit(48);}}>
        <option>All assessments</option>{Object.keys(labels).map(key=><option key={key} value={key}>{labels[key as Status]}</option>)}</select></label>
      <label className="mac-search"><Search size={13}/> Find a country or asset<input placeholder="Country, class, assessment…" value={text} onChange={v=>{setText(v.target.value);setLimit(48);}}/></label>
      <span className="mac-count">{shown.length} records</span>
    </div>
    {loading&&<div className="mac-empty">Loading original-source observations…</div>}
    {!loading&&report&&shown.length===0&&<div className="mac-empty">No indexed measurements match these filters. This is a coverage gap, not proof that assets are absent or unchanged.</div>}
    <div className="mac-list">
      {shown.slice(0,limit).map(r=><article className={'mac-record mac-'+r.status} key={r.id}>
        <button type="button" className="mac-row" onClick={()=>setOpen(open===r.id?null:r.id)} aria-expanded={open===r.id}>
          <span className="mac-country"><small>{r.code} · {category[r.kind]}</small><strong>{r.country}</strong><span>{r.metric}</span></span>
          <span className="mac-measure"><small>{r.observationYear} OBSERVATION</small><strong>{nice(r.value,r.kind)}</strong><span>8-year median {nice(r.baseline.median,r.kind)}</span></span>
          <span className="mac-trend"><small>RELATIVE TO HISTORICAL NORM</small><strong className={'mac-direction-'+r.baseline.direction}>{r.baseline.direction==='expanding'?<TrendingUp size={16}/>:r.baseline.direction==='contracting'?<TrendingDown size={16}/>:<Activity size={16}/>}
            {directions[r.baseline.direction]}</strong><span>{num(r.baseline.changePct)} · {labels[r.status]}</span></span>
          {open===r.id?<ChevronDown size={19}/>:<ChevronRight size={19}/>}
        </button>
        {open===r.id&&<div className="mac-detail">
          <p><strong>Evidence-based assessment</strong>{r.reason}</p>
          {r.analystRationale&&<p className="mac-ai"><BrainCircuit size={15}/> AI review: {r.analystRationale}</p>}
          <div className="mac-history">
            <div><strong>Annual source history</strong><small>Actual reported years only · no missing values filled in</small></div>
            <div className="mac-bars" role="img" aria-label={'Historical measurements: '+r.history.map(v=>v.year+' '+v.value).join(', ')}>
              {r.history.map((v,i)=><div key={v.year} className="mac-bar">
                <span>{r.kind==='arms-transfer-volume'?(v.value/1e6).toFixed(0):Math.round(v.value).toLocaleString('en-US')}</span>
                <i className={i===r.history.length-1?'latest':''} style={{height:Math.max(2,Math.round(100*v.value/Math.max(1,...r.history.map(x=>x.value))))+'%'}}/>
                <small>{String(v.year).slice(-2)}</small></div>)}
            </div>
            <small>Robust deviation: {r.baseline.robustZ===null?'not assessable':r.baseline.robustZ} · Source period {r.observationYear} · Not a statistical probability.</small>
          </div>
          <div className="mac-source">
            <strong>Original evidence</strong>
            {safe(r.sourceUrl)&&<a href={r.sourceUrl} target="_blank" rel="noopener noreferrer">{r.source} · {r.sourceDate} <ArrowUpRight size={13}/></a>}
            {safe(r.previousSourceUrl)&&<a href={r.previousSourceUrl||''} target="_blank" rel="noopener noreferrer">Previous official holdings report <ArrowUpRight size={13}/></a>}
            <span>Evidence: {r.evidenceClass} · {r.confidence} · {r.notInventoryChange?'No verified physical inventory change established':'Reported holdings change; provenance must be reviewed'}</span>
          </div>
        </div>}
      </article>)}
    </div>
    {shown.length>limit&&<button type="button" className="mac-more" onClick={()=>setLimit(n=>n+48)}>Show more source records ({shown.length-limit} remaining)</button>}
    {report&&<footer className="mac-foot"><strong>Evidence limitations:</strong> {report.limitations.join(' ')} <a href="https://www.unroca.org/" target="_blank" rel="noopener noreferrer">UNROCA <ArrowUpRight size={12}/></a></footer>}
  </section>;
}
