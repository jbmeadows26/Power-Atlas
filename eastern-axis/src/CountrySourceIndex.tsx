import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { Activity, ArrowUpRight, BookOpen, Database, FileSearch, Globe2, Layers3, Network, ShieldCheck } from 'lucide-react';
import './connections.css';
import AlliedSanctions from './AlliedSanctions';
import CountryDefenseSnapshot, { defenseCounts } from './CountryDefenseSnapshot';

type Country = { code:string; name:string; region:string; isTreatyAlly:boolean; relationship:string };
type Case = { id:string; code:string; date:string; title:string; summary:string; status:string; topic:string; source:string; agency:string };
type Assessment = { id:string; countries:string[]; title:string; agency:string; finding:string; published:string; url:string };
type Operation = { id:string; roles:{code:string;role:string}[]; title:string; state:string; summary:string; published:string; url:string };
type Asset = { id:string; code:string; name:string; quantity:string; published:string; detail:string; url:string };
type OfficialSource = { id:string; name:string; group:string; what:string; url:string };
type IntakeRecord = { id:string; sourceId:string; title:string; date:string; summary:string; sourceUrl:string; countryMention?:string; countryRule?:string; recordType:string; reviewState:string };
type Intelligence = { records:IntakeRecord[]; resultsNote:string };
type Defense = { assessments:Assessment[]; operations:Operation[]; assets:Asset[]; sources:OfficialSource[] };
type Indicator = { code:string; label:string; value:number|null; year:string|null; unit:string; sourceUrl:string };
type Systems = { indicators:Indicator[]; status:string };
type Props = { code:string; countries:Country[]; cases:Case[]; onSelect:(code:string)=>void };

const focus = new Set(['RU', 'CN', 'IR', 'KP']);
const modules = [
  {id:'cases', title:'Documented legal cases',icon:FileSearch,detail:'Reviewed DOJ announcements and procedural status — one evidence category'},
  {id:'intake', title:'Country-tagged source leads',icon:Database,detail:'Unreviewed official-source intake; headline mentions are not attribution'},
  {id:'reports', title:'Allied assessments',icon:BookOpen,detail:'Publicly curated and country-tagged government assessments'},
  {id:'sources', title:'U.S. + allied source network',icon:Globe2,detail:'Official government source portals, worldwide even where there is no country-tagged report'},
  {id:'operations', title:'Reported conflict context',icon:Activity,detail:'Dated reports, not real-time tracking'},
  {id:'assets', title:'Military capability references',icon:Layers3,detail:'Estimates and source-attributed descriptions'},
  {id:'economic', title:'Economic exposure',icon:Database,detail:'World Bank indicators with reporting years'},
] as const;
type Branch = typeof modules[number]['id'];
const selectedMetrics=new Set(['EG.IMP.CONS.ZS','NY.GDP.TOTL.RT.ZS','NE.TRD.GNFS.ZS','FP.CPI.TOTL.ZG']);
const num=(n:number)=>n.toLocaleString('en-US',{maximumFractionDigits:1})+'%';

