import { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, ChevronDown, Clock3, ExternalLink, TrendingDown, X } from 'lucide-react';
import FinancialTransmission from './FinancialTransmission';
import './financialMarkets.css';

type Point = { date: string; value: number };
type Metric = {
  id:string; label:string; group:string; unit:string; value:number; period:string;
  previous:number|null; previousPeriod:string|null; change1Pct:number|null;
  change5Pct:number|null; change5Points:number|null; drawdown60Pct:number|null;
  history:Point[]; source:string; sourceUrl:string; provider:string;
  cadence:'daily'|'weekly'; checkedAt:string; status:'ok'|'stale'; ageDays:number;
};
type Signal = {
  id:string; domain:string; level:'watch'|'investigate'; title:string;
  explanation:string; evidenceIds:string[]; rule:string;
};
type Source = {id:string;status:string;detail:string;sourceUrl:string;checkedAt:string};
type Snapshot = {
  schemaVersion:number; checkedAt:string; status:string; metrics:Metric[];
  signals:Signal[];sources:Source[];limitations:string[];cadence:string;
};
type Dossier = {id:string;title:string;date:string;finding:string;interpretation:string;sources:{label:string;url:string}[]};
const BASE = String(import.meta.env.BASE_URL || '/');
const SNAPSHOT = BASE + 'analysis/financial-markets.json';
const ORDER = [
  {id:'SP500', label:'S&P 500', group:'Equities'},
  {id:'NASDAQCOM', label:'Nasdaq Composite', group:'Equities'},
  {id:'VIXCLS', label:'VIX', group:'Volatility'},
  {id:'BAMLH0A0HYM2', label:'High-yield spread', group:'Credit'},
  {id:'T10Y2Y', label:'10y–2y Treasury', group:'Rates'},
  {id:'STLFSI4', label:'Financial stress', group:'Credit'},
];
const DOSSIERS:Dossier[] = [
  {
    id:'ai-selloff-2026-11-20', title:'AI equity selloff', date:'Nov 20, 2026',
    finding:'WSJ reported an approximately $4T AI-linked valuation wipeout following the Anthropic IPO amid a broader selloff.',
    interpretation:'Reported aggregate market-value decline, not independently reconstructed from company prices. It is not $4T in cash withdrawn or loan defaults.',
    sources:[
      {label:'Wall Street Journal',url:'https://www.wsj.com/finance/stocks/anthropics-ipo-bust-punctuates-4-trillion-ai-wipeout-on-wall-street-f1f1ec90'},
      {label:'Reuters: IPO and market reaction',url:'https://www.reuters.com/business/anthropics-post-debut-stumble-delivers-reality-check-ai-trade-2026-11-20/'},
    ],
  },
  {
    id:'ai-financing-2026-11-20', title:'GPU-backed financing', date:'Nov 20, 2026',
    finding:'Apollo and Goldman Sachs announced a $44B financing package tied to SpaceX GPU infrastructure.',
    interpretation:'Capital placement is not a default. Monitor tranche yields, collateral values, lease payments and refinancing; reported $32B and $44B figures need reconciliation by tranche and scope.',
    sources:[
      {label:'Apollo / Goldman statement',url:'https://ir.apollo.com/news-events/press-releases/detail/662/apollo-and-goldman-sachs-announce-pricing-of-44-billion'},
      {label:'Reuters debt financing report',url:'https://www.reuters.com/business/media-telecom/apollo-goldman-lead-44-billion-spacex-gpu-debt-financing-2026-11-20/'},
    ],
  },
  {
    id:'ecb-financial-stability-2026-11', title:'Regulator risk assessment', date:'Nov 2026',
    finding:'The ECB Financial Stability Review identifies AI valuations, circular financing and interlinked equity, debt and non-bank exposures as vulnerabilities.',
    interpretation:'This is an institutional risk assessment—not confirmation of a banking failure or recession.',
    sources:[
      {label:'European Central Bank',url:'https://www.ecb.europa.eu/press/financial-stability-publications/fsr/html/ecb.fsr202611~e03b919d36.en.html'},
    ],
  },
];
const fmt = (num:number, digits=2) => num.toLocaleString('en-US',{maximumFractionDigits:digits,minimumFractionDigits:digits});
const dateText = (str:string) => Number.isFinite(Date.parse(str)) ? new Date(str + (str.length===10?'T00:00:00Z':'')).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}) : str;
const validMetric = (m:unknown):m is Metric => {
  if(!m || typeof m!=='object')return false;
  const v=m as Partial<Metric>;
  return !!(typeof v.id==='string' && typeof v.period==='string' && typeof v.sourceUrl==='string'
      && v.sourceUrl.startsWith('https://fred.stlouisfed.org/series/')
      && Number.isFinite(v.value) && Array.isArray(v.history)
      && (v.status==='ok'||v.status==='stale'));
};
function Sparkline({points, label}:{points:Point[];label:string}){
  const usable=points.filter(p=>Number.isFinite(p.value)).slice(-30);
  if(usable.length<2)return <span className="fm-no-trend">Insufficient history</span>;
  const vals=usable.map(p=>p.value),min=Math.min(...vals),max=Math.max(...vals),delta=Math.max(max-min,Math.abs(max)*0.005,0.0001);
  const coords=vals.map((v,i)=>(6+i*188/(vals.length-1)).toFixed(1)+','+(48-42*(v-min)/delta).toFixed(1)).join(' ');
  return <svg viewBox="0 0 200 54" role="img" aria-label={label+' last '+usable.length+' observations, from '+dateText(usable[0].date)+' to '+dateText(usable[usable.length-1].date)}>
    <line x1="3" x2="197" y1="48" y2="48" stroke="currentColor" strokeOpacity=".2"/>
    <polyline points={coords} fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>;
}
export default function FinancialMarkets(){
  const [data,setData]=useState<Snapshot|null>(null);
  const [error,setError]=useState('');
  const [revision,setRevision]=useState(0);
  const [selected,setSelected]=useState<{kind:'metric';metric:Metric}|{kind:'dossier';dossier:Dossier}|{kind:'unavailable';item:{id:string;label:string;group:string};source?:Source}|null>(null);
  const [dossiersOpen,setDossiersOpen]=useState(false);
  useEffect(()=>{
    let alive=true;
    setError('');
    fetch(SNAPSHOT+'?v='+revision,{cache:'no-store'}).then(async response=>{
      if(!response.ok)throw new Error('Market snapshot not published ('+response.status+')');
      const payload=await response.json() as Partial<Snapshot>;
      if(payload.schemaVersion!==1 || !Array.isArray(payload.metrics) || !Array.isArray(payload.sources) || !Array.isArray(payload.signals))
        throw new Error('Financial market snapshot schema invalid');
      const safe:Snapshot={
        schemaVersion:1,checkedAt:String(payload.checkedAt||''),status:String(payload.status||'unknown'),
        metrics:payload.metrics.filter(validMetric),signals:payload.signals as Signal[],
        sources:payload.sources as Source[],limitations:Array.isArray(payload.limitations)?payload.limitations:[],
        cadence:String(payload.cadence||'Daily published data'),
      };
      if(alive)setData(safe);
    }).catch(e=>{if(alive){setData(null);setError(e instanceof Error?e.message:'Market feed unavailable');}});
    return()=>{alive=false;};
  },[revision]);
  useEffect(()=>{
    if(!selected)return;
    const onKey=(event:KeyboardEvent)=>{if(event.key==='Escape')setSelected(null);};
    window.addEventListener('keydown',onKey);
    return()=>window.removeEventListener('keydown',onKey);
  },[selected]);
  const byId=new Map((data?.metrics||[]).map(metric=>[metric.id,metric]));
  const checkedAge=data?Date.now()-Date.parse(data.checkedAt):NaN;
  const collectionStale=!!data && (!Number.isFinite(checkedAge)||checkedAge>12*3600000);
  const equitySignal=(data?.signals||[]).find(s=>s.id==='equity-stress');
  const creditSignal=(data?.signals||[]).find(s=>s.id==='credit-spread-stress');
  const riskSummary=(data?.signals||[]).find(s=>s.id==='cross-market-stress');
  const relevantSignals=(data?.signals||[]).filter(s=>s.id!=='cross-market-stress');
  return <section className="fm-root" aria-label="Financial market early-warning intelligence">
    <div className="fm-heading">
      <div><span className="fm-kicker"><Activity size={13}/> FINANCIAL MARKETS / EARLY WARNING</span>
      <h2>Market pressure <span>across asset classes</span></h2>
      <p>US benchmarks · globally relevant transmission screens · published observations, not live trading quotes</p></div>
      <button type="button" className="fm-refresh" onClick={()=>setRevision(n=>n+1)} aria-label="Reload financial data">Refresh data</button>
    </div>
    <div className="fm-status-strip" aria-live="polite">
      <span className={collectionStale||!data?'fm-status-missing':riskSummary?'fm-status-watch':'fm-status-fresh'}>
        {collectionStale?'STALE COLLECTION':!data?'NOT YET CONNECTED':riskSummary?'CROSS-MARKET SCREEN':data.status==='partial'?'PARTIAL SOURCE COVERAGE':'SOURCE CHECKED'}
      </span>
      <span>{data?('Checked '+dateText(data.checkedAt)+' · '+data.metrics.filter(m=>m.status==='ok').length+'/'+ORDER.length+' current'):'No verified market snapshot available'}</span>
      <span>Equities: <strong>{!data||collectionStale?'unknown':equitySignal?'watch':'no threshold breach in available data'}</strong></span>
      <span>Credit: <strong>{!data||collectionStale||!byId.get('BAMLH0A0HYM2')||byId.get('BAMLH0A0HYM2')?.status!=='ok'?'unknown':creditSignal?'spread watch':'no spread threshold breach'}</strong></span>
    </div>
    {(error||collectionStale)&&<p className="fm-warning" role="status">{error||'Collection is older than 12 hours. Last available observations remain visible with their dates; alerts are not current.'} Missing data never means low risk.</p>}
    <div className="fm-metrics">
      {ORDER.map(item=>{
        const metric=byId.get(item.id),fresh=metric?.status==='ok'&&!collectionStale;
        const delta=metric?.change5Pct;
        const points=metric?.change5Points;
        const movement=metric && points!==null && points!==undefined && (item.id==='BAMLH0A0HYM2'||item.id==='T10Y2Y')
          ?(points>0?'+':'')+fmt(points*100,0)+' bps / 5 obs'
          :metric && points!==null && points!==undefined && item.id==='STLFSI4'
            ?(points>0?'+':'')+fmt(points,2)+' pts / 5 obs'
            :metric && delta!==null && delta!==undefined
              ?(delta>0?'+':'')+fmt(delta)+'% / 5 obs':'—';
        return <button key={item.id} type="button" className={'fm-metric '+(!fresh?'fm-metric-missing':'')} onClick={()=>metric?setSelected({kind:'metric',metric}):setSelected({kind:'unavailable',item,source:data?.sources.find(s=>s.id===item.id)})} aria-label={item.label+' details and source'}>
          <div className="fm-metric-top"><span>{item.label}</span><small>{metric?metric.status==='stale'?'STALE':item.group:'UNAVAILABLE'}</small></div>
          <div className="fm-big">{metric?fmt(metric.value,metric.unit==='index'?1:2):'—'} <small>{metric?.unit==='percentage points'?'pp':metric?.unit==='index'?'':' '}</small></div>
          <div className={'fm-spark '+(delta!==null&&delta!==undefined&&delta<0?'negative':'')}>{metric?<Sparkline points={metric.history} label={item.label}/>:<span className="fm-no-trend">Awaiting observations</span>}</div>
          <div className="fm-metric-bottom"><span>{metric?'Observed '+dateText(metric.period):'Data pending'}</span><strong>{movement}</strong></div>
          <div className="fm-open">Open evidence <ArrowUpRight size={12}/></div>
        </button>;
      })}
    </div>
    <div className="fm-alerts">
      <div className="fm-alerts-title"><TrendingDown size={15}/><strong>Active measurement screens</strong><small>{collectionStale?'stale · not assessed':data?relevantSignals.length+' breached':'not assessed'}</small></div>
      <div className="fm-alerts-body">
        {!data||collectionStale?<p>Insufficient current observations. Equity, credit and household effects cannot be assessed from this snapshot.</p>:
        relevantSignals.length?relevantSignals.map(signal=><div key={signal.id} className="fm-alert"><b>{signal.domain}</b><span>{signal.title}</span><small>{signal.rule}</small></div>):
        <p>No disclosed thresholds breached among fresh sampled benchmarks; this is not an all-clear.</p>}
      </div>
      <p>Credit spread widening, loan defaults, guarantees, bank losses and household impact are separate tests. <strong>Equity losses alone cannot establish credit contagion.</strong></p>
    </div>
    <FinancialTransmission/>
    <div className="fm-dossier-toggle"><div><strong>AI financing & market transmission</strong><small>Nov 2026 source-backed event dossier · news claims are not market measurements</small></div>
      <button type="button" aria-expanded={dossiersOpen} onClick={()=>setDossiersOpen(v=>!v)}>{dossiersOpen?'Hide evidence':'Explore 3 events'} <ChevronDown size={15}/></button></div>
    {dossiersOpen&&<div className="fm-dossiers">{DOSSIERS.map(d=><button type="button" key={d.id} onClick={()=>setSelected({kind:'dossier',dossier:d})}><small>{d.date}</small><strong>{d.title}</strong><span>View source-backed summary <ArrowUpRight size={12}/></span></button>)}</div>}
    <div className="fm-footer"><Clock3 size={12}/> Check every 6h; most prices and spreads publish once per business day. <a href={SNAPSHOT} target="_blank" rel="noopener noreferrer">Full snapshot & source status <ExternalLink size={12}/></a></div>
    {selected&&<div className="fm-dialog-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setSelected(null);}}>
      <section className="fm-dialog" role="dialog" aria-modal="true" aria-label={selected.kind==='metric'?selected.metric.label:selected.kind==='dossier'?selected.dossier.title:selected.item.label}>
        <header><h3>{selected.kind==='metric'?selected.metric.label:selected.kind==='dossier'?selected.dossier.title:selected.item.label}</h3><button type="button" onClick={()=>setSelected(null)} aria-label="Close evidence panel"><X size={19}/></button></header>
        {selected.kind==='metric'?<>
          <div className="fm-dialog-stat"><strong>{fmt(selected.metric.value)} {selected.metric.unit}</strong><span>Observed {dateText(selected.metric.period)} · {selected.metric.status} · {selected.metric.cadence}</span></div>
          <Sparkline points={selected.metric.history} label={selected.metric.label}/>
          <dl><div><dt>Previous observation</dt><dd>{selected.metric.previous===null?'Unknown':fmt(selected.metric.previous)} · {selected.metric.previousPeriod?dateText(selected.metric.previousPeriod):'unknown date'}</dd></div>
            <div><dt>Five-observation change</dt><dd>{selected.metric.change5Pct===null?'Not enough history':fmt(selected.metric.change5Pct)+'%'}</dd></div>
            <div><dt>60-observation high drawdown</dt><dd>{selected.metric.drawdown60Pct===null?'Not applicable':fmt(selected.metric.drawdown60Pct)+'%'}</dd></div>
            <div><dt>Original provider</dt><dd>{selected.metric.provider} (via FRED)</dd></div></dl>
          <a href={selected.metric.sourceUrl} target="_blank" rel="noopener noreferrer">Open original indexed series <ExternalLink size={13}/></a>
          <p>End-of-day/last-published observations only. These screens do not measure loan defaults, bank losses, or private-credit positions.</p>
        </>:selected.kind==='dossier'?<>
          <p><strong>{selected.dossier.date}</strong> · reported development</p>
          <p>{selected.dossier.finding}</p><p>{selected.dossier.interpretation}</p>
          <div className="fm-dialog-links">{selected.dossier.sources.map(link=><a key={link.url} href={link.url} target="_blank" rel="noopener noreferrer">{link.label} <ExternalLink size={13}/></a>)}</div>
        </>:<>
          <p><strong>{selected.item.label}</strong> has no current validated observation in the published dataset.</p>
          <p>Source check: {selected.source?.status||'not collected'} · {selected.source?.detail||'Collector has not reported an observation yet.'}</p>
          <p>Missing evidence is not a healthy reading or a zero-value observation.</p>
          <a href={'https://fred.stlouisfed.org/series/'+selected.item.id} target="_blank" rel="noopener noreferrer">Inspect original series <ExternalLink size={13}/></a>
        </>}
      </section>
    </div>}
  </section>;
}
