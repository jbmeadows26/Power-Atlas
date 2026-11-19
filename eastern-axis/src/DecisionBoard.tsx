import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { Activity, ArrowRight, ArrowUpRight, Clock3, Database, ExternalLink, RefreshCcw, ShieldAlert } from 'lucide-react';
import './decision-board.css';

type Country = { code: string; name: string; region: string; isTreatyAlly: boolean; caseCount: number };
type CaseFile = { id: string; code: string; date: string; title: string; topic: string; status: string };
type SourceHealth = { status: 'ok' | 'error'; lastAttemptAt: string; lastSuccessAt?: string; lastError?: string };
type Intel = {
  sources: Array<{ id: string; name: string; health: SourceHealth | null }>;
  records: Array<{ id: string; sourceId: string; title: string; date: string; countryMention?: string; sourceUrl: string }>;
  ofac?: { checkedAt: string; records: number; programCounts: Record<string, number> } | null;
  sampled: number;
};
type WorldSignals = {
  generatedAt: string;
  checkedAt: string;
  events: Array<{ id: string; date: string }>;
  naturalEvents?: Array<{ id: string; date: string }>;
};
type Metric = { value: number; year: string; indicator: string; source: string };
type Brief = { code: string; updatedAt: string; metrics: Record<string, Metric>; mode?: string; warning?: string };
type Props = {
  countries: Country[];
  cases: CaseFile[];
  intel: Intel | null;
  worldSignals: WorldSignals | null;
  intelligenceError: boolean;
  signalError: boolean;
  activeCountry?: string;
  onCountrySelected?: (code: string) => void;
  openCases: (id?: string) => void;
  openDesk: () => void;
  openSources: () => void;
  refresh: () => void;
  lastRequestedAt: string | null;
};
const focusCodes = ['RU', 'CN', 'IR', 'KP', 'BY', 'VE', 'CU'];
const ofacLabels: Record<string, RegExp> = {
  RU: /^RUSSIA/i, CN: /^CHINA/i, IR: /^IRAN|^IFSR/i,
  KP: /^DPRK|^NKOREA/i, BY: /^BELARUS/i, VE: /^VENEZUELA/i, CU: /^CUBA/i,
};
const number = (n: number) => new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n);
const time = (v?: string) => {
  if (!v || !Number.isFinite(Date.parse(v))) return 'Not reported';
  return new Date(v).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit', timeZone: 'UTC', timeZoneName: 'short' });
};
const dateOnly = (v?: string) => {
  if (!v || !Number.isFinite(Date.parse(v))) return 'Undated';
  return new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
};
const flag = (code: string) => /^[A-Z]{2}$/.test(code) ? code.replace(/./g, c => String.fromCodePoint(127397 + c.charCodeAt(0))) : '🌐';
const ageText = (value?: string) => {
  const timestamp = value ? Date.parse(value) : NaN;
  if (!Number.isFinite(timestamp)) return 'No recorded check';
  const hours = (Date.now() - timestamp) / 3600000;
  if (hours < -1) return 'Timestamp discrepancy';
  if (hours < 1) return 'Checked within 1h';
  if (hours < 24) return Math.floor(hours) + 'h since check';
  return Math.floor(hours / 24) + 'd since check';
};
function MetricCard({ label, value, detail, warn = false }: { label: string; value: string; detail: string; warn?: boolean }) {
  return <article className={'db-stat' + (warn ? ' db-warn' : '')}>
    <span>{label}</span><strong>{value}</strong><small>{detail}</small>
  </article>;
}
export default function DecisionBoard({
  countries, cases, intel, worldSignals, intelligenceError, signalError,
  activeCountry, onCountrySelected, openCases, openDesk, openSources, refresh, lastRequestedAt,
}: Props) {
  const code = activeCountry && activeCountry !== 'all' ? activeCountry : 'all';
  const selected = countries.find(country => country.code === code);
  const [brief, setBrief] = useState<Brief | null>(null);
  const [briefError, setBriefError] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => {
    if (code === 'all') { setBrief(null); setBriefError(false); return; }
    let active = true;
    setBrief(null); setBriefError(false);
    api.get('/api/brief/' + encodeURIComponent(code))
      .then(result => { if (active) setBrief(result.data as Brief); })
      .catch(() => { if (active) setBriefError(true); });
    return () => { active = false; };
  }, [code, lastRequestedAt]);

  const scopedCases = useMemo(() => cases
    .filter(item => code === 'all' || item.code === code)
    .sort((a, b) => b.date.localeCompare(a.date)), [cases, code]);
  const byTopic = useMemo(() => Object.entries(scopedCases.reduce<Record<string, number>>((items, item) => {
    items[item.topic || 'Uncategorized'] = (items[item.topic || 'Uncategorized'] || 0) + 1;
    return items;
  }, {})).sort((a, b) => b[1] - a[1]), [scopedCases]);
  const recentCases = scopedCases.filter(item => {
    const reported = Date.parse(item.date);
    return Number.isFinite(reported) && reported <= now && reported >= now - 30 * 86400000;
  });
  const ordered = countries.filter(item => !item.isTreatyAlly)
    .sort((a, b) => (cases.filter(c => c.code === b.code).length - cases.filter(c => c.code === a.code).length)
      || (focusCodes.indexOf(a.code) === -1 ? 99 : focusCodes.indexOf(a.code))
       - (focusCodes.indexOf(b.code) === -1 ? 99 : focusCodes.indexOf(b.code)))
    .slice(0, 9);
  const cards = code === 'all' ? ordered : selected ? [selected] : [];
  const checks = intel?.sources || [];
  const healthy = checks.filter(item => item.health?.status === 'ok');
  const failing = checks.filter(item => item.health?.status === 'error');
  const pending = checks.filter(item => !item.health);
  const programCount = (countryCode: string) => {
    const pattern = ofacLabels[countryCode];
    return pattern ? Object.entries(intel?.ofac?.programCounts || {})
      .filter(([label]) => pattern.test(label)).reduce((sum, [, count]) => sum + count, 0) : null;
  };
  const newestCheck = checks.map(item => item.health?.lastAttemptAt).filter((v): v is string => !!v)
    .sort().reverse()[0];
  const countryMax = Math.max(1, ...cards.map(item => cases.filter(c => c.code === item.code).length));
  const topicMax = Math.max(1, ...byTopic.map(([, value]) => value));
  const showMetrics = code !== 'all' ? brief?.metrics : undefined;

  return <section className="db-root" aria-label="Decision intelligence dashboard">
    <div className="db-head">
      <div><span className="db-kicker"><Activity size={14}/> DECISION INTELLIGENCE / SOURCE-DATED</span>
        <h1>{selected ? selected.name : 'Global'} <em>intelligence pulse</em></h1>
        <p>Evidence counts, country comparisons, feed integrity, and emerging records at a glance. Counts reflect indexed coverage—not total real-world activity.</p>
      </div>
      <div className="db-actions">
        <span className="db-clock"><Clock3 size={13}/> {new Date(now).toLocaleTimeString('en-US', {timeZone:'UTC',hour:'2-digit',minute:'2-digit',hour12:false})} UTC</span>
        <button type="button" onClick={refresh}><RefreshCcw size={14}/> Refresh feeds</button>
      </div>
    </div>
    <div className="db-statusline">
      <span><span className={'db-led' + (failing.length || intelligenceError ? ' db-led-warn' : '')}/> {intelligenceError ? 'INTAKE UNAVAILABLE' : failing.length ? failing.length + ' FAILED SOURCE CHECKS' : !intel ? 'AWAITING INTAKE' : 'INTAKE STATUS RECEIVED'}</span>
      <span>Source check: {time(newestCheck)}</span>
      <span>Signal snapshot: {time(worldSignals?.generatedAt)}</span>
      <span>{lastRequestedAt ? 'Last dashboard request: ' + time(lastRequestedAt) : 'Loading data'}</span>
    </div>
    <div className="db-stat-grid">
      <MetricCard label="CURATED CASE RECORDS" value={number(scopedCases.length)} detail={code === 'all' ? 'All countries · selected evidence library' : code + ' · country-scoped cases'} />
      <MetricCard label="DATED CASES / 30 DAYS" value={number(recentCases.length)} detail="Cases by record date · not a real-time incident count" />
      <MetricCard label="SUCCESSFUL SOURCE CHECKS" value={intel ? healthy.length + ' / ' + checks.length : '—'} detail={intel ? failing.length + ' failed · ' + pending.length + ' unchecked · ' + ageText(newestCheck) : 'Waiting for health data'} warn={failing.length > 0 || intelligenceError}/>
      <MetricCard label="INTAKE RECORDS IN SAMPLE" value={intel ? number(intel.records.length) : '—'} detail="Visible sample · does not imply complete ingestion" />
      <MetricCard label="OFAC SDN ENTRIES" value={intel?.ofac ? number(intel.ofac.records) : '—'} detail={intel?.ofac ? 'Global SDN export · ' + dateOnly(intel.ofac.checkedAt) : 'Not validated / unavailable'} />
      <MetricCard label="GLOBAL HAZARD OBSERVATIONS" value={worldSignals ? number((worldSignals.events?.length || 0) + (worldSignals.naturalEvents?.length || 0)) : '—'} detail={signalError ? 'Source check failed · not zero events' : 'Sampled USGS + NASA · worldwide, separate from conflicts'} warn={signalError}/>
    </div>
    <div className="db-two-up">
      <section className="db-panel" aria-label="Country evidence cards">
        <div className="db-panel-head"><div><span>COUNTRY-LEVEL INTELLIGENCE</span><h2>{selected ? 'Selected country dossier' : 'Country comparison'}</h2></div><span>{cards.length} shown</span></div>
        <div className="db-countries">
          {cards.map(item => {
            const count = cases.filter(c => c.code === item.code).length;
            const programs = programCount(item.code);
            return <button key={item.code} type="button" className={'db-country' + (item.code === code ? ' is-active' : '')}
              onClick={() => onCountrySelected?.(item.code)} aria-label={'Focus dashboard on ' + item.name}>
              <div className="db-country-top"><span>{flag(item.code)} {item.name}</span><ArrowRight size={14}/></div>
              <div className="db-country-number"><strong>{count}</strong><small>curated case files</small></div>
              <div className="db-bar"><span style={{ width: Math.max(3, count / countryMax * 100) + '%' }}/></div>
              <div className="db-country-meta"><span>{item.code} · {item.region}</span><span>{programs === null || !intel?.ofac ? 'OFAC: unverified' : 'OFAC tags: ' + number(programs)}</span></div>
            </button>;
          })}
        </div>
        <p className="db-caveat">Bars compare indexed case counts, not danger, probability of conflict, or national culpability. OFAC program tags are not country-located sanctions entities.</p>
      </section>
      <section className="db-panel" aria-label="Evidence composition and freshest cases">
        <div className="db-panel-head"><div><span>EVIDENCE MIX / {code.toUpperCase()}</span><h2>Where the records concentrate</h2></div><button type="button" onClick={() => openCases()}>All cases <ArrowUpRight size={14}/></button></div>
        <div className="db-topic-list">
          {byTopic.slice(0, 6).map(([topic, count]) => <div key={topic} className="db-topic">
            <div><span>{topic}</span><strong>{count}</strong></div><div className="db-bar"><span style={{width: (count / topicMax * 100) + '%'}}/></div>
          </div>)}
          {!byTopic.length && <p className="db-empty">No cases indexed for this filter. This is not evidence that no activity exists.</p>}
        </div>
        <div className="db-latest-heading">LATEST DATED CASE RECORDS</div>
        <div className="db-latest">
          {scopedCases.slice(0, 4).map(item => <button type="button" key={item.id} onClick={() => openCases(item.id)}>
            <span>{item.code} · {dateOnly(item.date)}</span><strong>{item.title}</strong><ArrowUpRight size={13}/>
          </button>)}
        </div>
      </section>
    </div>
    {code !== 'all' && <section className="db-panel db-fact-panel">
      <div className="db-panel-head"><div><span>{code} / WORLD BANK</span><h2>Latest reported national indicators</h2></div><span>Observation year on every value</span></div>
      <div className="db-fact-grid">
        {([['population', 'Population', ''], ['gdp', 'GDP', '$'], ['lifeExpectancy', 'Life expectancy', '']] as const).map(([key, label, prefix]) => {
          const metric = showMetrics?.[key];
          return <article key={key}><span>{label}</span><strong>{metric && Number.isFinite(metric.value) ? prefix + number(metric.value) + (key === 'lifeExpectancy' ? ' yr' : '') : '—'}</strong>
            <small>{metric ? 'World Bank · ' + metric.year : briefError ? 'Indicator feed unavailable' : 'No reported value'}</small>
          </article>;
        })}
      </div>
      {brief?.warning && <p className="db-caveat">{brief.warning}</p>}
      <p className="db-caveat">Different indicators may use different reference years; data are not forecasts or surveillance measurements. <a href="https://data.worldbank.org/" target="_blank" rel="noopener noreferrer">World Bank original source <ExternalLink size={11}/></a></p>
    </section>}
    <div className="db-bottom-strip">
      <div><Database size={14}/><strong>COLLECTION INTEGRITY</strong>
        <span>{intelligenceError ? 'Intelligence API unavailable.' : failing.length ? failing.map(item => item.name).join(', ') + ' require investigation.' : intel ? 'No failures in returned checks; unmonitored sources are not implied healthy.' : 'Waiting for source checks.'}</span>
      </div>
      <div><button type="button" onClick={openDesk}>Inspect feeds <ArrowRight size={13}/></button><button type="button" onClick={openSources}>Source library <ExternalLink size={13}/></button></div>
    </div>
    <p className="db-footer-note"><ShieldAlert size={13}/> This page refreshes while open, not continuously while your device is offline. Source timestamps and missing-feed states take priority over animated "live" claims.</p>
  </section>;
}
