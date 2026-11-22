import {useEffect,useMemo,useState} from 'react';
import {Activity,ArrowUpRight,Bell,BookOpen,Bookmark,Clock3,ExternalLink,Layers3,Radio,ShieldAlert,ShieldCheck,TriangleAlert} from 'lucide-react';

export type SignalRecord={
  id:string;kind:string;title:string;group:string;source:string;sourceUrl:string;observedAt?:string;
  screened:boolean;fresh:boolean;anomalous:boolean;needsReview:boolean;status:string;confidence?:string;
  modelReviewed:boolean;corroborated?:boolean;reason?:string;severity?:string;sector?:string|null;
};
type Snapshot={schemaVersion:number;generatedAt:string;sourceCheckedAt:string;model?:{status:string;name:string|null};reviews:SignalRecord[];summary?:{observed:number;screened:number;reviewed:number;elevated:number}};
export type SavedWorkspace={id:string;title:string;domain:string;tab:string;country:string;region:string;horizon:string;severity:string;savedAt:string};
export type SignalView={records:SignalRecord[];promoted:SignalRecord[];pending:SignalRecord[];checkedAt?:string;generatedAt?:string;modelStatus?:string;stale:boolean;error:string|null;ready:boolean;filtersApplied:boolean};

const safeDate=(v?:string)=>{const t=Date.parse(v||'');return Number.isFinite(t)?t:0;};
const dateLabel=(v?:string)=>safeDate(v)?new Date(safeDate(v)).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}):'Date not verified';
const valid=(v:unknown):v is Snapshot=>{
  if(!v||typeof v!=='object')return false;
  const s=v as Partial<Snapshot>;
  return s.schemaVersion===1&&typeof s.generatedAt==='string'&&typeof s.sourceCheckedAt==='string'&&
    Array.isArray(s.reviews)&&s.reviews.every(r=>r&&typeof r.id==='string'&&typeof r.title==='string'&&
      typeof r.group==='string'&&typeof r.sourceUrl==='string'&&r.sourceUrl.startsWith('https://')&&
      typeof r.status==='string'&&typeof r.modelReviewed==='boolean');
};
const elevated=(r:SignalRecord,stale:boolean)=>!stale&&r.kind==='metric'&&r.status==='elevated'&&r.fresh===true&&
  r.modelReviewed===true&&r.anomalous===true&&r.corroborated===true;
const pending=(r:SignalRecord)=>r.needsReview===true&&!r.modelReviewed;
const signalAge=(horizon:string)=>horizon==='24h'?86400000:horizon==='7d'?604800000:horizon==='30d'?2592000000:null;

