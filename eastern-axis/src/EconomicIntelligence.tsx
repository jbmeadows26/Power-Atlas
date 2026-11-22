import { useEffect, useState } from 'react';
import { Activity, ArrowRight, BarChart3, BrainCircuit, Database, Globe2, Landmark, Layers3, PackageSearch, Radio, RefreshCcw, ShieldAlert, Ship } from 'lucide-react';
import { api } from '@appdeploy/client';
import GlobalSystems from './GlobalSystems';
import SupplyChain from './SupplyChain';
import PhysicalEarlyWarning from './PhysicalEarlyWarning';
import RiskDecisionBoard from './RiskDecisionBoard';
import FinancialMarkets from './FinancialMarkets';
import DecisionRadar from './DecisionRadar';
import ShortageForecasts from './ShortageForecasts';
import './economicIntelligence.css';

type Case = { id:string; code:string; title:string; date:string; topic:string; status:string; source:string; agency:string };
export type EconomicFocus = 'overview' | 'systems' | 'supply' | 'shortages' | 'signals' | 'risk';
type Indicator = {code:string;value:number|null;year:string|null;label:string};
type Systems = {status:string;checkedAt:string;covered:number;requested:number;indicators:Indicator[];warning?:string|null};
type Corridor = {id:string;name:string;percentChange:number|null;recentDays:number;baselineDays:number};
type Supply = {sourceStatus:string;checkedAt:string;sourceDate:string|null;corridors:Corridor[]};
type MarketMetric = {id:string;label:string;value:number;period:string;unit:string;status:string;sourceUrl:string};
type Markets = {checkedAt:string;status:string;metrics:MarketMetric[];sources:unknown[]};
type EarlyMetric = {id:string;group:string;changePct:number;changeBps?:number|null;changePp?:number|null;compareMode?:string};
type Early = {checkedAt:string|null;status:string;metrics:EarlyMetric[];sources:unknown[]};
type Triage = {generatedAt:string;summary:{observed:number;screened:number;reviewed:number;monitoring:number;elevated:number;historyReady:number};model:{status:string};reviews:unknown[]};
type Probe = {schemaVersion:number;checkedAt:string;status:string;incidents:unknown[];sampledCount?:number;history:unknown[]};
type Shortages = {schemaVersion:number;generatedAt:string;summary:{products:number;crossSourceWatch:number;inputCostWatch:number;transitWatch:number;dataGaps:number;commandEligible:number}};
type Picture = {systems?:Systems;supply?:Supply;shortages?:Shortages;markets?:Markets;early?:Early;triage?:Triage;probe?:Probe};
type Props = {
  countryCode:string;countryName?:string;cases:Case[];
  onCountryMap:()=>void;onDefense:()=>void;initialFocus?:EconomicFocus;
  initialMeasurementFilter?:'all'|'funding'|'commodities'|'gnss';
  hideNavigation?:boolean;onFocusChange?:(focus:EconomicFocus)=>void;
};
const PROBES = 'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json';
const fmt = (n:number)=>new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(n);
const date = (s?:string|null)=>s&&Number.isFinite(Date.parse(s))
  ? new Date(s).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'})
  : 'Not verified';
const ageDays = (s?:string|null)=>s&&Number.isFinite(Date.parse(s))?Math.max(0,(Date.now()-Date.parse(s))/86400000):null;
const pct = (n:number,d:number)=>d>0?Math.max(0,Math.min(100,100*n/d)):0;
function coverage(value:number|undefined,total:number|undefined,label:string) {
  if(typeof value!=='number'||typeof total!=='number')return <div className="ei-coverage unavailable"><span>Source coverage unavailable</span></div>;
  return <div className="ei-coverage">
    <div><span>{label}</span><strong>{value}/{total}</strong></div>
    <div className="ei-track" role="img" aria-label={value+' of '+total+' '+label}><i style={{width:pct(value,total)+'%'}}/></div>
  </div>;
}
const screens = (m:EarlyMetric)=>m.compareMode==='basis-points'?Math.abs(m.changeBps??0)>=20:
  m.compareMode==='percentage-points'?Math.abs(m.changePp??0)>=5:Math.abs(m.changePct)>=10;
