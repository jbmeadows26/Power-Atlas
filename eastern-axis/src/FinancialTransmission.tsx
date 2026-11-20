import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, ChevronDown, Clock3, ExternalLink, Landmark, X } from 'lucide-react';
import './financialTransmission.css';

type HistoricalPoint = {date:string;value:number};
type Metric = {id:string;label:string;domain:string;cadence:string;unit:string;value:number;period:string;previous:number|null;previousPeriod:string|null;changePoints:number|null;status:string;periodAgeDays:number;history:HistoricalPoint[];source:string;sourceUrl:string};
type Fact = {valueUSD:number;periodEnd:string;filed:string;form:string;taxonomyTag:string;sourceUrl:string|null};
type Issuer = {ticker:string;name:string;sector?:string;cik:number|null;status:string;sourceUrl?:string;latestReport:{form:string;filed:string;url:string}|null;balanceSheet:{cash:Fact|null;longTermDebt:Fact|null;note:string}|null};
type Filing = {id:string;ticker:string;company:string;filed:string;item:string;title:string;classification:string;sourceUrl:string;note:string};
type Signal = {id:string;domain:string;level:string;title:string;rule:string;evidenceIds:string[];claim:string};
type Source = {id:string;status:string;detail:string;sourceUrl:string;checkedAt:string};
type Snapshot = {schemaVersion:number;checkedAt:string;status:string;scope:string;householdMetrics:Metric[];issuers:Issuer[];filings:Filing[];signals:Signal[];sources:Source[];intradayQuotes:{status:string;reason:string};limitations:string[]};
type Selection =
  | {kind:'metric';metric:Metric}
  | {kind:'issuer';issuer:Issuer;filings:Filing[]}
  | {kind:'filing';filing:Filing}
  | {kind:'unavailable';id:string;title:string;detail:string;sourceUrl?:string};
const PATH = String(import.meta.env.BASE_URL || '/') + 'analysis/financial-transmission.json';
const TOP = ['DRCCLACBS','TDSP','DRTSCILM','BAMLC0A0CM'];
const compactUSD = (v:number) => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:1}).format(v);
const fmt = (v:number,places=2)=>new Intl.NumberFormat('en-US',{maximumFractionDigits:places}).format(v);
const dateText=(date?:string|null)=>date&&Number.isFinite(Date.parse(date))?
 new Date(date.length===10?date+'T00:00:00Z':date).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Unknown';
