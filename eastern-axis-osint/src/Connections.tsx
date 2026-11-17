import { useEffect, useMemo, useState } from 'react';
import { api } from './apiClient';
import { Activity, ArrowUpRight, BookOpen, Database, FileSearch, Globe2, Layers3, Network, ShieldCheck } from 'lucide-react';
import './connections.css';
import AlliedSanctions from './AlliedSanctions';

type Country = { code:string; name:string; region:string; isTreatyAlly:boolean; relationship:string };
type Case = { id:string; code:string; date:string; title:string; summary:string; status:string; topic:string; source:string };
type Assessment = { id:string; countries:string[]; title:string; agency:string; finding:string; published:string; url:string };
type Operation = { id:string; roles:{code:string;role:string}[]; title:string; state:string; summary:string; published:string; url:string };
type Asset = { id:string; code:string; name:string; quantity:string; published:string; detail:string; url:string };
type Defense = { assessments:Assessment[]; operations:Operation[]; assets:Asset[] };
type Indicator = { code:string; label:string; value:number|null; year:string|null; unit:string; sourceUrl:string };
type Systems = { indicators:Indicator[]; status:string };
type Props = { code:string; countries:Country[]; cases:Case[]; onSelect:(code:string)=>void };

const focus = new Set(['RU', 'CN', 'IR', 'KP']);
const modules = [
  {id:'cases', title:'Documented legal cases',icon:FileSearch,detail:'DOJ case files and procedural status'},
  {id:'reports', title:'Allied assessments',icon:BookOpen,detail:'Publicly curated official government excerpts'},
  {id:'operations', title:'Reported conflict context',icon:Activity,detail:'Dated reports, not real-time tracking'},
  {id:'assets', title:'Military capability references',icon:Layers3,detail:'Estimates and source-attributed descriptions'},
  {id:'economic', title:'Economic exposure',icon:Database,detail:'World Bank indicators with reporting years'},
] as const;
type Branch = typeof modules[number]['id'];
const selectedMetrics=new Set(['EG.IMP.CONS.ZS','NY.GDP.TOTL.RT.ZS','NE.TRD.GNFS.ZS','FP.CPI.TOTL.ZG']);
const num=(n:number)=>n.toLocaleString('en-US',{maximumFractionDigits:1})+'%';

