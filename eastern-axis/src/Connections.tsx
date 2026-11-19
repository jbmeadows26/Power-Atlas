import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { Activity, ArrowUpRight, BookOpen, Database, FileSearch, Globe2, Layers3, Network, Search, ShieldCheck } from 'lucide-react';
import './connections.css';
import AlliedSanctions from './AlliedSanctions';

type Country = { code:string; name:string; region:string; isTreatyAlly:boolean; relationship:string };
type Case = { id:string; code:string; date:string; title:string; summary:string; status:string; topic:string; source:string };
type Assessment = { id:string; countries:string[]; title:string; agency:string; finding:string; published:string; url:string };
type Operation = { id:string; roles:{code:string;role:string}[]; title:string; state:string; summary:string; published:string; url:string };
type Asset = { id:string; code:string; name:string; quantity:string; published:string; detail:string; url:string };
type OfficialSource = { id:string; name:string; group:string; what:string; url:string };
type Defense = { assessments:Assessment[]; operations:Operation[]; assets:Asset[]; sources?:OfficialSource[] };
type Indicator = { code:string; label:string; value:number|null; year:string|null; unit:string; sourceUrl:string };
type Systems = { indicators:Indicator[]; status:string };
type Props = { code:string; countries:Country[]; cases:Case[]; onSelect:(code:string)=>void };

