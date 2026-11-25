import { useEffect, useState } from 'react';
import { api } from '@appdeploy/client';
import { Activity, AlertCircle, ArrowUpRight, BarChart3, CheckCircle2, CircleHelp, Database, Globe2, Layers3, RefreshCcw, ShieldCheck } from 'lucide-react';
import './globalSystems.css';
import EnergySupply from './EnergySupply';

type Mode = 'systems' | 'risk' | 'coverage';
type Case = { id: string; code: string; title: string; date: string; topic: string; status: string; source: string; agency: string };
type Indicator = {
  code: string; label: string; category: string; unit: string; meaning: string;
  value: number | null; year: string | null; observationStatus: string | null; sourceUrl: string; sourceName?: string;
};
type GlobalData = {
  code: string; checkedAt: string; status: string; covered: number; requested: number;
  indicators: Indicator[]; warning: string | null; source: string; sourceUrl: string; method: string;
};
type Props = { mode: Mode; countryCode: string; cases: Case[]; countryName?: string; groupFilter?: string };

const groups = [
  { label: 'Energy & resources', text: 'Exposure to energy and resource systems. National totals do not identify beneficiaries or ownership.' },
  { label: 'Trade & finance', text: 'Cross-border dependence and investment context, not proof of illicit flows.' },
  { label: 'Economy', text: 'Economic conditions that can magnify disruptions and affect households.' },
  { label: 'People & climate', text: 'Population, inequality and emissions. Source definitions and reporting years may differ; WID pre-tax Gini is not survey Gini.' },
];

