import {useEffect,useId,useState} from 'react';
import {createPortal} from 'react-dom';
import {ArrowUpRight,Clock3,ExternalLink,FileJson,ShieldCheck,X} from 'lucide-react';
import './evidenceViewer.css';

/**
 * Keep publisher evidence distinct from analyst screening. The publisher record is
 * never altered and remains available via its exact HTTPS URL.
 */
type EvidenceLinkProps={
  title:string;
  source:string;
  sourceUrl:string;
  observedAt?:string;
  group?:string;
  status?:string;
  reason?:string;
  label?:string;
};

type NwsAlert={
  event?:string;
  headline?:string;
  areaDesc?:string;
  description?:string;
  instruction?:string;
  senderName?:string;
  sent?:string;
  effective?:string;
  onset?:string;
  expires?:string;
  ends?:string;
  severity?:string;
  urgency?:string;
  certainty?:string;
  status?:string;
  messageType?:string;
};

function readable(value:unknown):string|undefined{
  return typeof value==='string'&&value.trim()?value.trim():undefined;
}
function parseNwsAlert(value:unknown):NwsAlert|null{
  if(!value||typeof value!=='object')return null;
  const root=value as Record<string,unknown>;
  if(!root.properties||typeof root.properties!=='object')return null;
  const props=root.properties as Record<string,unknown>;
  const result:NwsAlert={};
  for(const key of ['event','headline','areaDesc','description','instruction','senderName',
    'sent','effective','onset','expires','ends','severity','urgency','certainty',
    'status','messageType'] as const){
    result[key]=readable(props[key]);
  }
  return result.event||result.headline?result:null;
}
function isNwsAlertUrl(url:string):boolean{
  try{
    const target=new URL(url);
    return target.protocol==='https:'&&target.hostname==='api.weather.gov'&&
      target.pathname.startsWith('/alerts/');
  }catch{return false;}
}
function safeSource(url:string):string|null{
  try{
    const u=new URL(url);
    return u.protocol==='https:'?u.href:null;
  }catch{return null;}
}
function formattedTime(value?:string):string{
  if(!value)return 'Not supplied by publisher';
  const date=new Date(value);
  return Number.isFinite(date.getTime())?date.toLocaleString(undefined,{
    year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',
    timeZoneName:'short'
  }):'Invalid publisher timestamp';
}
function Line({name,value}:{name:string;value?:string}){
  return <div className="ea-ev-field"><dt>{name}</dt><dd>{value||'Not supplied'}</dd></div>;
}

