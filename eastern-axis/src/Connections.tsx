import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { ArrowUpRight, CircleAlert, ExternalLink, GitBranch, Network, ShieldCheck } from 'lucide-react';
import './networkExplorer.css';

type Country = { code:string; name:string; region:string; isTreatyAlly:boolean; relationship:string };
type Case = { id:string; code:string; date:string; title:string; summary:string; status:string; topic:string; source:string };
type Props = { code:string; countries:Country[]; cases:Case[]; onSelect:(code:string)=>void; embedded?:boolean };
type Kind = 'Treaty'|'Partnership'|'Organization'|'Operation';
type Link = { id:string; from:string; to:string; kind:Kind; label:string; detail:string; asOf:string; publisher:string; url:string; caution?:string };
type Operation = {id:string; title:string; published:string; summary:string; roles:{code:string;role:string}[]; publisher:string;url:string;state:string};
type Defense = { operations:Operation[] };

const refs = {
 csto:'https://en.odkb-csto.org/25years/',
 nato:'https://www.nato.int/en/about-us/organization/nato-member-countries',
 russiaDprk:'https://www.everycrsreport.com/reports/IF12760.html',
 chinaDprk:'https://www.everycrsreport.com/reports/R49319.html',
 russiaChina:'https://www.everycrsreport.com/reports/R48977.html',
 anzus:'https://www.dfat.gov.au/geo/united-states-of-america/united-states-of-america-country-brief',
 japan:'https://www.mod.go.jp/en/j-us-alliance/joint-declaration/treaty/index.html',
 korea:'https://2021-2025.state.gov/u-s-security-cooperation-with-korea/',
 philippines:'https://2021-2025.state.gov/u-s-security-cooperation-with-the-philippines/',
 thailand:'https://www.everycrsreport.com/reports/R40614.html'
};

const primary:Link[] = [
 {id:'ru-kp-treaty',from:'RU',to:'KP',kind:'Treaty',label:'2024 mutual-assistance treaty',asOf:'2024 treaty; CRS reference',publisher:'U.S. Congressional Research Service',url:refs.russiaDprk,detail:'Russia and North Korea concluded a bilateral treaty with a military-assistance commitment. Terms and conditions matter; this is not a prediction of joint military action.'},
 {id:'cn-kp-treaty',from:'CN',to:'KP',kind:'Treaty',label:'1961 mutual-assistance treaty',asOf:'1961 treaty; CRS reference',publisher:'U.S. Congressional Research Service',url:refs.chinaDprk,detail:'China and North Korea have a distinct mutual-assistance treaty. Its terms must not be conflated with the Russia–North Korea treaty.'},
 {id:'ru-cn-partnership',from:'RU',to:'CN',kind:'Partnership',label:'Strategic / military partnership',asOf:'CRS 2026 assessment',publisher:'U.S. Congressional Research Service',url:refs.russiaChina,detail:'The relationship involves security and military cooperation, but is not a bilateral mutual-defense alliance.'},
 {id:'us-au-treaty',from:'US',to:'AU',kind:'Treaty',label:'ANZUS security relationship',asOf:'Official treaty context',publisher:'Australian Department of Foreign Affairs and Trade',url:refs.anzus,detail:'U.S.–Australia defense-treaty relationship; it does not imply identical actions in every conflict.'},
 {id:'us-jp-treaty',from:'US',to:'JP',kind:'Treaty',label:'U.S.–Japan security treaty',asOf:'Official treaty text',publisher:'Japan Ministry of Defense',url:refs.japan,detail:'Bilateral defense-treaty commitment defined by its published provisions.'},
 {id:'us-kr-treaty',from:'US',to:'KR',kind:'Treaty',label:'U.S.–South Korea security alliance',asOf:'U.S. State Department source',publisher:'U.S. Department of State',url:refs.korea,detail:'A bilateral defense relationship with the Republic of Korea, distinct from NATO membership.'},
 {id:'us-ph-treaty',from:'US',to:'PH',kind:'Treaty',label:'U.S.–Philippines mutual defense treaty',asOf:'U.S. State Department source',publisher:'U.S. Department of State',url:refs.philippines,detail:'A bilateral mutual-defense treaty; triggering conditions require reference to the original document.'},
 {id:'us-th-treaty',from:'US',to:'TH',kind:'Treaty',label:'U.S.–Thailand security arrangements',asOf:'CRS treaty context',publisher:'U.S. Congressional Research Service',url:refs.thailand,detail:'U.S. collective-defense arrangements include Thailand; do not equate these provisions with NATO Article 5.'}
];

