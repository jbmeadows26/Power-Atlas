import {useEffect,useState} from 'react';
import {score,type Forecast,type Outcome} from './forecastCore';
import './forecastCenter.css';
type Horizon='All'|'0–72 hours'|'1–4 weeks'|'1–12 months';
type Metric={id:string;label:string;value:number;unit:string;period:string;source:string;sourceUrl:string;status?:string;history?:{date?:string;period?:string;value:number}[]};
type Feed={checkedAt:string;metrics:Metric[];status?:string};
const forecasts:Forecast[]=[];const outcomes:Outcome[]=[];
const targets=[
 {name:'Regional energy disruption',domain:'Energy & Resources',h:'0–72 hours',source:'EIA / grid operators',gap:'Outage and independently observed supply-event archive'},
 {name:'Critical supply shortage',domain:'Trade & Supply Chains',h:'1–4 weeks',source:'EIA / FDA / UN Comtrade',gap:'Product-level stockouts, inventory, demand and release vintages'},
 {name:'US financial stress',domain:'Macroeconomics & Markets',h:'1–4 weeks',source:'FRED / ALFRED',gap:'Point-in-time historical vintages and preregistered threshold'},
 {name:'Industrial supply disruption',domain:'Trade & Supply Chains',h:'1–12 months',source:'UN Comtrade / World Bank',gap:'Vintage-aware trade histories and resolved events'},
 {name:'Major cyber service disruption',domain:'Defense, Security & Cyber',h:'0–72 hours',source:'CISA / independent outage records',gap:'Independent outage ground truth and historical observation windows'},
 {name:'Extreme weather',domain:'Energy & Resources',h:'0–72 hours',source:'NOAA GEFS',gap:'Archived ensemble forecasts matched to observations'}
] as const;
const choices:Horizon[]=['All','0–72 hours','1–4 weeks','1–12 months'];
const selected=['T10Y2Y','STLFSI4','sofr-rate','sofr-volume','worldbank-brent','fao-food'];
const fmt=(v:number)=>Number.isFinite(v)?v.toLocaleString('en-US',{maximumFractionDigits:4}):'Unavailable';
function Spark({metric}:{metric:Metric}){
 const values=(metric.history||[]).map(x=>x.value).filter(Number.isFinite);
 if(values.length<2)return <span className="fc-muted">History unavailable</span>;
 const min=Math.min(...values),max=Math.max(...values),span=max-min||1;
 const points=values.map((v,i)=>[4+i*232/(values.length-1),max===min?27:48-(v-min)/span*42].join(',')).join(' ');
 return <svg className="fc-spark" role="img" aria-label={metric.label+' historical reported observations'} viewBox="0 0 240 54"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="2.4" vectorEffect="non-scaling-stroke"/></svg>;
}
function Stat({name,value,note}:{name:string;value:string;note:string}){return <div className="fc-card fc-stat"><span>{name}</span><strong>{value}</strong><small>{note}</small></div>}
export default function ForecastCenter({track=false}:{track?:boolean}){
 const [horizon,setHorizon]=useState<Horizon>('All');
 const [feeds,setFeeds]=useState<Feed[]>([]);
 const [loading,setLoading]=useState(true);
 const [failed,setFailed]=useState(false);
 useEffect(()=>{let alive=true;setLoading(true);Promise.allSettled(['financial-markets','physical-early-warning'].map(async name=>{
   const response=await fetch(import.meta.env.BASE_URL+'analysis/'+name+'.json',{cache:'no-cache'});if(!response.ok)throw Error('Source unavailable');const d=await response.json();if(!Array.isArray(d.metrics)||!Number.isFinite(Date.parse(d.checkedAt)))throw Error('Invalid source snapshot');return d as Feed;
 })).then(results=>{if(alive){setFeeds(results.flatMap(x=>x.status==='fulfilled'?[x.value]:[]));setFailed(results.some(x=>x.status==='rejected'));setLoading(false);}});return()=>{alive=false}},[]);
 const metrics=score(forecasts,outcomes);
 const observations=selected.flatMap(id=>feeds.flatMap(f=>f.metrics.filter(m=>m.id===id&&Number.isFinite(m.value)&&/^https:\/\//.test(m.sourceUrl||'')).map(m=>({...m,checkedAt:f.checkedAt}))));
 const visible=targets.filter(t=>horizon==='All'||t.h===horizon);
 return <section className="fc-root" aria-label={track?'Forecast performance dashboard':'Predictive intelligence dashboard'}>
  <div className="eyebrow">PREDICTIVE INTELLIGENCE / EVIDENCE GATED</div><div className="page-heading"><h1>{track?'Forecast track record':'Forecast intelligence center'}</h1></div>
  <div className="fc-notice" role="status"><strong>{track?'Not yet scoreable':'Insufficient evidence to forecast'}</strong><span>No validated point-in-time reference classes or resolved forecasts are published. Indicators below are observations, not probabilities.</span></div>
  {track?<><div className="fc-stats"><Stat name="Resolved forecasts" value={String(metrics.n)} note="Published outcomes"/><Stat name="Brier score" value={metrics.brier===null?'—':fmt(metrics.brier)} note="Lower is better"/><Stat name="Base-rate benchmark" value={metrics.benchmarkBrier===null?'—':fmt(metrics.benchmarkBrier)} note="Same reference class"/><Stat name="Log loss" value={metrics.logLoss===null?'—':fmt(metrics.logLoss)} note="Lower is better"/></div>
  <div className="fc-card"><h2>Probability calibration</h2><svg className="fc-calibration" viewBox="0 0 340 240" role="img" aria-label="Calibration chart reference line only; no resolved forecasts">
  {[0,25,50,75,100].map(n=><g key={n}><line x1="42" x2="310" y1={194-n*1.6} y2={194-n*1.6} stroke="currentColor" opacity=".13"/><text x="35" y={198-n*1.6} textAnchor="end">{n}%</text><text x={42+n*2.68} y="211" textAnchor="middle">{n}%</text></g>)}
  <path d="M42 34 V194 H310" stroke="currentColor" fill="none"/><line x1="42" y1="194" x2="310" y2="34" stroke="#94a3b8" strokeDasharray="5 5"/><text x="176" y="234" textAnchor="middle">Predicted probability</text><text transform="translate(11 114) rotate(-90)" textAnchor="middle">Observed frequency</text></svg><p className="fc-muted">Dashed line: perfect calibration reference. No model points until outcomes are resolved.</p></div>
  <div className="fc-card"><h2>Outcome ledger</h2><p>No resolved forecasts. Hits, misses, revisions and voids will remain visible when available.</p></div></>:<>
  <div className="fc-stats"><Stat name="Open forecasts" value={String(forecasts.length)} note="Published probabilities"/><Stat name="Above 60%" value="—" note="No calibrated probabilities"/><Stat name="Resolved" value={String(metrics.n)} note="Independently scored"/></div>
  <div className="fc-controls" role="group" aria-label="Forecast horizon">{choices.map(h=><button type="button" key={h} aria-pressed={horizon===h} onClick={()=>setHorizon(h)}>{h}</button>)}</div>
  <div className="fc-grid">{visible.map(t=><details className="fc-card fc-target" key={t.name}><summary><div className="fc-summary-main"><span><strong>{t.name}</strong><small>{t.domain} · {t.h}</small></span><b aria-label="Probability unavailable">—</b></div><div className="fc-unavailable" aria-label="Probability not available"><span>Probability unavailable</span></div><div className="fc-meta"><span>Base rate: —</span><span>Change: —</span></div></summary><div className="fc-detail"><p>Candidate source: {t.source}</p><p>Required: {t.gap}</p><p>No resolution contract or forecast published.</p></div></details>)}</div>
  <h2>Leading indicator observations</h2><p className="fc-muted">Source-dated U.S. and global benchmarks. Historical movements are not forecast probabilities.</p>
  {loading&&<p role="status">Loading published indicators…</p>}{failed&&<p role="status">Some indicator snapshots could not be loaded; remaining observations retain their original dates.</p>}
  <div className="fc-grid">{observations.map(m=><article className="fc-card fc-observation" key={m.id}><span className="fc-muted">{m.label}</span><strong>{fmt(m.value)} <small>{m.unit}</small></strong><Spark metric={m}/><small>Observed: {m.period} · Retrieved: {m.checkedAt.slice(0,16).replace('T',' ')} UTC</small><small>{m.status&&m.status!=='ok'?m.status+' · ':''}<a href={m.sourceUrl} target="_blank" rel="noreferrer">{m.source}</a></small></article>)}</div>
  {!loading&&!observations.length&&<p className="fc-muted">No usable source observations loaded.</p>}
  </>}
 </section>;
}
