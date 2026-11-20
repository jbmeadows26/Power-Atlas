import {useEffect,useMemo,useState} from 'react';
import {api} from '@appdeploy/client';
import {Activity,ArrowRight,ArrowUpRight,ChevronDown,Globe2,RadioTower,RefreshCcw,ShieldAlert,TriangleAlert,Waves} from 'lucide-react';
import ResilienceWatch from './ResilienceWatch';
import GlobalSystems from './GlobalSystems';
import './riskDecisionBoard.css';

type WorldEvent={id:string;title:string;date:string;magnitude:number;sourceUrl:string;latitude:number;longitude:number};
type NaturalEvent={id:string;title:string;date:string;eventType?:string;sourceUrl:string};
type WorldSignals={checkedAt?:string;generatedAt?:string;count:number;events:WorldEvent[];naturalEvents?:NaturalEvent[];nasaStatus?:string};
type Probe={checkedAt:string;observed:number;alerts:number;errors:number};
type Resilience={schemaVersion:number;checkedAt:string;status:string;sampledCount:number;incidents:Array<{id:string;title:string;severity:string}>;screeningSignals?:Array<{id:string;title:string}>;history:Probe[];capabilities:Array<{id:string;status:string}>};
type EconomicIndicator={code:string;label:string;value:number|null;year:string|null;sourceUrl:string};
type EconomicData={status:string;checkedAt:string;indicators:EconomicIndicator[]};
type Case={id:string;code:string;date:string;title:string;topic:string;status:string;source:string;agency:string};
const SOURCE='https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json';
const official=(s:string)=>{try{const u=new URL(s);return u.protocol==='https:'?u.href:null;}catch{return null;}};
const stamp=(s?:string|null)=>s&&Number.isFinite(Date.parse(s))?new Date(s).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Date unknown';
const threshold=[
  {code:'FP.CPI.TOTL.ZG',label:'Inflation',cutoff:8,metric:'%',direction:'above'},
  {code:'SL.UEM.TOTL.ZS',label:'Unemployment',cutoff:10,metric:'%',direction:'above'},
  {code:'NY.GDP.TOTL.RT.ZS',label:'Resource dependence',cutoff:20,metric:'%',direction:'above'},
  {code:'EG.IMP.CONS.ZS',label:'Energy import exposure',cutoff:50,metric:'%',direction:'above'},
  {code:'NE.TRD.GNFS.ZS',label:'Trade exposure',cutoff:100,metric:'%',direction:'above'}
];
export default function RiskDecisionBoard({countryCode,countryName,cases,onCountryMap}:{
 countryCode:string;countryName?:string;cases:Case[];onCountryMap:()=>void;
}){
 const [revision,setRevision]=useState(0);
 const [world,setWorld]=useState<WorldSignals|null>(null),[probes,setProbes]=useState<Resilience|null>(null),[economic,setEconomic]=useState<EconomicData|null>(null);
 const [failed,setFailed]=useState<string[]>([]),[loading,setLoading]=useState(true),[details,setDetails]=useState(false);
 useEffect(()=>{
  let alive=true;setLoading(true);setFailed([]);setWorld(null);setProbes(null);setEconomic(null);
  const tasks=[
   api.get('/api/world-signals').then(r=>{if(alive)setWorld(r.data as WorldSignals);}),
   fetch(SOURCE+'?v='+Date.now(),{cache:'no-store'}).then(async r=>{if(!r.ok)throw Error('unavailable');return r.json() as Promise<Resilience>})
    .then(data=>{if(data.schemaVersion!==1||!Array.isArray(data.history))throw Error('invalid source');if(alive)setProbes(data);}),
   api.get('/api/global-systems/'+(countryCode==='all'?'WLD':countryCode)).then(r=>{if(alive)setEconomic(r.data as EconomicData);})
  ];
  Promise.allSettled(tasks).then(v=>{if(alive){setFailed(v.flatMap((x,i)=>x.status==='rejected'?[['Natural hazards','Infrastructure monitoring','Economic data'][i]]:[]));setLoading(false);}});
  return()=>{alive=false;};
 },[revision,countryCode]);
 const now=Date.now();
 const quakeSet=useMemo(()=>[...(world?.events||[])].filter(e=>typeof e.magnitude==='number'&&Number.isFinite(e.magnitude)),[world]);
 const recent=quakeSet.filter(e=>Number.isFinite(Date.parse(e.date))&&now-Date.parse(e.date)<=24*3600000&&now-Date.parse(e.date)>=0);
 const maxQuake=recent.length?Math.max(...recent.map(e=>e.magnitude)):null;
 const magnitudeBins=[{label:'M4.5–4.9',n:recent.filter(x=>x.magnitude>=4.5&&x.magnitude<5).length},{label:'M5.0–5.9',n:recent.filter(x=>x.magnitude>=5&&x.magnitude<6).length},{label:'M6.0+',n:recent.filter(x=>x.magnitude>=6).length}];
 const hits=magnitudeBins.reduce((sum,x)=>sum+x.n,0);
 const observationRows=threshold.map(t=>({...t,entry:economic?.indicators.find(x=>x.code===t.code)}));
 const reported=observationRows.filter(x=>typeof x.entry?.value==='number');
 const breached=reported.filter(x=>x.entry!.value!>x.cutoff);
 const riskNote=probes?.status==='watch'?'CORRELATED WATCH':probes?.status==='screening'?'UNCONFIRMED SCREEN':probes?'OBSERVATION ONLY':'NO PROBE FEED';
 const ageHours=probes&&Number.isFinite(Date.parse(probes.checkedAt))?(now-Date.parse(probes.checkedAt))/3600000:null;
 const stale=ageHours===null||ageHours>2;
 const history=(probes?.history||[]).slice(-10);
 const maxHistory=Math.max(1,...history.flatMap(x=>[x.observed,x.alerts,x.errors]));
 return <section className="rdb-root" aria-label="Risk summary visual dashboard">
   <header className="rdb-header">
     <div><span className="rdb-eyebrow"><ShieldAlert size={15}/> RISK INTELLIGENCE / METRICS FIRST</span>
       <h1>Risk signals, at a glance.</h1>
       <p>{countryCode==='all'?'Global research view':'Selected country: '+(countryName||countryCode)} · Live observations and historical vulnerabilities are separated. A screen is not an emergency forecast.</p>
     </div><button type="button" className="rdb-refresh" onClick={()=>setRevision(n=>n+1)} disabled={loading}><RefreshCcw size={15}/> Refresh</button>
   </header>
   <div className="rdb-headlines">
      <div><span>INFRASTRUCTURE WATCHES</span><strong>{probes?probes.incidents.length:'—'}</strong><small>{stale?'Snapshot stale or missing':riskNote}</small></div>
      <div><span>MACRO SCREENS</span><strong>{economic?breached.length+' / '+reported.length:'—'}</strong><small>Thresholds · annual observations</small></div>
      <div><span>EARTHQUAKES 24H</span><strong>{world?recent.length:'—'}</strong><small>USGS M4.5+ sampled feed</small></div>
      <div><span>STRONGEST 24H</span><strong>{maxQuake===null?'—':'M'+maxQuake.toFixed(1)}</strong><small>Largest recorded in sample</small></div>
   </div>
   {failed.length>0&&<div className="rdb-caveat" role="status"><TriangleAlert size={14}/> Unavailable sources: {failed.join(', ')}. Missing is not normal.</div>}
   <div className="rdb-charts">
    <article className="rdb-chart">
      <div className="rdb-chart-head"><div><RadioTower size={18}/><h2>Infrastructure stability</h2></div><span>{stale?'STALE / UNVERIFIED':riskNote}</span></div>
      <div className="rdb-chart-meta"><strong>{probes?.sampledCount??'—'}</strong> samples · <strong>{probes?.incidents.length??'—'}</strong> correlated watches</div>
      <div className="rdb-history" role="img" aria-label={'Infrastructure samples, errors and correlated alerts for '+history.length+' source snapshots'}>
       {history.map((p,i)=><div key={p.checkedAt+i}><div><i style={{height:Math.max(2,100*p.observed/maxHistory)+'%'}}/><b style={{height:Math.max(2,100*p.errors/maxHistory)+'%'}}/><em style={{height:Math.max(2,100*p.alerts/maxHistory)+'%'}}/></div><small>{new Date(p.checkedAt).toLocaleDateString('en-US',{month:'numeric',day:'numeric',timeZone:'UTC'})}</small></div>)}
       {!history.length&&<p className="rdb-empty">History unavailable</p>}
      </div>
      <div className="rdb-legend"><span><i/> Samples</span><span><b/> Errors</span><span><em/> Alerts</span></div>
      <small className="rdb-source">As of {stamp(probes?.checkedAt)} · <a href={SOURCE} target="_blank" rel="noopener noreferrer">Telemetry snapshot <ArrowUpRight size={12}/></a></small>
    </article>
    <article className="rdb-chart">
      <div className="rdb-chart-head"><div><Activity size={18}/><h2>Economic exposure</h2></div><span>STRUCTURAL · NOT LIVE</span></div>
      <div className="rdb-pressure">
       {observationRows.map(t=>{
        const value=t.entry?.value,available=typeof value==='number';
        return <div className="rdb-pressure-row" key={t.code}>
          <div><strong>{t.label}</strong><span>{available?value.toFixed(1)+t.metric:'Unknown'} · {t.entry?.year||'year unavailable'}</span></div>
          <div className="rdb-pressure-track" role="img" aria-label={t.label+': '+(available?value.toFixed(1)+' percent, screen at '+t.cutoff+' percent':'no data')}>
            <i style={{width:available?Math.min(100,100*value!/(t.cutoff*1.5))+'%':'0%'}} className={available&&value!>t.cutoff?'breach':''}/><b style={{left:(100/1.5)+'%'}}/>
          </div>
          {official(t.entry?.sourceUrl||'')&&<a href={t.entry!.sourceUrl} target="_blank" rel="noopener noreferrer" aria-label={'Source for '+t.label}><ArrowUpRight size={13}/></a>}
        </div>;
       })}
      </div>
      <small className="rdb-source">Tick = disclosed screening threshold · not a risk probability · <a href="https://data.worldbank.org/" target="_blank" rel="noopener noreferrer">World Bank <ArrowUpRight size={12}/></a></small>
    </article>
    <article className="rdb-chart">
      <div className="rdb-chart-head"><div><Waves size={18}/><h2>Earthquake activity</h2></div><span>USGS · 24 HOURS</span></div>
      <div className="rdb-quake-lines" role="img" aria-label={magnitudeBins.map(x=>x.label+': '+x.n).join(', ')}>
        {magnitudeBins.map(b=><div key={b.label}><span>{b.label}</span><div><i style={{width:hits?100*b.n/hits+'%':'0%'}}/></div><b>{b.n}</b></div>)}
      </div>
      <div className="rdb-note">{world?'Latest sampled feed · '+recent.length+' M4.5+ earthquakes, worldwide':'Waiting for USGS feed'}</div>
      <small className="rdb-source">USGS observation window, not a forecast · <a href="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php" target="_blank" rel="noopener noreferrer">Source feed <ArrowUpRight size={12}/></a></small>
    </article>
    <article className="rdb-chart rdb-overview">
      <div className="rdb-chart-head"><div><Globe2 size={18}/><h2>Natural hazards & blind spots</h2></div><span>NASA EONET</span></div>
      <div className="rdb-duo"><div><strong>{world?.naturalEvents?.length??'—'}</strong><span>Geolocated NASA observations</span></div><div><strong>{probes?probes.capabilities.filter(x=>x.status!=='sampled').length:'—'}</strong><span>Unobserved infrastructure capabilities</span></div></div>
      <div className="rdb-note">{world?.nasaStatus==='unavailable'?'NASA feed unavailable':world?'NASA observations are sampled events—not verified incidents or an all-clear.':'NASA source not yet checked'}</div>
      <button type="button" onClick={onCountryMap}>Explore geographic locations in Countries <ArrowRight size={14}/></button>
      <small className="rdb-source"><a href="https://eonet.gsfc.nasa.gov/" target="_blank" rel="noopener noreferrer">NASA EONET <ArrowUpRight size={12}/></a></small>
    </article>
   </div>
   <div className="rdb-evidence-footer">
    <div><strong>Detailed evidence & individual records</strong><p>Raw probe observations, economic definitions, source dates, and original earthquake/natural-hazard records. Hidden until requested.</p></div>
    <button type="button" aria-expanded={details} aria-controls="rdb-evidence" onClick={()=>setDetails(v=>!v)}>{details?'Hide details':'View source data'} <ChevronDown size={16}/></button>
   </div>
   {details&&<div className="rdb-evidence-expanded" id="rdb-evidence">
      <ResilienceWatch/>
      <GlobalSystems mode="risk" countryCode={countryCode} countryName={countryName} cases={cases}/>
      <section className="rdb-earth-records" aria-label="Individual environmental source records">
        <h2>Individual environmental observations</h2>
        <p>These are sourced hazards, not attributed security incidents. Only records from the bounded source sample are shown.</p>
        <div>{[...quakeSet,...(world?.naturalEvents||[])].slice(0,24).map(e=><article key={e.id}><div><strong>{e.title}</strong><small>{stamp(e.date)}{'magnitude'in e?' · M'+e.magnitude.toFixed(1):''}</small></div>{official(e.sourceUrl)&&<a href={e.sourceUrl} target="_blank" rel="noopener noreferrer">Original <ArrowUpRight size={12}/></a>}</article>)}</div>
        <button type="button" onClick={onCountryMap}>Open geospatial data layers in Countries <ArrowRight size={13}/></button>
      </section>
   </div>}
 </section>;
}