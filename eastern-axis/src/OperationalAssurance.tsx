import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Clock3, ExternalLink, RefreshCcw, ShieldAlert } from 'lucide-react';
import './operationalAssurance.css';

type Health = 'ok' | 'warning' | 'stale' | 'unknown' | 'pending';
type Check = { id:string; title:string; status:Health; detail:string; at?:string; href:string; scope:string };
type Json = Record<string, unknown>;

const REPO = 'https://github.com/jbmeadows26/Power-Atlas';
const LIVE = 'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json';
const API = 'https://api.github.com/repos/jbmeadows26/Power-Atlas/actions/workflows/';
const entries: Check[] = [
  {id:'early', title:'Early-warning collection', status:'pending', detail:'Checking published source-level results', href:REPO+'/actions/workflows/eastern-axis-early-warning.yml', scope:'Published source snapshot'},
  {id:'resilience', title:'Resilience telemetry', status:'pending', detail:'Checking independent observations', href:LIVE, scope:'Public sampled telemetry'},
  {id:'release', title:'GitHub Pages release', status:'pending', detail:'Checking latest main-branch release', href:REPO+'/actions/workflows/deploy-pages.yml', scope:'Build and publication, not uptime'},
  {id:'browser', title:'Live production browser QA', status:'pending', detail:'Checking latest real production browser run', href:REPO+'/actions/workflows/eastern-axis-pages-live-qa.yml', scope:'Deployed-site QA (deployment / schedule / manual), never PR previews'},
];