export function useIntelligenceFeed(country:string,horizon:string,severity:string):SignalView{
  const [snapshot,setSnapshot]=useState<Snapshot|null>(null);
  const [error,setError]=useState<string|null>(null);
  const [tick,setTick]=useState(0);
  useEffect(()=>{
    const timer=window.setInterval(()=>setTick(v=>v+1),5*60*1000);
    return()=>window.clearInterval(timer);
  },[]);
  useEffect(()=>{
    let alive=true;
    fetch(String(import.meta.env.BASE_URL||'/')+'analysis/early-warning-triage.json',{cache:'no-store'})
      .then(async response=>{
        if(!response.ok)throw Error('Published analyst review unavailable');
        const body:unknown=await response.json();
        if(!valid(body))throw Error('Published analyst review failed schema validation');
        return body;
      }).then(data=>{if(alive){setSnapshot(data);setError(null);}})
      .catch((e:unknown)=>{if(alive){setSnapshot(null);setError(e instanceof Error?e.message:'Analyst review unavailable');}});
    return()=>{alive=false;};
  },[tick]);
  return useMemo(()=>{
    const generated=safeDate(snapshot?.generatedAt);
    const stale=!!snapshot&&(!generated||generated>Date.now()||Date.now()-generated>72*3600000);
    const maxAge=signalAge(horizon);
    const records=(snapshot?.reviews||[]).filter(r=>{
      if(country!=='all'&&r.group!==country&&r.group!=='global')return false;
      if(maxAge!==null){
        const date=safeDate(r.observedAt);
        if(!date||date>Date.now()+3600000||Date.now()-date>maxAge)return false;
      }
      if(severity==='elevated')return elevated(r,stale);
      if(severity==='review')return pending(r);
      if(severity==='monitor')return !elevated(r,stale)&&!pending(r);
      return true;
    }).sort((a,b)=>safeDate(b.observedAt)-safeDate(a.observedAt));
    return {records,promoted:records.filter(r=>elevated(r,stale)),
      pending:records.filter(pending),checkedAt:snapshot?.sourceCheckedAt,generatedAt:snapshot?.generatedAt,
      modelStatus:snapshot?.model?.status,stale,error,ready:!!snapshot,filtersApplied:country!=='all'||horizon!=='all'||severity!=='all'};
  },[snapshot,country,horizon,severity,error]);
}
function Pill({children,tone='muted'}:{children:React.ReactNode;tone?:'muted'|'hot'|'caution'}){
  return <span className={'ea-ci-pill ea-ci-'+tone}>{children}</span>;
}
function Status({feed}:{feed:SignalView}){
  return feed.error?<div className="ea-ci-unavailable"><TriangleAlert size={15}/> {feed.error}. No live coverage is implied.</div>:
    !feed.ready?<div className="ea-ci-unavailable"><Activity size={15}/> Loading published analyst snapshot…</div>:
    <div className={'ea-ci-freshness'+(feed.stale?' stale':'')}><Clock3 size={13}/> {feed.stale?'Snapshot older than 72 hours · escalations suppressed':'Published analyst snapshot'} · {dateLabel(feed.generatedAt)}</div>;
}
function SignalEntry({item,stale}:{item:SignalRecord;stale:boolean}){
  const isElevated=elevated(item,stale);
  const isPending=pending(item);
  return <article className="ea-ci-entry" key={item.id}>
    <div className="ea-ci-entry-head"><Pill tone={isElevated?'hot':isPending?'caution':'muted'}>{isElevated?'Verified elevated':isPending?'Pending analyst review':'Monitored'}</Pill><time>{dateLabel(item.observedAt)}</time></div>
    <strong>{item.title}</strong>
    <small>{item.group==='global'?'Worldwide context · not country attribution':item.group.startsWith('regional:')?'Regional context · not country attribution':item.group} · {item.source}</small>
    <a href={item.sourceUrl} target="_blank" rel="noopener noreferrer">Original evidence <ArrowUpRight size={12}/></a>
  </article>;
}
export function ContextRail({feed,domain,country,onOpenAlerts}:{feed:SignalView;domain:string;country:string;onOpenAlerts:()=>void}){
  return <aside className="ea-ci-rail" aria-label="Source-backed intelligence context">
    <div className="ea-ci-rail-header"><div><span>CONTEXT / {country==='all'?'WORLDWIDE':country}</span><h2>{domain}</h2></div><button type="button" onClick={onOpenAlerts} title="Inspect complete alert inbox"><Bell size={17}/></button></div>
    <div className="ea-ci-context"><span className="ea-ci-kicker"><ShieldCheck size={14}/> EVIDENCE-GATED STATUS</span>
      <div className="ea-ci-stat-grid">
        <div><strong>{feed.ready?feed.promoted.length:'—'}</strong><span>Verified elevated</span></div>
        <div><strong>{feed.ready?feed.pending.length:'—'}</strong><span>Awaiting review</span></div>
        <div><strong>{feed.ready?feed.records.length:'—'}</strong><span>Visible records</span></div>
      </div>
      <p>{feed.ready?
        feed.promoted.length===0?'No corroborated metric anomalies are currently promoted in this filtered snapshot. This does not indicate an absence of threats.':
        feed.promoted.length+' corroborated metric '+(feed.promoted.length===1?'anomaly is':'anomalies are')+' elevated in the published review.':
        'Summary unavailable until a validated source-backed snapshot loads.'}</p>
      <small>Cross-domain screening context. A source without domain tags is never automatically attributed to {domain}. This panel does not generate new intelligence conclusions.</small>
    </div>
    <Status feed={feed}/>
    <div className="ea-ci-stream-title"><span><Radio size={15}/> DATED SOURCE OBSERVATIONS</span><small>{feed.records.length} records</small></div>
    <div className="ea-ci-stream" aria-label="Chronological source observations">
      {feed.records.slice(0,16).map(r=><SignalEntry key={r.id} item={r} stale={feed.stale}/>)}
      {feed.ready&&feed.records.length===0&&<div className="ea-ci-empty">No dated records match the selected country, time, and alert filters. Other sources may still have coverage gaps.</div>}
    </div>
    <div className="ea-ci-rail-footer">Updates checked every five minutes · dates represent source observations, not continuously streaming telemetry</div>
  </aside>;
}
export function MobileAlerts({feed}:{feed:SignalView}){
  return <section className="ea-mobile-interface" aria-label="Mobile alert inbox">
    <span className="ea-ci-kicker"><ShieldAlert size={16}/> INTELLIGENCE TRIAGE</span><h1>Alert inbox</h1>
    <p>Evidence-graded monitoring for your current global filters. Pending reviews are not flash alerts.</p>
    <div className="ea-ci-mobile-stat"><div><strong>{feed.ready?feed.promoted.length:'—'}</strong><span>Verified elevated</span></div><div><strong>{feed.ready?feed.pending.length:'—'}</strong><span>Review queue</span></div><div><strong>{feed.ready?feed.records.length:'—'}</strong><span>Observed</span></div></div>
    <Status feed={feed}/>
    {feed.ready&&feed.promoted.length===0&&<p className="ea-ci-empty">No analyst-verified flash alerts in this filtered snapshot. Monitored records remain listed below.</p>}
    <div className="ea-ci-mobile-feed">{feed.records.slice(0,35).map(r=><SignalEntry key={r.id} item={r} stale={feed.stale}/>)}</div>
    {feed.ready&&feed.records.length===0&&<p className="ea-ci-empty">No matching observations. Adjust your filters to inspect other records.</p>}
  </section>;
}
export function MobileDomains({items,onSelect}:{items:{id:string;title:string;Icon:typeof Activity}[];onSelect:(id:string)=>void}){
  return <section className="ea-mobile-interface" aria-label="Eight intelligence domains">
    <span className="ea-ci-kicker"><Layers3 size={16}/> GLOBAL DOMAINS</span><h1>Intelligence grid</h1><p>Choose one domain to open its existing research workspace.</p>
    <div className="ea-mobile-domain-grid">{items.map(item=><button type="button" key={item.id} onClick={()=>onSelect(item.id)}>
      <item.Icon size={24}/><span>{item.title}</span></button>)}</div>
  </section>;
}
export function MobileBriefcase({saved,onOpen,onRemove,onSave,onShare}:{saved:SavedWorkspace[];onOpen:(item:SavedWorkspace)=>void;onRemove:(id:string)=>void;onSave:()=>void;onShare:()=>void}){
  return <section className="ea-mobile-interface" aria-label="Saved intelligence workspaces">
    <span className="ea-ci-kicker"><BookOpen size={16}/> RESEARCH BRIEFCASE</span><h1>Your briefcase</h1>
    <p>Saved filter and navigation settings live in this browser. The underlying evidence continues to come from the published sources.</p>
    <div className="ea-ci-brief-actions"><button type="button" onClick={onSave}><Bookmark size={16}/> Save current workspace</button>
      <button type="button" onClick={onShare}><ExternalLink size={16}/> Share mobile handoff link</button></div>
    {saved.length===0?<p className="ea-ci-empty">No saved workspaces yet. Save the current country, domain, and filter settings for quick access.</p>:
      saved.map(item=><article className="ea-ci-saved" key={item.id}>
        <strong>{item.title}</strong><small>{item.country==='all'?'Worldwide':item.country} · {item.horizon} · {item.severity} · saved {dateLabel(item.savedAt)}</small>
        <div><button type="button" onClick={()=>onOpen(item)}>Open workspace</button><button type="button" onClick={()=>onRemove(item.id)}>Remove</button></div>
      </article>)}
    <p className="ea-ci-footnote">Offline synced briefings and push notifications are not enabled; this view will not pretend a notification or PDF exists. You can use your browser’s Print / Save as PDF for the currently loaded page.</p>
  </section>;
}
