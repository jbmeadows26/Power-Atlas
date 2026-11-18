import {useEffect,useMemo,useState} from 'react';
import {ArrowUpRight,BrainCircuit,CheckCircle2,CircleAlert,Filter,Layers3,RefreshCcw,Search,ShieldCheck} from 'lucide-react';
import './agentDesk.css';

type Connector={id:string;name:string;status:string;detail:string;checkedAt?:string};
type Evidence={id:string;title:string;publisher:string;url:string;date:string;detectedAt:string;countries:string[];changeType:string;sourceId?:string;topics?:string[]};
type Brief={code:string;sourceCount:number;publisherCount:number;publishers:string[];changedCount:number;topics:string[];sourceIds:string[];statement:string};
type Theme={topic:string;sourceCount:number;publisherCount:number;changedCount:number;countries:string[];sourceIds:string[];note:string};
type Relationship={sourceIds:string[];topics:string[];relation:string;note:string};
type Analysis={method:string;recordsAnalyzed:number;countryBriefs:Brief[];themes:Theme[];relatedReports:Relationship[];semantic:{status:string;method:string;model?:string;reason?:string};quality:{sourceTitlesWithoutDates:number;titlesOlderThan30Days:number;publisherCount:number;countryTaggedCount:number};limitations:string[]};
type Manifest={schemaVersion:number;generatedAt:string|null;sourceStatus:string;sourceHealth?:Record<string,string>;method:string;connectors:Connector[];records:Evidence[];analysis?:Analysis|null};
const fmt=(s?:string|null)=>s&&!Number.isNaN(Date.parse(s))?new Date(s).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Date unavailable';
const labels:Record<string,string>={ok:'Connected',error:'Failed','not-configured':'Not configured','not-run':'Not run',disabled:'Disabled'};
const topicNames:Record<string,string>={'cyber':'Cybersecurity','military':'Military & defense','sanctions':'Sanctions','foreign-influence':'Foreign influence','power-energy':'Energy & power','aviation':'Aviation & GNSS','connectivity':'Internet & networks','humanitarian':'Civilian impact','trade-finance':'Trade & finance','other':'Other reporting'};
function evidenceLink(r:Evidence){return <a href={r.url} target="_blank" rel="noopener noreferrer" key={r.id} className="ea-agent-link"><span>{r.publisher} · {r.changeType.replaceAll('-',' ')} · {fmt(r.date)}</span><strong>{r.title}</strong><small>Original source <ArrowUpRight size={13}/></small></a>}
export default function AgentDesk({countryCode}:{countryCode:string}){
 const [state,setState]=useState<Manifest|null>(null);const [error,setError]=useState('');const [loading,setLoading]=useState(false);
 const [query,setQuery]=useState('');const [topic,setTopic]=useState('all');const [showBaseline,setShowBaseline]=useState(false);
 const load=()=>{setLoading(true);setError('');
  fetch(import.meta.env.BASE_URL+'analysis/manifest.json?t='+Date.now(),{cache:'no-store'})
   .then(async r=>{if(!r.ok)throw Error('Missing manifest');return r.json()})
   .then((v:Manifest)=>{if(![1,2].includes(v.schemaVersion)||!Array.isArray(v.connectors)||!Array.isArray(v.records))throw Error('Invalid manifest');setState(v)})
   .catch(()=>{setState(null);setError('Analyst source snapshot unavailable. This is a data gap, not an all-clear.')})
   .finally(()=>setLoading(false));
 };
 useEffect(()=>{load()},[]);
 useEffect(()=>{setTopic('all');setQuery('')},[countryCode]);
 const countryRecords=useMemo(()=>(state?.records||[]).filter(r=>countryCode==='all'||r.countries.includes(countryCode)),[state,countryCode]);
 const sourceIndex=useMemo(()=>new Map((state?.records||[]).map(r=>[r.id,r])),[state]);
 const themes=useMemo(()=>(state?.analysis?.themes||[]).filter(t=>countryCode==='all'||t.countries.includes(countryCode)),[state,countryCode]);
 const records=useMemo(()=>countryRecords.filter(r=>(showBaseline||r.changeType!=='baseline')&&(topic==='all'||r.topics?.includes(topic))&&(!query||(r.title+' '+r.publisher+' '+r.sourceId).toLowerCase().includes(query.toLowerCase()))).slice(0,80),[countryRecords,showBaseline,topic,query]);
 const selectedBrief=state?.analysis?.countryBriefs.find(b=>b.code===countryCode);
 const currentPairs=state?.analysis?.relatedReports.filter(pair=>countryCode==='all'||pair.sourceIds.some(id=>sourceIndex.get(id)?.countries.includes(countryCode)))||[];
 const countNew=countryRecords.filter(r=>r.changeType!=='baseline').length;
 return <section className="ea-agent" aria-label="AI intelligence analyst">
  <header className="ea-agent-head"><div><span className="ea-agent-tag"><BrainCircuit size={16}/> EVIDENCE-LED RESEARCH DESK</span><h1>Intelligence analyst<span className="period">.</span></h1><p>Public-source signals, topic clustering and research-service health. Source mentions are observations; they are not corroborated intelligence conclusions.</p></div><button type="button" disabled={loading} onClick={load}><RefreshCcw size={15}/> Refresh sources</button></header>
  {error&&<div className="ea-agent-error" role="alert"><CircleAlert size={15}/>{error}</div>}
  <div className="ea-agent-stats">
   <span><small>Public records in scope</small><b>{countryRecords.length}</b></span>
   <span><small>New / revised publications</small><b>{countNew}</b></span>
   <span><small>Source publishers</small><b>{new Set(countryRecords.map(r=>r.publisher)).size}</b></span>
   <span><small>Indexed at (UTC)</small><b className="ea-agent-stat-date">{fmt(state?.generatedAt)}</b></span>
  </div>
  {state&&<div className="ea-agent-integrity"><CheckCircle2 size={15}/><span>Official publications: <strong>{state.sourceHealth?.officialPublications||state.sourceStatus}</strong> · DOJ / FARA / CISA intake: <strong>{state.sourceHealth?.governmentIntake||'not assessed'}</strong> · Open-weight similarity: <strong>{state.analysis?.semantic.status||'not assessed'}</strong></span></div>}
  <div className="ea-agent-split">
   <section className="ea-agent-focus"><h2>{countryCode==='all'?'Global source coverage':'Country evidence coverage · '+countryCode}</h2>
    {countryCode!=='all'&&selectedBrief&&<><p className="ea-agent-note">{selectedBrief.statement}</p><div className="ea-agent-statline">Distinct publishers: <strong>{selectedBrief.publisherCount}</strong> · New or revised: <strong>{selectedBrief.changedCount}</strong></div><div className="ea-agent-tags">{selectedBrief.topics.map(t=><span key={t}>{topicNames[t]||t}</span>)}</div></>}
    {countryCode!=='all'&&!selectedBrief&&<p className="ea-agent-empty">No original-source metadata explicitly tags this country in the current snapshot. This is a coverage limitation, not a safety finding.</p>}
    {countryCode==='all'&&<><p className="ea-agent-note">Jurisdictions are counted only when they are explicitly tagged in the original source collector. No affiliations or treaty status are inferred.</p><div className="ea-agent-countries">{(state?.analysis?.countryBriefs||[]).slice().sort((a,b)=>b.sourceCount-a.sourceCount).slice(0,12).map(b=><div key={b.code}><b>{b.code}</b><span>{b.sourceCount} records · {b.publisherCount} publishers</span></div>)}</div></>}
   </section>
   <section className="ea-agent-focus"><h2><Layers3 size={18}/> Topics to review</h2><p className="ea-agent-note">Title-level classification, not a danger ranking. Select one to filter the evidence list.</p><div className="ea-agent-topic-grid">{themes.map(t=><button className={topic===t.topic?'ea-agent-topic selected':'ea-agent-topic'} key={t.topic} type="button" onClick={()=>setTopic(v=>v===t.topic?'all':t.topic)} aria-pressed={topic===t.topic}><strong>{topicNames[t.topic]||t.topic}</strong><span>{t.sourceCount} titles</span><small>{t.publisherCount} publisher{t.publisherCount===1?'':'s'} · {t.changedCount} changed</small></button>)}</div>{themes.length===0&&<p className="ea-agent-note">No tagged topics for this scope.</p>}</section>
  </div>
  <section className="ea-agent-section"><div className="ea-agent-section-heading"><h2>Research services</h2><span>Optional connectors · actual connection states</span></div><div className="ea-agent-grid">{(state?.connectors||[]).map(c=><article className="ea-agent-card" key={c.id}><div><strong>{c.name}</strong><small data-status={c.status}>{labels[c.status]||'Unknown'}</small></div><p>{c.detail}</p>{c.checkedAt&&<span>Checked {fmt(c.checkedAt)}</span>}</article>)}</div>{!state&&!loading&&<p className="ea-agent-note">Connector health has not been verified.</p>}</section>
  {currentPairs.length>0&&<section className="ea-agent-section"><h2>Possibly related source titles</h2><p className="ea-agent-note">Open-weight model identified title similarity between different publishers. Similarity is not independent verification of either report.</p><div className="ea-agent-pairs">{currentPairs.slice(0,6).map((pair,i)=><article key={pair.sourceIds.join('-')||i}><span>{pair.topics.map(t=>topicNames[t]||t).join(' / ')}</span>{pair.sourceIds.map(id=>sourceIndex.get(id)).filter((v):v is Evidence=>Boolean(v)).map(evidenceLink)}</article>)}</div></section>}
  <section className="ea-agent-section"><div className="ea-agent-section-heading"><h2>Original-source evidence</h2><span>{records.length} visible of {countryRecords.length}</span></div>
   <div className="ea-agent-filters"><label><Search size={15}/><input aria-label="Search analyst evidence" placeholder="Search original-source titles…" value={query} onChange={e=>setQuery(e.target.value)}/></label><label><Filter size={14}/><select aria-label="Filter analyst topic" value={topic} onChange={e=>setTopic(e.target.value)}><option value="all">All topics</option>{themes.map(t=><option key={t.topic} value={t.topic}>{topicNames[t.topic]||t.topic}</option>)}</select></label><button type="button" aria-pressed={showBaseline} onClick={()=>setShowBaseline(v=>!v)}>{showBaseline?'Hide baseline':'Include baseline'}</button></div>
   <p className="ea-agent-note">New means newly detected by the collector, not newly confirmed military activity. Entries from investigative intake are baselines until specifically reviewed.</p>
   <div className="ea-agent-records">{records.map(evidenceLink)}</div>{state&&records.length===0&&<p className="ea-agent-empty">No records match these filters. Try including the baseline; zero results do not indicate low risk.</p>}
  </section>
  <footer><ShieldCheck size={16}/><div>{state?.analysis?.method||state?.method||'Awaiting a verified source digest.'}<p>AI-generated claims are never auto-published. Full-text reading, independent corroboration, attribution and analyst review are still required. {state?.analysis?.semantic.method||''}</p></div></footer>
 </section>;
}
