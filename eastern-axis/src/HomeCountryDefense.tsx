import {useEffect,useMemo,useState} from 'react';
import {api} from '@appdeploy/client';
import {Activity,ArrowRight,ArrowUpRight,BookOpen,Layers3,ShieldCheck} from 'lucide-react';
import CountryDefenseSnapshot, {defenseForCountry, type CountryDefenseDataset} from './CountryDefenseSnapshot';
import './homeCountryDefense.css';

type Country={code:string;name:string;scope:string};
type Defense=CountryDefenseDataset&{reviewedAsOf?:string};
type Props={
 countries:Country[];
 code:string;
 onCountryOpen:(code:string)=>void;
 onCountryFocus:(code:string)=>void;
 onOpenLibrary:()=>void;
};
type IndexedCountry={code:string;name:string;records:ReturnType<typeof defenseForCountry>;count:number};
const focus=['RU','CN','IR','KP','BY','VE','CU'];
const metric=(n:number)=>n>0?String(n):'—';
function flag(code:string){return /^[A-Z]{2}$/.test(code)?code.replace(/./g,c=>String.fromCodePoint(127397+c.charCodeAt(0))):'🌐';}
export default function HomeCountryDefense({countries,code,onCountryOpen,onCountryFocus,onOpenLibrary}:Props){
 const [data,setData]=useState<Defense|null>(null);
 const [failed,setFailed]=useState(false);
 const [expanded,setExpanded]=useState(false);
 useEffect(()=>{
   let active=true;
   api.get('/api/defense-intel')
     .then(r=>{if(active){setData(r.data as Defense);setFailed(false);}})
     .catch(()=>{if(active){setFailed(true);setData(null);}});
   return()=>{active=false;};
 },[]);
 useEffect(()=>setExpanded(false),[code]);
 const indexed=useMemo(()=>{
   if(!data)return [];
   return countries.filter(c=>c.scope==='state-or-observer').map(c=>{
     const records=defenseForCountry(data,c.code);
     return {code:c.code,name:c.name,records,count:records.assets.length+records.operations.length+records.assessments.length};
   }).filter(c=>c.count>0).sort((a,b)=>{
     const fa=focus.indexOf(a.code),fb=focus.indexOf(b.code);
     return (fa<0?999:fa)-(fb<0?999:fb)||b.count-a.count||a.name.localeCompare(b.name);
   });
 },[countries,data]);
 const current=useMemo(()=>{
   if(code==='all')return null;
   const country=countries.find(c=>c.code===code);
   const records=defenseForCountry(data,code);
   return {code,name:country?.name||code,records,count:records.assets.length+records.operations.length+records.assessments.length};
 },[countries,code,data]);
 const totals=data?{reports:data.assessments.length,operations:data.operations.length,assets:data.assets.length}:null;
 const cards:IndexedCountry[]=code==='all'?(expanded?indexed:indexed.slice(0,4)):(current?[current]:[]);
 return <section className="hcd-root" aria-label="Country-specific defense intelligence on Home">
   <div className="hcd-heading">
     <div>
       <span className="hcd-kicker"><ShieldCheck size={15}/> COUNTRY INTELLIGENCE / SOURCE-ATTRIBUTED</span>
       <h2>{code==='all'?'Defense intelligence by country':(current?.name||code)+' · military intelligence'}</h2>
       <p>Separate source-linked military inventories, reported operations and U.S. or allied government assessments for each country. <strong>Indexed evidence, not live military readiness or threat rankings.</strong></p>
     </div>
     <button type="button" className="hcd-library" onClick={onOpenLibrary}>Full defense library <ArrowRight size={14}/></button>
   </div>
   <div className="hcd-summary" aria-label="Indexed military intelligence record totals">
     <div><BookOpen size={16}/><strong>{totals?metric(code==='all'?totals.reports:current!.records.assessments.length):'—'}</strong><span>Allied assessments</span></div>
     <div><Activity size={16}/><strong>{totals?metric(code==='all'?totals.operations:current!.records.operations.length):'—'}</strong><span>Military operations</span></div>
     <div><Layers3 size={16}/><strong>{totals?metric(code==='all'?totals.assets:current!.records.assets.length):'—'}</strong><span>Military asset entries</span></div>
   </div>
   {failed&&<p className="hcd-warning" role="status">The defense source feed is unavailable. No counts or country capabilities are inferred.</p>}
   {!data&&!failed&&<p className="hcd-warning" role="status">Loading source-linked country intelligence…</p>}
   {data&&code==='all'&&<div className="hcd-grid">
     {cards.map(c=>{
       const asset=c.records.assets.find(item=>item.quantity!=='Not quantified')||c.records.assets[0];
       const operation=c.records.operations[0];
       const assessment=c.records.assessments[0];
       return <article className="hcd-country" key={c.code}>
         <div className="hcd-country-head"><span className="hcd-flag" aria-hidden="true">{flag(c.code)}</span><div><span className="hcd-country-label">{c.name}</span><small>{c.code} · {c.count} indexed source records</small></div><button type="button" aria-label={'Focus dashboard on '+c.name} onClick={()=>onCountryFocus(c.code)}>Focus <ArrowRight size={12}/></button></div>
         <div className="hcd-count-row"><span><strong>{metric(c.records.assessments.length)}</strong> assessments</span><span><strong>{metric(c.records.operations.length)}</strong> operations</span><span><strong>{metric(c.records.assets.length)}</strong> assets</span></div>
         <div className="hcd-highlights">
           {asset&&<a href={asset.url} target="_blank" rel="noopener noreferrer"><Layers3 size={14}/><span><strong>{asset.quantity} · {asset.name}</strong><small>{asset.publisher||'Published estimate'} · {asset.published}</small></span><ArrowUpRight size={13}/></a>}
           {operation&&<a href={operation.url} target="_blank" rel="noopener noreferrer"><Activity size={14}/><span><strong>{operation.title}</strong><small>{operation.published} · country role documented</small></span><ArrowUpRight size={13}/></a>}
           {assessment&&<a href={assessment.url} target="_blank" rel="noopener noreferrer"><BookOpen size={14}/><span><strong>{assessment.title}</strong><small>{assessment.agency} · {assessment.published}</small></span><ArrowUpRight size={13}/></a>}
         </div>
         <button className="hcd-open" type="button" onClick={()=>onCountryOpen(c.code)}>Open {c.name} country dossier <ArrowRight size={14}/></button>
       </article>;
     })}
     {indexed.length===0&&<p className="hcd-warning">No country-tagged defense records are indexed. This is not evidence that countries are unarmed.</p>}
   </div>}
   {data&&code!=='all'&&current&&<CountryDefenseSnapshot code={code} name={current.name} data={data}/>}
   {code==='all'&&data&&indexed.length>4&&<button type="button" className="hcd-more" onClick={()=>setExpanded(v=>!v)}>{expanded?'Show fewer country cards':'View all '+indexed.length+' countries with indexed defense records'} <ArrowRight size={13}/></button>}
   {code!=='all'&&<button type="button" className="hcd-more" onClick={()=>onCountryFocus('all')}>Return to worldwide country comparison <ArrowRight size={13}/></button>}
   <p className="hcd-disclaimer">Sources reviewed {data?.reviewedAsOf||'date unavailable'}. A dash means no reviewed source record, not zero real-world capability. Defense data include military estimates and historical reporting, not verified real-time unit positions.</p>
 </section>;
}