const csto = ['RU','BY','KZ','KG','TJ','AM'];
const operationMeaning: Record<string,{label:string;detail:string;caution:string}> = {
 'ru-ua': {label:'Opposing parties in Russia–Ukraine war',detail:'The same UN conflict briefing describes separate belligerent roles. This edge signifies opposition, not cooperation.',caution:'Dated conflict report; no live troop tracking.'},
 'iran-us': {label:'Opposing parties in reported hostilities',detail:'A March 2026 public assessment described U.S.–Iran hostilities. This is a dated confrontation reference, not a statement of present deployments.',caution:'November operational status not independently established.'},
 'dprk-support': {label:'Reported North Korean military support',detail:'ODNI described North Korean troops deployed to support Russian operations in 2024. This is historical evidence, not a current force estimate.',caution:'No verified current troop strength or location.'},
 'gaza': {label:'Parties and territories in Gaza hostilities',detail:'The UN source describes distinct Israeli military activity and affected Palestinian territories. Hamas and other armed groups are not equivalent to Palestinian authorities.',caution:'Conflict context does not attribute conduct to an entire population.'}
};

function datedOperations(operations:Operation[]):Link[]{
 return operations.flatMap(op=>{
  const meaning=operationMeaning[op.id];
  const participants=Array.from(new Set((op.roles||[]).map(r=>r.code)));
  if(!meaning||participants.length!==2||!op.url)return [];
  return [{id:'operation-'+op.id,from:participants[0],to:participants[1],kind:'Operation' as Kind,
   label:meaning.label,detail:meaning.detail,asOf:op.published||'Publication date unavailable',
   publisher:op.publisher||'Dated public-source report',url:op.url,caution:meaning.caution}];
 });
}
function actor(code:string,countries:Country[]):string{
 if(code==='NATO')return 'NATO';
 if(code==='CSTO')return 'CSTO';
 return countries.find(c=>c.code===code)?.name||code;
}
const labels:Kind[]=['Treaty','Partnership','Organization','Operation'];

