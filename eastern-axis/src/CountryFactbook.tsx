import { useEffect, useMemo, useState } from 'react';
import { api } from '@appdeploy/client';
import { BookOpen, ExternalLink, RefreshCcw, ShieldCheck } from 'lucide-react';
import './country-factbook.css';

type Archive = {
  status: string;
  code: string;
  country?: string;
  asOf?: string;
  gec?: string;
  sourceRevision?: string;
  sha256?: string;
  sourceUrl?: string;
  warning?: string;
  reason?: string;
  fields?: Record<string, unknown>;
};
const names: Record<string, string> = {
  background: 'Historical background', location: 'Location', area: 'Area',
  climate: 'Climate', terrain: 'Terrain', resources: 'Natural resources',
  population: 'Archived population', languages: 'Languages',
  government: 'Government', capital: 'Capital', economy: 'Economy',
  industries: 'Industries', electricity: 'Electricity access',
  military: 'Military', expenditure: 'Military expenditure',
  transportation: 'Transportation / ports', disputes: 'Border disputes'
};
const title = (key: string) => names[key] || key.replace(/[_-]/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
const officialUrl = (value?: string) => {
  try { const url = new URL(value || ''); return url.protocol === 'https:' ? url.href : null; }
  catch { return null; }
};
export default function CountryFactbook({ code, countryName }: { code: string; countryName?: string }) {
  const [archive, setArchive] = useState<Archive | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!/^[A-Z]{2}$/.test(code)) { setArchive(null); setError(false); return; }
    let active = true;
    setArchive(null); setError(false);
    api.get('/api/factbook/' + encodeURIComponent(code))
      .then(result => { if (active) setArchive(result.data as Archive); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [code, retry]);
  const entries = useMemo(() => Object.entries(archive?.fields || {})
    .filter((entry): entry is [string, string] => typeof entry[1] === 'string' && !!entry[1].trim()), [archive]);
  const source = officialUrl(archive?.sourceUrl);
  return <section className="country-factbook" aria-label={(countryName || code) + ' World Factbook archive'}>
    <header className="cf-head">
      <div><span className="cf-kicker"><BookOpen size={14}/> COUNTRY REFERENCE / SOURCE-PINNED ARCHIVE</span>
        <h2>{countryName || code} · World Factbook</h2>
        <p>All available archived country fields in one place. The CIA's final January 2026 archive is historical, not real-time intelligence.</p>
      </div>
      <span className="cf-status">HISTORICAL · 2026</span>
    </header>
    {error || archive?.status === 'archive_unavailable'
      ? <div className="cf-alert" role="status">Archived source unavailable. No estimated values substituted. {archive?.reason || ''}
        <button type="button" onClick={() => setRetry(value => value + 1)}><RefreshCcw size={13}/> Retry</button>
      </div>
      : !archive ? <p className="cf-wait">Loading the country archive…</p>
      : archive.status !== 'available' ? <p className="cf-wait">No verified archive profile for this country.</p>
      : <>
        <div className="cf-overview" aria-label="Selected historical country facts">
          {(['population','area','government','resources'] as const).map(key => {
            const value = entries.find(([name]) => name === key)?.[1];
            return <div key={key}><span>{title(key)}</span><strong>{value || 'Not recorded'}</strong></div>;
          })}
        </div>
        <div className="cf-field-heading"><strong>Complete available Factbook record</strong><span>{entries.length} populated fields · select to expand</span></div>
        <div className="cf-fields">
          {entries.map(([key, value], index) => <details key={key} open={index < 2}>
            <summary>{title(key)}<span>View source text</span></summary>
            <p>{value}</p>
          </details>)}
          {!entries.length && <p className="cf-wait">No archived fields in this response. Missing data is not inferred.</p>}
        </div>
        <footer className="cf-provenance">
          <ShieldCheck size={17}/>
          <div><strong>Archive provenance</strong>
            <small>As of {archive.asOf || 'unreported'} · GEC {archive.gec || 'unreported'} · Revision {archive.sourceRevision || 'unreported'} · SHA-256 {archive.sha256 || 'unreported'}</small>
            {archive.warning && <small>{archive.warning}</small>}
            {source ? <a href={source} target="_blank" rel="noopener noreferrer">Original pinned country record <ExternalLink size={13}/></a> : <small>Original source URL unavailable</small>}
          </div>
        </footer>
      </>}
  </section>;
}
