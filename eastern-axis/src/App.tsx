import { Fragment, useEffect, useMemo, useRef, useState } from 'react';
import IntakeDesk from './IntakeDesk';
import CountryPicker from './CountryPicker';
import BugReportDialog from './BugReportDialog';
import IntelCardDetails from './IntelCardDetails';
import { withSecurityContext } from './securityTreaties';
import GlobalSystems from './GlobalSystems';
import FinancialTransmission from './FinancialTransmission';
import ResilienceWatch from './ResilienceWatch';
import {ContextRail,MobileAlerts,MobileDomains,MobileBriefcase,useIntelligenceFeed,type SavedWorkspace} from './CommandInterface';
import {GlobalFiltersContext, type Horizon, type Severity} from './GlobalFiltersContext';
import ConnectedSources from './ConnectedSources';
import OperationalAssurance from './OperationalAssurance';
import EconomicIntelligence, { type EconomicFocus } from './EconomicIntelligence';
import Connections from './Connections';
import CountrySourceIndex from './CountrySourceIndex';
import EvidenceWorkbench from './EvidenceWorkbench';
import CommandCenter from './CommandCenter';
import Factbook from './Factbook';
import CountryFactbook from './CountryFactbook';
import './control-room.css';
import DefenseIntel from './DefenseIntel';
import AgentDesk from './AgentDesk';
import { api } from '@appdeploy/client';
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Bug,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Database,
  ExternalLink,
  FileSearch,
  Filter,
  Globe2,
  Layers3,
  Bell,
  Bookmark,
  BriefcaseBusiness,
  Command,
  Copy,
  Grid2X2,
  Link2,
  LoaderCircle,
  MapPin,
  Menu,
  Network,
  Radio,
  RefreshCcw,
  Search,
  Shield,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  X,
} from 'lucide-react';

type Country = {
  code: string;
  name: string;
  region: string;
  scope: string;
  relationship: string;
  securityNote?: string;
  usRelationship?: string;
  securitySources?: { label: string; url: string }[];
  isTreatyAlly: boolean;
  isMNNA: boolean;
  caseCount: number;
};
type CaseFile = {
  id: string;
  code: string;
  date: string;
  title: string;
  topic: string;
  status: string;
  level: string;
  summary: string;
  impact: string;
  source: string;
  agency: string;
};
type Source = {
  id: string;
  name: string;
  category: string;
  mode: string;
  cost: string;
  url: string;
  description: string;
};
type Overview = {
  countries: Country[];
  cases: CaseFile[];
  sources: Source[];
  snapshot: null | { updatedAt: string; coveredCountries: number };
  classificationAsOf: string;
  scopeDefinition: string;
  classificationSources: string[];
};
type Metric = {
  value: number;
  year: string;
  indicator: string;
  source: string;
};
type Brief = {
  code: string;
  updatedAt: string;
  mode: string;
  warning?: string;
  metrics: Record<string, Metric>;
};
// All existing workspaces are retained; taxonomy only changes where they are reached.
const sections = [
  'Overview', 'Countries', 'World Factbook', 'Economic intelligence',
  'AI analyst', 'Defense intelligence', 'Investigations', 'Collection desk',
  'Verification lab', 'Coverage audit', 'Source library', 'Methodology',
  'Macro indicators', 'Trade indicators', 'Corporate intelligence',
  'Energy & resources', 'Demographics & biosecurity', 'Cyber resilience',
] as const;
type Section = (typeof sections)[number];
type DomainId = 'command'|'geopolitics'|'defense'|'macro'|'trade'|'business'|'energy'|'demographics';
type DomainTab = { label:string; section:Section; focus?:EconomicFocus };
const domains: { id:DomainId; title:string; short:string; Icon:typeof Activity; tabs:DomainTab[] }[] = [
  {id:'command',title:'Command & Situation Room',short:'Command',Icon:Activity,tabs:[
    {label:'Situation room',section:'Overview'},
    {label:'AI analyst',section:'AI analyst'},
    {label:'Collection desk',section:'Collection desk'},
    {label:'Verification lab',section:'Verification lab'},
    {label:'Coverage audit',section:'Coverage audit'},
    {label:'Source library',section:'Source library'},
    {label:'Methodology',section:'Methodology'}]},
  {id:'geopolitics',title:'Geopolitics & Intelligence',short:'Geopolitics',Icon:Globe2,tabs:[
    {label:'Country dossiers',section:'Countries'},
    {label:'World Factbook',section:'World Factbook'},
    {label:'Investigations',section:'Investigations'}]},
  {id:'defense',title:'Defense, Security & Cyber',short:'Defense',Icon:Shield,tabs:[
    {label:'Defense intelligence',section:'Defense intelligence'},
    {label:'Cyber resilience',section:'Cyber resilience'}]},
  {id:'macro',title:'Macroeconomics & Markets',short:'Markets',Icon:Layers3,tabs:[
    {label:'Economic pulse',section:'Economic intelligence',focus:'overview'},
    {label:'Growth & labor',section:'Macro indicators'},
    {label:'Markets & early warning',section:'Economic intelligence',focus:'signals'},
    {label:'Systemic risk',section:'Economic intelligence',focus:'risk'}]},
  {id:'trade',title:'Trade & Supply Chains',short:'Trade',Icon:Network,tabs:[
    {label:'Supply chains',section:'Economic intelligence',focus:'supply'},
    {label:'Product shortages',section:'Economic intelligence',focus:'shortages'},
    {label:'Trade baselines',section:'Trade indicators'}]},
  {id:'business',title:'Business, Corporate & Tech',short:'Business',Icon:Sparkles,tabs:[
    {label:'Corporate intelligence',section:'Corporate intelligence'}]},
  {id:'energy',title:'Energy, Resources & Climate',short:'Energy',Icon:Radio,tabs:[
    {label:'Energy & resources',section:'Energy & resources'}]},
  {id:'demographics',title:'Demographics & Biosecurity',short:'Demographics',Icon:BookOpen,tabs:[
    {label:'Population & climate',section:'Demographics & biosecurity'}]},
];
const focusCodes = ['RU', 'CN', 'IR', 'KP'];
const fmt = (n: number) =>
  new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(n);
const getFlag = (code: string) =>
  code.replace(/./g, c => String.fromCodePoint(127397 + c.charCodeAt(0)));
const dateFmt = (d: string) =>
  new Date(d + (d.length === 10 ? 'T12:00:00Z' : '')).toLocaleDateString(
    'en-US',
    { month: 'short', day: 'numeric', year: 'numeric' }
  );
