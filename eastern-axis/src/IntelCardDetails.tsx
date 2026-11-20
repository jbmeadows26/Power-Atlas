import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowUpRight, BarChart3, Clock3, Database, ExternalLink, ShieldAlert, X } from 'lucide-react';
import './intelCardDetails.css';

/**
 * Shared evidence drilldown for all dashboard workspaces.
 * Uses existing rendered, source-attributed records instead of fabricating summaries
 * or creating a different, unmaintained detail dialog for each feed.
 *
 * Individual rows win over their containing cards, so a GNSS comparison, an
 * earthquake bin, an economic indicator, etc. opens its OWN detail window.
 * Existing buttons, country selectors, navigation and source links keep their actions.
 */
const itemSelectors = [
  '.dr-move', '.dr-snapshot', '.dr-report-list > div', '.dr-briefing > div',
  '.rdb-headlines > div', '.rdb-pressure-row', '.rdb-quake-lines > div',
  '.rdb-duo > div', '.rdb-history > div',
  '.db-stat', '.db-topic', '.db-latest > *', '.db-fact-grid > *',
  '.cx-record',
  '.gs-metric', '.gs-signal', '.gs-gap', '.gs-summary > *',
  '.pew-price', '.pew-node', '.pew-domains > article', '.pew-summary > *',
  '.rw-metrics > *', '.rw-incident', '.rw-probe', '.rw-capability',
  '.sc-kpis > *', '.sc-corridor', '.sc-step', '.sc-coverage > *',
  '.di-item', '.di-asset', '.di-sources > *',
  '.cds-panel', '.cds-grid > *',
  '.cf-fields > *', '.cf-overview > *',
  '.fb-stats > *', '.fb-facts > *', '.fb-chart-row',
  '.ea-agent-stats > *', '.ea-agent-card', '.ea-agent-records > *',
  '.ip-sanction-source', '.ip-firm', '.ip-regime',
  '.sp-head-counters > *', '.sp-feed', '.sp-record', '.sp-week',
  '.sp-allied-kpis > *', '.sp-allied-reports article',
  '.intake-stat', '.intake-source', '.intake-records > *',
  '.ea-lab-cards > *', '.ea-lab-list > *',
  '.oa-grid > *', '.cs-feed',
  '.metric-card', '.indicator', '.source-card', '.method-card',
  '.case-top', '.brief-top .brief-line',
  '.cc-map-source-record'
];
const ITEM = itemSelectors.join(',');
const SKIP = 'a, button, input, select, textarea, summary, [role="tab"], [role="option"], [role="link"], [contenteditable="true"]';
const WORKSPACE = [
  ['.dr-root','Home / decision radar'], ['.rdb-root','Risks'], ['.cx-root','Networks'],
  ['.gs-root','Global systems'], ['.sc-root','Supply chain'], ['.pew-root','Early warning'],
  ['.rw-root','Resilience watch'], ['.di-hero','Defense intelligence'],
  ['.fb-root','World Factbook'], ['.country-factbook','Country factbook'],
  ['.ea-agent','AI analyst'], ['.sp-root','Intelligence signals'],
  ['.intake-root','Collection desk'], ['.cs-root','Connected sources'],
  ['.ea-lab','Verification lab'], ['.oa-root','Operational assurance']
] as const;
type Point = { label:string; value:number; display:string };
type Detail = { title:string; workspace:string; lines:string[]; links:{title:string;url:string}[]; points:Point[]; status:'stale'|'missing'|'review'|'observed'; note:string; };

