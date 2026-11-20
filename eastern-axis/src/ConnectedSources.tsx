import {useEffect,useState} from 'react';
import {api} from '@appdeploy/client';
import {ArrowUpRight,Database,RefreshCcw} from 'lucide-react';
import './connectedSources.css';

type Feed={id:string;name:string;health:null|{status:string;lastSuccessAt?:string;lastAttemptAt?:string;examined?:number;inserted?:number;lastError?:string};documentation?:string};
const names:Record<string,string>={doj:'DOJ',ofac:'OFAC',fara:'FARA',cisa:'CISA'};
const sources:Record<string,string>={doj:'https://www.justice.gov/',ofac:'https://ofac.treasury.gov/',fara:'https://efile.fara.gov/',cisa:'https://www.cisa.gov/known-exploited-vulnerabilities-catalog'};
const format=(iso?:string)=>iso&&Number.isFinite(Date.parse(iso))?new Date(iso).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZone:'UTC'})+' UTC':'Unknown';
export default function ConnectedSources(){
 const [feeds,setFeeds]=useState<Feed[]|null>(null),[fail,setFail]=useState(false),[expanded,setExpanded]=useState(false),[refresh,setRefresh]=useState(0);
 useEffect(()=>{let active=true;setFeeds(null);setFail(false);
   api.get('/api/intelligence').then(r=>{if(active)setFeeds((r.data as {sources:Feed[]}).sources||[]);}).catch(()=>{if(active)setFail(true)});
   return()=>{active=false};
 },[refresh]);
 const list=['doj','ofac','fara','cisa'].map(id=>feeds?.find(f=>f.id===id)||{id,name:names[id],health:null});
 const recorded=list.filter(f=>f.health?.lastSuccessAt).length;
 return <section className="cs-root" aria-label="Connected sources and collector freshness">
  <header><div><span><Database size={14}/> SOURCE COLLECTION / HEALTH</span><h2>Source connections</h2><p>Last verified collection, not a guarantee of current coverage</p></div>
   <button type="button" onClick={()=>setRefresh(n=>n+1)}><RefreshCcw size={14}/> Recheck</button></header>
  <div className="cs-headline"><strong>{feeds?recorded+'/4':fail?'Unavailable':'—'}</strong><div><span>Feeds with recorded successful collection</span><small>DOJ · OFAC · FARA · CISA</small></div></div>
  <div className="cs-feed-grid">{list.map(f=>{
    const success=f.health?.lastSuccessAt,elapsed=success?Date.now()-Date.parse(success):Infinity,ok=Number.isFinite(elapsed)&&elapsed<24*3600000;
    return <div key={f.id} className="cs-feed"><div><b>{names[f.id]||f.id}</b><span className={ok?'recent':'unknown'}>{ok?'RECENT':success?'AGING':'NO SUCCESS DATA'}</span></div><span className="cs-time">{format(success)}</span><div className="cs-meter"><i style={{width:ok?'100%':success?'45%':'0%'}}/></div></div>;
  })}</div>
  <div className="cs-footer"><span>{fail?'Collector API unavailable; cannot infer feed health.':'Green = successful collection within 24h; this is not a source completeness score.'}</span><button type="button" aria-expanded={expanded} onClick={()=>setExpanded(v=>!v)}>{expanded?'Hide collector records':'View collector records'} <ArrowUpRight size={13}/></button></div>
  {expanded&&<div className="cs-details">{list.map(f=><div key={f.id}><strong>{f.name||names[f.id]}</strong><small>Last attempt: {format(f.health?.lastAttemptAt)} · Last success: {format(f.health?.lastSuccessAt)}</small><small>{f.health?.lastError?'Last reported error: '+f.health.lastError:'No error details supplied'}</small><a href={sources[f.id]} target="_blank" rel="noopener noreferrer">Original publisher <ArrowUpRight size={12}/></a></div>)}</div>}
 </section>;
}