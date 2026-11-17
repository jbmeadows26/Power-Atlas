import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { ArrowRight, BookOpen, ChevronDown, Database, ExternalLink, Globe2, Search, TrendingUp } from 'lucide-react';
import './factbook.css';

type Country = {
  code: string; iso: string | null; gec: string; name: string; region: string;
};
type Metric = { value: number; year: string; source: string; indicator: string };
type Profile = {
  status: string; code: string; country?: string; gec?: string; asOf?: string;
  fields?: Record<string, string | null>;
  sourceUrl?: string; sha256?: string; sourceRevision?: string;
  warning?: string; reason?: string;
};
type Brief = { metrics: Record<string, Metric> };
type Comparison = {
  rows: Array<{ code: string; name: string; metrics: Record<string, Metric> }>;
  warning: string;
};
const labels: Record<string, string> = {
  background: 'Historical background',
  location: 'Geographic location',
  area: 'Total area',
  climate: 'Climate',
  terrain: 'Terrain',
  resources: 'Natural resources',
  population: 'Archived population',
  languages: 'Languages',
  government: 'Government structure',
  capital: 'Capital',
  economy: 'Economic background',
  industries: 'Industries',
  electricity: 'Electricity access',
  military: 'Military structure',
  expenditure: 'Archived military spending',
  transportation: 'Ports and terminals',
  disputes: 'Cross-border disputes',
};
const flag = (code: string) => /^[A-Z]{2}$/.test(code)
  ? code.replace(/./g, c => String.fromCodePoint(127397 + c.charCodeAt(0)))
  : '🌐';
const fmt = (metric: Metric, kind: string) =>
  (kind === 'gdp' ? '$' : '') +
  new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(metric.value) +
  (kind === 'lifeExpectancy' ? ' years' : '');