type Gap = { area: string; label: string; status: 'live' | 'partial' | 'reference' | 'not connected'; detail: string };
const gaps: Gap[] = [
  { area: 'Intelligence & law', label: 'DOJ national-security releases', status: 'partial', detail: 'Scheduled headline-scoped recent intake; no systematic docket/disposition tracking' },
  { area: 'Intelligence & law', label: 'OFAC SDN sanctions', status: 'partial', detail: 'Official full-file count and selected sample; no complete person/entity graph or non-SDN ingestion' },
  { area: 'Intelligence & law', label: 'DOJ FARA active registrations', status: 'partial', detail: 'Active registrant index, not full principals, payments, filings and registration histories' },
  { area: 'Intelligence & law', label: 'CISA exploited-vulnerability catalog', status: 'partial', detail: 'KEV vulnerability entries, not actor or government attribution' },
  { area: 'Intelligence & law', label: 'Allied intelligence assessments', status: 'reference', detail: 'Curated US, NATO, Canada, EU, Australia and Japan extracts, not automatic full-document indexing' },
  { area: 'Intelligence & law', label: 'UK, EU, Canada and Australia sanctions', status: 'partial', detail: 'The current UK FCDO and Canada official lists now have snapshot collectors (UK scheduled; Canada verified). EU and Australia are still reference links. Cross-jurisdiction identity matching remains unimplemented.' },
  { area: 'Intelligence & law', label: 'Corporate, officer and beneficial-owner registries', status: 'not connected', detail: 'No validated international ownership graph' },
  { area: 'Intelligence & law', label: 'Historical prosecutions and court outcomes', status: 'not connected', detail: 'Curated examples only; no docket monitoring or structured disposition verification' },
  { area: 'Intelligence & law', label: 'Declassified intelligence and FOIA', status: 'reference', detail: 'Discovery references only; no archival corpus and no source-document capture' },
  { area: 'Intelligence & law', label: 'Foreign influence and transnational repression', status: 'partial', detail: 'Selected DOJ cases and allied reports; no systematic global case registry' },
  { area: 'Defense & risk', label: 'Documented conflicts and operations', status: 'partial', detail: 'Nine curated contextual records; not a worldwide conflict-event feed' },
  { area: 'Defense & risk', label: 'Military assets, forces and readiness', status: 'partial', detail: 'Nine public capability/inventory entries; estimates are not real-time' },
  { area: 'Defense & risk', label: 'Allied military-report monitoring', status: 'partial', detail: 'Three official metadata feeds; bounded monitoring only' },
  { area: 'Defense & risk', label: 'Proxies, arms transfers and defense procurement', status: 'reference', detail: 'SIPRI and agency links; no normalized actor-to-transfer analysis' },
  { area: 'Defense & risk', label: 'Nuclear, cyber and space capabilities', status: 'reference', detail: 'Selected public assessments; no comprehensive historical time series' },
  { area: 'Defense & risk', label: 'Predictive global flashpoints', status: 'not connected', detail: 'Evidence-led pressure indicators available; a validated forecasting model is not' },
  { area: 'Economy & power', label: 'World Bank social, energy and economy indicators', status: 'partial', detail: 'Twelve source-dated series; incomplete World Bank group responses now retried by indicator and explicitly labeled OWID/GCB/PIP/WID fallbacks for inequality and CO₂. Country-level completeness must be audited.' },
  { area: 'Economy & power', label: 'Oil, gas and power generation flows', status: 'partial', detail: 'OWID 2026 physical oil/gas/coal production and electricity data are ingested for 220 countries; bilateral trade flows, pipelines and freight links remain absent.' },
  { area: 'Economy & power', label: 'Critical mineral extraction, processing and ownership', status: 'not connected', detail: 'No validated mine, processor or beneficial-owner records' },
  { area: 'Economy & power', label: 'Trade flows and logistics chokepoints', status: 'partial', detail: 'PortWatch short-window vessel traffic is now displayed in Supply chain; UN Comtrade U.S.-reported partner/commodity import comparisons are available on demand; full trade matrix and freight-price history remain unavailable' },
  { area: 'Economy & power', label: 'Export controls, evasion and dual-use technologies', status: 'not connected', detail: 'No verified case-to-license or entity-to-transaction joins' },
  { area: 'Economy & power', label: 'Global political money and corporate influence', status: 'not connected', detail: 'Power Atlas international investigation models require distinct legal-source ingestion' },
  { area: 'Economy & power', label: 'Household impact and affordability', status: 'partial', detail: 'Macroeconomic proxies now visible; local price, welfare and causation joins absent' },
  { area: 'Evidence & operations', label: 'Reference fingerprints and bounded WARC', status: 'partial', detail: 'Capture after collector runs, no immutable object-lock guarantee' },
  { area: 'Evidence & operations', label: 'Independent corroboration and graded credibility', status: 'not connected', detail: 'De-duplication exists; analyst reliability/credibility ratings not assessed' },
  { area: 'Evidence & operations', label: 'Verified entity and attribution graph', status: 'not connected', detail: 'Only direct record-to-source links; no analyst-approved actor matches' },
  { area: 'Evidence & operations', label: 'Analyst verification and dispute workflow', status: 'partial', detail: 'Private browser-based dual-grading and research-memo worksheet added. Server-side authenticated reviewer authorization, publication approvals and dispute resolution remain unimplemented.' },
  { area: 'Evidence & operations', label: 'Historical backfill and completeness', status: 'partial', detail: 'Legacy curated case examples consolidated, but historical collector records not backfilled' },
  { area: 'Evidence & operations', label: 'Persistent country selection and alliance map', status: 'live', detail: 'Global header scope persists; blue treaty allies, red selected strategic adversaries, neutral other' },
  { area: 'Intelligence & law', label: 'Foreign-government actor attribution and identity disambiguation', status: 'not connected', detail: 'No independently reviewed identity merges or government-direction findings derived from unreviewed headlines' },
  { area: 'Intelligence & law', label: 'Country-level election and political-finance investigations', status: 'reference', detail: 'Some curated interference cases; no historical campaign-financing and cross-border money network' },
  { area: 'Defense & risk', label: 'Public military base and force-posture records', status: 'not connected', detail: 'No historical, sourced installation and publicly reported deployment catalog' },
  { area: 'Defense & risk', label: 'Humanitarian displacement and conflict consequences', status: 'not connected', detail: 'UN humanitarian country datasets are not normalized or joined to conflict records' },
  { area: 'Defense & risk', label: 'Strategic infrastructure and telecommunications resilience', status: 'reference', detail: 'Cyber and outage portals linked; no independently sourced critical-infrastructure dependency graph' },
  { area: 'Economy & power', label: 'Maritime freight, ports and navigation chokepoints', status: 'partial', detail: 'IMF PortWatch AIS daily chokepoint observations are now queried on demand in Supply chain; port economics, freight rates and causal event joins remain unconnected' },
  { area: 'Economy & power', label: 'Energy ownership and state-company relationships', status: 'partial', detail: 'UK FCDO-listed organizations may provide explicit parent-company fields, but those are not independently established beneficial ownership or connected to energy-operator registries.' },
  { area: 'Evidence & operations', label: 'Original document and filing preservation', status: 'partial', detail: 'Raw bounded API WARC captures exist, but linked documents, exhibits and PDFs are not automatically archived' },
  { area: 'Evidence & operations', label: 'Priority Intelligence Requirements and collection cycle', status: 'not connected', detail: 'No structured PIR assignment, requirements coverage, expiry or analytic production tracking' },
  { area: 'Evidence & operations', label: 'Source check freshness and missing-data alerts', status: 'partial', detail: 'Scheduler health is visible; end-to-end freshness, schema and source-coverage SLOs require validation' },
];
const signalDefinitions = [
  { code: 'FP.CPI.TOTL.ZG', threshold: 8, title: 'Price pressure', why: 'High annual inflation can strain household budgets and supply costs.' },
  { code: 'SL.UEM.TOTL.ZS', threshold: 10, title: 'Labor-market strain', why: 'A higher unemployment share can indicate economic vulnerability.' },
  { code: 'NY.GDP.TOTL.RT.ZS', threshold: 20, title: 'Resource-rent dependence', why: 'A larger resource-rent share can increase exposure to commodity cycles.' },
  { code: 'EG.IMP.CONS.ZS', threshold: 50, title: 'Net energy-import exposure', why: 'A high import share may increase sensitivity to external energy supply.' },
  { code: 'NE.TRD.GNFS.ZS', threshold: 100, title: 'Trade-system exposure', why: 'High cross-border trade share creates many channels for outside shocks, alongside economic benefits.' },
];
const icons: Record<string, typeof Globe2> = {
  'Energy & resources': Layers3,
  'Trade & finance': Globe2,
  Economy: BarChart3,
  'People & climate': Activity,
};
const number = (x: number, unit: string) => {
  if (unit === 'years' || unit === 'tonnes' || unit === 'index') return x.toLocaleString('en-US', { maximumFractionDigits: 2 }) + (unit === 'tonnes' ? ' t' : unit === 'years' ? ' yr' : '');
  if (unit === 'usd') return '$' + new Intl.NumberFormat('en-US', { notation: 'compact' }).format(x);
  if (unit === 'people') return new Intl.NumberFormat('en-US', { notation: 'compact' }).format(x);
  return x.toLocaleString('en-US', { maximumFractionDigits: 1 }) + '%';
};
export default function GlobalSystems({ mode, countryCode, countryName, groupFilter }: Props) {
  const code = countryCode === 'all' ? 'WLD' : countryCode;
  const [data, setData] = useState<GlobalData | null>(null);
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState(false);
  const [retry, setRetry] = useState(0);
  const [filter, setFilter] = useState('All');
  const [showCoverageDetails,setShowCoverageDetails]=useState(false);
  useEffect(() => {
    if (mode === 'coverage') return;
    let active = true;
    setPending(true);
    setFailure(false);
    setData(null);
    api.get('/api/global-systems/' + code)
      .then(res => { if (active) setData(res.data as GlobalData); })
      .catch(() => { if (active) setFailure(true); })
      .finally(() => { if (active) setPending(false); });
    return () => { active = false; };
  }, [code, mode, retry]);

  const target = countryCode === 'all' ? 'World aggregate' : (countryName || countryCode);

  if (mode === 'coverage') {
    const shown = filter === 'All' ? gaps : gaps.filter(g => g.area === filter);
    return <section className="gs-root">
      <div className="gs-eyebrow"><Database size={15}/> SOURCE COVERAGE / KNOWN LIMITATIONS</div>
      <h1>What we know. What we lack.</h1>
      <p className="gs-lead">A global implementation inventory—not a claim of worldwide coverage and not filtered by the selected country. Source links and manually curated references are separate from machine-readable data integrations.</p>
      <div className="gs-summary"><div><strong>{gaps.length}</strong><span>Tracked capabilities</span></div><div><strong>{gaps.filter(g=>g.status==='live').length}</strong><span>Implemented on-demand</span></div><div><strong>{gaps.filter(g=>g.status!=='live').length}</strong><span>Still partial or absent</span></div></div>
      <div className="gs-coverage-evidence"><div><strong>Individual coverage and integration status</strong><span>All tracked source gaps and methodology, available on request.</span></div><button type="button" aria-expanded={showCoverageDetails} onClick={()=>setShowCoverageDetails(v=>!v)}>{showCoverageDetails?'Hide technical records':'View technical records'} <ArrowUpRight size={13}/></button></div>
      {showCoverageDetails&&<>
      <div className="gs-filterbar" aria-label="Coverage area">
        {['All', ...Array.from(new Set(gaps.map(g => g.area)))].map(label => <button type="button" className={label === filter ? 'active' : ''} onClick={() => setFilter(label)} key={label}>{label}</button>)}
      </div>
      <div className="gs-gap-list">{shown.map(g => <div className="gs-gap" key={g.label}><div><strong>{g.label}</strong><p>{g.detail}</p></div><span className={'gs-status gs-'+g.status.replace(' ','-')}>{g.status}</span></div>)}</div>
      </>}
      <p className="gs-foot">Status is based on implemented source code and the current public app. It is not a guarantee that any external feed is available at this moment. Historical case outcomes require separate follow-up research.</p>
    </section>;
  }

  const observed = data?.indicators || [];
  const scoped = groupFilter ? observed.filter(item=>item.category===groupFilter) : observed;
  const requested = groupFilter ? (({ "Energy & resources":4,"Trade & finance":2,Economy:3,"People & climate":3 } as Record<string,number>)[groupFilter] ?? scoped.length) : (data?.requested ?? 12);
  const covered = scoped.filter(item=>typeof item.value==='number'&&Number.isFinite(item.value)).length;
  const checked = data?.checkedAt && Number.isFinite(Date.parse(data.checkedAt)) ? new Date(data.checkedAt).toLocaleString('en-US',{dateStyle:'medium',timeStyle:'short',timeZone:'UTC'})+' UTC' : null;
  const warning = data?.warning?.replace(/^WDI cached observations retrieved [^;]+; recheck for fresh values\.\s*/,'Cached observations; recheck to request newer data. ');
  return <section className="gs-root">
    <div className="gs-eyebrow"><Globe2 size={15}/> {mode === 'risk' ? 'EVIDENCE-BOUND RISK WATCH' : groupFilter ? 'SOURCE-DATED INDICATORS' : 'INTERNATIONAL POWER & RESOURCES'}</div>
    <h1>{mode === 'risk' ? 'Pressure points. Not predictions.' : groupFilter || 'The systems behind global power.'}</h1>
    <p className="gs-lead">{mode === 'risk'
      ? 'Track observed economic, energy and societal pressures. These screening thresholds are disclosed rules, not geopolitical threat ratings or forecasts.'
      : groupFilter ? 'Reported observations for ' + target + '. Each figure includes its source and year.' : 'Explore economic forces, energy dependence, resources and trade for ' + target + '. Each reported figure remains tied to its originating dataset and year.'}</p>
    <div className="gs-context"><div><Globe2 size={18}/><strong>{target}</strong><span>{data ? covered + ' of ' + requested + ' indicator series available' : pending ? 'Requesting indicators' : 'Coverage not yet verified'}</span>{checked&&<small className="gs-checked" title={data?.checkedAt}>Retrieved {checked}</small>}</div><button onClick={() => setRetry(v => v + 1)} disabled={pending}><RefreshCcw size={15}/> Recheck</button></div>
    {pending && <div className="gs-notice"><Activity size={18}/> Requesting official indicator observations…</div>}
    {(failure || data?.status === 'unavailable') && <div className="gs-notice gs-error"><AlertCircle size={18}/> The World Bank response is unavailable. No figures have been substituted. Retry or inspect the original source.</div>}
    {mode === 'systems' && <div className="gs-groups">{groups.filter(group=>!groupFilter||group.label===groupFilter).map(group => {
      const GroupIcon = icons[group.label] || Globe2;
      const items = observed.filter(indicator => indicator.category === group.label);
      return <section className="gs-group" key={group.label}>
        <div className="gs-group-top"><GroupIcon size={19}/><div><h2>{group.label} <span className="gs-group-count">{items.filter(item=>typeof item.value==='number'&&Number.isFinite(item.value)).length}/{groupFilter?requested:items.length} available</span></h2><p>{group.text}</p></div></div>
        {!items.length&&<p className="gs-empty">{pending?'Loading source observations…':'No verified observations available for this group.'}</p>}
        <div className="gs-metric-grid">{items.map(item => <article className="gs-metric" key={item.code}>
          <div className="gs-metric-head"><strong>{item.label}</strong><a href={item.sourceUrl} target="_blank" rel="noopener noreferrer" aria-label={'View original source for '+item.label}><ArrowUpRight size={15}/></a></div>
          <div className="gs-value">{item.value === null ? 'Not reported' : number(item.value, item.unit)}</div>
          <small>{item.year ? 'Reported ' + item.year + (Number(item.year) < 2021 ? ' · historic' : '') : 'No verified observation'}</small>
          {item.value!==null&&item.sourceName&&<div className="gs-metric-source"><span>Alternate measure / source</span><a href={item.sourceUrl} target="_blank" rel="noopener noreferrer">{item.sourceName} <ArrowUpRight size={11}/></a></div>}
          {item.value !== null && item.unit === 'percent' && <div className="gs-meter"><span style={{width:Math.max(0,Math.min(100,item.value))+'%'}}/></div>}
          <p>{item.meaning}</p>
        </article>)}</div>
      </section>;
    })}</div>}
    {warning && data?.status !== 'unavailable' && <div className="gs-notice"><CircleHelp size={18}/>{warning}</div>}
    {mode === 'systems' && <div className="gs-source-alternatives"><strong>Additional original datasets</strong><span>Values in these sources have different survey populations, measures or reporting years; they are not interchangeable without source labels.</span><div><a href="https://pip.worldbank.org/" target="_blank" rel="noopener noreferrer">World Bank PIP</a><a href="https://wid.world/" target="_blank" rel="noopener noreferrer">World Inequality Database</a><a href="https://www.wider.unu.edu/database/world-income-inequality-database-wiid" target="_blank" rel="noopener noreferrer">UNU-WIDER WIID</a><a href="https://www.oecd.org/en/data/datasets/income-and-wealth-distribution-database.html" target="_blank" rel="noopener noreferrer">OECD Income & Wealth Distribution</a><a href="https://ourworldindata.org/co2-and-greenhouse-gas-emissions" target="_blank" rel="noopener noreferrer">OWID CO₂</a><a href="https://edgar.jrc.ec.europa.eu/" target="_blank" rel="noopener noreferrer">EU EDGAR</a></div></div>}
    {mode === 'systems' && (!groupFilter || groupFilter==='Energy & resources') && <EnergySupply code={code==='WLD'?'all':code} />}
    {mode === 'risk' && <div className="gs-signal-grid">{signalDefinitions.map(signal => {
      const observation = observed.find(item => item.code === signal.code);
      const available = typeof observation?.value === 'number';
      const exceeds = available && observation!.value! > signal.threshold;
      return <article className="gs-signal" key={signal.code}>
        <div className="gs-signal-top"><Activity size={17}/><span>{available ? exceeds ? 'ABOVE SCREENING THRESHOLD' : 'AT / BELOW THRESHOLD' : 'INSUFFICIENT DATA'}</span></div>
        <h2>{signal.title}</h2>
        <div className="gs-signal-number">{available ? number(observation!.value!, 'percent') : '—'}<small>Screen: {signal.threshold}%</small></div>
        <p>{signal.why}</p>
        <small>{observation?.year ? 'Observation year ' + observation.year + ' · ' : 'No observation · '}threshold is illustrative, not predictive</small>
        {observation && <a href={observation.sourceUrl} target="_blank" rel="noopener noreferrer">Underlying dataset <ArrowUpRight size={13}/></a>}
      </article>;
    })}</div>}
    {mode === 'risk' && <div className="gs-interpretation"><ShieldCheck size={21}/><div><strong>What this screening cannot establish</strong><p>There is no validated escalation probability, event forecast, individual culpability, or proven causal link between one indicator and a military event. A higher trade share can reflect economic integration, not necessarily fragility. Compare dates and multiple independent sources before reaching a conclusion.</p></div></div>}
    <p className="gs-foot"><CheckCircle2 size={15}/> {data?.method || 'All observations require an official source response.'} World aggregates are not country averages and do not establish bilateral transactions. <a href="https://datahelpdesk.worldbank.org/knowledgebase/articles/1886674-new-features-and-enhancements-in-the-v2-api" target="_blank" rel="noopener noreferrer">Methodology <ArrowUpRight size={12}/></a></p>
  </section>;
}
