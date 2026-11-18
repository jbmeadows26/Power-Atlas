import {useEffect,useMemo,useState} from 'react';
import {BrainCircuit,RefreshCcw,ShieldCheck,ArrowUpRight,CircleAlert} from 'lucide-react';
import './agentDesk.css';
type Connector={id:string;name:string;status:string;detail:string;checkedAt?:string};
type Evidence={id:string;title:string;publisher:string;url:string;date:string;detectedAt:string;countries:string[];changeType:string};
type Manifest={schemaVersion:number;generatedAt:string|null;sourceStatus:string;method:string;connectors:Connector[];records:Evidence[]};
const fmt=(s?:string|null)=>s&&!Number.isNaN(Date.parse(s))?new Date(s).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Not checked';
const labels:Record<string,string>={ok:'Connected',error:'Failed','not-configured':'Not configured','not-run':'Not run',disabled:'Disabled'};
export default function AgentDesk({countryCode}:{countryCode:string}){
 const [state,setState]=useState<Manifest|null>(null);const [error,setError]=useState('');const [loading,setLoading]=useState(false);
 const load=()=>{setLoading(true);setError('');
  fetch(import.meta.env.BASE_URL+'analysis/manifest.json?t='+Date.now(),{cache:'no-store'})
   .then(async r=>{if(!r.ok)throw Error('Missing manifest');return r.json()})
   .then((v:Manifest)=>{if(v.schemaVersion!==1||!Array.isArray(v.connectors)||!Array.isArray(v.records))throw Error('Invalid manifest');setState(v)})
   .catch(()=>{setState(null);setError('Analyst source snapshot unavailable. This does not indicate low risk.')})
   .finally(()=>setLoading(false));
 };
 useEffect(()=>{load()},[]);
 const records=useMemo(()=>(state?.records||[]).filter(r=>countryCode==='all'||r.countries.includes(countryCode)).slice(0,60),[state,countryCode]);
 return <section className="ea-agent" aria-label="AI intelligence analyst">
  <header className="ea-agent-head"><div><span className="ea-agent-tag"><BrainCircuit size={15}/> RESEARCH AND ANALYSIS</span><h1>Intelligence analyst<span className="period">.</span></h1><p>Open-source intelligence with attributable evidence. AI-generated assessments remain unpublished until checked by an analyst.</p></div><button type="button" disabled={loading} onClick={load}><RefreshCcw size={15}/> Refresh</button></header>
  {error&&<p className="ea-agent-error" role="alert"><CircleAlert size={15}/>{error}</p>}
  <div className="ea-agent-stats"><span>Snapshot: <b>{fmt(state?.generatedAt)}</b></span><span>Official feed: <b>{state?.sourceStatus==='ok'?'Checked':'Not verified'}</b></span><span>Country records: <b>{records.length}</b></span></div>
  <h2>Integrated research services</h2><div className="ea-agent-grid">{(state?.connectors||[]).map(c=><article className="ea-agent-card" key={c.id}><div><strong>{c.name}</strong><small data-status={c.status}>{labels[c.status]||'Unknown'}</small></div><p>{c.detail}</p>{c.checkedAt&&<span>Checked {fmt(c.checkedAt)}</span>}</article>)}</div>
  {!state&&!loading&&<p className="ea-agent-note">Connector health has not been verified.</p>}
  <h2>Official-source changes {countryCode==='all'?'· global':'· '+countryCode}</h2>
  <p className="ea-agent-note">Publication metadata only. Country mentions do not prove attribution, wrongdoing, military activity, or a change in risk.</p>
  <div className="ea-agent-records">{records.map(r=><a key={r.id} href={r.url} target="_blank" rel="noopener noreferrer"><small>{r.publisher} · {r.changeType.replaceAll('-',' ')} · Published {fmt(r.date)}</small><strong>{r.title}</strong><span>Indexed {fmt(r.detectedAt)} <ArrowUpRight size={13}/></span></a>)}</div>
  {state&&records.length===0&&<p className="ea-agent-empty">No validated records for this selection. This is not an all-clear.</p>}
  <footer><ShieldCheck size={16}/>{state?.method||'Awaiting an independently checked source digest.'} Model output remains a review-only workflow artifact.</footer>
 </section>;
