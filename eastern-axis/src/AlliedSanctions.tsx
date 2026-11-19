import { useEffect,useState } from 'react';
import { api } from '@appdeploy/client';
import { AlertCircle, ArrowUpRight, BookOpenCheck, Building2, Clock3, Database, FileCheck, Network, ShieldCheck } from 'lucide-react';
import './internationalPanels.css';

type Firm = { identifier:string;name:string;kind:string;regime:string;reportedParent?:string };
type Source = {
 id:string;name:string;sourceUrl:string;status:string;lastAttemptAt:string|null;checkedAt:string|null;
 publicationDate:string|null;contentSha256:string|null;listedUniqueDesignations:number|null;
 parsedSourceRows:number|null;regimeRecordCount:number|null;samples:Firm[]|null;
 regimes:Array<{name:string;count:number}>|null;warning:string;
};
type Data = { scope:string;sources:Source[];checkedAt:string;policy:string;graphPolicy:string };
type Case = { id:string;date:string;title:string;status:string;source:string;agency:string };
export default function AlliedSanctions({code,cases}:{code:string;cases:Case[]}) {
 const [data,setData]=useState<Data|null>(null);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState('');
 const [open,setOpen]=useState<'uk'|'canada'|'none'>('canada');
 useEffect(()=>{
  let current=true;setLoading(true);setError('');setData(null);
  api.get('/api/allied-sanctions/'+code)
   .then(r=>{if(current)setData(r.data as Data);})
   .catch(()=>{if(current)setError('Official allied sanctions records could not be loaded. No sanctions status has been assumed.');})
   .finally(()=>{if(current)setLoading(false);});
  return()=>{current=false;};
 },[code]);
 return <section className="ip-section">
  <div className="ip-section-title">
   <div><span className="ip-kicker"><Network size={15}/> OFFICIAL ALLIED SANCTIONS / SOURCE-LINKED</span>
     <h2>What governments actually designated.</h2>
     <p>Two separate jurisdictions. A legal regime is not someone's nationality or an assertion of state responsibility.</p>
   </div>
  </div>
  {loading&&<div className="ip-note"><Clock3 size={15}/> Checking allied source snapshots…</div>}
  {error&&<div className="ip-note"><AlertCircle size={15}/>{error}</div>}
  {data && data.scope===code && Array.isArray(data.sources) && <>
    <div className="ip-legal"><ShieldCheck size={19}/><p>{data.policy}</p></div>
    <div className="ip-sanctions-grid">{data.sources.map(source=><article className="ip-sanction-source" key={source.id}>
       <div className="ip-sanction-head">
        <div><small>{source.id==='uk'?'FCDO · UNITED KINGDOM':'GLOBAL AFFAIRS CANADA'}</small><h3>{source.name}</h3></div>
        <span className={source.status==='snapshot'?'ip-state-active':'ip-state-pending'}>{source.status==='snapshot'?'SOURCE SNAPSHOT':'NOT YET VERIFIED'}</span>
       </div>
       <div className="ip-sanction-stats"><div><strong>{source.listedUniqueDesignations?.toLocaleString()||'—'}</strong><span>Distinct listed entries in source</span></div>
         <div><strong>{source.status==='snapshot'&&code!=='all'&&typeof source.regimeRecordCount==='number'?source.regimeRecordCount.toLocaleString():'—'}</strong><span>Records under selected legal regime</span></div></div>
       <div className="ip-sanction-meta"><span>Checked {source.checkedAt?.slice(0,10)||'Not collected'}</span><span>Source date {source.publicationDate||'Refer to official page'}</span></div>
       <button className="ip-expand" onClick={()=>setOpen(old=>old===source.id?'none':source.id as 'uk'|'canada')} aria-expanded={open===source.id}>{open===source.id?'Hide':'Explore'} source detail</button>
       {open===source.id&&<div className="ip-source-content">
         {!source.checkedAt&&<p>Not yet ingested. The large UK file is checked on the scheduled source rotation. Absence of a snapshot means unknown, not no sanctions.</p>}
         {(source.samples||[]).length>0&&<>
           <p>Selected source-listed organizational examples (not ownership findings):</p>
           {(source.samples||[]).map(s=><div className="ip-firm" key={s.identifier}><Building2 size={15}/><div><strong>{s.name}</strong><small>{s.kind} · ID {s.identifier}</small>{s.reportedParent&&<p>Publisher field “Parent company”: {s.reportedParent} — not independently verified.</p>}</div></div>)}
         </>}
         {code==='all'&&(source.regimes||[]).map(regime=><div key={regime.name} className="ip-regime"><span>{regime.name}</span><strong>{regime.count}</strong></div>)}
         <p>{source.warning}</p>
         <small>{source.contentSha256?'SHA-256 of downloaded source: '+source.contentSha256:'No verified file hash yet'}</small>
       </div>}
       <a className="ip-official" href={source.sourceUrl} target="_blank" rel="noopener noreferrer">Open official published list <ArrowUpRight size={14}/></a>
     </article>)}</div>
    <div className="ip-legal"><FileCheck size={19}/><p>{data.graphPolicy} Duplicate names between jurisdictions are never automatically merged into one identity.</p></div>
  </>}
  <div className="ip-case-heading"><BookOpenCheck size={17}/><div><h3>Case-outcome verification</h3><p>Procedural events in curated DOJ reports, not a continuous docket feed.</p></div></div>
  <div className="ip-case-list">
   {cases.length?cases.slice(0,8).map(c=><article key={c.id}>
      <small>{c.date} · {c.agency}</small><strong>{c.title}</strong>
      <span>Record stage: {c.status}</span>
      <p>Subsequent docket status: <b>not independently checked</b>. Charges and allegations do not establish a later conviction.</p>
      <a href={c.source} target="_blank" rel="noopener noreferrer">Source announcement <ArrowUpRight size={13}/></a>
    </article>):<div className="ip-note">No curated case records for this scope. This does not establish no enforcement activity.</div>}
  </div>
 </section>;
}
