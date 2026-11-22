import {useEffect,useMemo,useState} from 'react';
import {loadDefenseCatalog} from './lib/defenseData';
import {Activity,Anchor,BookOpen,ExternalLink,Globe2,Layers3,Search,Shield,ShieldCheck} from 'lucide-react';
import './defense.css';
import IntelInsights from './IntelInsights';
import CountryDefenseSnapshot from './CountryDefenseSnapshot';
type Assessment={id:string;title:string;agency:string;government:string;group:string;published:string;countries:string[];topic:string;finding:string;kind:string;url:string};
type Operation={id:string;title:string;theater:string;published:string;kind:string;summary:string;roles:{code:string;role:string}[];publisher:string;url:string;state:string};
type Asset={id:string;code:string;category:string;name:string;quantity:string;unit:string;published:string;publisher:string;url:string;basis:string;detail:string};
type Source={id:string;name:string;group:string;what:string;url:string};
type Data={reviewedAsOf:string;mode:string;assessments:Assessment[];operations:Operation[];assets:Asset[];sources:Source[];caveats:string[]};
type Props={code?:string;countryName?:string;mode?:'country'|'global'};
const first=['All','Military operations','Military assets','Allied assessments','Research sources'];
const date=(s:string)=>s.length>=10?new Date(s+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}):s;
export default function DefenseIntel({code,countryName,mode='country'}:Props){
 const [data,setData]=useState<Data|null>(null);
 const [problem,setProblem]=useState(false);
 const [partial,setPartial]=useState(false);
 const [showAllAssets,setShowAllAssets]=useState(false);
 const [term,setTerm]=useState('');
 const [focus,setFocus]=useState('All');
 const [group,setGroup]=useState('All partners');
 const [category,setCategory]=useState('All assets');
 useEffect(()=>setShowAllAssets(false),[code,category,term]);
 useEffect(()=>{let active=true;loadDefenseCatalog().then(r=>{if(active){setData(r.data as Data);setPartial(r.apiFailed||r.inventoryFailed);setProblem(false);}}).catch(()=>{if(active)setProblem(true);});return()=>{active=false;};},[]);
 const q=term.toLowerCase().trim();
 const assessments=useMemo(()=>(data?.assessments||[]).filter(x=>(!code||x.countries.includes(code))&&(group==='All partners'||x.group===group)&&(!q||[x.title,x.government,x.agency,x.topic,x.finding,x.countries.join(' ')].join(' ').toLowerCase().includes(q))),[data,code,group,q]);
 const operations=useMemo(()=>(data?.operations||[]).filter(x=>(!code||x.roles.some(r=>r.code===code))&&(!q||[x.title,x.theater,x.kind,x.summary,x.roles.map(r=>r.code+' '+r.role).join(' ')].join(' ').toLowerCase().includes(q))),[data,code,q]);
 const assets=useMemo(()=>(data?.assets||[]).filter(x=>(!code||x.code===code)&&(category==='All assets'||category===x.category)&&(!q||[x.code,x.name,x.category,x.detail,x.publisher].join(' ').toLowerCase().includes(q))),[data,code,category,q]);
 const sources=useMemo(()=>(data?.sources||[]).filter(x=>(group==='All partners'||x.group===group)&&(!q||[x.name,x.group,x.what].join(' ').toLowerCase().includes(q))),[data,group,q]);
 const global=mode==='global';
 const counted=assets.filter(a=>a.quantity!=='Not quantified'&&a.quantity!==''&&a.value!==null);
 const covered=new Set(counted.map(a=>a.code)).size;
 const shownAssets=global&&!showAllAssets?assets.slice(0,48):assets;
 const dateInfo=data?.reviewedAsOf||'';
 const tab=(key:string)=>focus==='All'||focus===key;
 return <div className={'defense-intel '+(global?'di-global':'di-country')}>
   <div className="di-hero"><div className="di-kicker"><ShieldCheck size={15}/> OFFICIAL & ALLIED SOURCES / PUBLIC RECORDS</div><h2>{global?'Defense intelligence & military assets':'Military & allied analysis'}</h2><p>{global?'Explore sourced operations, strategic capabilities and intelligence judgments across countries.':'Source-attributed context for '+(countryName||code)+'. Not a live battlefield picture.'}</p><small>Library reviewed {dateInfo?date(dateInfo):'pending'} · Historical observations, not live operational positions</small></div>
   {problem&&<div className="di-message">The defense source library and independent inventory baseline are unavailable. No values inferred.</div>}
   {partial&&<div className="di-message">Partial source coverage: one data channel did not respond. Existing attributed figures remain visible; missing does not mean zero.</div>}
   {!data&&!problem&&<div className="di-message">Loading public-source records…</div>}
   {data&&<>
     {global&&<div className="di-search"><Search size={16}/><input aria-label="Search defense intelligence" placeholder="Search countries, operations, military assets, reports…" value={term} onChange={e=>setTerm(e.target.value)}/></div>}
     {!global&&code&&<CountryDefenseSnapshot code={code} name={countryName||code} data={data} unavailable={problem} onSelect={category=>setFocus(category==='reports'?'Allied assessments':category==='operations'?'Military operations':'Military assets')}/>}
     <div className="di-tabs" aria-label="Defense intelligence sections">{first.slice(0,global?5:4).map(label=><button key={label} className={focus===label?'selected':''} onClick={()=>setFocus(label)}>{label}</button>)}</div>
     {tab('Military operations')&&<section className="di-section"><div className="di-sectionhead"><h3><Activity size={16}/> Military operations</h3><small>{operations.length} sourced record{operations.length===1?'':'s'}</small></div>
     <p className="di-sectionnote">Combat, deployments and support are distinct. Latest cited reporting dates are shown; “ongoing” is as of the source, never verified to the minute.</p>
     {operations.length?<div className="di-items">{operations.map(o=><article className="di-item" key={o.id}><div className="di-item-top"><span className="di-tag">{o.kind}</span><time>{date(o.published)}</time></div><strong>{o.title}</strong><div className="di-location"><Globe2 size={13}/>{o.theater}</div><p>{o.summary}</p><div className="di-status">{o.state}</div>{o.roles.filter(r=>!code||r.code===code).map(r=><div className="di-role" key={r.code}>{r.code}: {r.role}</div>)}<a href={o.url} target="_blank" rel="noopener noreferrer">Original: {o.publisher} <ExternalLink size={12}/></a></article>)}</div>:<div className="di-empty">No country-specific operation has been reviewed in this starter library. This does not establish an absence of military activity.</div>}
     </section>}
     {tab('Military assets')&&<section className="di-section"><div className="di-sectionhead"><h3><Layers3 size={16}/> Military asset tracker</h3><small>{assets.length} dated observations · {covered} countries with a figure</small></div><p className="di-sectionnote">Active, stored, deployed, retired and historical figures are distinct. Never add overlapping nuclear categories or present historic personnel as current strength. Missing values mean unindexed, not zero.</p>
       {global&&<div className="di-assetfilter"><label htmlFor="di-asset-category">Asset class</label><select id="di-asset-category" value={category} onChange={e=>setCategory(e.target.value)}>{['All assets','Personnel','Land','Naval','Air','Missiles','Nuclear','Spending'].map(x=><option key={x}>{x}</option>)}</select></div>}
       {assets.length?<div className="di-assets">{shownAssets.map(a=><article key={a.id} className="di-asset"><div className="di-asset-head"><span>{a.code} / {a.category}</span><small>{date(a.published)}</small></div><strong>{a.quantity}</strong><span className="di-asset-name">{a.name}</span><small>{a.unit} · {a.basis}</small><small className="di-asset-status">{a.status?String(a.status).replaceAll('-',' '):'Source-described capability'} · observation {a.observationYear||a.published}</small><p>{a.detail}</p><a href={a.url} target="_blank" rel="noopener noreferrer">{a.publisher} <ExternalLink size={12}/></a></article>)}</div>:<div className="di-empty">No sourced inventory indexed for this country and class. This does not mean zero capability; consult the linked source directory.</div>}
       {global&&assets.length>48&&<button className="di-show-more" type="button" onClick={()=>setShowAllAssets(v=>!v)}>{showAllAssets?'Show first 48 observations':'Show all '+assets.length+' observations'}</button>}
     </section>}
     {tab('Allied assessments')&&<section className="di-section"><div className="di-sectionhead"><h3><BookOpen size={16}/> Government & allied assessments</h3><small>{assessments.length} entries</small></div>
       {global&&<div className="di-assetfilter"><label htmlFor="di-group">Government group</label><select id="di-group" value={group} onChange={e=>setGroup(e.target.value)}>{['All partners','United States','Five Eyes','EU / NATO','Indo-Pacific allies','Multilateral','Research'].map(x=><option key={x}>{x}</option>)}</select></div>}
       {assessments.length?<div className="di-items">{assessments.map(a=><article className="di-item" key={a.id}><div className="di-item-top"><span className="di-tag">{a.group}</span><time>{date(a.published)}</time></div><strong>{a.title}</strong><small>{a.government} · {a.agency} · {a.kind}</small><p>{a.finding}</p><a href={a.url} target="_blank" rel="noopener noreferrer">Open government report <ExternalLink size={12}/></a></article>)}</div>:<div className="di-empty">No country-specific allied assessment curated here yet. This is a research gap, not evidence of no threat.</div>}
     </section>}
     {global&&tab('Research sources')&&<section className="di-section"><div className="di-sectionhead"><h3><Anchor size={16}/> Official reporting network</h3><small>{sources.length} sources</small></div><p className="di-sectionnote">Source directory is not proof of automated ingestion. Historical World Bank personnel and spending are collected at build time when available. IISS/Janes and equipment directories require licensing or case-by-case verification. SIPRI transfers are not current holdings.</p><div className="di-sources">{sources.map(s=><a href={s.url} key={s.id} target="_blank" rel="noopener noreferrer"><span><strong>{s.name}</strong><small>{s.group} · {s.what}</small></span><ExternalLink size={13}/></a>)}</div></section>}
     <IntelInsights code={code} countryName={countryName} mode={global?'global':'country'}/>
     {global&&<div className="di-caveats"><Shield size={16}/><span>{data.caveats.join(' ')}</span></div>}
   </>}
 </div>;
}