function Anchor({
  href,
  children,
  className = '',
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
    >
      {children} <ExternalLink size={12} />
    </a>
  );
}
function MetricCard({
  label,
  value,
  sub,
  icon,
}: {
  label: string;
  value: string;
  sub: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="metric-card">
      <span className="metric-top">
        {icon}
        {label}
      </span>
      <strong>{value}</strong>
      <span className="metric-sub">{sub}</span>
    </div>
  );
}
function Badge({
  children,
  kind = 'neutral',
}: {
  children: React.ReactNode;
  kind?: string;
}) {
  return <span className={'pill pill-' + kind}>{children}</span>;
}
function MiniGlobe() {
  return (
    <svg
      className="globe-art"
      viewBox="0 0 520 440"
      fill="none"
      role="img"
      aria-label="Illustrative globe highlighting worldwide coverage"
    >
      <defs>
        <radialGradient id="sphere" cx="40%" cy="35%" r="80%">
          <stop stopColor="#18465A" />
          <stop offset=".55" stopColor="#0C2739" />
          <stop offset="1" stopColor="#08161E" />
        </radialGradient>
        <linearGradient id="stroke" x1="0" y1="0" x2="520" y2="400">
          <stop stopColor="#8DE5D6" stopOpacity=".8" />
          <stop offset="1" stopColor="#4A8796" stopOpacity=".05" />
        </linearGradient>
      </defs>
      <circle
        cx="260"
        cy="217"
        r="183"
        fill="url(#sphere)"
        stroke="url(#stroke)"
      />
      <ellipse
        cx="260"
        cy="217"
        rx="86"
        ry="183"
        stroke="#82C7CC"
        strokeOpacity=".23"
      />
      <ellipse
        cx="260"
        cy="217"
        rx="151"
        ry="183"
        stroke="#82C7CC"
        strokeOpacity=".14"
      />
      <path
        d="M80 217h360M99 135h322M101 299h318"
        stroke="#82C7CC"
        strokeOpacity=".2"
      />
      <circle
        cx="260"
        cy="217"
        r="193"
        stroke="#67DEC2"
        strokeOpacity=".17"
        strokeDasharray="2 9"
      />
      <circle cx="260" cy="217" r="206" stroke="#67DEC2" strokeOpacity=".07" />
      <path
        d="M137 116l21-9 33 3 13 14-13 21 20 18-11 18-24 2-9 21-18 1-9-24-25-5-10-29 17-18Zm64 90 29 12 17 33-12 32-14 29-21 43-15-15 7-44-19-25 5-32Zm100-91 19-15 31 4 23 18-9 17 31 6 18 26-13 21-28-7-16 17-34-16-28 14-23-25 7-28Zm-3 116 31-8 24 24-8 42-28 27-17-28-12-30Zm81 79 31-4 12 16-10 17-29 3-13-17Z"
        fill="#438B91"
        opacity=".47"
      />
      <circle cx="316" cy="167" r="6" fill="#91F0CD" />
      <circle cx="165" cy="167" r="5" fill="#D6AF73" />
      <circle cx="229" cy="226" r="5" fill="#D6AF73" />
      <circle cx="378" cy="184" r="5" fill="#D6AF73" />
      <circle cx="316" cy="167" r="18" stroke="#91F0CD" strokeOpacity=".35" />
      <circle cx="165" cy="167" r="15" stroke="#D6AF73" strokeOpacity=".25" />
      <path
        d="M321 165l56-34h71M163 169l-58-37H47M226 227l-55 52h-68"
        stroke="#B6DFD4"
        strokeOpacity=".6"
      />
      <circle cx="448" cy="131" r="3" fill="#91F0CD" />
      <circle cx="47" cy="132" r="3" fill="#D6AF73" />
      <circle cx="103" cy="279" r="3" fill="#D6AF73" />
    </svg>
  );
}
function App() {
  const [startup] = useState(()=>{
    const params=new URLSearchParams(window.location.search);
    const match=domains.find(d=>d.id===params.get('ea_domain'))||domains[0];
    const tab=match.tabs.find(t=>t.label===params.get('ea_tab'))||match.tabs[0];
    const h=params.get('ea_time');
    const level=params.get('ea_level');
    const target=params.get('ea_country');
    const geo=params.get('ea_region');
    return {domain:match.id,tab,
      horizon:(['all','24h','7d','30d'].includes(h||'')?h:'all') as Horizon,
      severity:(['all','elevated','review','monitor'].includes(level||'')?level:'all') as Severity,
      country:(target&&(target==='all'||/^[A-Z]{2}$/.test(target))?target:null),
      region:(['All regions','Africa','Americas','Asia','Europe','Oceania','Other'].includes(geo||'')?geo:'All regions')||'All regions'};
  });
  const [view, setView] = useState<Section>(startup.tab.section);
  const [domain, setDomain] = useState<DomainId>(startup.domain);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [horizon, setHorizon] = useState<Horizon>(startup.horizon);
  const [severity, setSeverity] = useState<Severity>(startup.severity);
  const [networkOpen,setNetworkOpen] = useState(false);
  const [warningFocus,setWarningFocus]=useState<'all'|'funding'|'commodities'|'gnss'>('all');
  const [economicFocus,setEconomicFocus]=useState<EconomicFocus>(startup.tab.focus||'overview');
  const [geospatialOpen,setGeospatialOpen]=useState(false);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [region, setRegion] = useState(startup.region);
  const [showTerritories, setShowTerritories] = useState(false);
  const [showAllies, setShowAllies] = useState(true);
  const [selected, setSelected] = useState<string | null>('RU');
  const [countryScope, setCountryScope] = useState<string>(()=>{if(startup.country)return startup.country;try{return window.localStorage.getItem('ea.country.scope')||'all';}catch{return 'all';}});
  useEffect(()=>{try{window.localStorage.setItem('ea.country.scope',countryScope);}catch{};if(countryScope!=='all')setSelected(countryScope);},[countryScope]);
  const [brief, setBrief] = useState<Brief | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [caseTopic, setCaseTopic] = useState('All investigations');
  const [caseSelected, setCaseSelected] = useState<string | null>(null);
  const [sourceGroup, setSourceGroup] = useState('All');
  const [mobileMenu, setMobileMenu] = useState(false);
  const [mobilePane,setMobilePane]=useState<'workspace'|'domains'|'alerts'|'briefcase'>('workspace');
  const [mobileFiltersOpen,setMobileFiltersOpen]=useState(false);
  const [quickQuery,setQuickQuery]=useState('');
  const [quickMessage,setQuickMessage]=useState('');
  const quickRef=useRef<HTMLInputElement>(null);
  const [hoveredDomain,setHoveredDomain]=useState<DomainId|null>(null);
  const [flyoutPosition,setFlyoutPosition]=useState({top:86,left:235});
  const flyoutTimeout=useRef<number|null>(null);
  const [savedViews,setSavedViews]=useState<SavedWorkspace[]>(()=>{
    try{
      const parsed:unknown=JSON.parse(window.localStorage.getItem('ea.saved.workspaces')||'[]');
      return Array.isArray(parsed)?parsed.filter(x=>x&&typeof x.id==='string'&&typeof x.title==='string'&&typeof x.domain==='string'&&typeof x.tab==='string').slice(0,20):[];
    }catch{return [];}
  });
  const [bugReportOpen, setBugReportOpen] = useState(false);
  useEffect(()=>{try{window.localStorage.setItem('ea.saved.workspaces',JSON.stringify(savedViews));}catch{}},[savedViews]);
  useEffect(()=>{
    const handler=(event:KeyboardEvent)=>{
      if(event.key==='/'&&!event.ctrlKey&&!event.metaKey&&!event.altKey&&
        !['INPUT','TEXTAREA','SELECT'].includes((event.target as HTMLElement)?.tagName)){
        event.preventDefault();quickRef.current?.focus();
      }
      if(event.key==='Escape')quickRef.current?.blur();
    };
    window.addEventListener('keydown',handler);
    return()=>window.removeEventListener('keydown',handler);
  },[]);

  const reload = () => {
    setLoadError('');
    api
      .get('/api/overview')
      .then(r => { const data = r.data as Overview; setOverview({ ...data, countries: data.countries.map(withSecurityContext) }); })
      .catch(() => setLoadError('The catalog could not be loaded. Try again.'));
  };
  useEffect(reload, []);
  useEffect(() => {
    if (!selected) {
      setBrief(null);
      return;
    }
    let active = true;
    setBrief(null);
    setBriefLoading(true);
    api
      .get('/api/brief/' + selected)
      .then(r => {
        if (active) setBrief(r.data as Brief);
      })
      .catch(() => {
        if (active)
          setBrief({
            code: selected,
            updatedAt: '',
            mode: 'unavailable',
            metrics: {},
            warning: 'The external data feed is temporarily unavailable.',
          });
      })
      .finally(() => {
        if (active) setBriefLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selected]);
  const countries = overview?.countries || [];
  const cases = overview?.cases || [];
  const sources = overview?.sources || [];
  const mainStates = countries.filter(c => c.scope === 'state-or-observer');
  // Presentation-only read. Published analyst decisions and source records are untouched.
  const intelligenceFeed=useIntelligenceFeed(countryScope,horizon,severity);
  const notAllied = mainStates.filter(c => !c.isTreatyAlly);
  const filtered = useMemo(
    () =>
      countries.filter(
        c =>
          (showTerritories || c.scope === 'state-or-observer' || c.code === countryScope) &&
          (showAllies || !c.isTreatyAlly || c.code === countryScope) &&
          (countryScope === 'all' || c.code === countryScope) &&
          (region === 'All regions' || c.region === region) &&
          (c.name.toLowerCase().includes(search.toLowerCase()) ||
            c.code.toLowerCase().includes(search.toLowerCase()))
      ),
    [countries, search, region, showTerritories, showAllies, countryScope]
  );
  const country = countries.find(c => c.code === selected);
  const topics = [
    'All investigations',
    ...Array.from(new Set(cases.map(c => c.topic))),
  ];
  // A case's country code is its foreign-country association, not the
  // location of the U.S. interests described in its impact field.
  const caseList = cases.filter(
    c =>
      (caseTopic === 'All investigations' || c.topic === caseTopic) &&
      (countryScope === 'all' ||
        c.code === countryScope ||
        (countryScope === 'US' && /\b(?:US|U\.S\.)/i.test(c.impact)))
  );
  // Always open a valid record when the current filter has results.
  // Selecting a different country/topic must not leave stale case details.
  const chosenCase =
    caseList.find(c => c.id === caseSelected) ?? caseList[0] ?? null;
  const sourceCategories = [
    'All',
    ...Array.from(new Set(sources.map(s => s.category))),
  ];
  const openGeospatial=()=>{setGeospatialOpen(true);switchView('Countries');};
  const closeFlyoutSoon=()=>{
    if(flyoutTimeout.current!==null)window.clearTimeout(flyoutTimeout.current);
    flyoutTimeout.current=window.setTimeout(()=>setHoveredDomain(null),180);
  };
  const keepFlyout=()=>{if(flyoutTimeout.current!==null)window.clearTimeout(flyoutTimeout.current);};
  const showFlyout=(id:DomainId,element:HTMLElement)=>{
    keepFlyout();
    const rect=element.getBoundingClientRect();
    setFlyoutPosition({top:Math.max(8,Math.min(rect.top,window.innerHeight-350)),left:rect.right+10});
    setHoveredDomain(id);
  };
  const currentWorkspace=()=>({
    domain,tab:activeDomain.tabs.find(t=>activeTab(t))?.label||activeDomain.tabs[0].label,
    country:countryScope,region,horizon,severity
  });
  const workspaceUrl=()=>{
    const w=currentWorkspace();
    const url=new URL(window.location.href);
    const params=new URLSearchParams(url.search);
    params.set('ea_domain',w.domain);params.set('ea_tab',w.tab);
    params.set('ea_country',w.country);params.set('ea_region',w.region);
    params.set('ea_time',w.horizon);params.set('ea_level',w.severity);
    url.search=params.toString();url.hash='';
    return url.toString();
  };
  const saveCurrentWorkspace=()=>{
    const w=currentWorkspace();
    const stamp=new Date().toISOString();
    const item:SavedWorkspace={...w,id:stamp,title:activeDomain.title+' / '+w.tab,savedAt:stamp};
    setSavedViews(prev=>[item,...prev].slice(0,20));
    setQuickMessage('Workspace saved in this browser.');
  };
  const openSaved=(item:SavedWorkspace)=>{
    const d=domains.find(x=>x.id===item.domain);
    const t=d?.tabs.find(x=>x.label===item.tab);
    if(!d||!t){setQuickMessage('This saved workspace no longer matches a domain.');return;}
    selectDomainTab(d.id,t);
    if(item.country==='all'||/^[A-Z]{2}$/.test(item.country))setCountryScope(item.country);
    if(['All regions','Africa','Americas','Asia','Europe','Oceania','Other'].includes(item.region))setRegion(item.region);
    if(['all','24h','7d','30d'].includes(item.horizon))setHorizon(item.horizon as Horizon);
    if(['all','elevated','review','monitor'].includes(item.severity))setSeverity(item.severity as Severity);
  };
  const shareWorkspace=async()=>{
    const url=workspaceUrl();
    try{
      if(typeof navigator.share==='function')await navigator.share({title:'Eastern Axis intelligence workspace',url});
      else if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(url);setQuickMessage('Handoff URL copied. Open it on mobile to restore these filters.');}
      else setQuickMessage('Handoff URL: '+url);
    }catch(e){if((e as Error)?.name!=='AbortError')setQuickMessage('Handoff URL: '+url);}
  };
  const runCommand=(query:string)=>{
    const q=query.trim();if(!q)return;
    const countryCommand=q.match(/^\\/?(?:country|c)\\s+([a-z]{2})$/i);
    if(countryCommand){
      const match=mainStates.find(c=>c.code.toLowerCase()===countryCommand[1].toLowerCase());
      if(match){openCountry(match.code);setQuickMessage('Opened '+match.name+' country dossier.');}
      else setQuickMessage('No indexed country matches that ISO code.');
      setQuickQuery('');return;
    }
    if(/^\\/?(?:vessel|imo)\\b/i.test(q)){setQuickMessage('Vessel search requires a verified AIS provider. No vessel position has been inferred.');return;}
    const clean=q.replace(/^\\//,'').toLowerCase();
    const match=domains.flatMap(d=>d.tabs.map(t=>({d,t})))
      .find(({d,t})=>t.label.toLowerCase()===clean||d.title.toLowerCase()===clean||d.short.toLowerCase()===clean);
    if(match){selectDomainTab(match.d.id,match.t);setQuickMessage('Opened '+match.d.title+' / '+match.t.label);}
    else if(clean==='alerts'){setMobilePane('alerts');setQuickMessage('Open the mobile Alert inbox, or inspect Command analyst signals.');}
    else setQuickMessage('No indexed command. Try /country CN, /alerts, /supply chains, or /systemic risk.');
    setQuickQuery('');
  };
  const openCountry = (code: string) => {
    setCountryScope(code);
    setSelected(code);
    setView('Countries');
    setDomain('geopolitics');
    setMobilePane('workspace');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const navigateFromSignal = (target:'Early warning'|'Supply chain'|'Risk watch'|'Defense intelligence'|'Countries', focus?:'funding'|'commodities'|'gnss')=>{
    if(target==='Early warning'||target==='Supply chain'||target==='Risk watch'){
      switchView('Economic intelligence');
      setEconomicFocus(target==='Early warning'?'signals':target==='Supply chain'?'supply':'risk');
      setDomain(target==='Supply chain'?'trade':'macro');
      if(target==='Early warning')setWarningFocus(focus||'all');
    }else switchView(target);
  };
  const switchView = (next: Section) => {
    if(next==='Economic intelligence')setEconomicFocus('overview');
    setView(next);
    const match=domains.find(d=>d.tabs.some(t=>t.section===next));
    if(match)setDomain(match.id);
    setMobileMenu(false);
    setMobilePane('workspace');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const selectDomainTab = (id:DomainId, tab:DomainTab) => {
    setDomain(id);
    if(tab.section==='Economic intelligence')setEconomicFocus(tab.focus||'overview');
    setView(tab.section);
    setMobileMenu(false);
    setMobilePane('workspace');
    setHoveredDomain(null);
    window.scrollTo({top:0,behavior:'smooth'});
  };
  const activeDomain=domains.find(item=>item.id===domain)!;
  const activeTab=(tab:DomainTab)=>view===tab.section && (tab.section!=='Economic intelligence'||tab.focus===economicFocus);
  const onEconomicFocusChange=(next:EconomicFocus)=>{
    setEconomicFocus(next);
    if(next==='supply'||next==='shortages')setDomain('trade');
    else if(['overview','signals','systems','risk'].includes(next))setDomain('macro');
  };

  return (
    <GlobalFiltersContext.Provider value={{horizon,severity}}>
    <div className={"shell ea-control-room" + (sidebarCollapsed ? " ea-sidebar-collapsed" : "") + (mobilePane!=='workspace'?" ea-mobile-pane-active":"")}>
      <aside id="ea-primary-navigation" className={'sidebar ' + (mobileMenu ? 'sidebar-open' : '')}>
        <div className="brand">
          <span className="brand-mark">
            <Globe2 size={21} />
          </span>
          <div>
            <strong>
              EASTERN <em>AXIS</em>
            </strong>
            <small>OPEN-SOURCE INTELLIGENCE</small>
          </div>
        </div>
        <button type="button" className="sidebar-close" onClick={() => setMobileMenu(false)} aria-label="Close navigation"><X size={20} /></button>
        <div className="sidebar-rule" />
        <div className="nav-label">INTELLIGENCE DOMAINS</div>
        <div className="ea-menu-support">
          <button type="button" className="ea-report-bug"
            aria-haspopup="dialog" aria-expanded={bugReportOpen}
            onClick={() => { setMobileMenu(false); setBugReportOpen(true); }}>
            <Bug size={17} />
            <span>Report a bug</span>
            <small>No login</small>
          </button>
        </div>
        <nav aria-label="Main navigation">
          {domains.map(item=><div className="ea-nav-domain" key={item.id}>
            <button type="button" className={'nav-item '+(domain===item.id?'active':'')}
              aria-current={domain===item.id?'page':undefined} title={item.title}
              onMouseEnter={e=>showFlyout(item.id,e.currentTarget)}
              onFocus={e=>showFlyout(item.id,e.currentTarget)}
              onMouseLeave={closeFlyoutSoon}
              onClick={()=>selectDomainTab(item.id,item.tabs[0])}>
              <item.Icon size={17}/><span>{item.title}</span>
              {item.id==='command'&&intelligenceFeed.promoted.length>0&&<i className="ea-domain-anomaly" title="Verified elevated signal" aria-label="Verified elevated signal"/>}
            </button>
          </div>)}
        </nav>
        <div className="sidebar-bottom">
          <span className="tiny-live">
            <span className="live-dot" /> PUBLIC RECORDS / OPEN DATA
          </span>
          <p>
            Evidence, not conjecture.
            <br />
            Context, not blanket accusations.
          </p>
          <div className="bottom-rule" />
          <span className="sidebar-foot">EASTERN AXIS / RESEARCH DESK</span>
        </div>
      </aside>
      {hoveredDomain&&<nav className="ea-domain-flyout" aria-label={domains.find(d=>d.id===hoveredDomain)?.title+' quick tabs'}
        style={{top:flyoutPosition.top,left:flyoutPosition.left}}
        onMouseEnter={keepFlyout} onMouseLeave={()=>setHoveredDomain(null)} onKeyDown={e=>{if(e.key==='Escape')setHoveredDomain(null);}}>
        <strong>{domains.find(d=>d.id===hoveredDomain)?.title}</strong>
        {domains.find(d=>d.id===hoveredDomain)?.tabs.map(tab=><button type="button" key={tab.label}
          onClick={()=>selectDomainTab(hoveredDomain,tab)}>{tab.label}<ArrowUpRight size={12}/></button>)}
      </nav>}
      {mobileMenu && (
        <button
          className="menu-overlay"
          aria-label="Close menu"
          onClick={() => setMobileMenu(false)}
        />
      )}
      <div className="main">
        <header className="topbar">
          <div className="top-left">
            <button
              className="menu-btn"
              type="button"
              onClick={() => { if(window.matchMedia('(max-width: 980px)').matches)setMobilePane('domains'); else setSidebarCollapsed(v=>!v); }}
              aria-label={mobileMenu ? 'Close navigation' : 'Toggle navigation'}
              aria-controls="ea-primary-navigation"
              aria-expanded={mobileMenu}
            >
              <Menu size={21} />
            </button>
            <div className="breadcrumb">
              <span className="breadcrumb-prefix">INTELLIGENCE CONTROL ROOM</span> <ChevronRight size={13} />{' '}
              <strong>{activeDomain.title.toUpperCase()}</strong>
            </div>
          </div>
          <form className="ea-quick-search" role="search" onSubmit={e=>{e.preventDefault();runCommand(quickQuery);}}>
            <Command size={15}/><input ref={quickRef} aria-label="Global intelligence command search"
              placeholder="Search commands · /country CN · /supply chains" value={quickQuery}
              onChange={e=>setQuickQuery(e.target.value)}/><kbd>/</kbd>
            <button type="submit" aria-label="Execute intelligence command"><ArrowRight size={15}/></button>
          </form>
          <div className={'ea-global-filters'+(mobileFiltersOpen?' open':'')}>
          <div className="header-right">
            <button type="button" className="ea-close-filters" onClick={()=>setMobileFiltersOpen(false)} aria-label="Close global filters"><X size={18}/> Close filters</button>
            <label className="ea-global-filter ea-region-filter"><span>REGION</span>
              <select aria-label="Global region filter" value={region} onChange={event=>{const next=event.target.value;setRegion(next);if(countryScope!=='all' && next!=='All regions' && countries.find(c=>c.code===countryScope)?.region!==next)setCountryScope('all');}}>
                {['All regions','Africa','Americas','Asia','Europe','Oceania','Other'].map(value=><option key={value}>{value}</option>)}
              </select>
            </label>
            <CountryPicker countries={region==='All regions'?mainStates:mainStates.filter(c=>c.region===region)} value={countryScope} onChange={setCountryScope} />
            <label className="ea-global-filter"><span>TIME</span>
              <select aria-label="Time horizon filter" value={horizon} onChange={event=>setHorizon(event.target.value as Horizon)}>
                <option value="all">All dates</option><option value="24h">24 hours</option><option value="7d">7 days</option><option value="30d">30 days</option>
              </select>
            </label>
            <label className="ea-global-filter"><span>SEVERITY</span>
              <select aria-label="Alert severity filter" value={severity} onChange={event=>setSeverity(event.target.value as Severity)}>
                <option value="all">All signals</option><option value="elevated">Elevated</option><option value="review">Needs review</option><option value="monitor">Monitored</option>
              </select>
            </label>
          </div>
          </div>
        </header>
        <div className="ea-mobile-filter-pills" role="group" aria-label="Active intelligence filters">
          {[
            ['Region',region],['Country',mainStates.find(c=>c.code===countryScope)?.name||'Worldwide'],
            ['Time',horizon==='all'?'All dates':horizon],['Threat',severity==='all'?'All signals':severity]
          ].map(([label,value])=><button key={label} type="button" onClick={()=>setMobileFiltersOpen(true)} aria-label={'Edit '+label+' filter'}>
            <span>{label}</span><strong>{value}</strong><ChevronDown size={12}/></button>)}
        </div>
        {mobileFiltersOpen&&<button type="button" className="ea-filter-backdrop" aria-label="Close filter panel" onClick={()=>setMobileFiltersOpen(false)}/>}
        {quickMessage&&<div className="ea-command-status" role="status">{quickMessage}<button type="button" onClick={()=>setQuickMessage('')} aria-label="Dismiss command message"><X size={14}/></button></div>}
        <nav className="ea-domain-tabs" aria-label={activeDomain.title+' workspace tabs'}>
          {activeDomain.tabs.map(tab=><button type="button" key={tab.label}
            className={activeTab(tab)?'active':''} aria-current={activeTab(tab)?'page':undefined}
            onClick={()=>selectDomainTab(domain,tab)}>{tab.label}</button>)}
        </nav>
        <div className="ea-global-filter-note">Filters preserve original records. Time and severity apply to dated analyst signals; structural reference figures retain their published observation dates.</div>
        <div className="ea-workstation-row">
        <main className="content">
          <div className="ea-mobile-panel">
            {mobilePane==='domains'&&<MobileDomains items={domains.map(d=>({id:d.id,title:d.title,Icon:d.Icon}))}
              onSelect={id=>{const d=domains.find(x=>x.id===id);if(d)selectDomainTab(d.id,d.tabs[0]);}}/>}
            {mobilePane==='alerts'&&<MobileAlerts feed={intelligenceFeed}/>}
            {mobilePane==='briefcase'&&<MobileBriefcase saved={savedViews} onOpen={openSaved}
              onRemove={id=>setSavedViews(v=>v.filter(x=>x.id!==id))}
              onSave={saveCurrentWorkspace} onShare={shareWorkspace}/>}
            {mobilePane==='briefcase'&&<button type="button" className="ea-mobile-report-bug" onClick={()=>setBugReportOpen(true)}><Bug size={15}/> Report a bug · no login required</button>}
          </div>
          <div className="ea-original-workspace">
          <div className="ea-handoff-actions"><button type="button" onClick={saveCurrentWorkspace} title="Save filters and workspace in this browser"><Bookmark size={14}/> Save view</button>
            <button type="button" onClick={shareWorkspace} title="Copy or share a link that restores this workspace"><Copy size={14}/> Send to mobile</button></div>
          {loadError && (
            <div className="error-panel">
              <CircleAlert size={17} />
              {loadError}
              <button onClick={reload}>Retry</button>
            </div>
          )}
          {!overview && !loadError && (
            <div className="initial-loader">
              <LoaderCircle className="spinning" size={30} /> Loading the
              evidence catalog…
            </div>
          )}
          {overview && view === 'Overview' && (
            <CommandCenter overview={overview} openCountry={openCountry} activeCountry={countryScope} onCountrySelected={setCountryScope}
              openCases={id=>{const file=cases.find(c=>c.id===id);if(file)setCountryScope(file.code);setCaseSelected(id||null);switchView('Investigations');}}
              openDesk={()=>switchView('Collection desk')}
              openSources={()=>switchView('Source library')}
              openMethod={()=>switchView('Methodology')} onNavigate={navigateFromSignal} />
          )}
          {overview && view === 'Economic intelligence' && <EconomicIntelligence
            countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name}
            cases={cases} initialFocus={economicFocus} initialMeasurementFilter={warningFocus}
            onCountryMap={openGeospatial} onDefense={()=>switchView('Defense intelligence')}
            hideNavigation onFocusChange={onEconomicFocusChange} />}
          {overview && view === 'AI analyst' && <AgentDesk countryCode={countryScope} />}
          {overview && view === 'Coverage audit' && <><ConnectedSources/><OperationalAssurance/><GlobalSystems mode="coverage" countryCode={countryScope} cases={cases} /></>}
          {overview && view === 'Collection desk' && <IntakeDesk countryCode={countryScope} />}{overview && view === 'Verification lab' && <EvidenceWorkbench countryCode={countryScope} />}
          {overview && view === 'Defense intelligence' && <DefenseIntel mode="global" code={countryScope==='all'?undefined:countryScope} />}
          {overview && view === 'Cyber resilience' && <ResilienceWatch/>}
          {overview && view === 'Macro indicators' && <GlobalSystems mode="systems" groupFilter="Economy" countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} cases={cases}/>}
          {overview && view === 'Trade indicators' && <GlobalSystems mode="systems" groupFilter="Trade & finance" countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} cases={cases}/>}
          {overview && view === 'Corporate intelligence' && <FinancialTransmission/>}
          {overview && view === 'Energy & resources' && <GlobalSystems mode="systems" groupFilter="Energy & resources" countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} cases={cases}/>}
          {overview && view === 'Demographics & biosecurity' && <GlobalSystems mode="systems" groupFilter="People & climate" countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} cases={cases}/>}
          {overview && view === 'World Factbook' && <Factbook activeCountry={countryScope} onCountryChange={setCountryScope} />}
          {overview && view === 'Countries' && (
            <>

              <div className="eyebrow">
                <span className="eyebrow-line" /> RESEARCH DATABASE / COUNTRIES
              </div>
              <div className="page-heading">
                <div>
                  <h1>
                    Country intelligence<span className="period">.</span>
                  </h1>
                  <p>
                    Explore the global directory, then open a country to examine
                    original-source evidence and World Bank indicators. This directory includes countries and treaty allies by default. You can narrow the list; the selected country always remains visible. The historical World Factbook also includes territories and geographic profiles, so totals differ.
                  </p>
                </div>
                <Badge kind="green">
                  {filtered.length} jurisdictions shown
                </Badge>
              </div>
              <section className="ea-country-network-hub" aria-label="Integrated country relationship intelligence">
                <div className="ea-country-network-toolbar">
                  <div className="ea-country-network-heading">
                    <span className="ea-country-network-icon"><Network size={20} /></span>
                    <div>
                      <strong>Relationships &amp; networks</strong>
                      <span>Explore sourced treaties, security partnerships, international blocs and separately reported operations for {countryScope==='all'?'a global spotlight':(overview.countries.find(c=>c.code===countryScope)?.name||countryScope)}.</span>
                    </div>
                  </div>
                  <button type="button" aria-expanded={networkOpen} aria-controls="ea-country-network-graph" onClick={()=>setNetworkOpen(v=>!v)}>
                    {networkOpen?'Hide relationships':'Explore relationships'} <ChevronDown size={16} className={networkOpen?'ea-network-chevron-open':''}/>
                  </button>
                </div>
                {networkOpen&&<div id="ea-country-network-graph" className="ea-country-network-graph">
                  <Connections embedded code={countryScope} countries={overview.countries.filter(c=>c.scope==='state-or-observer')} cases={cases} onSelect={code=>{setCountryScope(code);setSelected(code);}} />
                </div>}
              </section>
              <div className="ea-geospatial-toggle"><div><strong>Geospatial country intelligence</strong><span>Explore geopolitical layers, global hazards and sourced map locations</span></div><button type="button" aria-expanded={geospatialOpen} aria-controls="ea-geospatial-map" onClick={()=>setGeospatialOpen(v=>!v)}>{geospatialOpen?'Hide map':'Open map'} <ChevronDown size={15}/></button></div>
              {geospatialOpen&&<div id="ea-geospatial-map" className="ea-country-geospatial"><CommandCenter mode="geospatial" overview={overview} openCountry={openCountry} activeCountry={countryScope} onCountrySelected={setCountryScope}
                openCases={id=>{const file=cases.find(c=>c.id===id);if(file)setCountryScope(file.code);setCaseSelected(id||null);switchView('Investigations');}}
                openDesk={()=>switchView('Collection desk')} openSources={()=>switchView('Source library')}
                openMethod={()=>switchView('Methodology')} onNavigate={navigateFromSignal} /></div>}
              <div className="country-layout">
                <div className="country-directory">
                  <div className="filters">
                    <div className="search-holder">
                      <Search size={18} />
                      <input
                        aria-label="Search countries"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        placeholder="Search country or ISO code…"
                      />
                    </div>

                  </div>
                  <div className="checks">
                    <label>
                      <input
                        type="checkbox"
                        checked={showAllies}
                        onChange={e => setShowAllies(e.target.checked)}
                      />{' '}
                      Include U.S. primary treaty allies
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={showTerritories}
                        onChange={e => setShowTerritories(e.target.checked)}
                      />{' '}
                      Include territories / separately administered
                      jurisdictions
                    </label>
                  </div>
                  <div className="table-top">
                    <span>COUNTRY / JURISDICTION</span>
                    <span>REGION</span>
                    <span>FILES</span>
                  </div>
                  <div className="country-list">
                    {filtered.length === 0 ? (
                      <div className="empty-state">
                        No countries match those filters. Try another region or
                        search.
                      </div>
                    ) : (
                      filtered.map(c => (
                        <button
                          className={
                            'country-row ' +
                            (selected === c.code ? 'chosen' : '')
                          }
                          key={c.code}
                          onClick={() => { setSelected(c.code); setCountryScope(c.code); }}
                        >
                          <span className="country-name">
                            <span className="flag">{getFlag(c.code)}</span>
                            <span>
                              <strong>{c.name}</strong>
                              <small>
                                {c.code}
                                {c.isMNNA ? ' · MNNA' : ''}
                                {c.scope !== 'state-or-observer'
                                  ? ' · special status'
                                  : ''}
                              </small>
                            </span>
                          </span>
                          <span className="region-text">{c.region}</span>
                          <span className="file-count">
                            {c.caseCount || '—'} <ChevronRight size={14} />
                          </span>
                        </button>
                      ))
                    )}
                  </div>
                  <div className="list-footer">
                    Scope uses ISO 3166 jurisdiction codes; default covers
                    states and UN observers.{' '}
                    <button onClick={() => switchView('Methodology')}>
                      Classification details <ArrowRight size={13} />
                    </button>
                  </div>
                </div>
                <aside className="country-brief">
                  {country ? (
                    <>
                      <div className="brief-top">
                        <span>COUNTRY BRIEF / {country.code}</span>
                        <Badge kind={country.isTreatyAlly ? 'gold' : 'green'}>
                          {country.isTreatyAlly
                            ? 'PRIMARY TREATY ALLY'
                            : 'IN RESEARCH SCOPE'}
                        </Badge>
                      </div>
                      <div className="brief-flag">{getFlag(country.code)}</div>
                      <h2>{country.name}</h2>
                      <p className="brief-region">
                        <MapPin size={14} />
                        {country.region} · {country.code}
                      </p>
                      <div className="brief-line" />
                      <div className="brief-relationship">
                        <span>DEFENSE TREATIES &amp; SECURITY TIES</span>
                        <strong>{country.relationship}</strong>
                         {country.securityNote && <small>{country.securityNote}</small>}
                         {country.usRelationship && <small><b>U.S. relationship:</b> {country.usRelationship}</small>}
                         {!!country.securitySources?.length && <div className="ea-treaty-sources">{country.securitySources.map(source => <Anchor key={source.url} href={source.url}>{source.label}</Anchor>)}</div>}
                        {country.isMNNA && (
                          <small>
                            Major non-NATO ally designation is not itself a
                            mutual-defense guarantee.
                          </small>
                        )}
                      </div>
                      <div className="brief-line" />
                      <div className="brief-section-title">
                        LATEST REPORTED INDICATORS <small>WORLD BANK</small>
                      </div>
                      {briefLoading ? (
                        <div className="brief-loading">
                          <LoaderCircle size={18} className="spinning" />{' '}
                          Checking free public-data feed…
                        </div>
                      ) : (
                        <div className="indicator-grid">
                          {(
                            [
                              ['gdp', 'GDP (US$)'],
                              ['population', 'Population'],
                              ['lifeExpectancy', 'Life expectancy'],
                            ] as const
                          ).map(([key, label]) => {
                            const m = brief?.metrics?.[key];
                            let value = '—';
                            if (m) {
                              value =
                                key === 'gdp'
                                  ? fmt(m.value)
                                  : key === 'population'
                                    ? fmt(m.value)
                                    : m.value.toFixed(1) + ' yrs';
                            }
                            return (
                              <div key={key} className="indicator">
                                <span>{label}</span>
                                <strong>{value}</strong>
                                <small>
                                  {m ? 'Reported ' + m.year : 'Not available'}
                                </small>
                              </div>
                            );
                          })}
                        </div>
                      )}
                      {brief?.warning && (
                        <div className="feed-warning">
                          <CircleAlert size={14} />
                          {brief.warning}
                        </div>
                      )}
                      <div className="data-note">
                        Data timestamps describe the reporting year, not
                        necessarily today. No missing values are estimated.
                      </div>
                      <div id="ea-country-factbook"><CountryFactbook key={country.code} code={country.code} countryName={country.name} /></div>
                      <div className="brief-line" />
                      <div className="brief-section-title">
                        CASE FILES <small>{country.caseCount} CURATED</small>
                      </div>
                      {cases.filter(c => c.code === country.code).length ? (
                        cases
                          .filter(c => c.code === country.code)
                          .map(c => (
                            <button
                              className="brief-case"
                              key={c.id}
                              onClick={() => {
                                setCaseSelected(c.id);
                                switchView('Investigations');
                              }}
                            >
                              <FileSearch size={17} />
                              <span>
                                {c.title}
                                <small>{dateFmt(c.date)}</small>
                              </span>
                              <ArrowUpRight size={14} />
                            </button>
                          ))
                      ) : (
                        <div className="no-case">
                          No curated case in this starter library. This is not
                          evidence of no activity.
                        </div>
                      )}
                      <button type="button" onClick={() => document.getElementById('ea-country-factbook')?.scrollIntoView({ behavior: 'smooth', block: 'start' })} style={{width:'100%',display:'flex',alignItems:'center',justifyContent:'space-between',padding:15,margin:'15px 0',background:'#174139',border:'1px solid #4f907f',color:'#b6f4da',borderRadius:8,fontWeight:700}}>View all World Factbook fields below <ArrowRight size={17}/></button>
                      <DefenseIntel key={country.code} code={country.code} countryName={country.name} />
                      <div className="brief-links">
                        <Anchor
                          href={
                            'https://api.worldbank.org/v2/country/' +
                            country.code +
                            '?format=json'
                          }
                        >
                          World Bank record
                        </Anchor>
                        <Anchor href="https://ofac.treasury.gov/sanctions-list-service">
                          OFAC records
                        </Anchor>
                        <Anchor href="https://www.justice.gov/nsd">
                          DOJ national security
                        </Anchor>
                      </div>
                    </>
                  ) : (
                    <div>Select a country</div>
                  )}
                </aside>
              </div>
            </>
          )}
          {overview && view === 'Investigations' && (
            <>
              <div className="eyebrow">
                <span className="eyebrow-line" /> EVIDENCE REVIEW /
                INVESTIGATIONS
              </div>
              <div className="page-heading">
                <div>
                  <h1>
                    Follow the evidence<span className="period">.</span>
                  </h1>
                  <p>
                    Primary-source case files. Dates show the originating public
                    record, not a claim of ongoing prosecution.
                  </p>
                </div>
                <Badge kind="gold">DOJ-SOURCED EXAMPLES</Badge>
              </div>
              <div className="investigation-intro">
                <ShieldAlert size={21} />
                <p>
                  <strong>Procedural guardrail.</strong> Charges and affidavits
                  describe allegations unless proven. A seizure or enforcement
                  action is not automatically a conviction; subjects and
                  nationalities do not establish state direction by themselves.
                </p>
              </div>
              <div className="topic-chips">
                {topics.map(topic => (
                  <button
                    className={
                      'chip ' + (caseTopic === topic ? 'selected' : '')
                    }
                    key={topic}
                    onClick={() => {
                      setCaseTopic(topic);
                      setCaseSelected(null);
                    }}
                  >
                    {topic}
                  </button>
                ))}
              </div>
              <div className="investigation-summary" role="status">
                <strong>{caseList.length} sourced {caseList.length === 1 ? 'investigation' : 'investigations'}</strong>
                <span>
                  {countryScope === 'US'
                    ? 'U.S. impact view · flags show the foreign country associated with each case, not proven government responsibility.'
                    : 'Country tags describe associations in public records, not proof of state direction.'}
                </span>
              </div>
              <div className={'investigations-layout' + (caseList.length === 0 ? ' investigations-empty' : '')}>
                <div className="case-rows" id="ea-investigation-list">
                  {caseList.length === 0 ? (
                    <div className="case-empty" role="status">
                      <FileSearch size={25} />
                      <h3>No sourced investigations match this selection</h3>
                      <p>The current curated case library has no matching record. This is a coverage gap, not evidence that nothing happened.</p>
                      <button type="button" className="case-reset" onClick={() => {
                        setCountryScope('all');
                        setCaseTopic('All investigations');
                        setCaseSelected(null);
                      }}>View all investigations</button>
                    </div>
                  ) : caseList.map(c => (
                    <button
                      key={c.id}
                      className={
                        'case-card ' +
                        (chosenCase?.id === c.id ? 'case-selected' : '')
                      }
                      aria-pressed={chosenCase?.id === c.id}
                      onClick={() => {
                        setCaseSelected(c.id);
                        if (window.matchMedia('(max-width: 980px)').matches) {
                          document.getElementById('ea-investigation-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                      }}
                    >
                      <div className="case-top">
                        <span>
                          {getFlag(c.code)}{' '}
                          {countries
                            .find(x => x.code === c.code)
                            ?.name.toUpperCase()}
                        </span>
                        <span>{dateFmt(c.date)}</span>
                      </div>
                      <h3>{c.title}</h3>
                      <p>{c.summary}</p>
                      <div className="case-footer">
                        <Badge>{c.topic}</Badge>
                        <span>
                          OPEN CASE <ArrowUpRight size={15} />
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
                <aside id="ea-investigation-detail" className={'evidence-panel' + (!chosenCase ? ' evidence-panel-hidden' : '')}>
                  {chosenCase ? (
                    <>
                      <button type="button" className="case-back" onClick={() =>
                        document.getElementById('ea-investigation-list')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                      }>← Back to investigations</button>
                      <div className="eyebrow smaller">
                        ORIGINAL CASE RECORD
                      </div>
                      <h3>{chosenCase.title}</h3>
                      <div className="evidence-line">
                        <span>COUNTRY</span>
                        <strong>
                          {
                            countries.find(c => c.code === chosenCase.code)
                              ?.name
                          }
                        </strong>
                      </div>
                      <div className="evidence-line">
                        <span>FILED / ANNOUNCED</span>
                        <strong>{dateFmt(chosenCase.date)}</strong>
                      </div>
                      <div className="evidence-line">
                        <span>RECORD STATUS</span>
                        <strong>{chosenCase.status}</strong>
                      </div>
                      <div className="evidence-line">
                        <span>EVIDENCE STANDARD</span>
                        <strong>{chosenCase.level}</strong>
                      </div>
                      <div className="evidence-line">
                        <span>U.S. RELEVANCE</span>
                        <strong>{chosenCase.impact}</strong>
                      </div>
                      <div className="source-callout">
                        <CheckCircle2 size={19} />
                        <div>
                          <strong>Primary-source record</strong>
                          <span>{chosenCase.agency}</span>
                        </div>
                      </div>
                      <Anchor
                        className="evidence-button"
                        href={chosenCase.source}
                      >
                        Read original DOJ release
                      </Anchor>
                      <p className="evidence-note">
                        This source may describe an earlier procedural stage.
                        Confirm subsequent judgments and appeals independently
                        before claiming a final outcome.
                      </p>
                    </>
                  ) : (
                    <div className="evidence-empty">
                      <FileSearch size={29} />
                      <h3>Select an investigation</h3>
                      <p>
                        Review the claim, its procedural status, the U.S. impact
                        and the original government record.
                      </p>
                      <div className="chain-diagram">
                        <span>COUNTRY</span>
                        <span>PUBLIC ACTION</span>
                        <span>ORIGINAL SOURCE</span>
                      </div>
                    </div>
                  )}
                </aside>
              </div>
            </>
          )}
          {overview && view === 'Source library' && (
            <>
              <div className="eyebrow">
                <span className="eyebrow-line" /> COLLECTION ENGINE / SOURCE
                REGISTRY
              </div>
              <div className="page-heading">
                <div>
                  <h1>
                    Sources, not secrets<span className="period">.</span>
                  </h1>
                  <p>
                    Free-first infrastructure. Each source says what it
                    contributes and whether the data is currently connected.
                  </p>
                </div>
                <Badge kind="green">{sources.length} SOURCES</Badge>
              </div>
              <div className="source-summary">
                <div>
                  <span className="status-dot teal" />
                  <strong>Scheduled intake</strong>
                  <small>DOJ, OFAC SDN, FARA and CISA · check health</small>
                </div>
                <div>
                  <span className="status-dot gold" />
                  <strong>On-demand data</strong>
                  <small>World Bank country indicators</small>
                </div>
                <div>
                  <span className="status-dot gray" />
                  <strong>Review & discovery</strong>
                  <small>Human-reviewed case files and research links</small>
                </div>
              </div>
              <div className="topic-chips">
                {sourceCategories.map(g => (
                  <button
                    className={'chip ' + (sourceGroup === g ? 'selected' : '')}
                    key={g}
                    onClick={() => setSourceGroup(g)}
                  >
                    {g}
                  </button>
                ))}
              </div>
              <div className="source-grid">
                {sources
                  .filter(
                    s => sourceGroup === 'All' || s.category === sourceGroup
                  )
                  .map(s => (
                    <article className="source-card" key={s.id}>
                      <div className="source-head">
                        <span>{s.category.toUpperCase()}</span>
                        <Badge
                          kind={
                            s.mode === 'On-demand API'
                              ? 'green'
                              : s.mode.includes('Linked') ||
                                  s.mode.includes('Not yet')
                                ? 'neutral'
                                : 'gold'
                          }
                        >
                          {s.mode}
                        </Badge>
                      </div>
                      <h3>{s.name}</h3>
                      <p>{s.description}</p>
                      <div className="source-end">
                        <span>{s.cost}</span>
                        <Anchor href={s.url}>Open source</Anchor>
                      </div>
                    </article>
                  ))}
              </div>
              <details className="source-index-disclosure" style={{border:'1px solid #35565c',borderRadius:10,background:'#102a34',margin:'18px 0',overflow:'hidden'}}>
                <summary style={{cursor:'pointer',padding:'16px 19px',fontWeight:750,color:'#c4e8db'}}>Country-linked source inventory · UK / Canadian sanctions snapshots</summary>
                <p style={{margin:'0 18px',fontSize:12,color:'#99b9b9',lineHeight:1.6}}>Reference and coverage records are kept here, separate from the Networks relationship graph. Selecting a country filters legal regimes, not the nationality of listed entities.</p>
                <CountrySourceIndex code={countryScope} countries={overview.countries.filter(c=>c.scope==='state-or-observer')} cases={cases} onSelect={setCountryScope} />
              </details>
              <div className="registry-note">
                <CircleAlert size={18} />
                <p>
                  <strong>
                    OSINT Framework is a research directory, not an ingestion
                    endpoint.
                  </strong>{' '}
                  Tool entries may require payment or registration. The platform
                  only labels a feed automated when data collection is actually
                  configured.
                </p>
              </div>
            </>
          )}
          {overview && view === 'Methodology' && (
            <>
              <div className="eyebrow">
                <span className="eyebrow-line" /> TRANSPARENCY / METHODOLOGY
              </div>
              <div className="page-heading">
                <div>
                  <h1>
                    How we know<span className="period">.</span>
                  </h1>
                  <p>
                    Evidence is only useful when the reader can test it. Every
                    important distinction is explicit.
                  </p>
                </div>
              </div>
              <div className="method-hero">
                <div>
                  <span className="eyebrow smaller">
                    OUR OPERATING PRINCIPLE
                  </span>
                  <h2>
                    Show the record.
                    <br />
                    <em>Show the limits.</em>
                  </h2>
                </div>
                <Shield size={71} />
              </div>
              <div className="method-grid">
                {[
                  [
                    '01',
                    'Scope is a definition, not a verdict',
                    'Default scope: 195 UN member and observer states, excluding 32 NATO treaty members (including the U.S.) and five other primary Indo-Pacific treaty allies. Rio Treaty and other treaty commitments require a separate classification review. Territories and Taiwan can be browsed separately.',
                  ],
                  [
                    '02',
                    'Separate relationships from allegations',
                    'NATO membership, defense-treaty ties and major non-NATO ally designation are different facts. Lack of an alliance is not evidence of hostility, spying or unlawful conduct.',
                  ],
                  [
                    '03',
                    'Preserve procedural status',
                    'Indictment, plea, conviction, sanction, civil forfeiture, affidavit and intelligence assessment should never be collapsed into the word proven. Our starter case records quote the status as of the original publication.',
                  ],
                  [
                    '04',
                    'Use the original record',
                    'Official government documents are used as primary evidence for state actions and court cases. Media articles may suggest leads; they do not automatically satisfy the publication threshold.',
                  ],
                  [
                    '05',
                    'Show collection completeness',
                    'World Bank indicators are requested on demand. DOJ, OFAC SDN, FARA and CISA official-source intake runs on daily schedules; see Collection desk for each source result. OFAC program tags are not locations or government attributions; aliases and non-SDN lists remain future work. Automatic intake is distinct from reviewed investigations.',
                  ],
                  [
                    '06',
                    'Correct without erasing history',
                    'As the system expands, every assertion should be versioned with its source, date, jurisdiction, evidence status, correction history and latest verification.',
                  ],
                ].map(([n, title, copy]) => (
                  <div className="method-card" key={n}>
                    <span>{n}</span>
                    <h3>{title}</h3>
                    <p>{copy}</p>
                  </div>
                ))}
              </div>
              <div className="method-links">
                <strong>Classification references</strong>
                {overview.classificationSources.map(u => (
                  <Anchor key={u} href={u}>
                    {u.includes('nato.int')
                      ? 'NATO official membership'
                      : 'Defense Security Cooperation Agency'}
                  </Anchor>
                ))}
                <Anchor href="https://www.oas.org/en/sla/dil/inter_american_treaties_A-41_reciprocal_assistance.asp">
                  Rio Treaty / OAS
                </Anchor>
              </div>
            </>
          )}
          </div>
        </main>
        {overview&&<ContextRail feed={intelligenceFeed} domain={activeDomain.title} country={countryScope}
          onOpenAlerts={()=>{if(window.matchMedia('(max-width: 980px)').matches)setMobilePane('alerts');else selectDomainTab('command',domains[0].tabs[1]);}}/>}
        </div>
        <footer className="footer">
          <div>
            <span className="live-dot" /> EASTERN AXIS / OPEN RESEARCH
          </div>
          <span>PUBLIC EVIDENCE · NO UNSOURCED THREAT RANKINGS</span>
        </footer>
      </div>
      <nav className="ea-mobile-primary" aria-label="Mobile primary navigation">
        <button type="button" onClick={()=>selectDomainTab('command',domains[0].tabs[0])} aria-current={mobilePane==='workspace'&&domain==='command'?'page':undefined}>
          <Globe2 size={20}/><span>Home</span></button>
        <button type="button" onClick={()=>{setMobilePane('domains');setMobileFiltersOpen(false);}} aria-current={mobilePane==='domains'?'page':undefined}>
          <Grid2X2 size={20}/><span>Domains</span></button>
        <button type="button" onClick={()=>{setMobilePane('alerts');setMobileFiltersOpen(false);}} aria-current={mobilePane==='alerts'?'page':undefined}>
          <Bell size={20}/><span>Alerts</span>{intelligenceFeed.promoted.length>0&&<small>{intelligenceFeed.promoted.length}</small>}</button>
        <button type="button" onClick={()=>{setMobilePane('briefcase');setMobileFiltersOpen(false);}} aria-current={mobilePane==='briefcase'?'page':undefined}>
          <BriefcaseBusiness size={20}/><span>Briefcase</span></button>
      </nav>
      <IntelCardDetails />
      <BugReportDialog open={bugReportOpen} onClose={() => setBugReportOpen(false)}
        section={view === 'Overview' ? 'Command center' : view} />

    </div>
    </GlobalFiltersContext.Provider>
  );
}
export default App;
