import { useEffect, useMemo, useState } from 'react';
import { api } from './apiClient';
import { feature } from 'topojson-client';
import { geoNaturalEarth1, geoGraticule10, geoPath } from 'd3-geo';
import { Activity, ArrowRight, ArrowUpRight, BadgeAlert, BookOpen, CheckCircle2, ChevronDown, CircleAlert, Clock3, Database, ExternalLink, Eye, Filter, Globe2, Layers3, LockKeyhole, Map, Minus, Network, Plus, Radio, RefreshCcw, Search, Shield, ShieldCheck, SlidersHorizontal, X } from 'lucide-react';
import './command.css';

type Country = {code:string;name:string;region:string;scope:string;relationship:string;isTreatyAlly:boolean;isMNNA:boolean;caseCount:number};
type CaseFile = {id:string;code:string;date:string;title:string;topic:string;status:string;level:string;summary:string;impact:string;source:string;agency:string};
type Source = {id:string;name:string;category:string;mode:string;cost:string;url:string;description:string};
type Overview = {countries:Country[];cases:CaseFile[];sources:Source[];snapshot:null|{updatedAt:string;coveredCountries:number}};
type Health={sourceId:string;status:'ok'|'error';lastAttemptAt:string;lastSuccessAt?:string;lastError?:string;examined:number;inserted:number};
type Intake = {id:string;sourceId:string;title:string;date:string;countryMention?:string;summary:string;sourceUrl:string;recordType:string;sanctionsPrograms?:string[]};
type OFACMeta = {checkedAt:string;records:number;sampleSize:number;programCounts:Record<string,number>;dataset:string;scope:string};
type Intel={sources:{id:string;name:string;health:Health|null;documentation:string}[];records:Intake[];ofac?:OFACMeta|null;sampled:number;resultsNote:string};
type Props={overview:Overview;openCountry:(code:string)=>void;openCases:(id?:string)=>void;openDesk:()=>void;openSources:()=>void;openMethod:()=>void;activeCountry?:string;onCountrySelected?:(code:string)=>void};
type Layer='cases'|'ofac'|'seismic'|'natural'|'all';
type Seismic={id:string;title:string;longitude:number;latitude:number;magnitude:number;date:string;source:string;sourceUrl:string};
type WorldSignals={status:'ok'|'partial'|'unavailable';count:number;generatedAt:string;checkedAt:string;events:Seismic[];naturalEvents?:Array<{id:string;title:string;eventType:string;longitude:number;latitude:number;date:string;source:string;sourceUrl:string}>;nasaStatus?:'ok'|'unavailable';usgsStatus?:'ok'|'unavailable';nasaError?:string|null;usgsError?:string|null};
type Shape={id:string|number;properties?:{name?:string};geometry:unknown};
type Anchor={code:string;name:string;lon:number;lat:number};
const anchors:Anchor[]=[
  {code:'RU',name:'Russia',lon:37.62,lat:55.75},
  {code:'CN',name:'China',lon:116.4,lat:39.9},
  {code:'IR',name:'Iran',lon:51.42,lat:35.68},
  {code:'KP',name:'North Korea',lon:125.75,lat:39.03},
  {code:'BY',name:'Belarus',lon:27.56,lat:53.9},
  {code:'CU',name:'Cuba',lon:-82.37,lat:23.13},
  {code:'VE',name:'Venezuela',lon:-66.9,lat:10.5}
];
const program:Record<string,RegExp>={
  RU:/^RUSSIA/i,CN:/^CHINA/i,IR:/^IRAN|^IFSR/i,KP:/^DPRK|^NKOREA/i,
  BY:/^BELARUS/i,CU:/^CUBA/i,VE:/^VENEZUELA/i
};
const regions=[
  {label:'GLOBAL',code:'GL',center:[0,8],scale:1},
  {label:'EURASIA',code:'EU',center:[72,34],scale:1.65},
  {label:'MIDDLE EAST',code:'ME',center:[45,29],scale:2.35},
  {label:'EAST ASIA',code:'AS',center:[115,30],scale:1.95},
  {label:'AMERICAS',code:'AM',center:[-78,13],scale:1.5}
] as const;
const sourceShort:Record<string,string>={doj:'DOJ',fara:'FARA',cisa:'CISA',ofac:'OFAC'};
// User-requested policy visualization, NOT a statutory hostile-country designation.
// Keep a transparent, narrow set rather than labeling every non-ally an enemy.
const strategicAdversaries = new Set(['RU', 'CN', 'IR', 'KP']);
const fmt=(n:number)=>new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1}).format(n);
const day=(d?:string)=>d ? new Date(d.length===10?d+'T12:00:00Z':d).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}) : 'Not confirmed';
const similar=(s:string)=>s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z]/g,'');
const aliases:Record<string,string>={'russianfederation':'RU','iranislamicrepublicof':'IR','koreademocraticpeoplesrepublicof':'KP','korearepublicof':'KR','unitedstatesofamerica':'US','bolivari anrepublicofvenezuela':'VE','democraticpeoplesrepublicofkorea':'KP','republicofkorea':'KR','viet nam':'VN','syria':'SY','taiwan':'TW','cotedivoire':'CI','democraticrepublicofthecongo':'CD','congo':'CG','tanzania':'TZ','unitedkingdom':'GB','turkey':'TR','czechrepublic':'CZ','laos':'LA','myanmar':'MM','vietnam':'VN','northkorea':'KP'};
const topologyURL='https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';
const width=1120, height=560;
const base=geoNaturalEarth1().scale(188).translate([width/2,height/2+12]);
const projector=geoPath(base);
const graticule=projector(geoGraticule10());
function CountryFlag({code}:{code:string}){return <span className="cc-flag">{code.replace(/./g,c=>String.fromCodePoint(127397+c.charCodeAt(0)))}</span>;}
function MiniState({state}:{state:Health|null|undefined}){return <span className={'cc-state '+(state?.status||'pending')}><span className="cc-status-dot"/>{state?.status==='ok'?'CHECKED':state?.status==='error'?'FAILED':'PENDING'}</span>;}
function link(href:string,label:string){return <a href={href} target="_blank" rel="noopener noreferrer">{label}<ExternalLink size={12}/></a>;}
export default function CommandCenter({overview,openCountry,openCases,openDesk,openSources,openMethod,activeCountry,onCountrySelected}:Props){
  const [intel,setIntel]=useState<Intel|null>(null);
  const [worldSignals,setWorldSignals]=useState<WorldSignals|null>(null);
  const [signalError,setSignalError]=useState(false);
  const [intelligenceError,setIntelligenceError]=useState(false);
  const [mapShapes,setMapShapes]=useState<Shape[]>([]);
  const [mapError,setMapError]=useState(false);
  const [layer,setLayer]=useState<Layer>('all');
  const [region,setRegion]=useState('GL');
  const [zoom,setZoom]=useState(1);
  const [selected,setSelected]=useState(activeCountry&&activeCountry!=='all'?activeCountry:'RU');
  useEffect(()=>{if(activeCountry&&activeCountry!=='all')setSelected(activeCountry);},[activeCountry]);
  const [search,setSearch]=useState('');
  const [queryFocus,setQueryFocus]=useState(false);
  const [showLayerLegend,setShowLayerLegend]=useState(true);
  const [expandedSource,setExpandedSource]=useState(false);
  const [now,setNow]=useState(new Date());
  useEffect(()=>{
    let active=true;
    fetch(topologyURL).then(r=>{if(!r.ok)throw new Error('Map unavailable');return r.json();})
      .then(topology=>{
        if(!active)return;
        const geo=feature(topology,topology.objects.countries) as unknown as {features:Shape[]};
        setMapShapes(geo.features);setMapError(false);
      }).catch(()=>{if(active)setMapError(true);});
    return ()=>{active=false;};
  },[]);
  useEffect(()=>{
    let active=true;
    api.get('/api/intelligence')
      .then(r=>{if(active){setIntel(r.data as Intel);setIntelligenceError(false);}})
      .catch(()=>{if(active)setIntelligenceError(true);});
    return()=>{active=false;};
  },[]);
  useEffect(()=>{
    let active=true;
    api.get('/api/world-signals').then(r=>{if(active){setWorldSignals(r.data as WorldSignals);setSignalError(false);}})
      .catch(()=>{if(active)setSignalError(true);});
    return()=>{active=false;};
  },[]);
  useEffect(()=>{const t=setInterval(()=>setNow(new Date()),60000);return()=>clearInterval(t);},[]);
  const allCountries=overview.countries.filter(c=>c.scope==='state-or-observer');
  const country=overview.countries.find(c=>c.code===selected);
  const cases=overview.cases.filter(c=>c.code===selected);
  const nonAllied=allCountries.filter(c=>!c.isTreatyAlly).length;
  const checks=intel?.sources||[];
  const checked=checks.filter(s=>s.health?.status==='ok').length;
  const ofac=intel?.ofac;
  const alerts=overview.cases.filter(c=>!activeCountry||activeCountry==='all'||c.code===activeCountry).sort((a,b)=>b.date.localeCompare(a.date));
  const searchResults=search.trim()?overview.countries.filter(c=>c.name.toLowerCase().includes(search.trim().toLowerCase()) || c.code.toLowerCase()===search.trim().toLowerCase()).slice(0,8):[];
  const programCount=(code:string)=>Object.entries(ofac?.programCounts||{}).filter(([p])=>program[code]?.test(p)).reduce((a,[,n])=>a+n,0);
  const markers=anchors.map(a=>({...a,count:overview.cases.filter(c=>c.code===a.code).length,programs:programCount(a.code)}))
    .filter(a=>(!activeCountry||activeCountry==='all'||a.code===activeCountry)&&((layer==='cases'&&a.count>0)||(layer==='ofac'&&a.programs>0)||(layer==='all'&&(a.count>0||a.programs>0))));
  const findCode=(name?:string)=>{
    if(!name)return null;
    const key=similar(name);
    if(aliases[key])return aliases[key];
    return overview.countries.find(c=>similar(c.name)===key)?.code || null;
  };
  const focused=regions.find(r=>r.code===region)||regions[0];
  const scale=zoom*focused.scale;
  // Layer zoom centers by translating the map's geographic center to the screen.
  const focusCenter=base(focused.center as unknown as [number,number])||[width/2,height/2];
  const tx=(width/2)-(focusCenter[0]*scale);
  const ty=(height/2)-(focusCenter[1]*scale);
  const selectCountry=(code:string)=>{setSelected(code);onCountrySelected?.(code);setSearch('');setQueryFocus(false);};
  const hoverCountry=(name?:string)=>{const code=findCode(name);if(code)selectCountry(code);};
  return <div className="command-center">
    <div className="cc-topline"><div className="cc-topline-main"><span className="cc-signal-beacon"/><span>GLOBAL INTELLIGENCE / RESEARCH WORKSPACE</span><strong>ORIGINAL-SOURCE FIRST</strong></div><span>{now.toLocaleString('en-US',{timeZone:'UTC',hour:'2-digit',minute:'2-digit',hour12:false})} UTC · {day(now.toISOString())}</span></div>
    <div className="cc-heading-row"><div className="cc-heading"><div className="cc-mini-label"><Globe2 size={13}/> SITUATIONAL AWARENESS / 01</div><h1>THE <span>WORLD</span> IN CONTEXT.</h1><p>Map the relationships. Inspect the evidence. Separate what is known from what is still under review.</p></div><div className="cc-top-actions"><button onClick={openDesk}><Activity size={15}/> Collection health <span className="cc-online-count">{checked}/{checks.length||4}</span></button><button onClick={openSources}><Database size={15}/> Sources</button></div></div>
    <div className="cc-metrics">
      <div><span>RESEARCH JURISDICTIONS</span><strong>{nonAllied}</strong><small>Not listed primary treaty allies · not assumed hostile</small></div>
      <div><span>CURATED CASE FILES</span><strong>{overview.cases.length}</strong><small>DOJ examples, not real-time incident count</small></div>
      <div><span>OFAC SDN LISTED ENTRIES</span><strong>{ofac?fmt(ofac.records):'—'}</strong><small>{ofac?'Official export checked '+day(ofac.checkedAt):'Awaiting validated first import'}</small></div>
      <div><span>SOURCE CONNECTORS</span><strong>{checked}<small> / 4</small></strong><small>Successful most recent checks · not all global feeds</small></div>
    </div>
    <div className="cc-main-grid">
      <section className="cc-map-panel">
        <div className="cc-map-nav"><div className="cc-map-title"><span className="cc-map-signal"><Radio size={15}/></span><div><strong>Geospatial intelligence</strong><small>RESEARCH ANCHORS · NOT INCIDENT LOCATIONS</small></div></div><div className="cc-map-actions"><button onClick={()=>{setRegion('GL');setZoom(1);}} title="Reset global map"><Globe2 size={16}/></button><button onClick={()=>setZoom(z=>Math.max(.75,z-.25))} title="Zoom out" aria-label="Zoom out"><Minus size={15}/></button><span>{Math.round(scale*100)}%</span><button onClick={()=>setZoom(z=>Math.min(3,z+.25))} title="Zoom in" aria-label="Zoom in"><Plus size={15}/></button></div></div>
        <div className="cc-region-tabs">{regions.map(r=><button key={r.code} className={region===r.code?'active':''} onClick={()=>{setRegion(r.code);setZoom(1);}}>{r.label}</button>)}</div>
        <div className="cc-layer-bar"><div><Layers3 size={14}/><strong>DATA LAYERS</strong></div>{([
          ['all','All mapped signals'],
          ['cases','DOJ case files'],
          ['ofac','OFAC programs'],
          ['seismic','USGS quakes'],
          ['natural','NASA hazards']
        ] as const).map(([value,label])=><button key={value} className={layer===value?'current':''} onClick={()=>setLayer(value)}>{label}</button>)}</div>
        <div className="cc-map-viewport">
          <div className="cc-map-background-grid" aria-hidden="true"/>
          <svg className="cc-world-svg" viewBox={'0 0 '+width+' '+height} role="img" aria-label="Interactive world map of country reference anchors linked to published case files and OFAC program codes">
            <defs><pattern id="cc-map-dots" width="12" height="12" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#3c7380" opacity=".18"/></pattern><linearGradient id="cc-land-shade" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#123644"/><stop offset="1" stopColor="#10252f"/></linearGradient></defs>
            <rect width={width} height={height} fill="url(#cc-map-dots)"/>
            <g transform={'translate('+tx+' '+ty+') scale('+scale+')'}>
              {graticule&&<path d={graticule} fill="none" stroke="#3b6c7a" strokeWidth=".55" opacity=".35"/>}
              {mapShapes.length?mapShapes.map((shape,i)=>{
                const code=findCode(shape.properties?.name);
                const selectedShape=code===selected;
                const d=projector(shape as never);
                if(!d)return null;
                return <path key={String(shape.id)+'-'+i} d={d} className={'cc-country-shape '+(code && overview.countries.find(c=>c.code===code)?.isTreatyAlly?'country-ally':code && strategicAdversaries.has(code)?'country-adversary':'country-neutral')+' '+(selectedShape?'selected':'')} strokeWidth={selectedShape?1.45:.7} onClick={()=>{if(code)selectCountry(code);}} role={code?'button':undefined} tabIndex={code?0:undefined} onKeyDown={e=>{if(code&&(e.key==='Enter'||e.key===' ')){e.preventDefault();selectCountry(code);}}}><title>{shape.properties?.name||'Jurisdiction'}{code?' · Open country reference':''}</title></path>;
              }):<g opacity=".63" fill="#14414b" stroke="#34646d" strokeWidth="2"><path d="M150 143 224 99 301 101 347 161 315 212 342 253 300 288 285 356 253 350 218 286 202 239 144 210Z"/><path d="M323 279 377 302 409 343 394 413 366 479 323 426 313 370Z"/><path d="M488 147 560 112 634 119 698 90 786 117 898 116 1000 149 984 207 920 225 868 281 802 270 763 218 700 227 656 203 618 222 583 190 530 206Z"/><path d="M549 258 603 275 633 313 621 380 570 428 538 382 514 311Z"/><path d="M874 396 967 381 1000 416 953 453 890 440Z"/></g>}
              {markers.map(a=>{
                const point=base([a.lon,a.lat]);
                if(!point)return null;
                const isSelected=selected===a.code;
                const hasCases=a.count>0&&(layer!=='ofac');
                const number=layer==='ofac'?a.programs:a.count;
                const bubbleScale=1/Math.max(.7,scale);
                return <g key={a.code} className={'cc-map-marker '+(isSelected?'selected':'')} transform={'translate('+point[0]+' '+point[1]+') scale('+bubbleScale+')'} onClick={()=>selectCountry(a.code)} role="button" tabIndex={0} onKeyDown={e=>{if(e.key==='Enter'){selectCountry(a.code);}}}>
                  <circle className="cc-marker-pulse" r={isSelected?31:22}/>
                  <circle className={'cc-marker-core '+(hasCases?'case':'sanction')} r={isSelected?13:10}/>
                  <circle className="cc-marker-hole" r="3.2"/>
                  <text x="16" y="-13" className="cc-map-marker-label">{a.code}</text>
                  {number>0&&<text x="16" y="2" className="cc-map-marker-count">{hasCases?a.count+' CASE'+(a.count===1?'':'S'):fmt(a.programs)+' TAGS'}</text>}
                  <title>{a.name} · {a.count} curated DOJ cases · {a.programs} OFAC program-coded entries (not entity location)</title>
                </g>;
              })}
              {(layer==='all'||layer==='seismic')&&(!activeCountry||activeCountry==='all')&&(worldSignals?.events||[]).map(event=>{
                const point=base([event.longitude,event.latitude]);
                if(!point)return null;
                return <a key={event.id} href={event.sourceUrl} target="_blank" rel="noopener noreferrer" aria-label={'USGS report: '+event.title}>
                  <circle cx={point[0]} cy={point[1]} r={Math.max(3.4,event.magnitude*.96)/Math.max(.9,scale)} stroke="#f6dbb3" strokeWidth={1/scale} fill="#dba16b" fillOpacity=".85">
                    <title>{event.title} · {day(event.date)} · USGS source</title>
                  </circle>
                </a>;
              })}
              {(layer==='all'||layer==='natural')&&(!activeCountry||activeCountry==='all')&&(worldSignals?.naturalEvents||[]).map(event=>{
                const point=base([event.longitude,event.latitude]);
                if(!point)return null;
                return <a key={event.id} href={event.sourceUrl} target="_blank" rel="noopener noreferrer" aria-label={'NASA EONET source: '+event.title}>
                  <circle cx={point[0]} cy={point[1]} r={5/Math.max(.9,scale)} stroke="#f4c87a" strokeWidth={1/scale} fill="#83dfbd" fillOpacity=".9"><title>{event.title} · {event.eventType} · {day(event.date)} · NASA EONET</title></circle>
                </a>;
              })}
            </g>
          </svg>
          {mapError&&<span className="cc-map-unavailable"><CircleAlert size={15}/> Boundary tiles unavailable · reference anchors remain available</span>}
          <div className="cc-compass"><span>N</span><span className="cc-compass-arrow">↑</span><small>MAP / 110M</small></div>
          <div className="cc-map-overlay-label">EASTERN AXIS / GEOSPATIAL VIEW <span>MAP BASE: OPEN TOPOGRAPHY</span></div>
        </div>
        <div className="cc-map-footer"><div><span className="cc-dot-ally"/> Blue: U.S. treaty allies <span className="cc-dot-adversary"/> Red: RU, CN, IR, KP (strategic-adversary context) <span className="cc-dot-neutral"/> Gray: other / not classified <span className="cc-dot-mint"/> DOJ-sourced jurisdiction marker <span className="cc-dot-gold"/> OFAC sanctions-program reference <span className="cc-dot-gold"/> USGS earthquake epicenter · NASA EONET natural event</div><button onClick={()=>setShowLayerLegend(v=>!v)}><Shield size={13}/> Legend & caveats <ChevronDown size={13}/></button></div>
        {layer==='natural'&&<div className="cc-legend-notice"><Activity size={16}/><span>{activeCountry&&activeCountry!=='all'?'Country filter active: global natural events are hidden. Choose Global / regional in the header to see NASA data.':signalError?'Environmental feed unavailable; no events have been invented.':worldSignals?.nasaStatus==='unavailable'?'NASA EONET events are unavailable. USGS earthquake data is independently checked; see Earth signals.':!worldSignals?'Checking NASA EONET source status…':(worldSignals.naturalEvents?.length||0)===0?'NASA EONET returned no eligible point events in the bounded window. Polygon-only events are excluded.':'NASA EONET: '+(worldSignals.naturalEvents?.length||0)+' source-reported point events in this sampled window.'}</span></div>}
        {layer==='seismic' && worldSignals?.usgsStatus==='unavailable' && <div className="cc-legend-notice"><CircleAlert size={16}/><span>USGS earthquake markers are unavailable right now. No synthetic epicenters are shown.</span></div>}
        {showLayerLegend&&<div className="cc-legend-notice"><ShieldCheck size={16}/><span>Blue marks U.S. treaty allies; red highlights Russia, China, Iran and North Korea for focused policy research; gray means neither grouping, not a security verdict. These categories are analytical choices, not universal legal designations. Markers are anchored to national capitals for navigation, <strong>not where an incident occurred.</strong> OFAC program tags do not establish listed-party locations or state direction. USGS epicenters and NASA EONET natural events use publisher-reported coordinates, not independent AI geolocation; neither implies foreign-government actions. Global hazards are hidden under a country-only filter to prevent false attribution.</span></div>}
      </section>      <aside className="cc-brief-panel">
        <div className="cc-aside-head"><span><Eye size={14}/> COUNTRY CONTEXT</span><span className="cc-aside-live">SOURCE-BACKED</span></div>
        <div className="cc-country-search"><Search size={16}/><input aria-label="Search any country" placeholder="Find a country…" value={search} onFocus={()=>setQueryFocus(true)} onBlur={()=>setTimeout(()=>setQueryFocus(false),120)} onChange={e=>setSearch(e.target.value)}/>{search&&<button aria-label="Clear search" onClick={()=>setSearch('')}><X size={14}/></button>}</div>
        {searchResults.length>0&&queryFocus&&<div className="cc-search-results">{searchResults.map(c=><button key={c.code} onMouseDown={e=>e.preventDefault()} onClick={()=>selectCountry(c.code)}><CountryFlag code={c.code}/><span>{c.name}</span><small>{c.code}</small></button>)}</div>}
        {country?<div className="cc-country-detail">
          <div className="cc-focus-head"><CountryFlag code={country.code}/><div><h2>{country.name}</h2><small>{country.region.toUpperCase()} · {country.code}</small></div></div>
          <div className="cc-country-tags"><span className={country.isTreatyAlly?'ally':'other'}>{country.isTreatyAlly?'PRIMARY TREATY ALLY':'RESEARCH SCOPE'}</span>{country.isMNNA&&<span>MNNA</span>}</div>
          <div className="cc-data-line"><span>SECURITY RELATIONSHIP</span><strong>{country.relationship}</strong></div>
          <div className="cc-data-line"><span>CURATED DOJ FILES</span><strong>{cases.length}</strong></div>
          <div className="cc-data-line"><span>OFAC PROGRAM TAGS</span><strong>{ofac?programCount(country.code).toLocaleString():'Not checked'}</strong></div>
          {ofac&&programCount(country.code)>0&&<p className="cc-program-disclaimer">Program labels may reference this country; they do not locate listed persons or establish government conduct.</p>}
          <div className="cc-aside-section-title">EVIDENCE IN VIEW</div>
          {cases.length?cases.slice(0,3).map(c=><button key={c.id} className="cc-brief-case" onClick={()=>openCases(c.id)}><small>{day(c.date)} · DOJ RECORD</small><strong>{c.title}</strong><span>{c.status} <ArrowUpRight size={13}/></span></button>):<div className="cc-empty-case">No curated case in this starter library. This does not indicate absence of activity.</div>}
          <button className="cc-country-open" onClick={()=>openCountry(country.code)}>Open full country dossier <ArrowRight size={15}/></button>
        </div>:<div className="cc-empty-case">Select a country to inspect its source-backed dossier.</div>}
        <div className="cc-aside-disclaimer"><LockKeyhole size={14}/><p>Evidence states: official listing, alleged conduct, adjudicated outcome and analytical inference remain separate.</p></div>
      </aside>
    </div>
    <div className="cc-bottom-grid">
      <section className="cc-stream-panel"><div className="cc-panel-head"><div><span className="cc-mini-label"><Radio size={13}/> PRIMARY SOURCES / CASE ACTIVITY</span><h2>Investigation wires</h2></div><button onClick={()=>openCases()}>VIEW ALL <ArrowUpRight size={14}/></button></div><div className="cc-wires">{alerts.slice(0,4).map(c=><button key={c.id} onClick={()=>openCases(c.id)}><span className="cc-wire-country">{c.code}</span><div><strong>{c.title}</strong><small>{c.topic} · {c.status}</small></div><span className="cc-wire-date">{day(c.date)}</span><ArrowUpRight size={14}/></button>)}</div><div className="cc-panel-foot">Curated archival case examples. Dates are published-record dates, not a continuous real-time alert stream.</div></section>
      <section className="cc-connect-panel"><div className="cc-panel-head"><div><span className="cc-mini-label"><Network size={13}/> DATA NETWORK / SOURCE TELEMETRY</span><h2>Connected intelligence</h2></div><button onClick={openDesk}>HEALTH <ArrowUpRight size={14}/></button></div>{intelligenceError&&<div className="cc-warning-inline"><CircleAlert size={14}/> Intake status unavailable · no sources assumed healthy</div>}<div className="cc-connectors">{['doj','ofac','fara','cisa'].map(id=>{
        const feed=checks.find(f=>f.id===id);
        return <div key={id} className="cc-connector"><span className="cc-connector-icon">{sourceShort[id]}</span><div><strong>{id==='doj'?'Justice Department':id==='fara'?'FARA disclosures':id==='ofac'?'Treasury sanctions':'Cyber advisories'}</strong><small>{feed?.health?.lastSuccessAt?'Last successful '+day(feed.health.lastSuccessAt):'No successful run recorded'}</small></div><MiniState state={feed?.health}/></div>;
      })}</div><button className="cc-all-tools" onClick={()=>setExpandedSource(v=>!v)}><Layers3 size={15}/> {expandedSource?'Hide':'Explore'} research tools & references <ChevronDown size={15}/></button>{expandedSource&&<div className="cc-external-tools">{overview.sources.map(s=><a key={s.id} href={s.url} target="_blank" rel="noopener noreferrer"><div><strong>{s.name}</strong><small>{s.mode}</small></div><ExternalLink size={13}/></a>)}</div>}</section>
    </div>

    <section className="cc-live-panel">
      <div className="cc-panel-head"><div><span className="cc-mini-label"><Activity size={13}/> LIVE ENVIRONMENTAL DATA / GEOLOCATED</span><h2>Earth signals</h2></div><a href="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php" target="_blank" rel="noopener noreferrer">USGS M4.5+ / 24H <ExternalLink size={13}/></a></div>
      {signalError
        ? <p className="cc-live-error"><CircleAlert size={15}/> Environmental-service status could not be loaded. No source has been assumed unavailable and no events have been invented.</p>
        : worldSignals ? <>
          {worldSignals.usgsStatus==='ok'
            ? <><p className="cc-live-updated"><CheckCircle2 size={14}/> USGS operational · feed generated {day(worldSignals.generatedAt)} · {worldSignals.count} reported M4.5+ earthquakes in the past 24 hours</p><div className="cc-live-events">{worldSignals.events.slice(0,8).map(e=><a key={e.id} href={e.sourceUrl} target="_blank" rel="noopener noreferrer"><span>M {e.magnitude.toFixed(1)}</span><strong>{e.title}</strong><small>{day(e.date)}</small><ExternalLink size={12}/></a>)}</div></>
            : <p className="cc-live-error"><CircleAlert size={15}/> USGS earthquake data unavailable{worldSignals.usgsError?' · '+worldSignals.usgsError:''}. No earthquake count is being inferred.</p>}
          {worldSignals.nasaStatus==='unavailable'
            ? <p className="cc-live-error"><CircleAlert size={15}/> NASA EONET natural-event feed unavailable{worldSignals.nasaError?' · '+worldSignals.nasaError:''}. This does not affect the USGS earthquake feed. <a href="https://eonet.gsfc.nasa.gov/api/v3/events" target="_blank" rel="noopener noreferrer">NASA source <ExternalLink size={13}/></a></p>
            : <p className="cc-live-updated"><CheckCircle2 size={14}/> NASA EONET responding · {(worldSignals.naturalEvents||[]).length} eligible point events displayed</p>}
        </> : <p className="cc-live-updated">Checking USGS earthquakes and NASA EONET independently…</p>}
      <p className="cc-live-caveat">These are observed earthquake locations, not espionage, conflict or foreign influence. The USGS layer can be isolated from investigation and sanctions-program references.</p>
    </section>
    <div className="cc-final-strip"><div><ShieldCheck size={17}/><strong>INTELLIGENCE ISN'T A VERDICT.</strong><span>Nonallied ≠ adversarial. A sanctions list ≠ criminal judgment. Media reports ≠ corroboration.</span></div><button onClick={openMethod}>EVIDENCE RULES <ArrowRight size={13}/></button></div>
  </div>;
}