import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { feature } from 'topojson-client';
import { geoNaturalEarth1, geoGraticule10, geoPath } from 'd3-geo';
import { Activity, ArrowRight, ArrowUpRight, BadgeAlert, BookOpen, CheckCircle2, ChevronDown, CircleAlert, Clock3, Database, ExternalLink, Eye, Filter, Globe2, Layers3, LockKeyhole, Map, Minus, Network, Plus, Radio, RefreshCcw, Search, Shield, ShieldCheck, SlidersHorizontal, X } from 'lucide-react';
import './command.css';
import DecisionRadar from './DecisionRadar';

type Country = {code:string;name:string;region:string;scope:string;relationship:string;securityNote?:string;usRelationship?:string;securitySources?:{label:string;url:string}[];isTreatyAlly:boolean;isMNNA:boolean;caseCount:number};
type CaseFile = {id:string;code:string;date:string;title:string;topic:string;status:string;level:string;summary:string;impact:string;source:string;agency:string};
type Source = {id:string;name:string;category:string;mode:string;cost:string;url:string;description:string};
type Overview = {countries:Country[];cases:CaseFile[];sources:Source[];snapshot:null|{updatedAt:string;coveredCountries:number}};
type Health={sourceId:string;status:'ok'|'error';lastAttemptAt:string;lastSuccessAt?:string;lastError?:string;examined:number;inserted:number};
type Intake = {id:string;sourceId:string;title:string;date:string;countryMention?:string;summary:string;sourceUrl:string;recordType:string;sanctionsPrograms?:string[]};
type OFACMeta = {checkedAt:string;records:number;sampleSize:number;programCounts:Record<string,number>;dataset:string;scope:string};
type Intel={sources:{id:string;name:string;health:Health|null;documentation:string}[];records:Intake[];ofac?:OFACMeta|null;sampled:number;resultsNote:string};
type Props={overview:Overview;openCountry:(code:string)=>void;openCases:(id?:string)=>void;openDesk:()=>void;openSources:()=>void;openMethod:()=>void;activeCountry?:string;onCountrySelected?:(code:string)=>void;onNavigate:(target:'Early warning'|'Supply chain'|'Risk watch'|'Defense intelligence'|'Countries',focus?:'funding'|'commodities'|'gnss')=>void;mode?:'home'|'geospatial'};
type Layer='cases'|'ofac'|'seismic'|'natural';
type Seismic={id:string;title:string;longitude:number;latitude:number;magnitude:number;date:string;source:string;sourceUrl:string};
type WorldSignals={status:string;count:number;generatedAt:string;checkedAt:string;events:Seismic[];naturalEvents?:Array<{id:string;title:string;eventType:string;longitude:number;latitude:number;date:string;source:string;sourceUrl:string}>;nasaStatus?:string;usgsStatus?:string};
type Shape={id:string|number;properties?:{name?:string};geometry:unknown};
type Anchor={code:string;name:string;lon:number;lat:number};
type MapEvent={id:string;title:string;longitude:number;latitude:number;date:string;sourceUrl:string;kind:'usgs'|'nasa';magnitude?:number;eventType?:string};
type MapCluster={id:string;longitude:number;latitude:number;events:MapEvent[]};
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
// External hazard pointers must be official event URLs. Unverifiable targets
// remain informative map dots, never misleading clickable links.
function officialEventUrl(value:string,kind:'usgs'|'nasa'):string|null {
  try {
    const url=new URL(value);
    if(url.protocol!=='https:' || url.username || url.password) return null;
    if(kind==='usgs') return url.hostname==='earthquake.usgs.gov'
      && url.pathname.startsWith('/earthquakes/eventpage/') ? url.href : null;
    return url.hostname==='eonet.gsfc.nasa.gov'
      && url.pathname.startsWith('/api/v3/events/') ? url.href : null;
  } catch {return null;}
}
const fmt=(n:number)=>new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1}).format(n);
const day=(d?:string)=>d ? new Date(d.length===10?d+'T12:00:00Z':d).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}) : 'Not confirmed';
const similar=(s:string)=>s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z]/g,'');
const aliases:Record<string,string>={'russianfederation':'RU','iranislamicrepublicof':'IR','koreademocraticpeoplesrepublicof':'KP','korearepublicof':'KR','unitedstatesofamerica':'US','bolivarianrepublicofvenezuela':'VE','democraticpeoplesrepublicofkorea':'KP','republicofkorea':'KR','viet nam':'VN','syria':'SY','taiwan':'TW','cotedivoire':'CI','democraticrepublicofthecongo':'CD','congo':'CG','tanzania':'TZ','unitedkingdom':'GB','turkey':'TR','czechrepublic':'CZ','laos':'LA','myanmar':'MM','vietnam':'VN','northkorea':'KP','macedonia':'MK','ssudan':'SS','demrepcongo':'CD','dominicanrep':'DO','eqguinea':'GQ','centralafricanrep':'CF','solomonis':'SB','bosniaandherz':'BA'};
const topologyURL='https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json';
const width=1120, height=560;
const base=geoNaturalEarth1().scale(188).translate([width/2,height/2+12]);
// One discoverable pin per proximity cluster. Never allow overlapping SVG links
// to send the user to a different earthquake than the title they selected.
function clusterMapEvents(events:MapEvent[],scale:number):MapCluster[] {
  const clusters:MapCluster[]=[];
  const threshold=22/Math.max(0.7,scale);
  for(const event of events){
    if(!Number.isFinite(event.longitude)||!Number.isFinite(event.latitude)
       || Math.abs(event.latitude)>90 || Math.abs(event.longitude)>180)continue;
    const p=base([event.longitude,event.latitude]);if(!p)continue;
    const existing=clusters.find(c=>{
      const q=base([c.longitude,c.latitude]);
      return q!==null&&Math.hypot(p[0]-q[0],p[1]-q[1])<threshold;
    });
    if(existing)existing.events.push(event);
    else clusters.push({id:event.kind+':'+event.id,longitude:event.longitude,latitude:event.latitude,events:[event]});
  }
  return clusters;
}
const projector=geoPath(base);
const graticule=projector(geoGraticule10());
function CountryFlag({code}:{code:string}){return <span className="cc-flag">{code.replace(/./g,c=>String.fromCodePoint(127397+c.charCodeAt(0)))}</span>;}
function MiniState({state}:{state:Health|null|undefined}){return <span className={'cc-state '+(state?.status||'pending')}><span className="cc-status-dot"/>{state?.status==='ok'?'CHECKED':state?.status==='error'?'FAILED':'PENDING'}</span>;}
function link(href:string,label:string){return <a href={href} target="_blank" rel="noopener noreferrer">{label}<ExternalLink size={12}/></a>;}
export default function CommandCenter({overview,openCountry,openCases,openDesk,openSources,openMethod,activeCountry,onCountrySelected,onNavigate,mode='home'}:Props){
  const [intel,setIntel]=useState<Intel|null>(null);
  const [worldSignals,setWorldSignals]=useState<WorldSignals|null>(null);
  const [signalError,setSignalError]=useState(false);
  const [intelligenceError,setIntelligenceError]=useState(false);
  const [mapShapes,setMapShapes]=useState<Shape[]>([]);
  const [mapError,setMapError]=useState(false);
  const [layer,setLayer]=useState<Layer>('cases');
  const [selectedMapCluster,setSelectedMapCluster]=useState<string|null>(null);
  const [region,setRegion]=useState('GL');
  const [zoom,setZoom]=useState(1);
  const [selected,setSelected]=useState(activeCountry&&activeCountry!=='all'?activeCountry:'RU');
  useEffect(()=>{if(activeCountry&&activeCountry!=='all')setSelected(activeCountry);},[activeCountry]);
  const [search,setSearch]=useState('');
  const [queryFocus,setQueryFocus]=useState(false);
  const [showLayerLegend,setShowLayerLegend]=useState(true);
  const [expandedSource,setExpandedSource]=useState(false);
  const [now,setNow]=useState(new Date());
  const [refreshToken,setRefreshToken]=useState(0);
  const [lastRequestedAt,setLastRequestedAt]=useState<string|null>(null);
  useEffect(()=>{const timer=window.setInterval(()=>setRefreshToken(value=>value+1),5*60*1000);return()=>window.clearInterval(timer);},[]);
  useEffect(()=>{setLastRequestedAt(new Date().toISOString());},[refreshToken,mode]);
  useEffect(()=>{
    if(mode!=='geospatial')return;
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
    if(mode!=='geospatial')return;
    let active=true;
    api.get('/api/intelligence')
      .then(r=>{if(active){setIntel(r.data as Intel);setIntelligenceError(false);}})
      .catch(()=>{if(active)setIntelligenceError(true);});
    return()=>{active=false;};
  },[refreshToken,mode]);
  useEffect(()=>{
    if(mode!=='geospatial')return;
    let active=true;
    api.get('/api/world-signals').then(r=>{if(active){setWorldSignals(r.data as WorldSignals);setSignalError(false);}})
      .catch(()=>{if(active)setSignalError(true);});
    return()=>{active=false;};
  },[refreshToken,mode]);
  useEffect(()=>{const t=setInterval(()=>setNow(new Date()),60000);return()=>clearInterval(t);},[]);
  const country=overview.countries.find(c=>c.code===selected);
  const cases=overview.cases.filter(c=>c.code===selected);
  const checks=intel?.sources||[];
  const ofac=intel?.ofac;
  const alerts=overview.cases.filter(c=>!activeCountry||activeCountry==='all'||c.code===activeCountry).sort((a,b)=>b.date.localeCompare(a.date));
  const searchResults=search.trim()?overview.countries.filter(c=>c.name.toLowerCase().includes(search.trim().toLowerCase()) || c.code.toLowerCase()===search.trim().toLowerCase()).slice(0,8):[];
  const programCount=(code:string)=>Object.entries(ofac?.programCounts||{}).filter(([p])=>program[code]?.test(p)).reduce((a,[,n])=>a+n,0);
  const markers=anchors.map(a=>({...a,count:overview.cases.filter(c=>c.code===a.code).length,programs:programCount(a.code)}))
    .filter(a=>(!activeCountry||activeCountry==='all'||a.code===activeCountry)&&((layer==='cases'&&a.count>0)||(layer==='ofac'&&a.programs>0)));
  const findCode=(name?:string)=>{
    if(!name)return null;
    const key=similar(name);
    if(aliases[key] && overview.countries.some(c=>c.code===aliases[key]))return aliases[key];
    return overview.countries.find(c=>similar(c.name)===key)?.code || null;
  };
  const focused=regions.find(r=>r.code===region)||regions[0];
  const scale=zoom*focused.scale;
  const mapEvents:MapEvent[]=(!activeCountry||activeCountry==='all')
    ? layer==='seismic'?(worldSignals?.events||[]).map(e=>({...e,kind:'usgs' as const}))
    :layer==='natural'?(worldSignals?.naturalEvents||[]).map(e=>({...e,kind:'nasa' as const}))
    :[] : [];
  const eventClusters=clusterMapEvents(mapEvents,scale);
  const selectedEventCluster=eventClusters.find(c=>c.id===selectedMapCluster);
  const focusEvent=(id:string)=>{
    const cluster=eventClusters.find(c=>c.events.some(e=>e.id===id));
    if(cluster)setSelectedMapCluster(cluster.id);
  };
  // Layer zoom centers by translating the map's geographic center to the screen.
  const focusCenter=base(focused.center as unknown as [number,number])||[width/2,height/2];
  const tx=(width/2)-(focusCenter[0]*scale);
  const ty=(height/2)-(focusCenter[1]*scale);
  const selectCountry=(code:string)=>{setSelected(code);onCountrySelected?.(code);setSearch('');setQueryFocus(false);};
  const hoverCountry=(name?:string)=>{const code=findCode(name);if(code)selectCountry(code);};
  return <div className={"command-center "+(mode==='geospatial'?'cc-geospatial-only':'cc-home-only')}>
    {mode==='home'&&<DecisionRadar countryCode={activeCountry||'all'} countryName={overview.countries.find(c=>c.code===activeCountry)?.name} onNavigate={onNavigate}/>}
    {mode==='geospatial'&&<>
      <div className="cc-geospatial-heading"><span>COUNTRY INTELLIGENCE / GEOSPATIAL</span><strong>Explore locations and documented country records</strong></div>
    <div className="cc-main-grid cc-map-only">
      <section className="cc-map-panel">
        <div className="cc-map-nav"><div className="cc-map-title"><span className="cc-map-signal"><Radio size={15}/></span><div><strong>Geospatial intelligence</strong><small>RESEARCH ANCHORS · NOT INCIDENT LOCATIONS</small></div></div><div className="cc-map-actions"><button onClick={()=>{setRegion('GL');setZoom(1);}} title="Reset global map"><Globe2 size={16}/></button><button onClick={()=>setZoom(z=>Math.max(.75,z-.25))} title="Zoom out" aria-label="Zoom out"><Minus size={15}/></button><span>{Math.round(scale*100)}%</span><button onClick={()=>setZoom(z=>Math.min(3,z+.25))} title="Zoom in" aria-label="Zoom in"><Plus size={15}/></button></div></div>
        <div className="cc-region-tabs">{regions.map(r=><button key={r.code} className={region===r.code?'active':''} onClick={()=>{setRegion(r.code);setZoom(1);}}>{r.label}</button>)}</div>
        <div className="cc-layer-bar"><div><Layers3 size={14}/><strong>DATA LAYERS</strong></div>{([
          ['cases','Curated cases'],
          ['ofac','OFAC program entries'],
          ['seismic','USGS earthquakes'],
          ['natural','NASA natural hazards']
        ] as const).map(([value,label])=><button key={value} className={layer===value?'current':''} onClick={()=>{setLayer(value);setSelectedMapCluster(null);}}>{label}</button>)}</div>
        <div className="cc-map-viewport">
          <div className="cc-map-background-grid" aria-hidden="true"/>
          <svg className="cc-world-svg" viewBox={'0 0 '+width+' '+height} role="group" aria-label="Interactive country reference map; choose a data layer to inspect cases, OFAC program tags, or separately sourced natural hazards">
            <defs><pattern id="cc-map-dots" width="12" height="12" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#3c7380" opacity=".18"/></pattern><linearGradient id="cc-land-shade" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#123644"/><stop offset="1" stopColor="#10252f"/></linearGradient></defs>
            <rect width={width} height={height} fill="url(#cc-map-dots)"/>
            <g transform={'translate('+tx+' '+ty+') scale('+scale+')'}>
              {graticule&&<path d={graticule} fill="none" stroke="#3b6c7a" strokeWidth=".55" opacity=".35"/>}
              {mapShapes.length?mapShapes.map((shape,i)=>{
                const code=findCode(shape.properties?.name);
                const selectedShape=code===selected;
                const d=projector(shape as never);
                if(!d)return null;
                return <path key={String(shape.id)+'-'+i} d={d} className={'cc-country-shape '+(code && (code==='US'||overview.countries.find(c=>c.code===code)?.isTreatyAlly)?'country-ally':code && strategicAdversaries.has(code)?'country-adversary':'country-neutral')+(code?' selectable':'')+(selectedShape?' selected':'')} strokeWidth={selectedShape?1.45:.7} onClick={code?()=>selectCountry(code):undefined} role={code?'button':undefined} tabIndex={code?0:undefined} onKeyDown={e=>{if(code&&(e.key==='Enter'||e.key===' ')){e.preventDefault();selectCountry(code);}}}><title>{overview.countries.find(c=>c.code===code)?.name||shape.properties?.name||'Jurisdiction'}{code?' · Select country context (not an incident marker)':' · No linked country record in this catalog'}</title></path>;
              }):null}
              {markers.map(a=>{
                const point=base([a.lon,a.lat]);
                if(!point)return null;
                const isSelected=selected===a.code;
                const hasCases=a.count>0&&(layer!=='ofac');
                const number=hasCases?a.count:a.programs;
                const bubbleScale=1/Math.max(.7,scale);
                return <g key={a.code} className={'cc-map-marker '+(isSelected?'selected':'')} transform={'translate('+point[0]+' '+point[1]+') scale('+bubbleScale+')'} onClick={()=>selectCountry(a.code)} role="button" tabIndex={0} onKeyDown={e=>{if(e.key==='Enter'){selectCountry(a.code);}}}>
                  <circle className="cc-marker-pulse" r={isSelected?31:22}/>
                  <circle className={'cc-marker-core '+(hasCases?'case':'sanction')} r={isSelected?13:10}/>
                  <circle className="cc-marker-hole" r="3.2"/>
                  <text x="16" y="-13" className="cc-map-marker-label">{a.code}</text>
                  {number>0&&<text x="16" y="2" className="cc-map-marker-count">{hasCases?a.count+' CASE'+(a.count===1?'':'S'):fmt(a.programs)+' OFAC ENTRIES'}</text>}
                  <title>{a.name} · {a.count} curated DOJ cases · {a.programs} OFAC program-coded entries (not entity location)</title>
                </g>;
              })}
              {eventClusters.map(cluster=>{
                const point=base([cluster.longitude,cluster.latitude]);if(!point)return null;
                const isQuake=layer==='seismic',size=cluster.events.length;
                const r=(size>1?11:isQuake?Math.max(5,(cluster.events[0].magnitude||4)*.96):6)/Math.max(.9,scale);
                return <g key={cluster.id} className={'cc-hazard-marker '+(selectedMapCluster===cluster.id?'selected':'')}
                  role="button" tabIndex={0} aria-label={size+' nearby '+(isQuake?'earthquake':'NASA')+' event'+(size===1?'':'s')+'; select exact sources'}
                  onClick={()=>setSelectedMapCluster(cluster.id)}
                  onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelectedMapCluster(cluster.id);}}}>
                  <circle cx={point[0]} cy={point[1]} r={r} stroke={isQuake?'#ffe4b4':'#9ce6f6'} strokeWidth={1.2/scale} fill={isQuake?'#dba16b':'#5db6e2'} fillOpacity=".92"/>
                  {size>1&&<text x={point[0]} y={point[1]+3.2/scale} textAnchor="middle" fontSize={9/scale} fontWeight="800" fill="#091923">{size}</text>}
                  <title>{size===1?cluster.events[0].title:'Nearby source events — select to inspect exact records'}</title>
                </g>;
              })}
            </g>
          </svg>
          {mapError&&<span className="cc-map-unavailable"><CircleAlert size={15}/> World boundaries unavailable · markers remain approximate research anchors</span>}
          <div className="cc-compass"><span>N</span><span className="cc-compass-arrow">↑</span><small>MAP / 110M</small></div>
          <div className="cc-map-overlay-label">EASTERN AXIS / GEOSPATIAL VIEW <span>BOUNDARIES: WORLD-ATLAS 110M</span></div>
        </div>
        {(layer==='seismic'||layer==='natural')&&<div className="cc-map-event-panel" aria-label="Map event sources">
          <div className="cc-map-event-head"><strong>{layer==='seismic'?'USGS earthquakes':'NASA EONET natural events'} · {mapEvents.length} observations / {eventClusters.length} map pins</strong><small>Markers select records; external sources open only from exact event details.</small></div>
          {selectedEventCluster&&<div className="cc-map-event-selected" aria-label="Selected map events">
            <div className="cc-map-selected-top"><strong>{selectedEventCluster.events.length===1?'Selected event':selectedEventCluster.events.length+' nearby events — choose the exact source'}</strong><button type="button" onClick={()=>setSelectedMapCluster(null)}>Clear selection</button></div>
            {selectedEventCluster.events.map(event=>{
              const href=officialEventUrl(event.sourceUrl,event.kind);
              return <article key={event.kind+event.id} className="cc-map-source-record">
                <div><strong>{event.title}</strong><small>{day(event.date)}{typeof event.magnitude==='number'?' · M '+event.magnitude.toFixed(1):event.eventType?' · '+event.eventType:''}</small></div>
                {href?<a href={href} target="_blank" rel="noopener noreferrer">{event.kind==='usgs'?'View exact USGS report':'NASA source (raw JSON)'} <ExternalLink size={13}/></a>:<span>Source link unavailable</span>}
              </article>;
            })}
          </div>}
          <details className="cc-map-event-list"><summary>Browse all {mapEvents.length} event records</summary>
            <div className="cc-map-event-rows">{mapEvents.map(event=><button type="button" key={event.kind+event.id} onClick={()=>focusEvent(event.id)}><strong>{event.title}</strong><small>{day(event.date)} · Select its map group</small></button>)}</div>
          </details>
          {mapEvents.length===0&&<p className="cc-map-event-empty">{activeCountry&&activeCountry!=='all'?'Select Worldwide to see global hazard observations.':signalError?'Environmental feed unavailable. No events inferred.':'No eligible point observations in the latest source sample.'}</p>}
        </div>}
        <div className="cc-map-footer">
          <div className="cc-legend-countries" aria-label="Country-area legend"><strong>COUNTRY STATUS</strong><span><i className="cc-dot-ally"/> U.S. + indexed treaty allies</span><span><i className="cc-dot-adversary"/> Four U.S. strategic focus states</span><span><i className="cc-dot-neutral"/> Other / unclassified</span></div>
          <div className="cc-legend-signals" aria-label="Current data-layer legend"><strong>VISIBLE MAP POINTS</strong>
            {layer==='cases'&&<span><i className="cc-dot-mint"/> Curated case → country context</span>}
            {layer==='ofac'&&<span><i className="cc-dot-gold"/> OFAC program entries → country context, NOT locations</span>}
            {layer==='seismic'&&<span><i className="cc-dot-quake"/> USGS earthquake point / cluster (number = nearby records)</span>}
            {layer==='natural'&&<span><i className="cc-dot-nasa"/> NASA natural event point / cluster (number = nearby records)</span>}
          </div>
          <button type="button" aria-expanded={showLayerLegend} onClick={()=>setShowLayerLegend(v=>!v)}><Shield size={13}/> Legend & caveats <ChevronDown size={13}/></button>
        </div>
        {layer==='natural'&&<div className="cc-legend-notice"><Activity size={16}/><span>{activeCountry&&activeCountry!=='all'?'Country filter active: global natural events are hidden. Choose Global / regional in the header to see NASA data.':signalError?'Environmental feed unavailable; no events have been invented.':worldSignals?.nasaStatus==='unavailable'?'NASA EONET is unavailable. USGS data may remain available.':!worldSignals?'Checking NASA EONET source status…':(worldSignals.naturalEvents?.length||0)===0?'NASA EONET returned no eligible point events in the bounded window. Polygon-only events are excluded.':'NASA EONET: '+(worldSignals.naturalEvents?.length||0)+' source-reported point events in this sampled window.'}</span></div>}
        {showLayerLegend&&<div className="cc-legend-notice"><ShieldCheck size={16}/><span>Blue marks the U.S. and countries indexed as U.S. treaty allies; red highlights Russia, China, Iran and North Korea for U.S. strategic-focus research; gray means neither category or incomplete treaty coverage, not a security verdict. These categories are analytical choices, not universal legal designations. Case and OFAC markers are anchored to national capitals for navigation, <strong>not where an incident occurred.</strong> OFAC program tags do not establish listed-party locations or state direction. USGS epicenters and NASA EONET natural events use publisher-reported coordinates, not independent AI geolocation; neither implies foreign-government actions. Earthquakes and NASA natural events appear only in their respective layers, and are hidden under country-only filters to avoid implying geopolitical causation. Numbered circles group nearby records; select a circle and then the exact source link below, never assume an overlapping dot identifies one event.</span></div>}
      </section>
    </div>
    </>}
  </div>;
}
