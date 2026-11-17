import { useEffect, useState } from 'react';
import { api } from './apiClient';
import { Activity, ArrowUpRight, BookOpenCheck, BrainCircuit, CircleAlert, RefreshCcw, ShieldCheck } from 'lucide-react';
import './intelInsights.css';

type Link = { label:string; title:string; url:string; agency?:string; publisher?:string; published?:string };
type AIResult = { status:string; text:string; mode?:string; generatedAt?:string; reused?:boolean; sources:Link[] };
type Health = { status:'ok'|'error'; lastAttemptAt:string; lastSuccessAt?:string; lastError?:string; changed:number; baselined:number };
type Feed = {id:string;name:string;url:string;health:Health|null};
type Record = {id:string;publisher:string;title:string;url:string;published:string;changedAt:string;countryMentions:string[];changeType:'baseline'|'new-publication'|'source-revised';excerpt:string};
type Watch = {feeds:Feed[];records:Record[];mode:string;explanation:string;nextScan:string};
type Props = { code?:string; countryName?:string; mode:'country'|'global' };
const fmt = (date?:string) => date ? new Date(date.length===10?date+'T12:00:00Z':date).toLocaleString('en-US',{month:'short',day:'numeric',year:'numeric'}) : 'Date unknown';

function AIText({value}:{value:AIResult}){
 return <div className="ii-answer" aria-live="polite">
  <div className="ii-answer-meta"><ShieldCheck size={14}/>{value.mode||'Evidence-limited AI summary'} · {value.generatedAt ? 'Generated '+fmt(value.generatedAt) : 'No generation needed'}{value.reused?' · Cached':''}</div>
  <div className="ii-answer-body">{value.text}</div>
  {value.sources.length>0&&<div className="ii-source-links">{value.sources.map(s=><a href={s.url} key={s.label} target="_blank" rel="noopener noreferrer"><span className="ii-source-label">[{s.label}]</span> {s.title} <ArrowUpRight size={12}/></a>)}</div>}
 </div>;
}
export default function IntelInsights({code,countryName,mode}:Props){
 const [comparison,setComparison] = useState<AIResult|null>(null);
 const [comparisonBusy,setComparisonBusy] = useState(false);
 const [comparisonError,setComparisonError] = useState('');
 const [watch,setWatch] = useState<Watch|null>(null);
 const [watchError,setWatchError] = useState('');
 const [watchLoading,setWatchLoading] = useState(true);
 const [analysis,setAnalysis] = useState<AIResult|null>(null);
 const [analysisBusy,setAnalysisBusy] = useState(false);
 const [analysisError,setAnalysisError] = useState('');
 const [showBaseline,setShowBaseline] = useState(false);
 const loadMonitor=()=>{
  setWatchLoading(true);setWatchError('');
  api.get('/api/source-monitor').then(r=>setWatch(r.data as Watch))
    .catch(()=>setWatchError('Source monitoring status unavailable. No changes can be confirmed.'))
    .finally(()=>setWatchLoading(false));
 };
 useEffect(()=>{setComparison(null);setComparisonError('');setAnalysis(null);setAnalysisError('');loadMonitor();},[code,mode]);
 const compare=()=>{
  setComparisonError('');setComparisonBusy(true);setComparison(null);
  api.post('/api/compare-allies',{code})
    .then(r=>setComparison(r.data as AIResult))
    .catch(()=>setComparisonError('AI comparison unavailable or usage limit reached. The original linked reports remain available.'))
    .finally(()=>setComparisonBusy(false));
 };
 const summarize=()=>{
  setAnalysisError('');setAnalysisBusy(true);setAnalysis(null);
  api.post('/api/watch-analyze',{code:code||''})
    .then(r=>setAnalysis(r.data as AIResult))
    .catch(()=>setAnalysisError('AI review unavailable or usage limit reached. Original official-feed entries remain available.'))
    .finally(()=>setAnalysisBusy(false));
 };
 const visible=(watch?.records||[]).filter(r=>(!code||r.countryMentions.includes(code))&&(showBaseline||r.changeType!=='baseline')).slice(0,mode==='country'?6:16);
 const changes=(watch?.records||[]).filter(r=>r.changeType!=='baseline'&&(!code||r.countryMentions.includes(code)));
 return <div className={'ii-root '+(mode==='country'?'ii-narrow':'')}>
   {mode==='country'&&<section className="ii-panel">
     <div className="ii-heading"><span className="ii-kicker"><BrainCircuit size={14}/> ALLIED PERSPECTIVES</span><h3>Where do governments agree?</h3><p>Compare public assessments referring to {countryName||code}. The AI compares curated summaries, not full classified or unpublished reports.</p></div>
     <button className="ii-action" onClick={compare} disabled={comparisonBusy}>{comparisonBusy?'Comparing assessments…':'Compare allied analysis'} <ArrowUpRight size={14}/></button>
     {comparisonError&&<div className="ii-warning"><CircleAlert size={13}/>{comparisonError}</div>}
     {comparison&&<AIText value={comparison}/>}
   </section>}
   <section className="ii-panel">
    <div className="ii-heading"><span className="ii-kicker"><Activity size={14}/> PUBLICATION CHANGE MONITOR</span><h3>{mode==='country'?'New official reporting':'Official-source change tracker'}</h3><p>Checks official U.S. defense, UK defense and UN news feeds daily. Sources retain actual last-check times. The first collection is a baseline, not an alert.</p></div>
    {watchLoading&&<div className="ii-quiet">Checking stored feed status…</div>}
    {watchError&&<div className="ii-warning"><CircleAlert size={13}/>{watchError}</div>}
    {watch&&<>
      <div className="ii-stats"><span>{changes.length} changed items visible</span><span>{watch.feeds.filter(f=>f.health?.status==='ok').length} / {watch.feeds.length} feeds last checked successfully</span></div>
      {mode==='global'&&<div className="ii-health">{watch.feeds.map(f=><a href={f.url} target="_blank" rel="noopener noreferrer" key={f.id} className="ii-feed">
       <span>{f.name}</span><small>{f.health?.status==='ok'?'Checked '+fmt(f.health.lastSuccessAt):f.health?.status==='error'?'Feed error: '+(f.health.lastError||'Unknown'):'Awaiting first scheduled check'} <ArrowUpRight size={12}/></small>
      </a>)}</div>}
      <div className="ii-controls">
       <button type="button" className="ii-secondary" onClick={()=>setShowBaseline(v=>!v)}>{showBaseline?'Hide initial baseline':'Show baseline records'}</button>
       <button type="button" className="ii-secondary" onClick={loadMonitor}><RefreshCcw size={13}/> Refresh</button>
      </div>
      <div className="ii-records">
       {visible.length===0&&<p className="ii-quiet">No tracked new or revised publications for this filter yet. Feed checks may be pending. This is not evidence of no military activity.</p>}
       {visible.map(item=><a className="ii-record" href={item.url} key={item.id} target="_blank" rel="noopener noreferrer">
        <span className="ii-record-meta">{item.changeType==='baseline'?'BASELINE':item.changeType==='new-publication'?'NEW PUBLICATION':'SOURCE REVISED'} · {item.publisher} · Published {fmt(item.published)}</span>
        <strong>{item.title}</strong>
        <small>Detected {fmt(item.changedAt)} · Unreviewed headline metadata{item.countryMentions.length?' · Country mentions: '+item.countryMentions.join(', '):''}</small>
       </a>)}
      </div>
      <button className="ii-action" onClick={summarize} disabled={analysisBusy||changes.length===0}>{analysisBusy?'Reviewing changes…':'AI review of new reporting'} <BookOpenCheck size={14}/></button>
      {analysisError&&<div className="ii-warning"><CircleAlert size={13}/>{analysisError}</div>}
      {analysis&&<AIText value={analysis}/>}
      <p className="ii-small-note">{watch.explanation} New publications are not validated capability changes, and no live unit positions are collected.</p>
    </>}
   </section>
 </div>;
}