export default function Factbook({
  activeCountry, onCountryChange,
}: {
  activeCountry: string; onCountryChange: (value: string) => void;
}) {
  const [catalog, setCatalog] = useState<Country[]>([]);
  const [catalogError, setCatalogError] = useState('');
  const [selected, setSelected] = useState(activeCountry === 'all' ? 'RU' : activeCountry);
  const [query, setQuery] = useState('');
  const [region, setRegion] = useState('All regions');
  const [profile, setProfile] = useState<Profile | null>(null);
  const [brief, setBrief] = useState<Brief | null>(null);
  const [loading, setLoading] = useState(true);
  const [profileError, setProfileError] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ background: true });
  const [comparisonCodes, setComparisonCodes] = useState<string[]>([]);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [compareError, setCompareError] = useState('');
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    api.get('/api/factbook/countries')
      .then(result => setCatalog((result.data as { countries: Country[] }).countries))
      .catch(() => setCatalogError('Historical archive directory is currently unavailable.'));
  }, []);
  useEffect(() => {
    if (activeCountry !== 'all') setSelected(activeCountry);
  }, [activeCountry]);
  useEffect(() => {
    let active = true;
    setProfile(null); setBrief(null); setProfileError(''); setLoading(true);
    api.get('/api/factbook/' + encodeURIComponent(selected))
      .then(result => { if (active) setProfile(result.data as Profile); })
      .catch(() => { if (active) setProfileError('Archived record unavailable; no data substituted.'); })
      .finally(() => { if (active) setLoading(false); });
    if (/^[A-Z]{2}$/.test(selected)) {
      api.get('/api/brief/' + selected)
        .then(result => { if (active) setBrief(result.data as Brief); })
        .catch(() => {});
    }
    return () => { active = false; };
  }, [selected, retryCount]);

  const visible = useMemo(() => catalog.filter(item =>
    (region === 'All regions' || item.region === region) &&
    (item.name.toLowerCase().includes(query.toLowerCase()) ||
      item.code.toLowerCase().includes(query.toLowerCase()) ||
      item.gec.includes(query.toLowerCase()))
  ), [catalog, query, region]);
  const current = catalog.find(item => item.code === selected);
  function selectCountry(item: Country) {
    setSelected(item.code); setExpanded({ background: true });
    onCountryChange(item.iso || 'all');
  }
  function toggleComparison(code: string) {
    setComparison(null);
    setComparisonCodes(codes => codes.includes(code)
      ? codes.filter(item => item !== code)
      : codes.length >= 3 ? [...codes.slice(1), code] : [...codes, code]);
  }
  function compare() {
    if (!comparisonCodes.length) return;
    setComparing(true); setCompareError('');
    api.get('/api/factbook/compare?codes=' + comparisonCodes.join(','))
      .then(result => setComparison(result.data as Comparison))
      .catch(() => setCompareError('Comparison unavailable; historical estimates were not substituted.'))
      .finally(() => setComparing(false));
  }

  return <div className="fb-root">
    <header className="fb-hero">
      <div className="fb-kicker"><Globe2 size={15}/> GLOBAL REFERENCE / HISTORICAL + CURRENT</div>
      <h1>The world, <em>explained.</em></h1>
      <p>Browse the final CIA World Factbook archive, then explore source-dated World Bank measurements and related intelligence.</p>
      <div className="fb-cues">
        <span><BookOpen size={13}/> January 2026 archive</span>
        <span><TrendingUp size={13}/> Updated indicators</span>
        <span><Database size={13}/> Original evidence links</span>
      </div>
    </header>
    <div className="fb-layout">
      <aside className="fb-directory">
        <div className="fb-topline"><strong>GLOBAL DIRECTORY</strong><small>{catalog.length} entities</small></div>
        <div className="fb-search"><Search size={15}/><input
          aria-label="Search Factbook countries and areas"
          placeholder="Country, ocean or territory"
          value={query} onChange={e => setQuery(e.target.value)}/></div>
        <div className="fb-filter"><select aria-label="Factbook region" value={region}
          onChange={e => setRegion(e.target.value)}>
          {['All regions', 'Africa', 'Americas', 'Asia', 'Europe', 'Oceania', 'Other']
            .map(item => <option key={item}>{item}</option>)}
        </select><ChevronDown size={15}/></div>
        {catalogError && <p className="fb-alert">{catalogError}</p>}
        <div className="fb-entries">
          {visible.map(item => <button key={item.code} type="button"
            className={selected === item.code ? 'selected' : ''}
            onClick={() => selectCountry(item)}>
            <span className="fb-flag">{flag(item.iso || '')}</span>
            <span className="fb-entry"><strong>{item.name}</strong>
              <small>{item.iso || 'Archive-only'} · GEC {item.gec.toUpperCase()}</small>
            </span>
            <ArrowRight size={13}/>
          </button>)}
          {catalog.length > 0 && visible.length === 0 && <p className="fb-note">No matching entities.</p>}
        </div>
        <p className="fb-note">Includes territories, disputed areas, oceans and the world.
          Inclusion does not imply recognition of sovereignty.</p>
      </aside>
      <div className="fb-main">
        <section className="fb-panel">
          <div className="fb-country">
            <div><small>WORLD FACTBOOK / {selected}</small>
              <h2>{flag(current?.iso || '')} {current?.name || 'Archived country profile'}</h2>
              <p>ISO: {current?.iso || 'No equivalent'} · CIA GEC: {current?.gec.toUpperCase() || '—'}</p>
            </div>
            <span className="fb-status">FROZEN 2026</span>
          </div>
          {loading && <p className="fb-note">Loading pinned historical source…</p>}
          {(profileError || profile?.status === 'archive_unavailable') &&
            <div className="fb-alert">{profileError || profile?.reason}
              <button onClick={() => setRetryCount(value => value + 1)}>Retry</button>
            </div>}
          {profile?.status === 'available' && <>
            <div className="fb-heading"><strong>WORLD BANK · LATEST REPORTED</strong><small>Observation year shown</small></div>
            <div className="fb-stats">
              {([
                ['population', 'Population'],
                ['gdp', 'GDP / current US$'],
                ['lifeExpectancy', 'Life expectancy'],
              ] as const).map(([key, label]) => {
                const metric = brief?.metrics?.[key];
                return <div key={key}><small>{label}</small>
                  <strong>{metric ? fmt(metric, key) : 'Unavailable'}</strong>
                  <span>{metric ? 'World Bank · ' + metric.year : 'No current observation'}</span>
                </div>;
              })}
            </div>
            <div className="fb-heading"><strong>HISTORICAL COUNTRY CONTEXT</strong><small>Archive as of January 2026</small></div>
            <div className="fb-facts">
              {Object.entries(labels).filter(([key]) => profile.fields?.[key]).map(([key, label]) =>
                <article key={key}><button aria-expanded={!!expanded[key]}
                  onClick={() => setExpanded(value => ({ ...value, [key]: !value[key] }))}>
                  <strong>{label}</strong><ChevronDown size={14}/>
                </button>{expanded[key] && <p>{profile.fields?.[key]}</p>}</article>)}
            </div>
            <div className="fb-source"><Database size={18}/><div>
              <strong>Historical source & verification</strong>
              <p>Baseline: {profile.asOf} · GEC {profile.gec} · SHA-256 {profile.sha256?.slice(0, 22)}…</p>
              <small>{profile.warning}</small>
              {profile.sourceUrl && <a href={profile.sourceUrl} target="_blank" rel="noopener noreferrer">
                Original pinned archive record <ExternalLink size={13}/></a>}
            </div></div>
          </>}
          <div className="fb-links">
            <a href="https://github.com/factbook/factbook.json" target="_blank" rel="noopener noreferrer">Factbook mirror <ExternalLink size={13}/></a>
            <a href="https://data.worldbank.org/" target="_blank" rel="noopener noreferrer">World Bank <ExternalLink size={13}/></a>
          </div>
        </section>
        <section className="fb-panel">
          <div className="fb-heading"><strong>COMPARE COUNTRIES</strong><small>Maximum three</small></div>
          <p className="fb-note">Compare only World Bank observations, never substitute archived estimates.</p>
          <div className="fb-choices">
            {catalog.filter(item => ['US','CN','RU','IR','IN','DE','GB','JP','BR','KR','UA','SA','FR','ID','MX','NG'].includes(item.code))
              .map(item => <button key={item.code}
                className={comparisonCodes.includes(item.code) ? 'selected' : ''}
                onClick={() => toggleComparison(item.code)}>
                {flag(item.code)} {item.name}
              </button>)}
          </div>
          <div className="fb-actions"><small>{comparisonCodes.length}/3 selected</small>
            <button disabled={!comparisonCodes.length || comparing} onClick={compare}>
              {comparing ? 'Comparing…' : 'Compare reported data'} <ArrowRight size={14}/>
            </button>
          </div>
          {compareError && <div className="fb-alert">{compareError}</div>}
          {comparison && <div className="fb-charts">
            {(['population', 'gdp', 'lifeExpectancy'] as const).map(key => {
              const max = Math.max(1, ...comparison.rows.map(row => row.metrics[key]?.value || 0));
              return <div key={key} className="fb-chart-group">
                <strong>{key === 'gdp' ? 'GDP / current US$' : key === 'population' ? 'Population' : 'Life expectancy'}</strong>
                {comparison.rows.map(row => {
                  const metric = row.metrics[key];
                  return <div className="fb-chart-row" key={row.code}>
                    <span>{flag(row.code)} {row.name}</span>
                    <div className="fb-bar"><i style={{ width: metric ? (metric.value / max * 100) + '%' : '0%' }}/></div>
                    <small>{metric ? fmt(metric, key) + ' · ' + metric.year : 'Unavailable'}</small>
                  </div>;
                })}
              </div>;
            })}
            <small>{comparison.warning}</small>
          </div>}
        </section>
      </div>
    </div>
  </div>;
}
