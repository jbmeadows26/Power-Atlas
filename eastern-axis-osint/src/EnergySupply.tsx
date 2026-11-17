import { useEffect, useMemo, useState } from 'react';
import { api } from './apiClient';
import { ArrowUpRight, Bolt, Database, Factory, Fuel, Globe2, RefreshCcw, ShieldCheck } from 'lucide-react';
import './internationalPanels.css';

type Metric = { key:string; label:string; unit:string; group:string; meaning:string; value:number|null; year:number|null };
type Energy = {
 code:string; checkedAt:string|null; status:string; sourceName:string; sourceUrl:string; downloadUrl:string;
 sourceHash:string|null; countryCount:number|null; parsedRows:number|null;
 location:string; indicators:Metric[]; warning:string; interpretation:string;
};
const display=(value:number)=>value.toLocaleString('en-US',{maximumFractionDigits:1});
const symbols:Record<string, typeof Factory> = {
 'Fuel production':Fuel,'Energy supply':Factory,'Electricity systems':Bolt
};
export default function EnergySupply({code}:{code:string}) {
 const [data,setData]=useState<Energy|null>(null);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState('');
 const [revision,setRevision]=useState(0);
 useEffect(()=>{
  let current=true;setData(null);setLoading(true);setError('');
  api.get('/api/energy-supply/'+code)
   .then(r=>{if(current)setData(r.data as Energy);})
   .catch(()=>{if(current)setError('Physical energy data could not be loaded. Existing World Bank indicators remain independent.');})
   .finally(()=>{if(current)setLoading(false);});
  return()=>{current=false;};
 },[code,revision]);
 const groups=useMemo(()=>Array.from(new Set(data?.indicators.map(item=>item.group)||[])),[data]);
 return <section className="ip-section">
   <div className="ip-section-title">
    <div><span className="ip-kicker"><Factory size={15}/> PHYSICAL ENERGY / OBSERVED ANNUAL DATA</span>
     <h2>Production is power. So is dependence.</h2>
     <p>Measured fuel production, energy supply and electricity—not proxies inferred from GDP.</p>
    </div>
    <button className="ip-reload" onClick={()=>setRevision(x=>x+1)} disabled={loading}><RefreshCcw size={14}/> Refresh</button>
   </div>
   {(loading||error||data?.status!=='reported')&&<div className="ip-note">{loading?'Retrieving country energy observations…':error||data?.warning||'No matching source observations.'}</div>}
   {data?.status==='reported'&&<>
     <div className="ip-summarybar"><Globe2 size={16}/><strong>{data.location}</strong><span>{data.countryCount} countries indexed · Collected {data.checkedAt?.slice(0,10)} · Latest year differs by metric</span></div>
     <div className="ip-energy-groups">{groups.map(group=>{
      const Icon=symbols[group]||Database;
      return <section className="ip-energy-group" key={group}>
       <h3><Icon size={15}/>{group}</h3>
       <div className="ip-energy-grid">{data.indicators.filter(i=>i.group===group).map(item=><article key={item.key}>
        <strong>{item.label}</strong>
        <div className="ip-energy-number">{item.value===null?'—':display(item.value)}</div>
        <small>{item.value===null?'Not reported':item.unit+' · '+item.year}</small>
        <p>{item.meaning}</p>
       </article>)}</div>
      </section>;
     })}</div>
    <p className="ip-method"><ShieldCheck size={17}/> {data.interpretation} {data.warning}</p>
   </>}
   <div className="ip-source-link">Source: <a href="https://catalog.ourworldindata.org/energy/owid_energy/" target="_blank" rel="noopener noreferrer">Our World in Data energy catalog <ArrowUpRight size={12}/></a><span>Source version, upstream providers, CC BY attribution and methodology available at the catalog.</span></div>
 </section>;
}