function object(value:unknown):value is Json {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function stamp(iso:unknown):number | null {
  if (typeof iso !== 'string') return null;
  const ms=Date.parse(iso);
  return Number.isFinite(ms) ? ms : null;
}
function ageState(iso:unknown, maxHours:number):'fresh'|'stale'|'unknown' {
  const ms=stamp(iso);
  if (ms===null) return 'unknown';
  const elapsed=Date.now()-ms;
  if (elapsed < -5*60_000) return 'unknown';
  return elapsed > maxHours*3_600_000 ? 'stale' : 'fresh';
}
function displayDate(iso?:string):string {
  const ms=stamp(iso);
  return ms===null?'No valid timestamp':new Date(ms).toLocaleString('en-US',{
    month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit',timeZone:'UTC'
  })+' UTC';
}
async function json(url:string, signal:AbortSignal):Promise<Json> {
  const response=await fetch(url,{cache:'no-store',signal,headers:{Accept:'application/json'}});
  if(!response.ok) throw new Error('HTTP '+response.status);
  const payload:unknown=await response.json();
  if (!object(payload)) throw new Error('Invalid response object');
  return payload;
}
function checkEarly(data:Json):Check {
  const base=entries[0];
  if (data.schemaVersion!==1 || !Array.isArray(data.sources) || !Array.isArray(data.metrics))
    throw new Error('Unexpected early-warning schema');
  const health=data.sources.filter(object);
  const failures=health.filter(x=>x.status==='error').length;
  const successes=health.filter(x=>x.status==='ok').length;
  const freshness=ageState(data.checkedAt,48);
  const at=typeof data.checkedAt==='string'?data.checkedAt:undefined;
  const metrics=data.metrics.filter(object);
  const dated=metrics.filter(m=>typeof m.period==='string').length;
  const status:Health=freshness==='unknown'?'unknown':freshness==='stale'?'stale':
    !health.length||!successes?'warning':failures?'warning':'ok';
  return {...base,status,at,detail:health.length+' adapters reported ('+successes+' ok, '+failures+' errors); '+dated+' source-dated metrics. '+(freshness==='stale'?'Snapshot is older than 48 hours.':'Adapter success does not certify the underlying observation is current.')};
}
function checkResilience(data:Json):Check {
  const base=entries[1];
  if(data.schemaVersion!==1||!Array.isArray(data.observations)||!Array.isArray(data.capabilities))
    throw new Error('Unexpected resilience schema');
  const freshness=ageState(data.checkedAt,2);
  const at=typeof data.checkedAt==='string'?data.checkedAt:undefined;
  const obs=data.observations.filter(object);
  const collected=obs.filter(x=>x.status==='observed'||x.status==='warning').length;
  const failures=obs.filter(x=>x.status==='error'||x.status==='unavailable').length;
  const alerts=Array.isArray(data.incidents)?data.incidents.length:0;
  const status:Health=freshness==='unknown'?'unknown':freshness==='stale'?'stale':
    !collected?'warning':alerts||failures||data.status==='unavailable'?'warning':'ok';
  return {...base,status,at,detail:collected+' observed/warning checks, '+failures+' unavailable/error checks, '+alerts+' correlated watches. '+(freshness==='stale'?'Latest snapshot exceeds two hours.':'Public samples do not prove global infrastructure health.')};
}
function checkWorkflow(data:Json, kind:'release'|'browser'):Check {
  const base=entries[kind==='release'?2:3];
  if (!Array.isArray(data.workflow_runs)) throw new Error('Unexpected GitHub Actions schema');
  // Only count trusted main-branch runs whose workflow tests deployed Pages.
  // Pull requests and push-triggered candidate builds do not certify production.
  const matching=data.workflow_runs.filter(object).filter(run=>
    kind==='release' || (
      run.head_branch==='main' &&
      (run.event==='workflow_run'||run.event==='schedule'||run.event==='workflow_dispatch')
    )
  );
  const run=matching[0];
  if (!run) return {...base,status:'unknown',detail:kind==='browser'
    ?'No deployment-triggered, scheduled, or manually run production browser QA is publicly recorded yet.'
    :'No main-branch release run was returned.'};
  const at=typeof run.updated_at==='string'?run.updated_at:undefined;
  const freshness=ageState(at,kind==='browser'?9*24:30*24);
  const pending=run.status!=='completed';
  const success=run.conclusion==='success';
  const status:Health=pending?'pending':!success?'warning':
    freshness==='stale'?'stale':freshness==='unknown'?'unknown':'ok';
  const details=kind==='browser'?'Deployed-site browser checks (event: '+String(run.event||'unknown')+')':'Main-branch build and deployment';
  return {...base,status,at,href:typeof run.html_url==='string'&&run.html_url.startsWith('https://github.com/')?run.html_url:base.href,
    detail:details+': '+(pending?'still running':success?'workflow succeeded':'workflow failed or was cancelled')+
    '. '+(freshness==='stale'?'Last run exceeds the review window.':'A successful run does not guarantee current service or feed health.')};
}
const sourceLinks=[
  {title:'Early-warning source inventory',href:REPO+'/blob/main/eastern-axis/EARLY-WARNING-SOURCES.md'},
  {title:'Resilience methods and limitations',href:REPO+'/blob/main/eastern-axis/RESILIENCE.md'},
  {title:'Weekly source connection audit',href:REPO+'/actions/workflows/eastern-axis-weekly-audit.yml'},
];
const statusNames:Record<Health,string>={ok:'Verified check',warning:'Attention required',stale:'Stale evidence',unknown:'Unverified',pending:'Checking'};
function Marker({status}:{status:Health}) {
  return status==='ok'?<CheckCircle2 size={17}/>:status==='warning'?<ShieldAlert size={17}/>:status==='stale'?<Clock3 size={17}/>:status==='pending'?<Activity size={17}/>:<AlertTriangle size={17}/>;
}
export default function OperationalAssurance(){
  const [checks,setChecks]=useState<Check[]>(entries);
  const [cycle,setCycle]=useState(0);
  const [pending,setPending]=useState(true);
  useEffect(()=>{
    const controller=new AbortController();
    let active=true;
    setPending(true);
    setChecks(entries);
    const tasks=[
      json(String(import.meta.env.BASE_URL||'/')+'analysis/physical-early-warning.json',controller.signal).then(checkEarly),
      json(LIVE+'?checked='+Date.now(),controller.signal).then(checkResilience),
      json(API+'deploy-pages.yml/runs?branch=main&per_page=1',controller.signal).then(d=>checkWorkflow(d,'release')),
      json(API+'eastern-axis-pages-live-qa.yml/runs?branch=main&per_page=20',controller.signal).then(d=>checkWorkflow(d,'browser')),
    ];
    Promise.allSettled(tasks).then(results=>{
      if(!active)return;
      setChecks(results.map((r,i)=>r.status==='fulfilled'?r.value:{
        ...entries[i], status:'unknown',
        detail:'Independent evidence could not be retrieved or validated. Do not interpret this as a healthy service.'
      }));
      setPending(false);
    });
    return ()=>{active=false;controller.abort();};
  },[cycle]);
  return <section className="oa-root" aria-label="Operational assurance checks">
    <div className="oa-heading">
      <div><div className="oa-kicker"><Activity size={15}/> LIVE SOURCE AND DELIVERY EVIDENCE</div>
        <h2>Operational assurance</h2>
        <p>Checks here are independent. A green deployment does not turn missing telemetry into healthy data. Source-level timestamps and coverage gaps remain visible below.</p>
      </div>
      <button type="button" onClick={()=>setCycle(n=>n+1)} disabled={pending}><RefreshCcw size={15}/> Recheck</button>
    </div>
    <div className="oa-grid">
      {checks.map(c=><article className={'oa-card oa-'+c.status} key={c.id} aria-label={c.title}>
        <div className="oa-card-head"><span>{c.title}</span><span className="oa-indicator"><Marker status={c.status}/>{statusNames[c.status]}</span></div>
        <p>{c.detail}</p>
        <div className="oa-foot"><small>{c.scope}<span>{c.at?' · '+displayDate(c.at):''}</span></small>
          <a href={c.href} target="_blank" rel="noopener noreferrer" aria-label={'Inspect '+c.title+' evidence'}>Evidence <ExternalLink size={13}/></a>
        </div>
      </article>)}
    </div>
    <div className="oa-disclosure">
      <strong>Not independently connected:</strong> commercial maritime insurance, confidential utility and IXP utilization, operator PTP drift, private supplier backlogs, submarine distributed acoustic sensing, and validated cascade probabilities. These are coverage limitations, not zero-risk readings.
    </div>
    <div className="oa-links">
      {sourceLinks.map(s=><a key={s.href} href={s.href} target="_blank" rel="noopener noreferrer">{s.title}<ExternalLink size={13}/></a>)}
    </div>
  </section>;
}