export default function Connections({code,countries,cases,onSelect}:Props){
 const [defense,setDefense]=useState<Defense|null>(null);
 const [systems,setSystems]=useState<Systems|null>(null);
 const [defenseError,setDefenseError]=useState(false);
 const [systemsError,setSystemsError]=useState(false);
 const [active,setActive]=useState<Branch>('cases');
 const [region,setRegion]=useState('All regions');
 const selected=countries.find(c=>c.code===code);
 useEffect(()=>{
   let valid=true;
   api.get('/api/defense-intel').then(r=>{if(valid){setDefense(r.data as Defense);setDefenseError(false);}}).catch(()=>{if(valid)setDefenseError(true);});
   return()=>{valid=false;};
 },[]);
 useEffect(()=>{
   if(code==='all'){setSystems(null);return;}
   let valid=true;
   setSystems(null);setSystemsError(false);
   api.get('/api/global-systems/'+code).then(r=>{if(valid)setSystems(r.data as Systems);}).catch(()=>{if(valid)setSystemsError(true);});
   return()=>{valid=false;};
 },[code]);
 const relatedCases=useMemo(()=>cases.filter(c=>c.code===code),[cases,code]);
 const assessments=(defense?.assessments||[]).filter(r=>r.countries.includes(code));
 const operations=(defense?.operations||[]).filter(r=>r.roles.some(p=>p.code===code));
 const assets=(defense?.assets||[]).filter(r=>r.code===code);
 const economics=(systems?.indicators||[]).filter(i=>selectedMetrics.has(i.code));
 const counts:{[key in Branch]:number}={cases:relatedCases.length,reports:assessments.length,operations:operations.length,assets:assets.length,economic:economics.filter(i=>i.value!==null).length};
 const regions=['All regions', ...Array.from(new Set(countries.map(c=>c.region))).sort()];
 const countriesByRegion=countries.filter(c=>region==='All regions'||c.region===region)
   .sort((a,b)=>(cases.filter(x=>x.code===b.code).length-cases.filter(x=>x.code===a.code).length)||a.name.localeCompare(b.name));
 return <section className="cx-root">
  <div className="cx-eyebrow"><Network size={15}/> CROSS-DOMAIN INTELLIGENCE / COUNTRY-INDEXED</div>
  <h1>Follow the documented connections.</h1>
  <p className="cx-sub">Browse the same country across legal records, allied reporting, conflict context, capabilities and economic conditions. Every connection here is a <strong>shared country index</strong>, not an inferred relationship between people, companies or governments.</p>
  {code==='all'||!selected?<div className="cx-directory">
   <div className="cx-region-heading"><div><h2>Choose a country or region</h2><p>Country-specific records are examined separately. Regional grouping is for discovery, not an assertion that neighbors share responsibility.</p></div><select aria-label="Filter countries by region" value={region} onChange={e=>setRegion(e.target.value)}>{regions.map(r=><option key={r} value={r}>{r}</option>)}</select></div>
   <div className="cx-country-grid">{countriesByRegion.slice(0,45).map(c=><button key={c.code} onClick={()=>onSelect(c.code)} className="cx-country"><strong>{c.name}</strong><span>{c.region} · {focus.has(c.code)?'Strategic focus':c.isTreatyAlly?'Treaty ally':'Regional research'}</span><small>{cases.filter(x=>x.code===c.code).length} curated DOJ files <ArrowUpRight size={12}/></small></button>)}</div>
   {countriesByRegion.length>45&&<p className="cx-foot">Showing the first 45 jurisdictions in this region. Use the persistent country selector above to open any other jurisdiction.</p>}
  </div>:<>
   <div className="cx-center"><Globe2 size={24}/><div><small>COUNTRY INDEX</small><h2>{selected.name}</h2><span>{selected.region} · {selected.relationship}</span></div></div>
   <div className="cx-branch-tabs" role="group" aria-label="Connection categories">{modules.map(m=>{
     const Icon=m.icon;
     return <button type="button" key={m.id} onClick={()=>setActive(m.id)} className={active===m.id?'active':''}>
      <Icon size={17}/><strong>{m.title}</strong><small>{counts[m.id]} indexed</small>
     </button>;
   })}</div>
   <div className="cx-branch"><div className="cx-branch-title"><div><h2>{modules.find(m=>m.id===active)?.title}</h2><p>{modules.find(m=>m.id===active)?.detail}</p></div><span>{counts[active]} available</span></div>
     {active==='cases'&&(relatedCases.length?relatedCases.map(x=><article className="cx-record" key={x.id}><small>{x.date} · {x.topic}</small><h3>{x.title}</h3><p>{x.summary}</p><span>{x.status}</span><a href={x.source} target="_blank" rel="noopener noreferrer">DOJ original record <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated DOJ case for this country. This is an indexing gap, not proof of no activity.</p>)}
     {active==='reports'&&(assessments.length?assessments.map(x=><article className="cx-record" key={x.id}><small>{x.published} · {x.agency}</small><h3>{x.title}</h3><p>{x.finding}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original assessment <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated country-specific allied assessment. Official sources may report elsewhere.</p>)}
     {active==='operations'&&(operations.length?operations.map(x=><article className="cx-record" key={x.id}><small>{x.published} · DATED PUBLIC REPORT</small><h3>{x.title}</h3><p>{x.summary}</p><span>{x.state}</span><a href={x.url} target="_blank" rel="noopener noreferrer">Original report <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated conflict or operation entry. This is not a live battlefield assessment.</p>)}
     {active==='assets'&&(assets.length?assets.map(x=><article className="cx-record" key={x.id}><small>{x.published} · PUBLIC ASSET ESTIMATE</small><h3>{x.name}</h3><p>{x.quantity} · {x.detail}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original public source <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No sourced asset entry yet; do not infer zero forces or capabilities.</p>)}
     {active==='economic'&&(economics.length?economics.map(x=><article className="cx-record" key={x.code}><small>{x.year?'REPORTED '+x.year:'NO OBSERVATION'}</small><h3>{x.label}</h3><p className="cx-figure">{typeof x.value==='number'?num(x.value):'Unavailable'}</p><a href={x.sourceUrl} target="_blank" rel="noopener noreferrer">World Bank indicator <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">{systemsError?'World Bank unavailable.': 'No official indicators available in this scope.'} No estimates are substituted.</p>)}
     {(defenseError&&active!=='economic')&&<p className="cx-empty">Defense-intelligence API unavailable. Only the already-curated case index can be relied on.</p>}
   </div>
  </>}
  <AlliedSanctions code={code} cases={code==='all'?cases:relatedCases} />
  <div className="cx-guardrail"><ShieldCheck size={20}/><div><strong>Relationship confidence is not established by these links</strong><p>These panels join public records on a country field. Allegations, government assessments and estimates retain their separate evidence status. No entity identification, ownership chain, government-direction attribution or causal link is inferred. Source dates and downstream court outcomes require separate verification.</p></div></div>
 </section>;
}