export default function EvidenceLink({title,source,sourceUrl,observedAt,group,status,reason,label='View evidence'}:EvidenceLinkProps){
  const [open,setOpen]=useState(false);
  const [state,setState]=useState<'idle'|'loading'|'loaded'|'failed'>('idle');
  const [alert,setAlert]=useState<NwsAlert|null>(null);
  const headingId=useId();
  const url=safeSource(sourceUrl);
  const nws=!!url&&isNwsAlertUrl(url);

  useEffect(()=>{
    if(!open||!nws||!url)return;
    const abort=new AbortController();
    setState('loading');
    setAlert(null);
    fetch(url,{signal:abort.signal,headers:{Accept:'application/geo+json, application/json'},cache:'no-store'})
      .then(async response=>{
        if(!response.ok)throw Error('Publisher response unavailable');
        return parseNwsAlert(await response.json());
      })
      .then(parsed=>{
        if(abort.signal.aborted)return;
        setAlert(parsed);
        setState(parsed?'loaded':'failed');
      })
      .catch(()=>{if(!abort.signal.aborted)setState('failed');});
    return()=>abort.abort();
  },[open,nws,url]);

  useEffect(()=>{
    if(!open)return;
    const onKey=(event:KeyboardEvent)=>{if(event.key==='Escape')setOpen(false);};
    window.addEventListener('keydown',onKey);
    return()=>window.removeEventListener('keydown',onKey);
  },[open]);

  const endDate=alert?.ends||alert?.expires;
  const expired=!!endDate&&Number.isFinite(Date.parse(endDate))&&Date.parse(endDate)<=Date.now();
  const isActual=alert?.status==='Actual';
  return <>
    <button type="button" className="ea-ev-open" onClick={()=>setOpen(true)}
      aria-label={label+': '+title}>{label}<ArrowUpRight size={14} aria-hidden="true"/></button>
    {open&&createPortal(
      <div className="ea-ev-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setOpen(false);}}>
        <section className="ea-ev-modal" role="dialog" aria-modal="true" aria-labelledby={headingId}>
          <div className="ea-ev-head">
            <div><span className="ea-ev-kicker"><ShieldCheck size={15}/> VERIFIED SOURCE REFERENCE</span>
              <h2 id={headingId}>{alert?.event||title}</h2></div>
            <button type="button" className="ea-ev-close" onClick={()=>setOpen(false)}
              aria-label="Close evidence"><X size={20}/></button>
          </div>
          <p className="ea-ev-subtitle">{source} · {group==='global'?'Worldwide':group||'Unattributed'}</p>
          <div className="ea-ev-tagline">
            <span>Evidence source · {nws?'NOAA / National Weather Service':'External publisher'}</span>
            {alert&&<span className={expired?'ea-ev-expired':'ea-ev-current'}>
              {expired?'Publisher warning expired':isActual?'Actual publisher alert':alert.status||'Publisher alert'}</span>}
          </div>
          {nws&&state==='loading'&&<p className="ea-ev-note">Retrieving the original NOAA advisory details…</p>}
          {nws&&state==='failed'&&<p className="ea-ev-note">The live NOAA record could not be displayed here. Its original link is preserved below; the details have not been guessed or reconstructed.</p>}
          {alert&&<>
            {alert.headline&&<p className="ea-ev-headline">{alert.headline}</p>}
            <dl className="ea-ev-facts">
              <Line name="Affected area" value={alert.areaDesc}/>
              <Line name="Issued by" value={alert.senderName}/>
              <Line name="Source severity" value={alert.severity}/>
              <Line name="Urgency / certainty" value={[alert.urgency,alert.certainty].filter(Boolean).join(' / ')}/>
              <Line name="Issued" value={formattedTime(alert.sent)}/>
              <Line name="Effective" value={formattedTime(alert.effective||alert.onset)}/>
              <Line name="Expires / ends" value={formattedTime(endDate)}/>
              <Line name="Publisher status" value={[alert.status,alert.messageType].filter(Boolean).join(' · ')}/>
            </dl>
            {alert.description&&<div className="ea-ev-section"><h3>Official advisory</h3><p>{alert.description}</p></div>}
            {alert.instruction&&<div className="ea-ev-section"><h3>Official safety instructions</h3><p>{alert.instruction}</p></div>}
          </>}
          <div className="ea-ev-section ea-ev-analyst">
            <h3>Eastern Axis screening context</h3>
            <dl className="ea-ev-facts">
              <Line name="Triage status" value={status}/>
              <Line name="Observed in snapshot" value={observedAt?formattedTime(observedAt):'Not supplied'}/>
            </dl>
            {reason?<p>{reason}</p>:<p>Source record collected for monitoring. No independent assessment is implied by its appearance here.</p>}
            <small>Publisher classification and Eastern Axis analyst status are different. Expiry describes the warning's validity, not necessarily its historical research value.</small>
          </div>
          <div className="ea-ev-actions">
            {url&&<a href={url} target="_blank" rel="noopener noreferrer">
              {nws?<FileJson size={17}/>:<ExternalLink size={17}/>}
              {nws?'View raw NOAA record':'Open original publisher source'}<ArrowUpRight size={15}/></a>}
            <button type="button" onClick={()=>setOpen(false)}>Back to alerts</button>
          </div>
          <p className="ea-ev-footnote"><Clock3 size={13}/> Publisher content is loaded from its official URL where supported. Source data is not rewritten or represented as analyst-verified intelligence.</p>
        </section>
      </div>,document.body)}
  </>;
}