const focus = new Set(['RU', 'CN', 'IR', 'KP']);
const modules = [
  {id:'cases', title:'U.S. DOJ cases',icon:FileSearch,detail:'Reviewed U.S. Department of Justice case records only, not the entire allied evidence library'},
  {id:'reports', title:'U.S. & allied reports',icon:BookOpen,detail:'Country-indexed official assessments, plus cross-cutting allied context and original sources'},
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
 const [active,setActive]=useState<Branch>('reports');
 const [region,setRegion]=useState('All regions');
 const [countryQuery,setCountryQuery]=useState('');
 const [showAllCountries,setShowAllCountries]=useState(false);
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
 const assessments=(defense?.assessments||[]).filter(r=>Array.isArray(r.countries)&&r.countries.includes(code));
 // Broad strategic reports are relevant context, but must never be counted as country-specific findings.
 const crossCuttingReports=(defense?.assessments||[]).filter(r=>!r.countries?.length);
 const officialSources=(defense?.sources||[]).filter(s=>/^https:\/\//.test(s.url));
 const operations=(defense?.operations||[]).filter(r=>r.roles.some(p=>p.code===code));
 const assets=(defense?.assets||[]).filter(r=>r.code===code);
 const economics=(systems?.indicators||[]).filter(i=>selectedMetrics.has(i.code));
 const counts:{[key in Branch]:number}={cases:relatedCases.length,reports:assessments.length,operations:operations.length,assets:assets.length,economic:economics.filter(i=>i.value!==null).length};
 const regions=['All regions', ...Array.from(new Set(countries.map(c=>c.region))).sort()];
 const countryCounts=new Map(countries.map(c=>[c.code,{
   doj:cases.filter(x=>x.code===c.code).length,
   allied:(defense?.assessments||[]).filter(r=>r.countries?.includes(c.code)).length
 }]));
 const countriesByRegion=countries.filter(c=>
    (region==='All regions'||c.region===region) &&
    (c.name.toLowerCase().includes(countryQuery.trim().toLowerCase())||
     c.code.toLowerCase().includes(countryQuery.trim().toLowerCase())))
   .sort((a,b)=>{const ac=countryCounts.get(a.code)!,bc=countryCounts.get(b.code)!;
     return (bc.doj+bc.allied-ac.doj-ac.allied)||a.name.localeCompare(b.name);});
 const countryCards=showAllCountries?countriesByRegion:countriesByRegion.slice(0,45);
 return <section className="cx-root">
  <div className="cx-eyebrow"><Network size={15}/> CROSS-DOMAIN INTELLIGENCE / COUNTRY-INDEXED</div>
  <h1>Follow the documented connections.</h1>
  <p className="cx-sub">Browse the same country across legal records, allied reporting, conflict context, capabilities and economic conditions. Every connection here is a <strong>shared country index</strong>, not an inferred relationship between people, companies or governments.</p>
  {code==='all'||!selected?<div className="cx-directory">
   <div className="cx-region-heading"><div><h2>Choose a country or region</h2><p>Every country can open the U.S. and allied source library, even without a curated DOJ record. A missing case is an indexing gap, not zero intelligence.</p></div>
     <div className="cx-directory-controls">
       <label className="cx-search"><Search size={15}/><input aria-label="Search countries by name or ISO code" placeholder="Search countries…" value={countryQuery} onChange={e=>{setCountryQuery(e.target.value);setShowAllCountries(false);}}/></label>
       <select aria-label="Filter countries by region" value={region} onChange={e=>{setRegion(e.target.value);setShowAllCountries(false);}}>{regions.map(r=><option key={r} value={r}>{r}</option>)}</select>
     </div></div>
   <div className="cx-country-grid">{countryCards.map(c=>{
     const count=countryCounts.get(c.code)!;
     return <button type="button" key={c.code} onClick={()=>onSelect(c.code)} className="cx-country"><strong>{c.name}</strong><span>{c.region} · {focus.has(c.code)?'Strategic focus':c.isTreatyAlly?'Treaty ally':'Regional research'}</span>
       <small>{count.doj?count.doj+' curated DOJ '+(count.doj===1?'case':'cases'):'No curated DOJ cases'} · {defense?(count.allied?count.allied+' indexed allied '+(count.allied===1?'report':'reports'):'Allied sources linked'):'Checking allied index'} <ArrowUpRight size={12}/></small>
     </button>;
   })}</div>
   {countriesByRegion.length===0&&<p className="cx-empty">No matching countries. Try another name or region.</p>}
   {!showAllCountries&&countriesByRegion.length>countryCards.length&&<div className="cx-more"><span>{countryCards.length} of {countriesByRegion.length} countries</span><button type="button" onClick={()=>setShowAllCountries(true)}>Show all matching countries</button></div>}
  </div>:<>
   <div className="cx-center"><Globe2 size={24}/><div><small>COUNTRY INDEX</small><h2>{selected.name}</h2><span>{selected.region} · {selected.relationship}</span></div></div>
   <p className="cx-coverage-status">Coverage: {relatedCases.length} curated U.S. DOJ cases · {defense?assessments.length+' country-indexed allied assessments':'Allied assessment index loading or unavailable'}. All official publisher links remain available below; no unindexed document is treated as a zero finding.</p>
   <div className="cx-branch-tabs" role="group" aria-label="Connection categories">{modules.map(m=>{
     const Icon=m.icon;
     return <button type="button" key={m.id} onClick={()=>setActive(m.id)} className={active===m.id?'active':''}>
      <Icon size={17}/><strong>{m.title}</strong><small>{counts[m.id]} indexed</small>
     </button>;
   })}</div>
   <div className="cx-branch"><div className="cx-branch-title"><div><h2>{modules.find(m=>m.id===active)?.title}</h2><p>{modules.find(m=>m.id===active)?.detail}</p></div><span>{counts[active]} available</span></div>
     {active==='cases'&&(relatedCases.length?relatedCases.map(x=><article className="cx-record" key={x.id}><small>{x.date} · {x.topic}</small><h3>{x.title}</h3><p>{x.summary}</p><span>{x.status}</span><a href={x.source} target="_blank" rel="noopener noreferrer">DOJ original record <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated DOJ case for this country. This is an indexing gap, not proof of no activity.</p>)}
     {active==='reports'&&<>
       {assessments.length?assessments.map(x=><article className="cx-record" key={x.id}><small>{x.published} · {x.agency}</small><h3>{x.title}</h3><p>{x.finding}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original assessment <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No country-indexed official assessment is curated here. This does not mean allied agencies have no relevant files.</p>}
       {crossCuttingReports.length>0&&<div className="cx-crosscut"><h3>Cross-cutting allied context — not country-attributed findings</h3>{crossCuttingReports.map(x=><article className="cx-record" key={x.id}><small>{x.published} · {x.agency}</small><h3>{x.title}</h3><p>{x.finding}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original allied report <ArrowUpRight size={13}/></a></article>)}</div>}
     </>}
     {active==='operations'&&(operations.length?operations.map(x=><article className="cx-record" key={x.id}><small>{x.published} · DATED PUBLIC REPORT</small><h3>{x.title}</h3><p>{x.summary}</p><span>{x.state}</span><a href={x.url} target="_blank" rel="noopener noreferrer">Original report <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated conflict or operation entry. This is not a live battlefield assessment.</p>)}
     {active==='assets'&&(assets.length?assets.map(x=><article className="cx-record" key={x.id}><small>{x.published} · PUBLIC ASSET ESTIMATE</small><h3>{x.name}</h3><p>{x.quantity} · {x.detail}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original public source <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No sourced asset entry yet; do not infer zero forces or capabilities.</p>)}
     {active==='economic'&&(economics.length?economics.map(x=><article className="cx-record" key={x.code}><small>{x.year?'REPORTED '+x.year:'NO OBSERVATION'}</small><h3>{x.label}</h3><p className="cx-figure">{typeof x.value==='number'?num(x.value):'Unavailable'}</p><a href={x.sourceUrl} target="_blank" rel="noopener noreferrer">World Bank indicator <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">{systemsError?'World Bank unavailable.': 'No official indicators available in this scope.'} No estimates are substituted.</p>)}
     {(defenseError&&active!=='economic')&&<p className="cx-empty">Defense-intelligence API unavailable. Only the already-curated case index can be relied on.</p>}
   </div>
  </>}
  <section className="cx-allied-library" aria-label="Allied government source library">
    <div className="cx-allied-heading"><div><div className="cx-eyebrow"><BookOpen size={15}/> ALLIED GOVERNMENT EVIDENCE / ORIGINAL PUBLISHERS</div><h2>U.S. and allied sources, always in scope.</h2></div><span>{officialSources.length} official and research source gateways</span></div>
    <p>Use the original publisher's records to investigate this {code==='all'?'global':'country'} context. These are source gateways, <strong>not claims that every document has been downloaded, indexed or independently corroborated</strong>. Country-tagged reports appear above; broader allied reporting remains discoverable below regardless of the selected country.</p>
    {officialSources.length>0?<div className="cx-allied-grid">{officialSources.map(src=><a key={src.id} href={src.url} target="_blank" rel="noopener noreferrer" className="cx-allied-item">
      <small>{src.group} · Official / source reference</small><strong>{src.name}</strong><span>{src.what}</span><em>Open original publisher <ArrowUpRight size={12}/></em>
    </a>)}</div>:<p className="cx-empty">The official source directory is loading or temporarily unavailable. Source coverage has not been assumed complete.</p>}
    {defenseError&&<p className="cx-empty">The official assessment catalog is temporarily unavailable; no missing source has been counted as zero.</p>}
  </section>
  <AlliedSanctions code={code} cases={code==='all'?cases:relatedCases} />
  <div className="cx-guardrail"><ShieldCheck size={20}/><div><strong>Relationship confidence is not established by these links</strong><p>These panels join public records on a country field. Allegations, government assessments and estimates retain their separate evidence status. No entity identification, ownership chain, government-direction attribution or causal link is inferred. Source dates and downstream court outcomes require separate verification.</p></div></div>
 </section>;
}
