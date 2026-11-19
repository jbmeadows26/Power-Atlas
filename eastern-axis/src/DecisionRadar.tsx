import {useEffect,useMemo,useState} from 'react';
import {api} from '@appdeploy/client';
import {Activity,AlertTriangle,ArrowRight,ArrowUpRight,BarChart3,Database,Globe2,Landmark,RefreshCcw,Shield,Ship,Wifi} from 'lucide-react';
import './decision-radar.css';

type Metric={
  id:string;label:string;value:number;previous:number;unit:string;period:string;previousPeriod:string;
  changePct:number;changeBps?:number|null;changePp?:number|null;
  compareMode?:'percent'|'basis-points'|'percentage-points';group:string;source:string;sourceUrl:string;
};
type Physical={schemaVersion:number;checkedAt:string|null;status:string;metrics:Metric[]};
type Corridor={id:string;name:string;dailyAverage:number|null;baselineDailyAverage:number|null;percentChange:number|null;recentDays:number;baselineDays:number};
type Supply={sourceStatus:string;sourceDate:string|null;checkedAt:string;dataAgeDays:number|null;corridors:Corridor[];source:string};
type Operation={id:string;title:string;published:string;kind?:string;state?:string;publisher:string;url:string;roles:{code:string;role:string}[]};
type Defense={reviewedAsOf:string;operations:Operation[];assessments:{id:string;title:string;published:string;countries:string[]}[]};
type Resilience={schemaVersion:number;checkedAt:string;status:string;incidents:{id:string;title:string;severity:string}[];screeningSignals?:{id:string;title:string}[];history?:{checkedAt:string;errors:number;alerts:number;observed:number}[];capabilities:{status:string}[]};
type Workspace='Early warning'|'Supply chain'|'Risk watch'|'Defense intelligence'|'Countries';
type Key='finance'|'trade'|'security'|'infrastructure';
type Mode='all'|'screens'|'gaps';
type Lane={key:Key;title:string;hint:string;detail:string;workspace:Workspace;status:'review'|'stale'|'reference'|'observed'|'gap';screens:number};
const RESILIENCE='https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json';
const day=(value?:string|null)=>value&&Number.isFinite(Date.parse(value))?new Date(value).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Date unknown';
const ago=(value?:string|null,now=Date.now())=>!value||!Number.isFinite(Date.parse(value))?null:Math.max(0,now-Date.parse(value));
const fmt=(n:number,decimals=1)=>new Intl.NumberFormat('en-US',{maximumFractionDigits:decimals}).format(n);
const unit=(m:Metric)=>m.compareMode==='basis-points'?'bps':m.compareMode==='percentage-points'?'pp':'%';
const change=(m:Metric)=>m.compareMode==='basis-points'?(m.changeBps??0):m.compareMode==='percentage-points'?(m.changePp??0):m.changePct;
const screen=(m:Metric)=>Number.isFinite(change(m))&&Math.abs(change(m))>=(m.compareMode==='basis-points'?20:m.compareMode==='percentage-points'?5:10);
const https=(value?:string)=>{try{const u=new URL(value||'');return u.protocol==='https:'?u.href:null;}catch{return null;}};
const sortChanges=(list:Metric[])=>[...list].sort((a,b)=>Number(screen(b))-Number(screen(a))||Math.abs(change(b))-Math.abs(change(a)));
const countriesToRegions:Record<string,string[]>={
  IR:['regional:persian-gulf','regional:strait-of-hormuz'],OM:['regional:persian-gulf','regional:strait-of-hormuz'],
  AE:['regional:persian-gulf','regional:strait-of-hormuz'],SA:['regional:persian-gulf'],QA:['regional:persian-gulf'],
  CN:['regional:taiwan-strait','regional:east-asia'],TW:['regional:taiwan-strait','regional:east-asia'],
  JP:['regional:east-asia'],KP:['regional:east-asia'],KR:['regional:east-asia'],
  RU:['regional:baltic-sea'],EE:['regional:baltic-sea'],FI:['regional:baltic-sea'],LV:['regional:baltic-sea'],LT:['regional:baltic-sea'],
  TR:['regional:eastern-mediterranean'],CY:['regional:eastern-mediterranean'],GR:['regional:eastern-mediterranean']
};
/** The scope tag on regional aviation observations is context, not state attribution. */
function relevance(m:Metric,code:string){
  if(code==='all')return true;
  if(m.group==='global'||m.group==='US'&&m.id.startsWith('sofr-'))return true;
  if(m.group===code)return true;
  return !!countriesToRegions[code]?.includes(m.group);
}
function TwoPoint({previous,current,previousLabel,currentLabel}:{previous:number;current:number;previousLabel:string;currentLabel:string}){
  const scale=Math.max(1,Math.abs(previous),Math.abs(current));
  const max=(n:number)=>Math.max(2,Math.min(100,100*Math.abs(n)/scale))+'%';
  return <div className="dr-pair" role="img" aria-label={previousLabel+': '+fmt(previous,2)+'; '+currentLabel+': '+fmt(current,2)}>
    <div><small>{previousLabel}</small><span><i style={{width:max(previous)}}/></span><b>{fmt(previous,2)}</b></div>
    <div><small>{currentLabel}</small><span><i style={{width:max(current)}}/></span><b>{fmt(current,2)}</b></div>
  </div>;
}
function MetricMove({m}:{m:Metric}){
  const signed=change(m);
  const href=https(m.sourceUrl);
  return <div className={'dr-move '+(screen(m)?'dr-move-screen':'')} key={m.id}>
    <div className="dr-move-top"><strong>{m.label}</strong><span className={screen(m)?'dr-change-flag':'dr-change'}>{signed>0?'+':''}{fmt(signed,1)} {unit(m)}</span></div>
    <TwoPoint previous={m.previous} current={m.value} previousLabel={m.previousPeriod} currentLabel={m.period}/>
    <div className="dr-move-foot"><span>{m.unit} · {m.group.startsWith('regional:')?'Regional aviation sample':m.group==='global'?'Global benchmark':m.group==='US'?'US benchmark':m.group+' observation'}</span>
      {href&&<a href={href} target="_blank" rel="noopener noreferrer" title={m.source}>{m.source} <ArrowUpRight size={11}/></a>}</div>
  </div>;
}
export default function DecisionRadar({countryCode,countryName,onNavigate}:{
  countryCode:string;countryName?:string;onNavigate:(target:Workspace,focus?:'funding'|'commodities'|'gnss')=>void;
}){
 const [physical,setPhysical]=useState<Physical|null>(null),[supply,setSupply]=useState<Supply|null>(null);
 const [defense,setDefense]=useState<Defense|null>(null),[resilience,setResilience]=useState<Resilience|null>(null);
 const [failed,setFailed]=useState<string[]>([]),[loading,setLoading]=useState(true),[refresh,setRefresh]=useState(0);
 const [mode,setMode]=useState<Mode>('all');
 const [now,setNow]=useState(()=>Date.now());
 useEffect(()=>{const t=window.setInterval(()=>setNow(Date.now()),60000);return()=>window.clearInterval(t);},[]);
 useEffect(()=>{
   let alive=true;setLoading(true);setFailed([]);setPhysical(null);setSupply(null);setDefense(null);setResilience(null);
   const requests=[
     fetch(import.meta.env.BASE_URL+'analysis/physical-early-warning.json?t='+Date.now(),{cache:'no-store'})
       .then(async r=>{if(!r.ok)throw Error('Physical measurements unavailable');return r.json() as Promise<Physical>;})
       .then(v=>{if(v.schemaVersion!==1||!Array.isArray(v.metrics))throw Error('Invalid market snapshot');if(alive)setPhysical(v);}),
     api.get('/api/supply-chain/'+encodeURIComponent(countryCode)).then(r=>{
       const value=r.data as Supply;if(!Array.isArray(value.corridors))throw Error('Invalid trade data');if(alive)setSupply(value);}),
     api.get('/api/defense-intel').then(r=>{const value=r.data as Defense;if(!Array.isArray(value.operations))throw Error('Invalid defense data');if(alive)setDefense(value);}),
     fetch(RESILIENCE+'?t='+Date.now(),{cache:'no-store'}).then(async r=>{
       if(!r.ok)throw Error('Resilience feed unavailable');return r.json() as Promise<Resilience>;
     }).then(v=>{if(v.schemaVersion!==1||!Array.isArray(v.capabilities))throw Error('Invalid resilience snapshot');if(alive)setResilience(v);})
   ];
   Promise.allSettled(requests).then(results=>{if(alive){
     setFailed(results.flatMap((r,i)=>r.status==='rejected'?[['Finance/commodities','Trade routes','Defense reports','Infrastructure probes'][i]]:[]));
     setLoading(false);
   }});
   return()=>{alive=false;};
 },[countryCode,refresh]);
 const metrics=useMemo(()=>(physical?.metrics||[]).filter(m=>Number.isFinite(m.value)&&Number.isFinite(m.previous)&&relevance(m,countryCode)),[physical,countryCode]);
 const finance=sortChanges(metrics.filter(m=>m.id.startsWith('sofr-'))).slice(0,2);
 const commodities=sortChanges(metrics.filter(m=>m.id.startsWith('worldbank-')||m.id.startsWith('fao-'))).slice(0,2);
 const gnss=sortChanges(metrics.filter(m=>m.id.startsWith('gps-'))).slice(0,2);
 const corridor=useMemo(()=>[...(supply?.corridors||[])].filter(c=>c.percentChange!==null&&c.dailyAverage!==null&&c.baselineDailyAverage!==null)
   .sort((a,b)=>(a.percentChange||0)-(b.percentChange||0))[0],[supply]);
 const operations=useMemo(()=>(defense?.operations||[]).filter(o=>countryCode==='all'||o.roles.some(r=>r.code===countryCode))
   .sort((a,b)=>b.published.localeCompare(a.published)).slice(0,2),[defense,countryCode]);
 const agePhysical=ago(physical?.checkedAt,now);
 const stalePhysical=physical!==null&&(agePhysical===null||agePhysical>4*86400000);
 const tradeStale=supply!==null&&(supply.sourceStatus!=='observed'||supply.dataAgeDays===null||supply.dataAgeDays>10);
 const resilienceAge=ago(resilience?.checkedAt,now);
 const resilienceStale=resilience!==null&&(resilienceAge===null||resilienceAge>2*3600000);
 const latestScreen=gnss.filter(screen).length;
 const screened=(stalePhysical?0:metrics.filter(screen).length)+(!tradeStale&&corridor?.percentChange!==undefined&&corridor.percentChange!==null&&corridor.percentChange<=-20?1:0);
 const gapCount=failed.length+(stalePhysical?1:0)+(tradeStale?1:0)+(resilienceStale?1:0);
 const lanes:Lane[]=[
  {key:'finance',title:'Finance',hint:'Funding + market transmission',workspace:'Early warning',screens:finance.filter(screen).length,detail:'Exposure check: funding costs, refinancing, liquidity',status:!physical?'gap':stalePhysical?'stale':finance.some(screen)?'review':'observed'},
  {key:'trade',title:'Trade & essential goods',hint:'Shipping + fuel + food',workspace:'Supply chain',screens:commodities.filter(screen).length+(corridor?.percentChange!==null&&corridor?.percentChange!==undefined&&corridor.percentChange<=-20?1:0),detail:'Exposure check: routes, fuel, food, industrial inputs',status:!physical&&!supply?'gap':stalePhysical&&tradeStale?'stale':commodities.some(screen)||(corridor?.percentChange??0)<=-20&&!!corridor?'review':tradeStale?'stale':'observed'},
  {key:'infrastructure',title:'Infrastructure & survival',hint:'GNSS + networks + grid proxies',workspace:'Risk watch',screens:latestScreen+(resilience?.screeningSignals?.length||0),detail:'Exposure check: navigation, communications, grid',status:!physical&&!resilience?'gap':resilienceStale?'stale':latestScreen>0||(resilience?.screeningSignals?.length||0)>0||(resilience?.incidents?.length||0)>0?'review':'observed'},
  {key:'security',title:'Military & intelligence',hint:'Documented operations + reporting',workspace:'Defense intelligence',screens:0,detail:'Check official current advisories before security decisions',status:!defense?'gap':'reference'}
 ];
 const sorted=[...lanes].sort((a,b)=>({review:0,stale:1,gap:2,observed:3,reference:4}[a.status])-({review:0,stale:1,gap:2,observed:3,reference:4}[b.status]));
 const shown=sorted.filter(l=>mode==='all'||(mode==='screens'?l.status==='review':l.status==='gap'||l.status==='stale'));
 const sourcesAvailable=[physical,supply,resilience,defense].filter(Boolean).length;
 return <section className="dr-root" aria-label="Decision radar by domain">
   <header className="dr-head">
     <div><span className="dr-kicker"><Activity size={15}/> DECISION RADAR / OBSERVED CHANGE</span>
       <h1>What needs <em>attention now?</em></h1><p>{countryCode==='all'?'Global source measurements':'Country focus: '+(countryName||countryCode)+' · worldwide benchmarks explicitly labeled'} · Compare changes, verify exposure, open original evidence.</p>
     </div><button className="dr-refresh" type="button" onClick={()=>setRefresh(v=>v+1)} disabled={loading}><RefreshCcw size={14}/> Refresh data</button>
   </header>
   <div className="dr-briefing">
     <div><span>MEASURED CHANGE SCREENS</span><strong>{physical||supply?screened:'—'}</strong><small>Movement thresholds; not confirmed threats</small></div>
     <div><span>FRESHNESS / ACCESS GAPS</span><strong>{loading?'…':gapCount}</strong><small>Missing feeds + stale collections</small></div>
     <div><span>FETCHED SOURCE FAMILIES</span><strong>{sourcesAvailable}/4</strong><small>Finance · trade · defense · resilience</small></div>
     <div><span>MEASUREMENT AS OF</span><strong className="dr-asof">{day(physical?.checkedAt)}</strong><small>Dates on each comparison below</small></div>
   </div>
   <div className="dr-toolbar"><div><button type="button" className={mode==='all'?'active':''} aria-pressed={mode==='all'} onClick={()=>setMode('all')}>All domains</button><button type="button" className={mode==='screens'?'active':''} aria-pressed={mode==='screens'} onClick={()=>setMode('screens')}>Review triggers</button><button type="button" className={mode==='gaps'?'active':''} aria-pressed={mode==='gaps'} onClick={()=>setMode('gaps')}>Blind spots</button></div><span>Sorted by review need · not a probability ranking</span></div>
   {failed.length>0&&<p className="dr-gap-alert" role="status"><AlertTriangle size={14}/> Unavailable inputs: {failed.join(', ')}. No zeros or safe conditions inferred.</p>}
   <div className="dr-grid">
    {shown.map(l=><article className={'dr-lane dr-'+l.key} key={l.key}>
      <div className="dr-lane-heading"><span>{l.key==='finance'?<Landmark size={19}/>:l.key==='trade'?<Ship size={19}/>:l.key==='security'?<Shield size={19}/>:<Wifi size={19}/>}</span><div><small>{l.hint}</small><h2>{l.title}</h2></div><b className={'dr-tag dr-tag-'+l.status}>{l.status==='review'?'REVIEW':l.status==='stale'?'STALE':l.status==='gap'?'NO DATA':l.status==='reference'?'SOURCE LOG':'OBSERVED'}</b></div>
      {l.key==='finance'&&<div className="dr-moves">{finance.map(m=><MetricMove m={m} key={m.id}/>)}{!finance.length&&<p className="dr-empty">No verified funding measurements in scope.</p>}</div>}
      {l.key==='trade'&&<div className="dr-moves">
        {corridor&&<div className={'dr-move '+((corridor.percentChange??0)<=-20?'dr-move-screen':'')}>
          <div className="dr-move-top"><strong>{corridor.name} · vessel transits/day</strong><span className={(corridor.percentChange??0)<=-20?'dr-change-flag':'dr-change'}>{(corridor.percentChange??0)>0?'+':''}{fmt(corridor.percentChange??0)}%</span></div>
          <TwoPoint previous={corridor.baselineDailyAverage!} current={corridor.dailyAverage!} previousLabel="Prior 7d" currentLabel="Recent 7d"/>
          <div className="dr-move-foot"><span>{corridor.baselineDays} / {corridor.recentDays} reported days · {day(supply?.sourceDate)}</span><a href={https(supply?.source)||'https://portwatch.imf.org/'} target="_blank" rel="noopener noreferrer">IMF PortWatch <ArrowUpRight size={11}/></a></div>
        </div>}
        {commodities.map(m=><MetricMove m={m} key={m.id}/>)}{!corridor&&!commodities.length&&<p className="dr-empty">No comparable observed trade or input prices.</p>}
      </div>}
      {l.key==='infrastructure'&&<div className="dr-moves">
        {gnss.map(m=><MetricMove m={m} key={m.id}/>)}
        {resilience&&<div className="dr-snapshot"><div><strong>{resilienceStale?'Probe snapshot stale':(resilience.screeningSignals?.length||0)+(resilience.incidents?.length||0)+' screening/correlated indicators'}</strong><span>Independent telemetry · {day(resilience.checkedAt)}</span></div>
          {resilience.history&&resilience.history.length>0&&<div className="dr-history" role="img" aria-label={'Reported probe errors across '+resilience.history.length+' snapshots'}>{resilience.history.slice(-9).map((h,i)=><span key={h.checkedAt+i} style={{height:Math.max(5,100*Math.max(0,h.errors)/(Math.max(1,...resilience.history!.map(x=>x.errors))))+'%'}}/>)}</div>}
        </div>}
        {!gnss.length&&!resilience&&<p className="dr-empty">No in-scope GNSS measurements or probe feed.</p>}
      </div>}
      {l.key==='security'&&<div className="dr-report-list">{operations.map(o=><div key={o.id}><strong>{o.title}</strong><span>{day(o.published)} · {o.publisher} · historical reporting</span><a href={https(o.url)||'#'} target="_blank" rel="noopener noreferrer">Original report <ArrowUpRight size={11}/></a></div>)}{!operations.length&&<p className="dr-empty">No country-tagged military operation report in the reviewed index; activity not determined.</p>}</div>}
      <footer><span>{l.status==='review'?l.screens+' deviation screen(s) to verify':l.detail}</span><button type="button" onClick={()=>onNavigate(l.workspace,l.key==='finance'?'funding':undefined)}>Analyze <ArrowRight size={13}/></button></footer>
    </article>)}
    {shown.length===0&&<p className="dr-empty">No domains match this filter in the current source snapshot. This is not an all-clear.</p>}
   </div>
   <p className="dr-footnote"><Database size={12}/> Screens: price/volume ±10%, SOFR ±20 basis points, GNSS ±5 percentage points, or PortWatch transit decline ≥20%. Screening thresholds are analyst review prompts, not validated predictive signals. Financial and aviation benchmarks retain their original geographic scope. Source records and military reports are not incident alerts.</p>
 </section>;
}