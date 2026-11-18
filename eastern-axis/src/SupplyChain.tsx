import {useEffect,useMemo,useState} from 'react';
import {Activity,ArrowRight,ArrowUpRight,Database,Globe2,RefreshCcw,Ship,ShieldAlert,Zap} from 'lucide-react';
import './supplyChain.css';
import SupplyContext from './SupplyContext';
import {api} from './lib/api';

type Corridor={
  id:string;name:string;sector:string;exposure:string;pathway:string;countries:string[];
  recentDays:number;baselineDays:number;dailyAverage:number|null;baselineDailyAverage:number|null;
  percentChange:number|null;observation:string;note:string;reportedDays:number;
};
type Source={name:string;url:string;mode:string};
type SupplyResponse={
  code:string;checkedAt:string;sourceDate:string|null;sourceStatus:string;dataAgeDays:number|null;
  source:string;method:string;corridors:Corridor[];sources:Source[];limitations:string[];sourceCoverage:string;warning?:string;
};
const PATHWAYS=[
  {id:'energy',label:'Energy & fertilizer',scope:'Illustrative transmission pathway',steps:['Shipping or production constraint','Oil, LNG and fertilizer feedstock availability','Fuel, industrial power and farm input costs','Potential transport and food-price pressure'],source:'https://unctad.org/publication/strait-hormuz-disruptions-implications-global-trade-and-development'},
  {id:'technology',label:'Electronics & critical minerals',scope:'Illustrative transmission pathway',steps:['Factory, smelter or trade-route interruption','Chip, magnet or processed-mineral inputs delayed','Automotive, electronics and defense production exposed','Potential lead-time and inventory effects'],source:'https://lpi.worldbank.org/en/home'},
  {id:'food',label:'Food & agriculture',scope:'Illustrative transmission pathway',steps:['Bulk-shipping, harvest or fertilizer disruption','Grain, feed and agricultural inputs delayed','Food processing and agricultural costs exposed','Potential grocery-price and food-security pressure'],source:'https://unctad.org/topic/transport-and-trade-logistics'},
  {id:'trade',label:'Shipping & manufacturing',scope:'Illustrative transmission pathway',steps:['Port, canal or freight corridor constraint','Longer journey or limited vessel capacity','Parts and finished-goods delivery uncertainty','Potential freight surcharges and consumer-price pressure'],source:'https://portwatch.imf.org/'}
];
const COVERAGE=[
  {title:'Maritime chokepoints',state:'Daily AIS estimate',detail:'Vessel transit volumes and short-window comparisons; route attribution not inferred'},
  {title:'Global manufacturing pressure',state:'Monthly observed',detail:'New York Fed revision-vintage GSCPI loaded on demand, with date and index units'},
  {title:'International logistics',state:'Benchmark reference',detail:'World Bank LPI 2.0 linked; shipment-level country measures not yet normalized'},
  {title:'Country-to-country commodity trade',state:'Partial',detail:'Bounded U.S. import partner and HS commodity comparisons loaded on demand; full bilateral trade matrices remain out of scope'},
  {title:'Air, rail, road & port delay',state:'Not connected',detail:'No verified unified multimodal freight latency feed'},
  {title:'Sanctions, cyber & weather attribution',state:'Not connected',detail:'Events need independently sourced evidence before being linked to traffic changes'}
];
const number=(n:number|null)=>n===null?'—':new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(n);
function formatDate(value:string|null){if(!value)return 'Not available';const d=new Date(value+'T12:00:00Z');return Number.isFinite(d.getTime())?d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):value;}
export default function SupplyChain({countryCode,countryName}:{countryCode:string;countryName?:string}){
  const [data,setData]=useState<SupplyResponse|null>(null);
  const [pending,setPending]=useState(true);
  const [problem,setProblem]=useState('');
  const [revision,setRevision]=useState(0);
  const [sector,setSector]=useState('All');
  const [pathway,setPathway]=useState('energy');
  const name=countryCode==='all'?'Worldwide':countryName||countryCode;
  useEffect(()=>{
    let active=true;setData(null);setPending(true);setProblem('');
    api.get('/api/supply-chain/'+encodeURIComponent(countryCode))
      .then(r=>{if(active)setData(r.data as SupplyResponse);})
      .catch(()=>{if(active)setProblem('Supply-chain source endpoint is unavailable. No data has been substituted.');})
      .finally(()=>{if(active)setPending(false);});
    return()=>{active=false;};
  },[countryCode,revision]);
  const showing=useMemo(()=>data?.corridors.filter(c=>sector==='All'||c.sector===sector)||[],[data,sector]);
  const measured=data?.corridors.filter(c=>c.percentChange!==null)||[];
  const biggestDecline=measured.filter(c=>(c.percentChange||0)<0).sort((a,b)=>(a.percentChange||0)-(b.percentChange||0))[0];
  const selected=PATHWAYS.find(p=>p.id===pathway)||PATHWAYS[0];
  return <section className="sc-root">
    <div className="sc-top"><span><Ship size={15}/> GLOBAL SYSTEMS / SUPPLY CHAIN INTELLIGENCE</span><span>OBSERVATIONS ≠ ATTRIBUTION</span></div>
    <div className="sc-titlebar"><div><h1>When supply chains break, <em>who pays?</em></h1><p>Follow chokepoints, strategic dependencies and the pathways through which overseas disruption can reach factories, farms and households. Country scope stays linked to the global selector.</p></div><button type="button" className="sc-recheck" onClick={()=>setRevision(v=>v+1)} disabled={pending}><RefreshCcw size={15}/> Recheck source</button></div>
    <div className="sc-kpis">
      <div><span>GEOGRAPHIC SCOPE</span><strong>{name}</strong><small>Country corridor mapping, not proof of its trade exposure</small></div>
      <div><span>CHOKEPOINTS WITH COMPARABLE DATA</span><strong>{measured.length} <small>/ {data?.corridors.length??'—'}</small></strong><small>Both seven-day windows need at least five observations</small></div>
      <div><span>LARGEST OBSERVED DECLINE</span><strong>{biggestDecline?biggestDecline.percentChange+'%':'—'}</strong><small>{biggestDecline?.name||'No verified comparative decline'}</small></div>
      <div><span>PORTWATCH DATA THROUGH</span><strong>{formatDate(data?.sourceDate||null)}</strong><small>{data?.dataAgeDays===null||data?.dataAgeDays===undefined?'Feed unverified':data.dataAgeDays+' days before latest check'}</small></div>
    </div>
    {(pending||problem||data?.sourceStatus!=='observed')&&<div className={'sc-notice '+(problem||data?.sourceStatus==='unavailable'?'sc-problem':'')}><ShieldAlert size={17}/>{pending?'Requesting bounded AIS observations…':problem?problem:data?.sourceStatus==='stale'?'PortWatch data is older than 10 days. Treat figures as historical, not current.':data?.warning||'No verified source observations. Figures are unavailable.'}</div>}
    <div className="sc-section-header"><div><span className="sc-eyebrow"><Activity size={15}/> 01 / OBSERVED TRADE ROUTES</span><h2>Where the traffic is changing</h2><p>Percent change in <strong>average daily vessel transits</strong>: latest available seven days versus the preceding seven. A decline is a research lead, not a confirmed incident.</p></div><a href="https://portwatch.imf.org/" target="_blank" rel="noopener noreferrer">IMF original dataset <ArrowUpRight size={14}/></a></div>
    <div className="sc-filters">{['All','Energy','Trade routes','Industrial goods','Food & materials'].map(s=><button type="button" key={s} className={sector===s?'selected':''} onClick={()=>setSector(s)}>{s}</button>)}</div>
    {!pending&&showing.length===0&&<div className="sc-empty">{countryCode==='all'?'No corridor observations match this category.':'No monitored direct chokepoint is mapped to '+name+' for this category. This does not mean its supply chains are unaffected.'}</div>}
    <div className="sc-corridors">{showing.map(c=><article key={c.id} className="sc-corridor">
      <div className="sc-corridor-head"><span><Globe2 size={15}/>{c.sector.toUpperCase()}</span><span className={c.percentChange===null?'sc-flag-muted':c.percentChange<=-20?'sc-flag-watch':'sc-flag-neutral'}>{c.percentChange===null?'NOT COMPARABLE':c.percentChange<=-20?'TRANSIT DECLINE / SCREEN':'OBSERVED / NO EVENT CLAIM'}</span></div>
      <h3>{c.name}</h3><p>{c.exposure}</p>
      <div className="sc-variation"><strong className={c.percentChange!==null&&c.percentChange<0?'sc-down':''}>{c.percentChange===null?'—':(c.percentChange>0?'+':'')+number(c.percentChange)+'%'}</strong><div><small>Average vessels / day</small><span>{number(c.dailyAverage)} <em>vs {number(c.baselineDailyAverage)} prior</em></span></div></div>
      <div className="sc-mini-track"><span style={{width:c.percentChange===null?'0%':Math.min(100,Math.max(2,100+Math.min(0,c.percentChange)))+'%'}}/></div>
      <p className="sc-path">{c.pathway}</p>
      <footer><span>{c.recentDays} recent / {c.baselineDays} baseline days</span><a href={data?.source||'https://portwatch.imf.org/'} target="_blank" rel="noopener noreferrer">Source <ArrowUpRight size={12}/></a></footer>
    </article>)}</div>
    <div className="sc-section-header sc-after"><div><span className="sc-eyebrow"><Zap size={15}/> 02 / CONSEQUENCE EXPLORER</span><h2>How a local disruption becomes a global problem</h2><p>Transparent pathways for investigation, not forecasts or claims that these events are presently occurring.</p></div></div>
    <div className="sc-path-tabs">{PATHWAYS.map(p=><button key={p.id} type="button" onClick={()=>setPathway(p.id)} className={pathway===p.id?'selected':''}>{p.label}</button>)}</div>
    <div className="sc-chain"><div className="sc-chain-header"><strong>{selected.label}</strong><span>{selected.scope}</span></div><div className="sc-steps">{selected.steps.map((step,i)=><div className="sc-step" key={step}><span>{String(i+1).padStart(2,'0')}</span><p>{step}</p>{i<selected.steps.length-1&&<ArrowRight size={17}/>}</div>)}</div><a href={selected.source} target="_blank" rel="noopener noreferrer">Research and methodology <ArrowUpRight size={13}/></a></div>
    <SupplyContext countryCode={countryCode} countryName={countryName}/>
    <div className="sc-section-header sc-after"><div><span className="sc-eyebrow"><Database size={15}/> 05 / SOURCE TRANSPARENCY</span><h2>What is connected—and what isn't</h2></div></div>
    <div className="sc-coverage">{COVERAGE.map(c=><div key={c.title}><span>{c.state}</span><strong>{c.title}</strong><p>{c.detail}</p></div>)}</div>
    {data&&<div className="sc-method"><strong>Method and limitations</strong><p>{data.method}</p><p>{data.sourceCoverage}</p>{data.limitations.map((x,i)=><p key={i}>{x}</p>)}</div>}
    <div className="sc-source-list">{(data?.sources||[
      {name:'IMF PortWatch',url:'https://portwatch.imf.org/',mode:'source'},
      {name:'New York Fed Global Supply Chain Pressure Index',url:'https://www.newyorkfed.org/research/policy/gscpi',mode:'monthly index'},
      {name:'World Bank LPI 2.0',url:'https://lpi.worldbank.org/en/home',mode:'logistics data'}
    ]).map(s=><a href={s.url} target="_blank" rel="noopener noreferrer" key={s.url}><span>{s.name}<small>{s.mode}</small></span><ArrowUpRight size={15}/></a>)}</div>
  </section>;
}