export default function CountrySourceIndex({code,countries,cases,onSelect}:Props){
 const [defense,setDefense]=useState<Defense|null>(null);
 const [systems,setSystems]=useState<Systems|null>(null);
 const [intelligence,setIntelligence]=useState<Intelligence|null>(null);
 const [intelligenceError,setIntelligenceError]=useState(false);
 const [defenseError,setDefenseError]=useState(false);
 const [systemsError,setSystemsError]=useState(false);
 const [active,setActive]=useState<Branch>('cases');
 const [region,setRegion]=useState('All regions');
 const [query,setQuery]=useState('');
 const selected=countries.find(c=>c.code===code);
 useEffect(()=>{
   let valid=true;
   api.get('/api/defense-intel').then(r=>{if(valid){setDefense(r.data as Defense);setDefenseError(false);}}).catch(()=>{if(valid)setDefenseError(true);});
   api.get('/api/intelligence').then(r=>{if(valid){setIntelligence(r.data as Intelligence);setIntelligenceError(false);}}).catch(()=>{if(valid)setIntelligenceError(true);});
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
 const leads=(intelligence?.records||[]).filter(r=>code!=='all'&&r.countryMention===code);
 const alliedSources=(defense?.sources||[]).filter(r=>['United States','Five Eyes','EU / NATO','Indo-Pacific allies'].includes(r.group));
 const supportingSources=(defense?.sources||[]).filter(r=>!['United States','Five Eyes','EU / NATO','Indo-Pacific allies'].includes(r.group));
 const operations=(defense?.operations||[]).filter(r=>r.roles.some(p=>p.code===code));
 const assets=(defense?.assets||[]).filter(r=>r.code===code);
 const economics=(systems?.indicators||[]).filter(i=>selectedMetrics.has(i.code));
 const counts:{[key in Branch]:number}={cases:relatedCases.length,intake:leads.length,reports:assessments.length,sources:alliedSources.length,operations:operations.length,assets:assets.length,economic:economics.filter(i=>i.value!==null).length};
 const regions=['All regions', ...Array.from(new Set(countries.map(c=>c.region))).sort()];
 const countriesByRegion=countries.filter(c=>(region==='All regions'||c.region===region) && (c.name.toLowerCase().includes(query.toLowerCase())||c.code.toLowerCase().includes(query.toLowerCase())))
   .sort((a,b)=>{const score=(c:Country)=>{const n=defenseCounts(defense,c.code);return cases.filter(x=>x.code===c.code).length+n.assessments+n.operations+n.assets;};return score(b)-score(a)||a.name.localeCompare(b.name);});
 return <section className="cx-root">
  <div className="cx-eyebrow"><Network size={15}/> CROSS-DOMAIN INTELLIGENCE / COUNTRY-INDEXED</div>
  <h1>Follow the documented connections.</h1>
  <p className="cx-sub">All relevant public U.S. and allied evidence stays in scope for every country: legal records, Five Eyes reporting, NATO and EU assessments, regional defense assessments, sanctions and source-indexed leads. Show original sources and their limits. <strong>Zero curated cases never means zero evidence.</strong> A shared country index does not establish a relationship or government attribution.</p>
  {code==='all'||!selected?<div className="cx-directory">
   <div className="cx-region-heading"><div><h2>Choose a country or region</h2><p>Country-specific records are examined separately. Regional grouping is for discovery, not an assertion that neighbors share responsibility.</p></div><div className="cx-directory-filters"><input type="search" aria-label="Find country or ISO code" placeholder="Search country or code…" value={query} onChange={e=>setQuery(e.target.value)}/><select aria-label="Filter countries by region" value={region} onChange={e=>setRegion(e.target.value)}>{regions.map(r=><option key={r} value={r}>{r}</option>)}</select></div></div>
   <div className="cx-country-grid">{countriesByRegion.slice(0,45).map(c=><button key={c.code} onClick={()=>onSelect(c.code)} className="cx-country"><strong>{c.name}</strong><span>{c.region} · {focus.has(c.code)?'Strategic focus':c.isTreatyAlly?'Treaty ally':'Regional research'}</span><div className="cx-country-evidence">{defense?(()=>{const n=defenseCounts(defense,c.code);return <><span>{n.assessments?`${n.assessments} allied reports`:'Reports not indexed'}</span><span>{n.operations?`${n.operations} operations`:'Operations not indexed'}</span><span>{n.assets?`${n.assets} asset entries`:'Assets not indexed'}</span></>;})():<span>{defenseError?'Source unavailable':'Loading defense records…'}</span>}</div><small>Open country intelligence card <ArrowUpRight size={12}/></small></button>)}</div>
   {countriesByRegion.length>45&&<p className="cx-foot">Showing 45 of {countriesByRegion.length} matching jurisdictions. Search by country or ISO code, or use the persistent selector to reach every country.</p>}
   {countriesByRegion.length===0&&<p className="cx-empty">No matching countries. Try another name or region.</p>}
   <section className="cx-global-evidence" aria-label="Worldwide allied intelligence sources">
    <h2>Worldwide U.S. and allied evidence</h2>
    <p className="cx-sub">These are all currently curated country-tagged allied assessments, even when a country's DOJ case index is empty. Each link opens an original report. The source library is broader than the curated report sample; unindexed reporting is not an absence of evidence.</p>
    {(defense?.assessments||[]).map(r=><article className="cx-record" key={r.id}><small>{r.published} · {r.agency} · {r.countries.length?r.countries.join(', '):'Regional context — not country-tagged'}</small><h3>{r.title}</h3><p>{r.finding}</p><a href={r.url} target="_blank" rel="noopener noreferrer">Original allied assessment <ArrowUpRight size={13}/></a></article>)}
    <h3 className="cx-source-heading">Official allied source network</h3>
    <div className="cx-source-links">{alliedSources.map(r=><a key={r.id} href={r.url} target="_blank" rel="noopener noreferrer">{r.name} <ArrowUpRight size={12}/></a>)}</div>
    {defenseError&&<p className="cx-empty">Allied source catalog could not be loaded. Coverage is unknown, not zero.</p>}
   </section>
  </div>:<>
   <div className="cx-center"><Globe2 size={24}/><div><small>ALL-SOURCE COUNTRY INDEX</small><h2>{selected.name}</h2><span>{selected.region} · {selected.relationship}</span></div></div>
   <p className="cx-sub">Every country remains connected to the complete allied source network, whether or not its curated DOJ index has entries. Country-tagged records and worldwide discovery portals are shown separately so unreviewed mentions cannot be mistaken for verified government activity.</p>
   <CountryDefenseSnapshot code={code} name={selected.name} data={defense} unavailable={defenseError} onSelect={setActive}/>
   <div className="cx-branch-tabs" role="group" aria-label="Connection categories">{modules.map(m=>{
     const Icon=m.icon;
     return <button type="button" key={m.id} onClick={()=>setActive(m.id)} className={active===m.id?'active':''}>
      <Icon size={17}/><strong>{m.title}</strong><small>{counts[m.id]} indexed</small>
     </button>;
   })}</div>
   <div className="cx-branch"><div className="cx-branch-title"><div><h2>{modules.find(m=>m.id===active)?.title}</h2><p>{modules.find(m=>m.id===active)?.detail}</p></div><span>{counts[active]} available</span></div>
     {active==='cases'&&(relatedCases.length?relatedCases.map(x=><article className="cx-record" key={x.id}><small>{x.date} · {x.topic}</small><h3>{x.title}</h3><p>{x.summary}</p><span>{x.status}</span><a href={x.source} target="_blank" rel="noopener noreferrer">DOJ original record <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated DOJ case for this country. This is an indexing gap, not proof of no activity.</p>)}
     {active==='intake'&&(leads.length?leads.map(x=><article className="cx-record" key={x.id}><small>{x.date||'Publication date unavailable'} · {x.sourceId.toUpperCase()} · UNREVIEWED SOURCE REFERENCE</small><h3>{x.title}</h3><p>{x.summary}</p><span>{x.countryRule||'Source headline mentions this country; no attribution established.'}</span><a href={x.sourceUrl} target="_blank" rel="noopener noreferrer">Original source record <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No country-tagged leads in the bounded intake sample. Untagged FARA, OFAC and CISA references remain accessible in the global Collection desk. This is not evidence of no activity.</p>)}
     {active==='sources'&&<><p className="cx-empty">These are source portals and reference collections available across every country, not claims that their publishers have reported on the selected country. Only assessments with an explicit country tag appear under Allied assessments.</p>{alliedSources.map(x=><article className="cx-record" key={x.id}><small>OFFICIAL SOURCE · {x.group}</small><h3>{x.name}</h3><p>{x.what}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Browse original publisher <ArrowUpRight size={13}/></a></article>)}{supportingSources.length>0&&<><h3>Additional multilateral and research references</h3>{supportingSources.map(x=><article className="cx-record" key={x.id}><small>SUPPORTING SOURCE · {x.group}</small><h3>{x.name}</h3><p>{x.what}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original publisher <ArrowUpRight size={13}/></a></article>)}</>}</>}
     {active==='reports'&&(assessments.length?assessments.map(x=><article className="cx-record" key={x.id}><small>{x.published} · {x.agency}</small><h3>{x.title}</h3><p>{x.finding}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original assessment <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated country-specific allied assessment. Official sources may report elsewhere.</p>)}
     {active==='operations'&&(operations.length?operations.map(x=><article className="cx-record" key={x.id}><small>{x.published} · DATED PUBLIC REPORT</small><h3>{x.title}</h3><p>{x.summary}</p><span>{x.state}</span><a href={x.url} target="_blank" rel="noopener noreferrer">Original report <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No curated conflict or operation entry. This is not a live battlefield assessment.</p>)}
     {active==='assets'&&(assets.length?assets.map(x=><article className="cx-record" key={x.id}><small>{x.published} · PUBLIC ASSET ESTIMATE</small><h3>{x.name}</h3><p>{x.quantity} · {x.detail}</p><a href={x.url} target="_blank" rel="noopener noreferrer">Original public source <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">No sourced asset entry yet; do not infer zero forces or capabilities.</p>)}
     {active==='economic'&&(economics.length?economics.map(x=><article className="cx-record" key={x.code}><small>{x.year?'REPORTED '+x.year:'NO OBSERVATION'}</small><h3>{x.label}</h3><p className="cx-figure">{typeof x.value==='number'?num(x.value):'Unavailable'}</p><a href={x.sourceUrl} target="_blank" rel="noopener noreferrer">World Bank indicator <ArrowUpRight size={13}/></a></article>):<p className="cx-empty">{systemsError?'World Bank unavailable.': 'No official indicators available in this scope.'} No estimates are substituted.</p>)}
     {defenseError&&['reports','operations','assets','sources'].includes(active)&&<p className="cx-empty">Allied assessment and source catalog unavailable. Coverage is unknown, not zero; curated cases remain separate.</p>}
     {intelligenceError&&active==='intake'&&<p className="cx-empty">Official-source intake is unavailable. Country-tagged lead coverage cannot be assessed.</p>}
   </div>
  </>}
  <AlliedSanctions code={code} cases={code==='all'?cases:relatedCases} />
  <div className="cx-guardrail"><ShieldCheck size={20}/><div><strong>Relationship confidence is not established by these links</strong><p>These panels join public records on a country field. Allegations, government assessments and estimates retain their separate evidence status. No entity identification, ownership chain, government-direction attribution or causal link is inferred. Source dates and downstream court outcomes require separate verification.</p></div></div>
 </section>;
}