export default function Connections({code,countries,cases,onSelect,embedded=false}:Props){
 const [defense,setDefense]=useState<Defense|null>(null);
 const [defenseError,setDefenseError]=useState(false);
 const [kind,setKind]=useState<Kind|'All'>('All');
 const [picked,setPicked]=useState('');
 const focus=code==='all'?'RU':code;
 useEffect(()=>{
  let active=true;
  api.get('/api/defense-intel').then(r=>{if(active){setDefense(r.data as Defense);setDefenseError(false);}})
   .catch(()=>{if(active)setDefenseError(true);});
  return()=>{active=false;};
 },[]);
 const allLinks=useMemo(()=>{
  const membership:Link[]=countries.filter(c=>c.relationship.includes('NATO collective-defense')).map(c=>({
   id:'nato-'+c.code,from:c.code,to:'NATO',kind:'Organization',label:'NATO treaty membership',
   detail:'NATO membership is a multilateral collective-defense relationship. It is not a claim of identical operational participation.',
   asOf:'NATO official membership directory',publisher:'NATO',url:refs.nato
  }));
  const collective:Link[]=csto.map(code=>({
   id:'csto-'+code,from:code,to:'CSTO',kind:'Organization',
   label:code==='AM'?'CSTO membership · participation frozen':'CSTO collective-security membership',
   detail:code==='AM'?'Armenia has frozen its participation despite formal membership. Membership must not be read as current operational cooperation.':'Formal CSTO membership; it does not prove participation in a specific operation.',
   asOf:'CSTO official history',publisher:'CSTO',url:refs.csto
  }));
  return [...primary,...membership,...collective,...datedOperations(defense?.operations||[])];
 },[countries,defense]);
 const forCountry=allLinks.filter(l=>l.from===focus||l.to===focus);
 const scoped=forCountry.filter(l=>kind==='All'||l.kind===kind).slice(0,12);
 const chosen=scoped.find(l=>l.id===picked)||scoped[0];
 const peer=(l:Link)=>l.from===focus?l.to:l.from;
 const neighbors=new Set(forCountry.map(peer));
 const svgHeight=Math.max(330,scoped.length*71+65);
 const centerY=svgHeight/2;
 const caseCount=cases.filter(c=>c.code===focus).length;
 return <section className={"nx-root"+(embedded?" nx-embedded":"")} aria-label="Sourced relationship networks">
  <header className="nx-head">
   <div><div className="nx-kicker"><Network size={16}/> ALL-SOURCE RELATIONSHIP INTELLIGENCE</div>
    {embedded?<h2 className="nx-embedded-title">Documented relationship map</h2>:<h1>Networks<span className="nx-period">.</span></h1>}
    <p>Documented security ties, partnerships and separately reported conflict relationships. Follow the connection, inspect its source, then judge its meaning.</p>
   </div>
   <div className="nx-scope"><span>{code==='all'?'GLOBAL NETWORK SPOTLIGHT':'COUNTRY NETWORK'}</span><strong>{actor(focus,countries)}</strong><small>{code==='all'?'Choose a country above to focus the graph':'Persistent country selector is applied'}</small></div>
  </header>
  <div className="nx-metrics" aria-label="Relationship coverage">
   <div><strong>{forCountry.length}</strong><span>Sourced relationship records</span></div>
   <div><strong>{neighbors.size}</strong><span>Connected actors / blocs</span></div>
   <div><strong>{new Set(forCountry.map(l=>l.kind)).size}</strong><span>Relationship categories</span></div>
   <div><strong>{forCountry.filter(l=>l.kind==='Operation').length}</strong><span>Dated operation links</span></div>
  </div>
  <div className="nx-filter" role="group" aria-label="Network relationship filters">
   {(['All',...labels] as const).map(option=>{
    const count=option==='All'?forCountry.length:forCountry.filter(l=>l.kind===option).length;
    return <button key={option} type="button" className={kind===option?'selected':''} aria-pressed={kind===option}
      onClick={()=>{setKind(option);setPicked('');}}>{option} <span>{count}</span></button>;
   })}
  </div>
  {scoped.length?<div className="nx-graph-shell">
   <div className="nx-chart-top"><strong><GitBranch size={16}/> Relationship map</strong><span>Select a connection below for source evidence</span></div>
   <div className="nx-chart-scroll">
    <svg className="nx-graph" viewBox={'0 0 1000 '+svgHeight} role="img" aria-label={'Sourced relationship map for '+actor(focus,countries)}>
     <title>{actor(focus,countries)} — documented relationships</title>
     {scoped.map((l,i)=>{
      const y=65+i*71;
      return <g key={l.id} className={'nx-edge nx-type-'+l.kind.toLowerCase()+(chosen?.id===l.id?' current':'')}>
       <path d={'M 246 '+centerY+' C 490 '+centerY+', 500 '+y+', 738 '+y} fill="none" strokeWidth={chosen?.id===l.id?3.8:2.1}/>
       <circle cx="738" cy={y} r="5.5"/>
       <rect x="745" y={y-23} width="235" height="46" rx="11"/>
       <text x="762" y={y+5} fontSize="18" fontWeight="650">{actor(peer(l),countries).slice(0,21)}</text>
      </g>;
     })}
     <rect className="nx-center-node" x="20" y={centerY-47} width="226" height="94" rx="17"/>
     <text className="nx-center-name" x="37" y={centerY-5} fontSize="21" fontWeight="800">{actor(focus,countries).slice(0,19)}</text>
     <text className="nx-center-caption" x="37" y={centerY+22} fontSize="14">Selected country</text>
    </svg>
   </div>
   <div className="nx-legend"><span><i className="nx-dot treaty"/> Treaty</span><span><i className="nx-dot partnership"/> Partnership</span><span><i className="nx-dot organization"/> Organization</span><span><i className="nx-dot operation"/> Dated operation</span></div>
  </div>:<div className="nx-empty"><CircleAlert size={18}/> No source-backed relationship is indexed for this country and filter. This is a coverage gap—not evidence that no relationships exist.</div>}
  {scoped.length>0&&<div className="nx-two">
   <section className="nx-list" aria-label="Documented connection records">
    <div className="nx-subhead"><h2>Connections</h2><span>{scoped.length} displayed</span></div>
    {scoped.map(l=><button type="button" key={l.id} className={'nx-connection '+(chosen?.id===l.id?'picked':'')} onClick={()=>setPicked(l.id)}>
     <span className={'nx-kind nx-type-'+l.kind.toLowerCase()}>{l.kind}</span>
     <strong>{actor(focus,countries)} <span aria-hidden="true">↔</span> {actor(peer(l),countries)}</strong>
     <small>{l.label}</small>
    </button>)}
   </section>
   <aside className="nx-detail" aria-live="polite">
    {chosen&&<><span className={'nx-kind nx-type-'+chosen.kind.toLowerCase()}>{chosen.kind} · SOURCE-LINKED</span>
     <h2>{chosen.label}</h2><p>{chosen.detail}</p>
     {chosen.caution&&<p className="nx-caution">{chosen.caution}</p>}
     <div className="nx-provenance"><span>Published / assessed</span><strong>{chosen.asOf}</strong><span>Original publisher</span><strong>{chosen.publisher}</strong></div>
     <a className="nx-source" href={chosen.url} target="_blank" rel="noopener noreferrer">Examine original evidence <ExternalLink size={15}/></a>
     {countries.some(c=>c.code===peer(chosen))&&<button type="button" className="nx-follow" onClick={()=>{onSelect(peer(chosen));setPicked('');setKind('All');}}>Follow {actor(peer(chosen),countries)} network <ArrowUpRight size={15}/></button>}
    </>}
   </aside>
  </div>}
  {defenseError&&<p className="nx-alert"><CircleAlert size={16}/> The defense-intelligence feed is unavailable; dated operation edges may be missing. Treaty and organizational references remain visible.</p>}
  <footer className="nx-method"><ShieldCheck size={18}/><p>Edges indicate only the relationship described by their cited source. Opposition, treaty membership, partnership and military support are distinct. No ownership chain, proxy control, culpability or causal relationship is inferred from common country tags. {caseCount} curated DOJ case{caseCount===1?'':'s'} for this country are catalogued separately until entity-level links are verified. Sanctions totals and source portals belong in Source Library, not the relationship graph.</p></footer>
 </section>;
}
