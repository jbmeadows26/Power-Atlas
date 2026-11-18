import { useEffect, useMemo, useState } from 'react';
import IntakeDesk from './IntakeDesk';
import CountryPicker from './CountryPicker';
import { withSecurityContext } from './securityTreaties';
import GlobalSystems from './GlobalSystems';
import ResilienceWatch from './ResilienceWatch';
import OperationalAssurance from './OperationalAssurance';
import SupplyChain from './SupplyChain';
import PhysicalEarlyWarning from './PhysicalEarlyWarning';
import Connections from './Connections';
import EvidenceWorkbench from './EvidenceWorkbench';
import CommandCenter from './CommandCenter';
import Factbook from './Factbook';
import DefenseIntel from './DefenseIntel';
import AgentDesk from './AgentDesk';
import { api } from '@appdeploy/client';
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
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
const sections = [
  'Overview',
  'Countries',
  'World Factbook',
  'Global systems',
  'Supply chain',
  'Early warning',
  'Risk watch',
  'AI analyst',
  'Coverage audit',
  'Connections',
  'Defense intelligence',
  'Investigations',
  'Collection desk',
  'Verification lab',
  'Source library', 
  'Methodology',
] as const;
type Section = (typeof sections)[number];
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
  const [view, setView] = useState<Section>('Overview');
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [region, setRegion] = useState('All regions');
  const [showTerritories, setShowTerritories] = useState(false);
  const [showAllies, setShowAllies] = useState(false);
  const [selected, setSelected] = useState<string | null>('RU');
  const [countryScope, setCountryScope] = useState<string>(()=>{try{return window.localStorage.getItem('ea.country.scope')||'all';}catch{return 'all';}});
  useEffect(()=>{try{window.localStorage.setItem('ea.country.scope',countryScope);}catch{};if(countryScope!=='all')setSelected(countryScope);},[countryScope]);
  const [brief, setBrief] = useState<Brief | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [caseTopic, setCaseTopic] = useState('All investigations');
  const [caseSelected, setCaseSelected] = useState<string | null>(null);
  const [sourceGroup, setSourceGroup] = useState('All');
  const [mobileMenu, setMobileMenu] = useState(false);

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
  const notAllied = mainStates.filter(c => !c.isTreatyAlly);
  const filtered = useMemo(
    () =>
      countries.filter(
        c =>
          (showTerritories || c.scope === 'state-or-observer') &&
          (showAllies || !c.isTreatyAlly) &&
          (countryScope === 'all' || c.code === countryScope) &&
          (region === 'All regions' || c.region === region) &&
          (c.name.toLowerCase().includes(search.toLowerCase()) ||
            c.code.toLowerCase().includes(search.toLowerCase()))
      ),
    [countries, search, region, showTerritories, showAllies, countryScope]
  );
  const country = countries.find(c => c.code === selected);
  const chosenCase = cases.find(c => c.id === caseSelected);
  const topics = [
    'All investigations',
    ...Array.from(new Set(cases.map(c => c.topic))),
  ];
  const caseList = cases.filter(
    c => (caseTopic === 'All investigations' || c.topic === caseTopic) && (countryScope==='all'||c.code===countryScope)
  );
  const sourceCategories = [
    'All',
    ...Array.from(new Set(sources.map(s => s.category))),
  ];
  const openCountry = (code: string) => {
    setCountryScope(code);
    setSelected(code);
    setView('Countries');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const switchView = (next: Section) => {
    setView(next);
    setMobileMenu(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="shell">
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
        <div className="nav-label">EXPLORE INTELLIGENCE</div>
        <nav aria-label="Main navigation">
          {sections.map((s, i) => {
            const icons = [
              <Activity size={17} />,
              <Globe2 size={17} />,
              <BookOpen size={17} />,
              <Layers3 size={17} />,
              <Activity size={17} />,
              <Activity size={17} />,
              <ShieldAlert size={17} />,
              <Sparkles size={17} />,
              <Database size={17} />,
              <Network size={17} />,
              <Shield size={17} />,
              <FileSearch size={17} />,
              <Radio size={17} />,
              <FileSearch size={17} />,
              <Database size={17} />,
              <BookOpen size={17} />,
            ];
            return (
              <button
                key={s}
                type="button"
                className={'nav-item ' + (view === s ? 'active' : '')}
                aria-current={view === s ? 'page' : undefined}
                onClick={() => switchView(s)}
              >
                {icons[i]}
                <span>{s === 'Overview' ? 'Command center' : s}</span>
                {s === 'Investigations' && cases.length > 0 ? (
                  <small>{cases.length}</small>
                ) : null}
              </button>
            );
          })}
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
              onClick={() => setMobileMenu(v => !v)}
              aria-label={mobileMenu ? 'Close navigation' : 'Open navigation'}
              aria-controls="ea-primary-navigation"
              aria-expanded={mobileMenu}
            >
              <Menu size={21} />
            </button>
            <div className="breadcrumb">
              <span className="breadcrumb-prefix">INTELLIGENCE DESK</span> <ChevronRight size={13} />{' '}
              <strong>{view === 'Overview' ? 'COMMAND CENTER' : view.toUpperCase()}</strong>
            </div>
          </div>
          <div className="header-right">
            <CountryPicker countries={mainStates} value={countryScope} onChange={setCountryScope} />
            <span className="header-meta">
              <span className="live-dot" /> UNCLASSIFIED / PUBLIC DATA
            </span>
            <span className="asof">SOURCE-DATED DATA</span>
          </div>
        </header>
        <main className="content">
          {overview && view === 'Overview' && (
            <section className="mobile-brief" aria-labelledby="ea-mobile-brief-title">
              <div className="mobile-brief-heading">
                <span className="mobile-brief-kicker"><span className="live-dot" /> INTELLIGENCE BRIEFING</span>
                <span className="mobile-brief-label">PUBLIC SOURCES</span>
              </div>
              <h1 id="ea-mobile-brief-title">The world, <em>at a glance.</em></h1>
              <p>
                {countryScope === 'all'
                  ? 'Explore global risks, country records and the evidence behind each signal.'
                  : 'Focused on ' + (countries.find(c => c.code === countryScope)?.name || countryScope) + '. Your selection follows you across the dashboard.'}
              </p>
              <div className="mobile-brief-metrics">
                <div><strong>{countryScope === 'all' ? cases.length : cases.filter(c => c.code === countryScope).length}</strong><span>Curated cases</span></div>
                <div><strong>{sources.length}</strong><span>Source listings</span></div>
              </div>
              <div className="mobile-brief-actions" aria-label="Quick navigation">
                <button type="button" onClick={() => switchView('Risk watch')}><ShieldAlert size={17} /> Risk watch <ArrowRight size={16} /></button>
                <button type="button" onClick={() => switchView('Supply chain')}><Layers3 size={17} /> Supply chain <ArrowRight size={16} /></button>
                <button type="button" onClick={() => switchView('Early warning')}><Activity size={17} /> Early warning <ArrowRight size={16} /></button>
              </div>
            </section>
          )}
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
              openMethod={()=>switchView('Methodology')} />
          )}
          {overview && view === 'Global systems' && <GlobalSystems mode="systems" countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} cases={cases} />}
          {overview && view === 'Supply chain' && <SupplyChain countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} />}
          {overview && view === 'Early warning' && <PhysicalEarlyWarning countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} onOpenSupplyChain={()=>switchView('Supply chain')} />}
          {overview && view === 'Risk watch' && <><ResilienceWatch/><GlobalSystems mode="risk" countryCode={countryScope} countryName={overview.countries.find(c=>c.code===countryScope)?.name} cases={cases} /></>}
          {overview && view === 'AI analyst' && <AgentDesk countryCode={countryScope} />}
          {overview && view === 'Coverage audit' && <><OperationalAssurance/><GlobalSystems mode="coverage" countryCode={countryScope} cases={cases} /></>}
                    {overview && view === 'Connections' && <Connections code={countryScope} countries={overview.countries.filter(c=>c.scope==='state-or-observer')} cases={cases} onSelect={setCountryScope} />}
          {overview && view === 'Collection desk' && <IntakeDesk countryCode={countryScope} />}{overview && view === 'Verification lab' && <EvidenceWorkbench countryCode={countryScope} />}
          {overview && view === 'Defense intelligence' && <DefenseIntel mode="global" code={countryScope==='all'?undefined:countryScope} />}
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
                    verified case files and World Bank indicators.
                  </p>
                </div>
                <Badge kind="green">
                  {filtered.length} jurisdictions shown
                </Badge>
              </div>
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
                    <div className="region-holder">
                      <Filter size={16} />
                      <select
                        aria-label="Filter by region"
                        value={region}
                        onChange={e => setRegion(e.target.value)}
                      >
                        {[
                          'All regions',
                          'Africa',
                          'Americas',
                          'Asia',
                          'Europe',
                          'Oceania',
                          'Other',
                        ].map(x => (
                          <option key={x}>{x}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} />
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
                      <button type="button" onClick={() => { setCountryScope(country.code); switchView('World Factbook'); }} style={{width:'100%',display:'flex',alignItems:'center',justifyContent:'space-between',padding:15,margin:'15px 0',background:'#174139',border:'1px solid #4f907f',color:'#b6f4da',borderRadius:8,fontWeight:700}}>Explore historical World Factbook <ArrowRight size={17}/></button>
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
              <div className="investigations-layout">
                <div className="case-rows">
                  {caseList.map(c => (
                    <button
                      key={c.id}
                      className={
                        'case-card ' +
                        (caseSelected === c.id ? 'case-selected' : '')
                      }
                      onClick={() => setCaseSelected(c.id)}
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
                <aside className="evidence-panel">
                  {chosenCase ? (
                    <>
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
        </main>
        <footer className="footer">
          <div>
            <span className="live-dot" /> EASTERN AXIS / OPEN RESEARCH
          </div>
          <span>PUBLIC EVIDENCE · NO UNSOURCED THREAT RANKINGS</span>
        </footer>
      </div>
      <nav className="mobile-bottom-nav" aria-label="Mobile primary navigation">
        <button type="button" className={view === 'Overview' ? 'selected' : ''} aria-current={view === 'Overview' ? 'page' : undefined} onClick={() => switchView('Overview')}>
          <Activity size={20} strokeWidth={2} /><span>Home</span>
        </button>
        <button type="button" className={view === 'Countries' || view === 'World Factbook' ? 'selected' : ''} aria-current={view === 'Countries' || view === 'World Factbook' ? 'page' : undefined} onClick={() => switchView('Countries')}>
          <Globe2 size={20} strokeWidth={2} /><span>Countries</span>
        </button>
        <button type="button" className={view === 'Risk watch' ? 'selected' : ''} aria-current={view === 'Risk watch' ? 'page' : undefined} onClick={() => switchView('Risk watch')}>
          <ShieldAlert size={20} strokeWidth={2} /><span>Risks</span>
        </button>
        <button type="button" className={view === 'Connections' ? 'selected' : ''} aria-current={view === 'Connections' ? 'page' : undefined} onClick={() => switchView('Connections')}>
          <Network size={20} strokeWidth={2} /><span>Networks</span>
        </button>
        <button type="button" className={mobileMenu || !(['Overview','Countries','World Factbook','Risk watch','Connections'] as Section[]).includes(view) ? 'selected' : ''} aria-expanded={mobileMenu} aria-controls="ea-primary-navigation" onClick={() => setMobileMenu(v => !v)}>
          <Menu size={20} strokeWidth={2} /><span>More</span>
        </button>
      </nav>
    </div>
  );
}
export default App;
