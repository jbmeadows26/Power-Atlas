import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ArrowUpRight, BrainCircuit, ChevronDown, ChevronRight, Database, PackageSearch, RefreshCcw, Ship, TrendingUp } from 'lucide-react';
import './shortageForecasts.css';

type Status = 'cross-source-watch' | 'inventory-watch' | 'input-cost-watch' | 'transit-watch' | 'baseline' | 'data-gap';
type Evidence = {kind:string; title:string;publisher:string;url:string;period:string;changePct?:number;changeYearPct?:number;value?:number;unit?:string;scope?:string;baselinePremiumPct?:number;momentumPct?:number;recentDays?:number;baselineDays?:number};
type Forecast = {
  id:string;product:string;category:string;status:Status;screenScore:number;scoreType:string;
  planningWindow:string;horizonType:string;confidence:string;coverage:string;countryScope:string;
  confirmedShortage:boolean;commandEligible:boolean;summary:string;signal:string;
  inputSeriesAvailable:number;inputSeriesExpected:number;routeSeriesAvailable:number;routeSeriesExpected:number;
  inventorySeriesAvailable?:number;inventoryStockScreen?:boolean;modelReviewed:boolean;
  modelAssessment?:{decision:'monitor'|'investigate';rationale:string;sourceEvidenceIds:string[]};
  missingEvidence:string[];evidence:Evidence[];
};
type Outlook = {schemaVersion:number;generatedAt:string;sourceCheckedAt:string;status:string;
  analyst:{mode:string;reviewGate:string;probabilityCalibration:string;portwatch:string;status?:string;screened?:number;reviewed?:number;eligibleForModel?:number};
  inventoryContext?:{checkedAt:string|null;directProducts:number;sectorRatios:Evidence[];sources:{id:string;status:string;period?:string;url:string}[]};
  summary:{products:number;crossSourceWatch:number;inputCostWatch:number;transitWatch:number;inventoryWatch?:number;inventoryFeeds?:number;modelReviewed?:number;dataGaps:number;commandEligible:number};
  forecasts:Forecast[];limitations:string[]};
const labels:Record<Status,string> = {
  'cross-source-watch':'Cross-source watch','input-cost-watch':'Input costs rising',
  'transit-watch':'Shipping pressure','inventory-watch':'Measured stock decline',
  'baseline':'No elevated screen','data-gap':'Coverage gap'
};
const order:Status[]=['cross-source-watch','inventory-watch','input-cost-watch','transit-watch','baseline','data-gap'];
const date=(s?:string)=>s&&Number.isFinite(Date.parse(s))?
  new Date(s).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Not verified';
const num=(n?:number)=>typeof n==='number'&&Number.isFinite(n)?(n>0?'+':'')+n.toFixed(1)+'%':'—';
const age=(s?:string)=>s&&Number.isFinite(Date.parse(s))?Math.max(0,(Date.now()-Date.parse(s))/86400000):null;