const moneyFact=(fact:Fact|null)=>fact?compactUSD(fact.valueUSD):'—';
const changeText=(m:Metric)=>m.changePoints===null?'—':(m.changePoints>0?'+':'')+(m.unit==='persons'?fmt(m.changePoints,0)+' people':m.unit==='percentage points'?fmt(m.changePoints*100,0)+' bps':fmt(m.changePoints)+' pp');
function Line({metric}:{metric:Metric}){
 const pts=(metric.history||[]).filter(v=>Number.isFinite(v.value)).slice(-16);
 if(pts.length<2)return <span className="ft-no-history">Not enough history</span>;
 const lo=Math.min(...pts.map(p=>p.value)),hi=Math.max(...pts.map(p=>p.value));
 const spread=Math.max(hi-lo,Math.abs(hi)*.005,.001);
 return <svg viewBox="0 0 220 50" role="img" aria-label={metric.label+' '+pts.length+' original observations from '+dateText(pts[0].date)+' to '+dateText(pts[pts.length-1].date)}>
   <polyline points={pts.map((p,i)=>(5+210*i/(pts.length-1)).toFixed(1)+','+(44-(p.value-lo)/spread*38).toFixed(1)).join(' ')}
     fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round"/>
 </svg>;
}
export default function FinancialTransmission(){
 const [data,setData]=useState<Snapshot|null>(null);
 const [error,setError]=useState('');
 const [revision,setRevision]=useState(0);
 const [showAll,setShowAll]=useState(false);
 const [showIssuers,setShowIssuers]=useState(false);
 const [issuerGroup,setIssuerGroup]=useState('AI ecosystem');
 const [selected,setSelected]=useState<Selection|null>(null);
 useEffect(()=>{
  let alive=true;setError('');
  fetch(PATH+'?v='+revision,{cache:'no-store'}).then(async response=>{
   if(!response.ok)throw Error('Financial transmission source unavailable ('+response.status+')');
   const raw=await response.json() as Partial<Snapshot>;
   if(raw.schemaVersion!==1||!Array.isArray(raw.householdMetrics)||!Array.isArray(raw.issuers)||!Array.isArray(raw.filings)||!Array.isArray(raw.sources)||!Array.isArray(raw.signals))
    throw Error('Unexpected source format');
   if(alive)setData(raw as Snapshot);
  }).catch(e=>{if(alive){setData(null);setError(e instanceof Error?e.message:'Source unavailable');}});
  return()=>{alive=false;};
 },[revision]);
 useEffect(()=>{
  if(!selected)return;
  const onKey=(event:KeyboardEvent)=>{if(event.key==='Escape')setSelected(null);};
  window.addEventListener('keydown',onKey);
  return()=>window.removeEventListener('keydown',onKey);
 },[selected]);
 const metrics=useMemo(()=>new Map((data?.householdMetrics||[]).map(m=>[m.id,m])),[data]);
 const issuerOk=data?.issuers.filter(i=>i.status==='ok').length||0;
 const ageMs=data?Date.now()-Date.parse(data.checkedAt):Infinity;
 const stale=!data||!Number.isFinite(ageMs)||ageMs>12*3600000;
 const recordedFilings=(data?.filings||[]).filter(f=>f.classification==='filing-review');
 const sourceProblem=(data?.status==='partial'||data?.status==='unavailable'||stale);
 const secBlock=data?.sources.find(s=>s.id==='sec:tickers'&&s.status==='error');
 const openMissing=(id:string,title:string,detail:string,sourceUrl?:string)=>setSelected({kind:'unavailable',id,title,detail,sourceUrl});
 return <section className="ft-root" aria-label="Credit and household financial transmission">
  <div className="ft-header">
   <div><span className="ft-kicker"><Landmark size={14}/> CREDIT / COMPANY FILINGS / HOUSEHOLDS</span>
     <h3>Financial transmission indicators</h3></div>
   <button type="button" onClick={()=>setRevision(v=>v+1)}>Recheck sources</button>
  </div>
  <div className="ft-summary">
   <span className={sourceProblem?'ft-incomplete':'ft-current'}>{stale?'STALE / MISSING':data?.status==='ok'?'SOURCE CHECKED':'PARTIAL COVERAGE'}</span>
   <span>{data?'Checked '+dateText(data.checkedAt):'No observations'}</span>
   <span>Issuers <strong>{data?issuerOk+'/'+data.issuers.length:'—'}</strong></span>
   <span>SEC review items <strong>{data&&issuerOk>0?recordedFilings.length:'Unknown'}</strong></span>

  </div>
  {(error||sourceProblem)&&<p className="ft-caution" role="status">{error||('Some source results are missing or stale; unavailable is not an all-clear.'+(secBlock?' SEC issuer access: '+secBlock.detail+'.':''))}</p>}
  <div className="ft-top">
   {TOP.map(id=>{
    const m=metrics.get(id);
    return <button type="button" className={'ft-tile '+(!m||m.status!=='ok'?'ft-dim':'')} key={id}
      onClick={()=>m?setSelected({kind:'metric',metric:m}):openMissing(id,({DRCCLACBS:'Card delinquency',TDSP:'Debt service',DRTSCILM:'Bank tightening',BAMLC0A0CM:'Investment-grade spread'} as Record<string,string>)[id],data?.sources.find(s=>s.id==='fred:'+id)?.detail||'No verified observation','https://fred.stlouisfed.org/series/'+id)}>
     <div className="ft-tile-heading">{m?.label||id}<ArrowUpRight size={13}/></div>
     <strong>{m?fmt(m.value):'—'} <small>{m?.unit||''}</small></strong>
     <div className="ft-chart">{m?<Line metric={m}/>:<span className="ft-no-history">No valid data</span>}</div>
     <div className="ft-tile-bottom"><span>{m?dateText(m.period)+' · '+m.cadence:'Unobserved'}</span><b>{m?changeText(m):'—'}</b></div>
    </button>;
   })}
  </div>
  {data?.signals?.length?<div className="ft-alerts" role="status"><strong>{data.signals.length} independent transmission screens</strong>{data.signals.map(s=>
   <button type="button" key={s.id} onClick={()=>s.id==='sec-disclosure-review'?
      setShowIssuers(true):setSelected({kind:'metric',metric:metrics.get(s.evidenceIds[0])!})} disabled={s.id!=='sec-disclosure-review'&&!metrics.get(s.evidenceIds[0])}>
      <span>{s.domain}</span> {s.title} <ArrowUpRight size={12}/>
   </button>)}</div>:<div className="ft-neutral">No additional threshold screens confirmed among available observations. This is not an all-clear.</div>}
  <div className="ft-panels">
   <div className="ft-panel">
    <div className="ft-panel-heading"><h4>Households & lending</h4><span>Source periods, not causal impact</span></div>
    <div className="ft-submetrics">{['PSAVERT','UNRATE','ICSA'].map(id=>{
      const m=metrics.get(id);
      return <button type="button" key={id} onClick={()=>m?setSelected({kind:'metric',metric:m}):openMissing(id,id,data?.sources.find(s=>s.id==='fred:'+id)?.detail||'Not connected','https://fred.stlouisfed.org/series/'+id)}>
        <span>{m?.label||id}</span><strong>{m?fmt(m.value,m.unit==='persons'?0:2):'—'}</strong>
        <small>{m?dateText(m.period)+' · '+m.unit:'Missing'}</small>
      </button>;
    })}</div>
   </div>
   <div className="ft-panel">
     <div className="ft-panel-heading"><h4>AI & private-credit filings</h4><span>SEC EDGAR · sampled issuers</span></div>
     <div className="ft-issuer-summary">
       <strong>{data&&issuerOk>0?recordedFilings.length:'—'}</strong><span>item 1.03 / 2.04 disclosures in sampled 120-day window</span>
       <strong>{issuerOk||'—'}</strong><span>issuers with SEC index access</span>
     </div>
     <div className="ft-submetrics ft-credit-proxies">{['DRBLACBS','QBPLNTLNNCUR'].map(id=>{
       const m=metrics.get(id);
       return <button type="button" key={id} onClick={()=>m?setSelected({kind:'metric',metric:m}):openMissing(id,id,data?.sources.find(s=>s.id==='fred:'+id)?.detail||'Unavailable','https://fred.stlouisfed.org/series/'+id)}>
         <span>{m?.label||id}</span><strong>{m?fmt(m.value):'—'}</strong><small>{m?dateText(m.period)+' · '+m.unit:'Missing'}</small>
       </button>;
     })}</div>
     <button className="ft-more" type="button" aria-expanded={showIssuers} onClick={()=>setShowIssuers(v=>!v)}>{showIssuers?'Hide issuer evidence':'Open issuer evidence'} <ChevronDown size={15}/></button>
   </div>
  </div>
  {showIssuers&&<div className="ft-issuers">
    <div className="ft-issuer-filter"><label htmlFor="ft-sector">Issuer group</label><select id="ft-sector" value={issuerGroup} onChange={event=>setIssuerGroup(event.target.value)}><option value="AI ecosystem">AI ecosystem</option><option value="Listed private-credit BDC">Listed private-credit lenders</option></select></div>
    {(data?.issuers||[]).filter(issuer=>(issuer.sector||"AI ecosystem")===issuerGroup).map(issuer=><button type="button" key={issuer.ticker} onClick={()=>setSelected({kind:'issuer',issuer,filings:(data?.filings||[]).filter(f=>f.ticker===issuer.ticker)})}>
      <b>{issuer.ticker}</b><span>{issuer.name}</span>
      <small>{issuer.status==='ok'?(issuer.latestReport?.form||'SEC index')+' · '+dateText(issuer.latestReport?.filed):'SOURCE UNAVAILABLE'}</small><ArrowUpRight size={13}/>
    </button>)}
    {!data&&<p>No verified issuer index</p>}
    {recordedFilings.filter(f=>data?.issuers.find(i=>i.ticker===f.ticker)?.sector===issuerGroup).length>0&&<div className="ft-filings"><h4>Filings requiring inspection</h4>{recordedFilings.filter(f=>data?.issuers.find(i=>i.ticker===f.ticker)?.sector===issuerGroup).slice(0,16).map(f=><button type="button" key={f.id} onClick={()=>setSelected({kind:'filing',filing:f})}><b>{f.ticker}</b><span>{f.item}: {f.title}</span><small>{dateText(f.filed)}</small></button>)}</div>}
  </div>}
  <div className="ft-auxiliary"><button type="button" aria-expanded={showAll} onClick={()=>setShowAll(v=>!v)}>
    {showAll?'Hide data-access gaps':'Source coverage & intraday limitations'} <ChevronDown size={14}/></button>
    {showAll&&<div className="ft-limitations">
      <p><strong>Intraday quotes:</strong> {data?.intradayQuotes?.reason||'No licensed price feed is configured.'}</p>
      <p><strong>Private credit:</strong> SEC event metadata and public spread metrics do not reveal private loan tapes, undisclosed defaults or lender losses.</p>
      <p><strong>Household exposure:</strong> Aggregate delinquency, unemployment and borrowing indicators do not establish household losses caused by an AI selloff.</p>
      <div className="ft-readable-sources">
        <strong>Connected sources: {data?.householdMetrics.filter(m=>m.status==='ok').length??0}/9 financial indicators</strong>
        <span>Issuer filings: {issuerOk}/{data?.issuers.length??14} connected{secBlock?' · '+secBlock.detail:''}</span>
        {(data?.householdMetrics||[]).map(m=><a key={m.id} href={m.sourceUrl} target="_blank" rel="noopener noreferrer">{m.label} · observed {dateText(m.period)} <ExternalLink size={12}/></a>)}
      </div>
      <p><a href={PATH} target="_blank" rel="noopener noreferrer">Raw JSON dataset (technical / developers) <ExternalLink size={13}/></a></p>
    </div>}
  </div>
  {selected&&<div className="ft-modal-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setSelected(null);}}>
   <article className="ft-modal" role="dialog" aria-modal="true" aria-label={selected.kind==='metric'?selected.metric.label:selected.kind==='issuer'?selected.issuer.ticker:selected.kind==='filing'?selected.filing.title:selected.title}>
    <header><h3>{selected.kind==='metric'?selected.metric.label:selected.kind==='issuer'?selected.issuer.ticker+' · '+selected.issuer.name:selected.kind==='filing'?selected.filing.title:selected.title}</h3>
    <button type="button" aria-label="Close financial evidence" onClick={()=>setSelected(null)}><X size={19}/></button></header>
    {selected.kind==='metric'?<>
       <strong className="ft-modal-value">{fmt(selected.metric.value)} {selected.metric.unit}</strong>
       <Line metric={selected.metric}/>
       <dl><div><dt>Observation period</dt><dd>{dateText(selected.metric.period)} · {selected.metric.cadence}</dd></div>
         <div><dt>Previous period</dt><dd>{dateText(selected.metric.previousPeriod)}</dd></div>
         <div><dt>Period-to-period change</dt><dd>{selected.metric.changePoints===null?'Unavailable':changeText(selected.metric)}</dd></div>
         <div><dt>Underlying producer</dt><dd>{selected.metric.source}</dd></div>
         <div><dt>Source freshness</dt><dd>{selected.metric.status} · period {selected.metric.periodAgeDays} days before collection</dd></div></dl>
       <a href={selected.metric.sourceUrl} target="_blank" rel="noopener noreferrer">Original FRED data <ExternalLink size={13}/></a>
       <p>Government aggregates do not identify AI-induced losses, individual loan defaults or household portfolio returns.</p>
     </>:selected.kind==='issuer'?<>
       <p>{selected.issuer.status==='ok'?'SEC filer indexed':'Issuer SEC index currently unavailable'} · CIK {selected.issuer.cik??'unavailable'}</p>
       <div className="ft-financial-facts"><div><span>Reported cash / equivalents</span><strong>{moneyFact(selected.issuer.balanceSheet?.cash||null)}</strong><small>{dateText(selected.issuer.balanceSheet?.cash?.periodEnd)}</small></div>
         <div><span>Reported long-term debt</span><strong>{moneyFact(selected.issuer.balanceSheet?.longTermDebt||null)}</strong><small>{dateText(selected.issuer.balanceSheet?.longTermDebt?.periodEnd)}</small></div></div>
       <p>These are selected XBRL balance-sheet facts, not issuer share prices. Different definitions and periods cannot be netted.</p>
       {selected.issuer.latestReport&&<a href={selected.issuer.latestReport.url} target="_blank" rel="noopener noreferrer">Latest {selected.issuer.latestReport.form} filing <ExternalLink size={13}/></a>}
       <h4>Recent financing / distress-coded 8-K items</h4>
       {selected.filings.length?selected.filings.map(f=><div className="ft-filing-line" key={f.id}><span>{dateText(f.filed)} · {f.item} {f.title}</span><a href={f.sourceUrl} target="_blank" rel="noopener noreferrer">Filing <ExternalLink size={12}/></a></div>):<p>{selected.issuer.status==='ok'?'No matching item-coded events found within the sampled index and window.':'The filing index is unavailable; no absence-of-risk claim can be made.'}</p>}
       {selected.issuer.sourceUrl&&<a href={selected.issuer.sourceUrl} target="_blank" rel="noopener noreferrer">Original SEC submissions index <ExternalLink size={13}/></a>}
     </>:selected.kind==='filing'?<>
       <p><strong>{selected.filing.ticker}</strong> · {dateText(selected.filing.filed)} · SEC item {selected.filing.item}</p>
       <p>{selected.filing.note}</p>
       <p>{selected.filing.classification==='financing-context'?'New obligations are not default evidence.':'Item-coded financial distress requires inspection of the primary document, counterparty and actual obligation.'}</p>
       <a href={selected.filing.sourceUrl} target="_blank" rel="noopener noreferrer">Read original SEC filing <ExternalLink size={13}/></a>
     </>:<><p>{selected.detail}</p><p>Missing observation is not a zero or an all-clear.</p>
       {selected.sourceUrl&&<a href={selected.sourceUrl} target="_blank" rel="noopener noreferrer">Inspect original source <ExternalLink size={13}/></a>}</>}
   </article>
  </div>}
 </section>;
}