const normal = (value?:string|null) => (value||'').replace(/\s+/g,' ').trim();
const getText = (node:Element|null|undefined) => normal(node?.textContent).slice(0,360);
function getLink(anchor:HTMLAnchorElement){
  try{
    const uri=new URL(anchor.href,window.location.href);
    if(uri.protocol!=='https:' || uri.username || uri.password) return null;
    return {title:normal(anchor.textContent)||uri.hostname, url:uri.href};
  }catch{return null;}
}
function contextFor(el:HTMLElement) {
  if(el.matches('.dr-move') && /GNSS|aviation|interference/i.test(el.innerText))
    return 'Aviation GNSS values are sampled ADS-B-derived quality proxies. They do not independently establish intentional jamming, spoofing, a perpetrator, or an aircraft-specific impact. A percentage-point change is not a relative percent change.';
  if(el.closest('.rdb-root') || el.matches('.gs-signal, .gs-metric'))
    return 'An indicator crossing an illustrative screen is a review prompt, not an estimated probability, confirmed escalation, or prediction. Check reporting years and original data definitions.';
  if(el.closest('.cx-root, .di-hero, .cds-root, .ip-section'))
    return 'Country tags, sanctions programs, public assessments and reported operations are distinct evidence classes. Their appearance together does not establish ownership, government direction, an operational link, or live position.';
  if(el.closest('.sc-root') || /transit|shipping|corridor|commodity/i.test(el.innerText))
    return 'Changes in route volume or prices can have several causes and should be compared with the source window, baseline and independent data. They do not establish a supply disruption by themselves.';
  if(el.closest('.rw-root') || el.matches('.dr-snapshot'))
    return 'A probe snapshot measures the sampled systems and time shown, not worldwide infrastructure health. Stale probes or missing capabilities are coverage gaps, never an all-clear.';
  if(el.closest('.fb-root, .country-factbook') || el.matches('.indicator'))
    return 'These are contextual country statistics. Historical reporting years and different source definitions are not live measurements; missing observations must not be interpolated.';
  return 'This window preserves the selected record and any original source links shown with it. Evidence date, geographic scope and data coverage must be checked before treating a screen as a confirmed event.';
}
function capture(el:HTMLElement):Detail {
  const summaryRow=el.matches('.dr-briefing > div,.rdb-headlines > div,.db-stat,.rdb-duo > div,.metric-card,.intake-stat');
  const heading=el.querySelector(summaryRow
    ? '.metric-top,span,h2,h3,small,strong'
    : 'h2,h3,.dr-move-top strong,.rdb-pressure-row strong,.dr-snapshot strong,.cx-record h3,.gs-metric-head strong,.sp-record strong,.fb-chart-row strong,.metric-top,small,strong');
  const label=getText(heading) || normal(el.innerText.split('\n').find(Boolean)) || 'Selected evidence';
  const workspace=WORKSPACE.find(([selector])=>el.closest(selector))?.[1]||'Eastern Axis intelligence';
  const detailLines=(el.innerText||'').split('\n').map(normal).filter(Boolean);
  const lines=[...new Set(detailLines)].filter(s=>s!==label).slice(0,24);
  // Only inherit a source from the nearest single-purpose chart, never an
  // unrelated sibling record in a broad domain lane or country panel.
  const sourceHost=el.closest('.rdb-chart');
  const selectedLinks=[...el.querySelectorAll<HTMLAnchorElement>('a[href]')];
  if(selectedLinks.length===0 && sourceHost && sourceHost!==el)
    selectedLinks.push(...sourceHost.querySelectorAll<HTMLAnchorElement>('a[href]'));
  const sourceMap=new Map(selectedLinks.map(getLink).filter((x):x is {title:string;url:string}=>!!x).map(x=>[x.url,x]));
  if(el.matches('.dr-snapshot'))
    sourceMap.set('https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json',
      {title:'Independent resilience probe snapshot',url:'https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/telemetry/eastern-axis-live/eastern-axis/public/telemetry/resilience.json'});
  const links=[...sourceMap.values()].slice(0,12);
  const points=[...el.querySelectorAll<HTMLElement>('.dr-pair > div')].map(row=>{
    const display=getText(row.querySelector('b'));
    return {label:getText(row.querySelector('small')),value:Number(display.replace(/,/g,'')),display};
  }).filter(p=>p.label && p.display && Number.isFinite(p.value));
  // Some cards use explicit aria-valued bars rather than DOM text.
  const matchText=normal(el.innerText);
  const status:Detail['status'] = /\bstale\b|\boutdated\b/i.test(matchText)?'stale':
    /\bunavailable\b|\bno data\b|\bmissing\b|\bunknown\b/i.test(matchText)?'missing':
    /\breview\b|\babove screen\b|\banomaly\b/i.test(matchText)?'review':'observed';
  return {title:label.slice(0,200),workspace,lines,links,points,status,note:contextFor(el)};
}
function isInteractive(target:Element,container:HTMLElement){
  const control=target.closest(SKIP);
  return control!==null && (control===container || container.contains(control));
}
export default function IntelCardDetails(){
  const [detail,setDetail]=useState<Detail|null>(null);
  const closeRef=useRef<HTMLButtonElement>(null);
  const priorFocus=useRef<HTMLElement|null>(null);
  useEffect(()=>{
    let scheduled=0;
    const decorate=()=>{
      scheduled=0;
      document.querySelectorAll<HTMLElement>(ITEM).forEach(el=>{
        if(el.closest('.ea-detail-backdrop') || el.closest('[hidden]'))return;
        if(el.matches(SKIP) || el.getAttribute('data-ea-details')==='off')return;
        if(!el.hasAttribute('tabindex'))el.tabIndex=0;
        if(!el.hasAttribute('role'))el.setAttribute('role','button');
        el.setAttribute('data-ea-drillable','');
        if(!el.hasAttribute('aria-label')){
          const title=getText(el.querySelector('h2,h3,strong,.metric-top,small'))||normal(el.innerText.split('\n')[0]);
          el.setAttribute('aria-label','Explore '+title.slice(0,120));
        }
      });
    };
    const schedule=()=>{if(!scheduled)scheduled=window.requestAnimationFrame(decorate);};
    schedule();
    const observer=new MutationObserver(schedule);
    const root=document.getElementById('root');
    if(root)observer.observe(root,{childList:true,subtree:true});
    const open=(target:Element,ev:Event)=>{
      if(target.closest('.ea-detail-backdrop'))return;
      const el=target.closest<HTMLElement>(ITEM);
      if(!el || el.closest('[hidden]') || el.getAttribute('data-ea-details')==='off')return;
      if(isInteractive(target,el))return;
      // Items within other clickable controls preserve their original navigation.
      if(el.parentElement?.closest('button,a,[role="tab"]'))return;
      priorFocus.current=document.activeElement as HTMLElement;
      setDetail(capture(el));
      ev.preventDefault();
      ev.stopPropagation();
    };
    const click=(event:MouseEvent)=>{if(event.button===0 && event.target instanceof Element)open(event.target,event);};
    const key=(event:KeyboardEvent)=>{
      if(event.key!=='Enter'&&event.key!==' ')return;
      if(!(event.target instanceof HTMLElement)||!event.target.matches(ITEM))return;
      if(event.target.matches(SKIP))return;
      open(event.target,event);
    };
    // Capture so clicking a record opens its detail without changing page context.
    document.addEventListener('click',click,true);
    document.addEventListener('keydown',key,true);
    return()=>{observer.disconnect();if(scheduled)cancelAnimationFrame(scheduled);document.removeEventListener('click',click,true);document.removeEventListener('keydown',key,true);};
  },[]);
  useEffect(()=>{
    if(!detail)return;
    const previous=document.body.style.overflow;
    document.body.style.overflow='hidden';
    closeRef.current?.focus();
    const key=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){event.preventDefault();setDetail(null);}
      if(event.key==='Tab'){
        const dialog=document.querySelector<HTMLElement>('.ea-detail-dialog');
        const focusable=dialog?.querySelectorAll<HTMLElement>('button:not([disabled]),a[href]');
        if(!focusable?.length)return;
        const first=focusable[0],last=focusable[focusable.length-1];
        if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
        else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
      }
    };
    window.addEventListener('keydown',key);
    return()=>{document.body.style.overflow=previous;window.removeEventListener('keydown',key);priorFocus.current?.focus();};
  },[detail]);
  if(!detail)return null;
  const max=Math.max(1,...detail.points.map(p=>Math.abs(p.value)));
  return createPortal(<div className="ea-detail-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setDetail(null);}}>
    <section className="ea-detail-dialog" role="dialog" aria-modal="true" aria-labelledby="ea-detail-heading" aria-describedby="ea-detail-context">
      <header className="ea-detail-header">
        <div><span className="ea-detail-kicker"><Database size={13}/> {detail.workspace.toUpperCase()} / RECORD DRILLDOWN</span><h2 id="ea-detail-heading">{detail.title}</h2></div>
        <button className="ea-detail-close" ref={closeRef} type="button" onClick={()=>setDetail(null)} aria-label="Close evidence detail"><X size={21}/></button>
      </header>
      <div className="ea-detail-body">
        <div className="ea-detail-meta"><span className={'ea-detail-status ea-detail-'+detail.status}>{detail.status==='stale'?'STALE — VERIFY DATE':detail.status==='missing'?'DATA GAP':detail.status==='review'?'REQUIRES REVIEW':'SOURCE RECORD'}</span><span>Selected item · original country filter retained</span></div>
        {detail.points.length>0&&<section className="ea-detail-section" aria-label="Comparison breakdown"><h3><BarChart3 size={16}/> Observed comparison</h3>
          <div className="ea-detail-comparisons">{detail.points.map((point,i)=><div className="ea-detail-comparison" key={point.label+i}>
            <span>{point.label}</span><div className="ea-detail-track"><i style={{width:Math.max(2,100*Math.abs(point.value)/max)+'%'}}/></div><strong>{point.display}</strong>
          </div>)}</div>
          <small>Bars are scaled against the largest displayed absolute value in this comparison, not an external risk threshold.</small>
        </section>}
        <section className="ea-detail-section"><h3><BarChart3 size={16}/> Selected measurement & context</h3>
          <div className="ea-detail-facts">{detail.lines.length?detail.lines.map((line,i)=><div key={i}>{line}</div>):<div>No further fields were reported on this card.</div>}</div>
        </section>
        <section className="ea-detail-section"><h3><ShieldAlert size={16}/> Interpretation & limitations</h3><p id="ea-detail-context">{detail.note}</p>
          <p><Clock3 size={13}/> A current page view does not imply a current underlying observation. Use the publisher's original record to verify its date, scope, collection method and revision history.</p>
        </section>
        <section className="ea-detail-section ea-detail-evidence"><h3><ExternalLink size={16}/> Original sources</h3>
          {detail.links.length?<div className="ea-detail-links">{detail.links.map(link=><a key={link.url} href={link.url} target="_blank" rel="noopener noreferrer">{link.title}<span>{new URL(link.url).hostname}</span><ArrowUpRight size={15}/></a>)}</div>:<p>No direct original-source URL accompanies this selected item. Treat that as an evidence-link gap, not confirmation.</p>}
        </section>
      </div>
      <footer className="ea-detail-footer"><span>DETAILS ONLY · NO UNSOURCED THREAT RANKING</span><button type="button" onClick={()=>setDetail(null)}>Back to dashboard</button></footer>
    </section>
  </div>,document.body);
}