const sourceStatus=(s?:string,checked?:string|null,maxDays=7)=>{
  if(!s||s==='unavailable'||s==='error')return 'UNAVAILABLE';
  const age=ageDays(checked);
  if(age===null||age>maxDays)return 'HISTORICAL';
  if(s==='partial'||s==='stale')return 'PARTIAL / STALE';
  return 'SOURCE-DATED';
};
export default function EconomicIntelligence({countryCode,countryName,cases,onCountryMap,onDefense,initialFocus='overview',initialMeasurementFilter='all',hideNavigation=false,onFocusChange}:Props) {
  const [focus,setFocus]=useState<EconomicFocus>(initialFocus);
  const [signalView,setSignalView]=useState<'signals'|'markets'>('signals');
  const [activeMeasurementFilter,setActiveMeasurementFilter]=useState<'all'|'funding'|'commodities'|'gnss'>(initialMeasurementFilter);
  useEffect(()=>setActiveMeasurementFilter(initialMeasurementFilter),[initialMeasurementFilter]);
  const [picture,setPicture]=useState<Picture>({});
  const [loading,setLoading]=useState(true);
  const [refresh,setRefresh]=useState(0);
  useEffect(()=>setFocus(initialFocus),[initialFocus]);
  useEffect(()=>{onFocusChange?.(focus);},[focus]);
  useEffect(()=>{
    let active=true;
    setLoading(true);setPicture({});
    const base=String(import.meta.env.BASE_URL||'/');
    const json=async(url:string)=>{
      const res=await fetch(url,{cache:'no-store'});
      if(!res.ok)throw Error('Source unavailable: '+res.status);
      return res.json();
    };
    const requests=[
      api.get('/api/global-systems/'+encodeURIComponent(countryCode==='all'?'WLD':countryCode)).then(r=>r.data),
      api.get('/api/supply-chain/'+encodeURIComponent(countryCode)).then(r=>r.data),
      json(base+'analysis/product-shortage-outlook.json'),
      json(base+'analysis/financial-markets.json'),
      json(base+'analysis/physical-early-warning.json'),
      json(base+'analysis/early-warning-triage.json'),
      json(PROBES)
    ];
    Promise.allSettled(requests).then(results=>{
      if(!active)return;
      const pick=(i:number):any=>results[i].status==='fulfilled'?(results[i] as PromiseFulfilledResult<unknown>).value:undefined;
      const sys=pick(0),sup=pick(1),short=pick(2),mar=pick(3),ear=pick(4),tri=pick(5),pro=pick(6);
      setPicture({
        systems:sys&&Array.isArray(sys.indicators)?sys:undefined,
        supply:sup&&Array.isArray(sup.corridors)?sup:undefined,
        shortages:short?.schemaVersion===1&&short.summary&&typeof short.summary.products==='number'?short:undefined,
        markets:mar?.schemaVersion===1&&Array.isArray(mar.metrics)?mar:undefined,
        early:ear?.schemaVersion===1&&Array.isArray(ear.metrics)?ear:undefined,
        triage:tri?.schemaVersion===1&&Array.isArray(tri.reviews)&&tri.summary?tri:undefined,
        probe:pro?.schemaVersion===1&&Array.isArray(pro.history)&&Array.isArray(pro.incidents)?pro:undefined
      });
      setLoading(false);
    });
    return()=>{active=false;};
  },[countryCode,refresh]);
  const {systems,supply,shortages,markets,early,triage,probe}=picture;
  const scope=countryCode==='all'?'Worldwide':countryName||countryCode;
  const observed=systems?.indicators.filter(x=>typeof x.value==='number')||[];
  const inflation=systems?.indicators.find(x=>x.code==='FP.CPI.TOTL.ZG');
  const corridors=supply?.corridors.filter(c=>typeof c.percentChange==='number'&&c.recentDays>=5&&c.baselineDays>=5)||[];
  const falling=[...corridors].filter(x=>x.percentChange!<0).sort((a,b)=>a.percentChange!-b.percentChange!)[0];
  const marketRows=markets?.metrics.filter(m=>typeof m.value==='number'&&Number.isFinite(m.value))||[];
  const earlyRows=early?.metrics.filter(m=>countryCode==='all'||m.group==='global'||m.group===countryCode)||[];
  const alerts=earlyRows.filter(screens);
  const age=ageDays(probe?.checkedAt);
  const reviewAge=ageDays(triage?.generatedAt);
  const reviewFresh=reviewAge!==null&&reviewAge<=3;
  const probeFresh=age!==null&&age<=2/24;
  const lanes=[
    {key:'systems' as const,title:'Economy & energy',description:'Growth, inflation, jobs, energy dependency and resource exposure.',Icon:Globe2,
      number:systems?observed.length+' / '+systems.indicators.length:'—',measure:'reported indicators',status:sourceStatus(systems?.status,systems?.checkedAt,35),
      detail:inflation&&typeof inflation.value==='number'?'Inflation '+fmt(inflation.value)+'% · '+(inflation.year||'year unknown'):'No verified inflation reading'},
    {key:'supply' as const,title:'Supply chains',description:'Shipping corridors, trade chokepoints and downstream dependencies.',Icon:Ship,
      number:supply?corridors.length+' / '+supply.corridors.length:'—',measure:'comparable corridors',status:sourceStatus(supply?.sourceStatus,supply?.checkedAt,12),
      detail:falling?'Largest decline: '+falling.name+' ('+fmt(falling.percentChange!)+'%)':'No comparable transit decline'},
    {key:'shortages' as const,title:'Product shortages',description:'Predictive input-pressure scenarios, route changes, missing inventory evidence.',Icon:PackageSearch,
      number:shortages?shortages.summary.crossSourceWatch:'—',measure:'cross-source watch scenarios',status:sourceStatus(shortages?'ok':'unavailable',shortages?.generatedAt,3),
      detail:shortages?shortages.summary.products+' product groups · '+shortages.summary.inputCostWatch+' input cost watches':'Forecast model data unavailable'},
    {key:'signals' as const,title:'Markets & early warning',description:'Market movements, screened anomalies and AI analyst triage.',Icon:Activity,
      number:triage?triage.summary.screened:'—',measure:'global review candidates',status:sourceStatus(early?.status,early?.checkedAt,4),
      detail:triage?'AI reviewed '+triage.summary.reviewed+' · elevated '+(reviewFresh?triage.summary.elevated:'unverified')+' globally':'AI triage report unavailable'},
    {key:'risk' as const,title:'Systemic risk',description:'Infrastructure reliability, hazards and country pressure screens.',Icon:ShieldAlert,
      number:probe&&probeFresh?probe.incidents.length:'—',measure:'global correlated watches',status:sourceStatus(probe?.status,probe?.checkedAt,2/24),
      detail:probe?'Telemetry checked '+date(probe.checkedAt)+(probeFresh?' · recent':' · stale'):'No probe telemetry verified'}
  ];
  return <section className="ei-root" aria-label="Unified economic intelligence">
    <header className="ei-heading">
      <div><div className="ei-kicker"><Layers3 size={14}/> SYSTEM INTELLIGENCE / ECONOMIC INTELLIGENCE</div>
        <h1>Economic <em>intelligence.</em></h1>
        <p>One picture of economic pressure, product shortage scenarios, trade dependencies, market movements and systemic risk. Observations and uncalibrated forecasts are clearly labeled.</p>
      </div>
      <div className="ei-heading-right"><span>GEOGRAPHIC CONTEXT</span><strong>{scope}</strong>
        <small>Global benchmarks remain labeled; geographic context is not attribution.</small>
        <button type="button" onClick={()=>setRefresh(v=>v+1)} disabled={loading}><RefreshCcw size={14}/> {loading?'Checking…':'Refresh overview'}</button>
      </div>
    </header>
    <div className="ei-pulse" aria-label="Source-dated intelligence pulse">
      <div><span>MACRO INDICATORS</span><strong>{systems?observed.length:'—'}<small>{systems?' / '+systems.indicators.length:''}</small></strong><small>{systems?'World Bank and disclosed alternatives':'Feed unavailable'}</small></div>
      <div><span>TRADE COMPARISONS</span><strong>{supply?corridors.length:'—'}</strong><small>IMF PortWatch · 7d vs 7d</small></div>
      <div><span>PRODUCT SHORTAGE WATCH</span><strong>{shortages?shortages.summary.crossSourceWatch:'—'}</strong><small>{shortages?shortages.summary.products+' categories screened':'Forecast feed unavailable'}</small></div>
      <div><span>MARKET SERIES</span><strong>{markets?marketRows.length:'—'}</strong><small>US / global financial benchmarks</small></div>
      <div><span>CHANGE SCREENS</span><strong>{early?alerts.length:'—'}</strong><small>{countryCode==='all'?'All tracked regions':'Country + global benchmark'} · not alerts</small></div>
      <div><span>AI REVIEWED</span><strong>{triage?triage.summary.reviewed:'—'}<small>{triage?' / '+triage.summary.screened:''}</small></strong><small>Worldwide review candidates · {date(triage?.generatedAt)}</small></div>
    </div>
    {loading&&<div className="ei-source-note"><Radio size={15}/> Checking independently dated data sources. Missing readings stay unavailable.</div>}
    {!loading&&(!systems||!supply||!shortages||!markets||!early||!triage||!probe)&&<div className="ei-source-note ei-source-limited"><Database size={15}/> Partial source coverage: {[
      !systems&&'macro',!supply&&'shipping',!shortages&&'shortage outlook',!markets&&'markets',!early&&'measurements',!triage&&'AI review',!probe&&'infrastructure'
    ].filter(Boolean).join(', ')} unavailable. No missing measurements have been replaced with zero.</div>}
    {!hideNavigation && <nav className="ei-tabs" aria-label="Economic intelligence views">
      {([
        ['overview','At a glance',BarChart3],
        ['systems','Economy & energy',Globe2],
        ['supply','Supply chains',Ship],
        ['shortages','Product shortages',PackageSearch],
        ['signals','Markets & early warning',Activity],
        ['risk','Systemic risk',ShieldAlert],
      ] as const).map(([key,label,Icon])=><button type="button" key={key} onClick={()=>setFocus(key)} className={focus===key?'active':''} aria-current={focus===key?'page':undefined}><Icon size={16}/>{label}</button>)}
    </nav>}
    {focus==='overview'&&<>
      <div className="ei-overview-intro"><div><strong>Five connected intelligence domains</strong><span>Compact coverage first. Select a domain for its complete charts, source links and filters.</span></div><span>SOURCE COVERAGE ≠ THREAT LEVEL</span></div>
      <div className="ei-grid">{lanes.map(l=><button key={l.key} type="button" className="ei-domain" onClick={()=>setFocus(l.key)}>
        <div className="ei-domain-top"><span><l.Icon size={20}/></span><small>{l.status}</small></div>
        <h2>{l.title}</h2><p>{l.description}</p>
        <div className="ei-domain-number"><strong>{loading?'…':l.number}</strong><span>{l.measure}</span></div>
        <div className="ei-domain-detail">{loading?'Fetching observations…':l.detail}</div>
        {l.key==='systems'&&coverage(systems?observed.length:undefined,systems?.indicators.length,'Indicators reported')}
        {l.key==='supply'&&coverage(supply?corridors.length:undefined,supply?.corridors.length,'Corridors comparable')}
        {l.key==='shortages'&&coverage(shortages?shortages.summary.products-shortages.summary.dataGaps:undefined,shortages?.summary.products,'Product groups with priced or route inputs')}
        {l.key==='signals'&&coverage(triage?.summary.reviewed,triage?.summary.screened,'Candidates AI reviewed')}
        {l.key==='risk'&&<div className="ei-coverage"><div><span>Latest global telemetry</span><strong>{date(probe?.checkedAt)}</strong></div><div className="ei-status-line">{probeFresh?'Recent probe check':'Stale or unavailable · no all-clear implied'}</div></div>}
        <div className="ei-open">Explore full intelligence <ArrowRight size={15}/></div>
      </button>)}</div>
      <div className="ei-footnote"><BrainCircuit size={16}/><span>Screening sends source anomalies to analyst review. Only fresh, independently corroborated, evidence-qualified findings are eligible for Command Center escalation; ordinary movements remain monitored.</span></div>
    </>}
    {focus!=='overview'&&<div className="ei-workspace">
      <div className="ei-workspace-head">{!hideNavigation&&<button type="button" onClick={()=>setFocus('overview')}>← Overview</button>}<span>{scope} · {lanes.find(l=>l.key===focus)?.title}</span></div>
      {focus==='systems'&&<GlobalSystems mode="systems" countryCode={countryCode} countryName={countryName} cases={cases}/>}
      {focus==='supply'&&<SupplyChain countryCode={countryCode} countryName={countryName}/>}
      {focus==='shortages'&&<ShortageForecasts countryCode={countryCode} countryName={countryName}/>}
      {focus==='signals'&&<>
        <div className="ei-subtabs" role="group" aria-label="Markets and signal investigation">
          <button type="button" className={signalView==='signals'?'active':''} aria-pressed={signalView==='signals'} onClick={()=>setSignalView('signals')}><BrainCircuit size={16}/> Early warning & analyst review</button>
          <button type="button" className={signalView==='markets'?'active':''} aria-pressed={signalView==='markets'} onClick={()=>setSignalView('markets')}><Landmark size={16}/> Financial markets</button>
        </div>
        {signalView==='markets'?<FinancialMarkets/>:<>
          <PhysicalEarlyWarning countryCode={countryCode} countryName={countryName} initialMeasurementFilter={activeMeasurementFilter} onOpenSupplyChain={()=>setFocus('supply')}/>
          <details className="pew-context-radar"><summary>Cross-domain screening radar · context only, not Command alerts</summary>
            <DecisionRadar countryCode={countryCode} countryName={countryName} onNavigate={(target,measurementFocus)=>{
              if(target==='Supply chain')setFocus('supply');
              else if(target==='Risk watch')setFocus('risk');
              else if(target==='Early warning'){setActiveMeasurementFilter(measurementFocus||'all');setSignalView('signals');setFocus('signals');}
              else if(target==='Countries')onCountryMap();
              else if(target==='Defense intelligence')onDefense();
            }}/>
          </details>
        </>}
      </>}
      {focus==='risk'&&<RiskDecisionBoard countryCode={countryCode} countryName={countryName} cases={cases} onCountryMap={onCountryMap} showFinancialMarkets={false}/>}
    </div>}
  </section>;
}
