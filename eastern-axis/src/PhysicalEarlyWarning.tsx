import { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowRight, ArrowUpRight, AlertTriangle, Database, GitBranch, Globe2, Search, ShieldCheck, Ship } from 'lucide-react';
import { earlyDomains, scenarios, type Coverage } from './earlyWarningCatalog';
import { isValidObservedPeriod } from './earlyWarningDates';
import './physicalEarlyWarning.css';

type Metric = {
  interval?: 'daily' | 'monthly'; compareMode?: 'percent' | 'basis-points' | 'percentage-points'; changeBps?: number | null; changePp?: number | null; sampleSize?: number;
  id: string; label: string; value: number; unit: string; period: string;
  previous: number; previousPeriod: string; changePct: number;
  source: string; sourceUrl: string; group: string;
};
type SourceHealth = { id: string; status: 'ok' | 'error'; detail: string; checkedAt: string };
type OssProject = {repository:string;score:number;published:string;checkedAt:string;sourceUrl:string;codeReview:number|null;signedReleases:number|null;previousScore:number|null};
type Snapshot = { schemaVersion: number; checkedAt: string | null; status: string; metrics: Metric[]; oss: OssProject[]; sources: SourceHealth[]; limitations: string[] };
const EMPTY: Snapshot = {schemaVersion:1,checkedAt:null,status:'not-checked',metrics:[],oss:[],sources:[],limitations:['No collected source observations have been published yet.']};
const categoryLabel: Record<Coverage,string> = {
  measured:'OBSERVED / OTHER PLATFORM PANEL',
  'public-source':'PUBLIC SOURCE / NEEDS DATA NORMALIZATION',
  restricted:'COMMERCIAL OR AUTHORIZED ACCESS',
  'not-connected':'NOT CONNECTED'
};
const readableDate = (value:string|null|undefined) => {
  if (!value) return 'Not checked';
  const d = new Date(value);
  return Number.isFinite(d.getTime()) ? d.toLocaleString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}) : 'Invalid source date';
};
const format = (n:number) => new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(n);
function isMetric(x:unknown):x is Metric {
  if (!x || typeof x !== 'object') return false;
  const m = x as Partial<Metric>;
  return !!(typeof m.id==='string' && typeof m.label==='string' && typeof m.period==='string'
    && typeof m.previousPeriod==='string' && typeof m.source==='string'
    && typeof m.sourceUrl==='string' && m.sourceUrl.startsWith('https://')
    && typeof m.unit==='string' && typeof m.group==='string' && Number.isFinite(m.value)
    && Number.isFinite(m.previous) && Number.isFinite(m.changePct) && Math.abs(m.changePct)<100000);
}
const isSafeDate=isValidObservedPeriod;
export default function PhysicalEarlyWarning({countryCode,countryName,onOpenSupplyChain}:
  {countryCode:string;countryName?:string;onOpenSupplyChain?:()=>void}) {
  const [category,setCategory]=useState('maritime');
  const [search,setSearch]=useState('');
  const [measurementFilter,setMeasurementFilter]=useState('all');
  const [scenario,setScenario]=useState('shipping');
  const [snapshot,setSnapshot]=useState<Snapshot>(EMPTY);
  const [loadError,setLoadError]=useState('');
  const [recheck,setRecheck]=useState(0);
  useEffect(()=>{
    let active=true;
    // GitHub Pages and Vercel both ship this as a versioned static asset; never call an unknown 3rd-party API from the browser.
    const base = String(import.meta.env.BASE_URL||'/');
    const url = base + 'analysis/physical-early-warning.json';
    fetch(url,{cache:'no-store'}).then(async r=>{
      if(!r.ok)throw new Error('Public observation snapshot unavailable ('+r.status+')');
      const raw=await r.json() as Partial<Snapshot>;
      if(raw.schemaVersion!==1 || !Array.isArray(raw.metrics) || !Array.isArray(raw.sources))
        throw new Error('Observation snapshot failed schema validation');
      const safe: Snapshot = {schemaVersion:1,
        checkedAt:typeof raw.checkedAt==='string'?raw.checkedAt:null,
        status:typeof raw.status==='string'?raw.status:'unavailable',
        metrics:raw.metrics.filter(isMetric).filter(x=>isSafeDate(x.period)&&isSafeDate(x.previousPeriod)),
        oss:Array.isArray(raw.oss)?raw.oss.filter((x): x is OssProject => !!x && typeof x.repository==='string' && /^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(x.repository) && Number.isFinite(x.score) && x.score>=0 && x.score<=10 && typeof x.published==='string' && isSafeDate(x.published) && typeof x.sourceUrl==='string' && x.sourceUrl.startsWith('https://scorecard.dev/')):[],
        sources:raw.sources.filter(x=>x&&typeof x.id==='string'&&(x.status==='ok'||x.status==='error')
          &&typeof x.detail==='string' && typeof x.checkedAt==='string'),
        limitations:Array.isArray(raw.limitations)?raw.limitations.filter((x):x is string=>typeof x==='string').slice(0,12):[]};
      if(active){setSnapshot(safe);setLoadError('');}
    }).catch((e:unknown)=>{if(active){setSnapshot(EMPTY);setLoadError(e instanceof Error?e.message:'Snapshot unavailable');}});
    return()=>{active=false};
  },[recheck]);
  const domain = earlyDomains.find(d=>d.id===category)||earlyDomains[0];
  const shown = useMemo(()=>domain.indicators.filter(i=>(i.label+' '+i.evidence+' '+i.source).toLowerCase().includes(search.toLowerCase().trim())),[domain,search]);
  const activeScenario=scenarios.find(s=>s.id===scenario)||scenarios[0];
  const global = countryCode==='all';
  const scope=global?'Worldwide':countryName||countryCode;
  const relevant=global||domain.geos.length===0||domain.geos.includes(countryCode);
  // These regional corridors are shown only as neighboring geography. A regional
  // reading is never asserted to be a national measurement or an attribution.
  const neighboringRegions:Record<string,string[]> = {
    IR:['regional:persian-gulf','regional:strait-of-hormuz'],
    OM:['regional:persian-gulf','regional:strait-of-hormuz'],
    AE:['regional:persian-gulf','regional:strait-of-hormuz'],
    TW:['regional:taiwan-strait','regional:east-asia'],
    CN:['regional:taiwan-strait','regional:east-asia'],
    JP:['regional:east-asia'],
    KR:['regional:east-asia'],
    EG:['regional:eastern-mediterranean'],
    IL:['regional:eastern-mediterranean'],
    TR:['regional:eastern-mediterranean'],
    EE:['regional:baltic-sea'],
    LV:['regional:baltic-sea'],
    LT:['regional:baltic-sea'],
    FI:['regional:baltic-sea'],
    SE:['regional:baltic-sea'],
    PL:['regional:baltic-sea']
  };
  const regionalContext=neighboringRegions[countryCode]||[];
  const metrics=snapshot.metrics.filter(m=>global||m.group==='global'||m.group===countryCode||regionalContext.includes(m.group));
  const observedAge=snapshot.checkedAt?Math.floor((Date.now()-new Date(snapshot.checkedAt).getTime())/86400000):null;
  const fresh=observedAge!==null&&observedAge>=0&&observedAge<=4;
  const signalScreen=(m:Metric)=>m.compareMode==='basis-points'
    ? Math.abs(m.changeBps??0)>=20
    : m.compareMode==='percentage-points'
    ? Math.abs(m.changePp??0)>=5 : Math.abs(m.changePct)>=10;
  const signals=metrics.filter(signalScreen);
  const metricClass=(m:Metric)=>m.id.startsWith('sofr-')?'funding':
    m.id.startsWith('gps-')?'gnss':m.id.startsWith('fao-')?'food':'commodities';
  const sourceFilters=[
    {id:'all',name:'All measurements'},
    {id:'funding',name:'Overnight funding'},
    {id:'commodities',name:'Industrial inputs'},
    {id:'food',name:'Food prices'},
    {id:'gnss',name:'GNSS accuracy'}
  ];
  const visibleMetrics=metrics.filter(m=>measurementFilter==='all'||metricClass(m)===measurementFilter);
  const checked=snapshot.sources.filter(s=>s.status==='ok').length;
  return <section className="pew-root" aria-label="Global physical and economic early-warning intelligence">
    <div className="pew-eyebrow"><Activity size={15}/> INTELLIGENCE / GLOBAL SYSTEMIC EARLY WARNING</div>
    <div className="pew-heading">
      <div><h1>Before systems <em>break.</em></h1><p>Watch stress in the physical economy before it reaches critical infrastructure, factories and households. Fourteen risk domains, attributable public observations, and explicitly hypothetical cascade models.</p></div>
      {onOpenSupplyChain&&<button type="button" onClick={onOpenSupplyChain}>Existing freight data <ArrowRight size={15}/></button>}
    </div>
    <div className="pew-summary">
      <div><span>INTELLIGENCE DOMAINS</span><strong>{earlyDomains.length}</strong><small>Cross-sector coverage registry</small></div>
      <div><span>VALIDATED MARKET OBSERVATIONS</span><strong>{metrics.length}</strong><small>Source-dated daily and monthly readings</small></div>
      <div><span>CHANGE SCREENS</span><strong>{signals.length}</strong><small>Price/volume ≥10%, SOFR ≥20 bps, GNSS ≥5 pp — review only</small></div>
      <div><span>LAST COLLECTION</span><strong className="pew-date">{readableDate(snapshot.checkedAt)}</strong><small>{fresh?'Recent check':observedAge===null?'No source check':'Stale or unverified — not live'}</small></div>
    </div>
    <div className={'pew-health '+(!fresh?'pew-health-warn':'')}>
      {fresh?<ShieldCheck size={17}/>:<AlertTriangle size={17}/>}
      <span><strong>{loadError?'Snapshot unavailable':snapshot.status==='ok'?'Published official-source snapshot':snapshot.status==='partial'?'Partial source collection':'No verified collection'}</strong>
      {' '}— {checked}/{snapshot.sources.length} scheduled source adapters succeeded. A check is not a claim of global monitoring coverage.</span>
      <button onClick={()=>setRecheck(x=>x+1)} type="button">Reload snapshot</button>
    </div>
    <div className="pew-source-readings">
      <div className="pew-section-title"><span><Database size={16}/> VERIFIED INPUTS & INFRASTRUCTURE PROXIES</span><h2>Observed signals, not predictions</h2><p>Source-specific monthly prices, daily U.S. funding, and regional aircraft-reported GNSS quality. The latter is not a confirmed jamming rate and cannot establish PTP or datacenter failure.</p></div>
      {!global&&metrics.some(m=>m.group.startsWith('regional:'))&&<p className="pew-region-note">Neighboring-region GNSS readings are **regional context only**. They are not measurements within {scope}, evidence of a country's involvement, or confirmation of terrestrial infrastructure failure.</p>}
      <div className="pew-scenario-nav" aria-label="Filter source measurements">{sourceFilters.map(filter=><button key={filter.id} type="button" className={measurementFilter===filter.id?'active':''} aria-pressed={measurementFilter===filter.id} onClick={()=>setMeasurementFilter(filter.id)}>{filter.name}</button>)}</div>
      {visibleMetrics.length===0?<p className="pew-empty">No validated observations match this filter and country context. Existing PortWatch and Comtrade panels remain under Supply chain.</p>:
      <div className="pew-price-grid">{visibleMetrics.map(m=><article key={m.id}>
        <span>{m.source} · {m.group==='global'?'GLOBAL BENCHMARK':m.group.startsWith('regional:')?'REGIONAL CONTEXT: '+m.group.slice('regional:'.length).replaceAll('-',' ').toUpperCase():m.group}</span><strong>{m.label}</strong>
        <div className="pew-price"><b>{format(m.value)}</b> <small>{m.unit}</small></div>
        <div className={'pew-change '+(signalScreen(m)?'pew-screen':'')}>
          {m.compareMode==='basis-points'?((m.changeBps??0)>0?'+':'')+format(m.changeBps??0)+' bps':
          m.compareMode==='percentage-points'?((m.changePp??0)>0?'+':'')+format(m.changePp??0)+' percentage points':
          (m.changePct>0?'+':'')+format(m.changePct)+'%'} vs previous observation{signalScreen(m)?' · REVIEW SIGNAL':''}</div>
        <small>{m.period} vs {m.previousPeriod} · {m.interval==='daily'?'daily':'monthly'} observation{m.sampleSize?' · '+m.sampleSize.toLocaleString('en-US')+' sampled hexagons':''}</small>
        <small>{m.id.startsWith('gps-')?'Geographic proxy only; aviation sampling changes can shift the percentage. No attribution or navigation claim.':m.id.startsWith('fao-')?'Global wholesale commodity index, not local food inflation.':''}</small>
        <a href={m.sourceUrl} target="_blank" rel="noopener noreferrer">Original data <ArrowUpRight size={13}/></a>
      </article>)}</div>}
    </div>
    <details className="pew-source-health"><summary>Source collection and missing-data audit · {checked}/{snapshot.sources.length} checks passed</summary>
      <p>Success means a schema-validated reading, not full geographic coverage. Failures remain visible; no zeros are substituted.</p>
      <div>{snapshot.sources.map(src=><div key={src.id}><strong>{src.id}</strong><span className={src.status==='ok'?'pew-check-ok':'pew-check-bad'}>{src.status.toUpperCase()}</span><small>{src.detail} · {readableDate(src.checkedAt)}</small></div>)}</div>
    </details>
    <div className="pew-section-title pew-offset"><span><ShieldCheck size={16}/> OSS SECURITY PRACTICES</span><h2>Foundational package hygiene</h2><p>OpenSSF checks on a small named sample of critical open-source projects. Scores are published security-practice measurements, not compromise probabilities or accusations against maintainers.</p></div>
    {snapshot.oss.length>0?<div className="pew-price-grid">{snapshot.oss.map(o=><article key={o.repository}>
      <span>OpenSSF Scorecard · {o.published}</span><strong>{o.repository}</strong>
      <div className="pew-price"><b>{format(o.score)}</b><small>/ 10</small></div>
      <small>Code review: {o.codeReview===null?'Unreported':o.codeReview+'/10'} · Signed releases: {o.signedReleases===null?'Unreported':o.signedReleases+'/10'}</small>
      <small>{o.previousScore===null?'Historical baseline not yet captured':'Prior captured score: '+format(o.previousScore)+'/10'}</small>
      <a href={o.sourceUrl} target="_blank" rel="noopener noreferrer">Published scorecard <ArrowUpRight size={13}/></a>
    </article>)}</div>:<p className="pew-empty">No verified project practice snapshot. Public OpenSSF security scores will appear here once the daily collection workflow succeeds.</p>}
    <div className="pew-section-title pew-offset"><span><Globe2 size={16}/> {earlyDomains.length} INTELLIGENCE DOMAINS</span><h2>Leading-indicator source registry</h2><p>Filter an evidence category to review what should be collected, how frequently, and what remains restricted or unconnected. Selecting a country preserves global macro indicators but does not invent country-specific readings.</p></div>
    <div className="pew-domains">
      <nav className="pew-domain-nav" aria-label="Early warning categories">{earlyDomains.map((d,i)=>
        <button type="button" className={d.id===category?'active':''} key={d.id} onClick={()=>{setCategory(d.id);setSearch('');}}>
          <small>{String(i+1).padStart(2,'0')}</small><span>{d.title}</span><ArrowRight size={14}/>
        </button>)}</nav>
      <div className="pew-domain-body">
        <div className="pew-domain-top"><span>{domain.horizon.toUpperCase()} / {scope.toUpperCase()}</span><span>{domain.indicators.length} INDICATORS</span></div>
        <h3>{domain.title}</h3><p>{domain.explanation}</p>
        {!relevant&&<div className="pew-scope-warn">This panel does not have a verified direct monitored-node match for {scope}. Listed sources describe global or third-country pathways, not measured exposure for this country.</div>}
        <label className="pew-search"><Search size={15}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search indicators or agencies" aria-label="Search indicators and sources"/></label>
        {shown.length===0?<div className="pew-empty">No indicators match this search.</div>:
        <div className="pew-indicators">{shown.map((item,i)=><article key={item.label}>
          <div className="pew-indicator-top"><span>{String(i+1).padStart(2,'0')}</span><span className={'pew-status pew-'+item.coverage}>{categoryLabel[item.coverage]}</span></div>
          <h4>{item.label}</h4><p>{item.evidence}</p>
          <footer><span>{item.cadence}</span><a href={item.url} target="_blank" rel="noopener noreferrer">{item.source} <ArrowUpRight size={13}/></a></footer>
        </article>)}</div>}
      </div>
    </div>
    <div className="pew-section-title pew-offset"><span><GitBranch size={16}/> CASCADE PATHWAYS</span><h2>What can fail next?</h2><p>These are analytical what-if pathways only, not a measured supplier graph, causal attribution, or calibrated propagation probabilities. Each step requires independent corroboration during a real event.</p></div>
    <div className="pew-scenario-nav">{scenarios.map(s=><button type="button" className={s.id===scenario?'active':''} key={s.id} onClick={()=>setScenario(s.id)}>{s.label}</button>)}</div>
    <div className="pew-nodes">{activeScenario.nodes.map((node,i)=><div key={node} className="pew-node"><span>{String(i+1).padStart(2,'0')}</span><strong>{node}</strong>{i<activeScenario.nodes.length-1&&<ArrowRight size={17}/>}</div>)}</div>
    <div className="pew-caveat"><Ship size={17}/><p><strong>How to use this:</strong> correlate independent changes with date-matched baselines, affected geography and verified dependency links. An increased input price or expiring labor contract is not sufficient evidence to issue a red alert. The source registry has no numeric contagion probabilities until a measured network is established. Anomalous maintenance patterns alone must not be attributed to a malicious developer.</p></div>
  </section>;
}
