import {useState} from 'react';
import {score,type Forecast,type Outcome} from './forecastCore';
const forecasts:Forecast[]=[];const outcomes:Outcome[]=[];
const targets=[
 ['US credit stress','1–4 weeks','FRED / ALFRED','Historical vintage and threshold validation'],
 ['US energy supply stress','1–4 weeks','EIA','Historical inventory and release dates'],
 ['Extreme weather','0–72 hours','NOAA GEFS','Archived ensemble forecasts and observed verification'],
 ['Cyber exploitation','1–4 weeks','CISA KEV / EPSS','Historical vulnerability cohort and outcome coverage'],
 ['Industrial supply disruption','1–12 months','UN Comtrade / World Bank','Release lag and historical outcome definitions']
];
export default function ForecastCenter({track=false}:{track?:boolean}){
 const [horizon,setHorizon]=useState('All');
 const metrics=score(forecasts,outcomes);
 return <section><div className="eyebrow">PREDICTIVE INTELLIGENCE / EVIDENCE GATED</div><div className="page-heading"><h1>{track?'Forecast track record':'Forecast intelligence center'}</h1></div>
 <div className="metric-card"><strong>{track?'Not yet scoreable':'Insufficient evidence to forecast'}</strong><span className="metric-sub">No validated point-in-time reference classes or resolved forecasts are published. Missing data is not zero risk.</span></div>
 {track?<><div className="metric-card"><strong>Resolved forecasts: {metrics.n}</strong><p>Brier score: {metrics.brier??'Not available'} · Base-rate benchmark: {metrics.benchmarkBrier??'Not available'} · Log loss: {metrics.logLoss??'Not available'}</p></div><p>Calibration, misses and probability revisions will be published when independently resolved outcomes exist.</p></>:<>
 <label>Horizon <select value={horizon} onChange={e=>setHorizon(e.target.value)}>{['All','0–72 hours','1–4 weeks','1–12 months'].map(h=><option key={h}>{h}</option>)}</select></label>
 {targets.filter(t=>horizon==='All'||t[1]===horizon).map(t=><details className="metric-card" key={t[0]}><summary>{t[0]} · {t[1]} · Unavailable</summary><p>Candidate source: {t[2]}</p><p>Required: {t[3]}</p><p>Probability and baseline withheld until validation. No command-center escalation.</p></details>)}</>}
 </section>;
}