export default function ShortageForecasts({countryCode,countryName}:{countryCode:string;countryName?:string}) {
  const [report,setReport]=useState<Outlook|null>(null);
  const [error,setError]=useState('');
  const [pending,setPending]=useState(true);
  const [refresh,setRefresh]=useState(0);
  const [group,setGroup]=useState('All products');
  const [status,setStatus]=useState('All signals');
  const [open,setOpen]=useState<string|null>(null);
  useEffect(()=>{
    let active=true; setPending(true);setError('');
    const base=String(import.meta.env.BASE_URL||'/');
    fetch(base+'analysis/product-shortage-outlook.json',{cache:'no-store'})
      .then(async r=>{if(!r.ok)throw Error('Forecast snapshot is not yet published');return r.json();})
      .then((r:Outlook)=>{
        if(!active)return;
        if(r.schemaVersion!==1||!Array.isArray(r.forecasts)||!r.summary||!r.analyst)throw Error('Forecast schema did not pass validation');
        setReport(r);
      })
      .catch(e=>{if(active){setError(String(e?.message||'Forecast source unavailable'));setReport(null);}})
      .finally(()=>{if(active)setPending(false);});
    return()=>{active=false};
  },[refresh]);
  const groups=useMemo(()=>['All products',...new Set(report?.forecasts.map(x=>x.category)||[])],[report]);
  const shown=useMemo(()=>report?.forecasts.filter(x=>
    (group==='All products'||x.category===group)&&(status==='All signals'||x.status===status))||[],[report,group,status]);
  const daysOld=age(report?.generatedAt);
  const fresh=daysOld!==null&&daysOld<=3;
  const scope=countryCode==='all'?'Worldwide':countryName||countryCode;
  return <section className="sf-root" aria-label="Product shortage outlook">
    <header className="sf-head">
      <div><div className="sf-kicker"><PackageSearch size={16}/> ECONOMIC INTELLIGENCE / SHORTAGE ANALYST</div>
        <h2>Product shortage <em>outlook.</em></h2>
        <p>Forward-looking pressure screens using commodity prices, dated vessel transits, EIA fuel stocks and Census inventory ratios. No claimed stockouts, invented probabilities or unsupported arrival dates.</p>
      </div>
      <button type="button" onClick={()=>setRefresh(v=>v+1)} disabled={pending}><RefreshCcw size={14}/>{pending?'Checking…':'Refresh forecast'}</button>
    </header>
    <div className="sf-metrics">
      <div><small>PRODUCT CATEGORIES</small><strong>{report?.summary.products??'—'}</strong><span>Monitored product groups</span></div>
      <div><small>CROSS-SOURCE WATCHES</small><strong>{report?.summary.crossSourceWatch??'—'}</strong><span>Independent price + route screens</span></div>
      <div><small>INPUT PRESSURE</small><strong>{report?.summary.inputCostWatch??'—'}</strong><span>Commodity movement only</span></div>
      <div><small>SHIPPING PRESSURE</small><strong>{report?.summary.transitWatch??'—'}</strong><span>Broad route movements</span></div>
      <div><small>DIRECT STOCK FEEDS</small><strong>{report?.inventoryContext?.directProducts??'—'}</strong><span>EIA measured gasoline inventories</span></div>
      <div><small>AI REVIEWED</small><strong>{report?.summary.modelReviewed??'—'}</strong><span>{report?.analyst.status||'Model status unknown'}</span></div>
      <div><small>VERIFIED SHORTAGES</small><strong>0</strong><span>No retail stockout verification</span></div>
    </div>
    <div className="sf-context">
      <span><BrainCircuit size={15}/> Analyst: {report?.analyst.screened??'—'} rule-screened · {report?.analyst.reviewed??0} independently AI-reviewed · {report?'Run '+date(report.generatedAt):'Awaiting verified run'} · {fresh?'recent snapshot':'historical / unavailable'}</span>
      <span>Geography: {scope} · {countryCode==='all'?'global input benchmarks':'local product exposure not confirmed'}</span>
    </div>
    {countryCode!=='all'&&<div className="sf-caveat"><AlertCircle size={16}/> Country selection provides context only. Global commodity and chokepoint trends are not verified forecasts of shortages in {scope}.</div>}
    {!fresh&&report&&<div className="sf-caveat"><AlertCircle size={16}/> The published forecast is older than three days. It is historical and cannot establish present conditions.</div>}
    {report&&report.analyst.status!=='available'&&<div className="sf-caveat"><AlertCircle size={16}/> Local AI review: {report.analyst.status||'unavailable'}. Statistical screening continues; model output never confirms a shortage.</div>}
    {error&&<div className="sf-caveat"><AlertCircle size={16}/> {error}. No shortage alerts have been synthesized from unavailable inputs.</div>}
    <div className="sf-legend"><strong>FORECAST ≠ CONFIRMED SHORTAGE</strong>
      <span>Scores are screening priorities, not shortage probabilities. The time window is for monitoring, not a predicted stockout date.</span>
    </div>
    <div className="sf-filterbar">
      <label>Product sector<select value={group} onChange={e=>setGroup(e.target.value)}>{groups.map(g=><option key={g}>{g}</option>)}</select></label>
      <label>Signal status<select value={status} onChange={e=>setStatus(e.target.value)}><option>All signals</option>{order.map(k=><option key={k} value={k}>{labels[k]}</option>)}</select></label>
      <span>{shown.length} of {report?.summary.products??0} products</span>
    </div>
    <div className="sf-list">
      {shown.map(item=><article key={item.id} className={'sf-item '+item.status}>
        <button type="button" className="sf-item-head" aria-expanded={open===item.id} onClick={()=>setOpen(open===item.id?null:item.id)}>
          <span className="sf-product"><small>{item.category}</small><strong>{item.product}</strong><span>{item.signal}</span></span>
          <span className="sf-risk"><small>SCREEN SCORE</small><strong>{item.screenScore}<em>/100</em></strong><span>Not probability</span></span>
          <span className="sf-horizon"><small>PLANNING WINDOW</small><strong>{item.planningWindow}</strong><span>{labels[item.status]}</span></span>
          {open===item.id?<ChevronDown size={19}/>:<ChevronRight size={19}/>}
        </button>
        <div className="sf-priority-track"><i style={{width:Math.min(100,Math.max(0,item.screenScore))+'%'}}/></div>
        {open===item.id&&<div className="sf-details">
          <p>{item.summary}</p>
          <div className="sf-evidence-coverage">
            <span><TrendingUp size={14}/> Price histories: {item.inputSeriesAvailable}/{item.inputSeriesExpected}</span>
            <span><Ship size={14}/> Route comparisons: {item.routeSeriesAvailable}/{item.routeSeriesExpected}</span>
            <span><Database size={14}/> Direct inventory: {item.inventorySeriesAvailable??0} · {item.inventoryStockScreen?'drawdown screen':'no drawdown screen'}</span>
            <span><Database size={14}/> Confidence: {item.confidence}; no confirmed shortage</span>
          </div>
          {item.modelAssessment&&<div className="sf-ai-review"><BrainCircuit size={16}/><div><strong>Local AI review · {item.modelAssessment.decision}</strong><span>{item.modelAssessment.rationale}</span><small>Analyst advice only; supporting evidence must come from the linked measurements below</small></div></div>}
          {!item.modelReviewed&&<div className="sf-unreviewed">Model review unavailable or not required for this screen. Rules-based checks still ran.</div>}
          <h3>Measured source evidence</h3>
          {item.evidence.length?<div className="sf-evidence-list">{item.evidence.map((e,i)=><a key={e.url+'-'+e.kind+'-'+i} href={e.url} target="_blank" rel="noopener noreferrer">
            <div><strong>{e.title}</strong><small>{e.publisher} · observation {e.period}</small></div>
            <span>{e.kind==='corridor-transit'?'Transits '+num(e.changePct):e.kind==='direct-inventory'?'Stocks WoW '+num(e.changePct):'Monthly '+num(e.changePct)}<ArrowUpRight size={13}/></span>
          </a>)}</div>:<p className="sf-no-evidence">No dated product-input evidence connected. This is a monitoring coverage gap, not an all-clear.</p>}
          <details className="sf-missing"><summary>Evidence required before stronger conclusions</summary><ul>{item.missingEvidence.map(x=><li key={x}>{x}</li>)}</ul></details>
        </div>}
      </article>)}
      {!pending&&report&&shown.length===0&&<div className="sf-empty">No forecasts match these filters. This is not evidence that all products are available.</div>}
      {pending&&<div className="sf-empty">Checking independently dated forecast snapshot…</div>}
    </div>
    {report?.inventoryContext&&<details className="sf-inventory-context"><summary><Database size={15}/> Inventory collection: {report.inventoryContext.sources.filter(s=>s.status==='ok').length}/{report.inventoryContext.sources.length} verified feeds · inspect US-wide sector context</summary>
      <div>{report.inventoryContext.sectorRatios.map(m=><a key={m.url} href={m.url} target="_blank" rel="noopener noreferrer"><span>{m.title}<small>{m.period} · {m.scope}</small></span><strong>{m.value?.toFixed(2)} <ArrowUpRight size={12}/></strong></a>)}</div>
      <p>Aggregate ratios are context only; no product-level coverage is inferred.</p>
    </details>}
    <footer className="sf-method"><strong>Analyst validation gate</strong><p>Production shortages require independently documented inventory, purchasing or product-specific delivery data. A commodity price jump, an aggregate vessel decline, or a U.S. gasoline stock drawdown alone does not establish a retail shortage. No unreviewed forecast is promoted to Command Center.</p><a href="https://www.eia.gov/petroleum/supply/weekly/" target="_blank" rel="noopener noreferrer">EIA gasoline inventory <ArrowUpRight size={13}/></a><a href="https://www.worldbank.org/en/research/commodity-markets" target="_blank" rel="noopener noreferrer">World Bank commodity data <ArrowUpRight size={13}/></a><a href="https://portwatch.imf.org/" target="_blank" rel="noopener noreferrer">IMF PortWatch <ArrowUpRight size={13}/></a><a href="https://www.fao.org/worldfoodsituation/foodpricesindex/en/" target="_blank" rel="noopener noreferrer">FAO food price index <ArrowUpRight size={13}/></a></footer>
  </section>;
}
