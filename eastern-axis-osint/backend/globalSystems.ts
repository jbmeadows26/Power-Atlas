import { db } from '@appdeploy/sdk';

/*
 * Country-system observations from the World Bank's official free Indicators API.
 * One response per country (or WLD global aggregate), source 2 (WDI).
 * This is not an intelligence-attribution engine and never manufactures missing data.
 */
export type SystemIndicator = {
  code: string;
  label: string;
  unit: 'percent' | 'usd' | 'index' | 'years' | 'people' | 'tonnes';
  category: 'Economy' | 'Energy & resources' | 'Trade & finance' | 'People & climate';
  meaning: string;
};

export const systemIndicators: SystemIndicator[] = [
  { code: 'NY.GDP.MKTP.KD.ZG', label: 'GDP growth', unit: 'percent', category: 'Economy', meaning: 'Real annual economic growth, not a forecast.' },
  { code: 'FP.CPI.TOTL.ZG', label: 'Consumer price inflation', unit: 'percent', category: 'Economy', meaning: 'Annual consumer-price change; different from an item-level cost-of-living index.' },
  { code: 'SL.UEM.TOTL.ZS', label: 'Unemployment', unit: 'percent', category: 'Economy', meaning: 'ILO-modelled estimate of unemployment as a share of the labor force.' },
  { code: 'EG.ELC.ACCS.ZS', label: 'Electricity access', unit: 'percent', category: 'Energy & resources', meaning: 'Share of people with access to electricity.' },
  { code: 'EG.FEC.RNEW.ZS', label: 'Renewable energy consumption', unit: 'percent', category: 'Energy & resources', meaning: 'Renewable share of total final energy consumption.' },
  { code: 'EG.IMP.CONS.ZS', label: 'Net energy imports', unit: 'percent', category: 'Energy & resources', meaning: 'Net imports as a share of energy use. Negative values indicate a net exporter.' },
  { code: 'NY.GDP.TOTL.RT.ZS', label: 'Natural-resource rents', unit: 'percent', category: 'Energy & resources', meaning: 'Estimated natural-resource rents as a share of GDP. Does not identify ownership.' },
  { code: 'NE.TRD.GNFS.ZS', label: 'Trade openness', unit: 'percent', category: 'Trade & finance', meaning: 'Total exports plus imports of goods and services divided by GDP.' },
  { code: 'BX.KLT.DINV.WD.GD.ZS', label: 'FDI net inflows', unit: 'percent', category: 'Trade & finance', meaning: 'Net foreign direct investment inflows as a share of GDP.' },
  { code: 'SI.POV.GINI', label: 'Income inequality (Gini)', unit: 'index', category: 'People & climate', meaning: 'Survey-derived inequality index; coverage and reference years vary.' },
  { code: 'SP.DYN.LE00.IN', label: 'Life expectancy', unit: 'years', category: 'People & climate', meaning: 'Life expectancy at birth, not a prediction for any one person.' },
  { code: 'EN.ATM.CO2E.PC', label: 'CO₂ emissions per person', unit: 'tonnes', category: 'People & climate', meaning: 'Historical annual territorial CO₂ emissions, tonnes per person.' },
];

type WorldBankRow = {
  indicator?: { id?: string };
  country?: { id?: string };
  value?: number | null;
  date?: string;
  obs_status?: string;
};
type Observation = SystemIndicator & {
  value: number | null;
  year: string | null;
  observationStatus: string | null;
  sourceUrl: string;
};

type SavedObservation = {
  code: string;
  value: number;
  year: string;
  observationStatus: string | null;
};
type SavedSystem = {
  id: string;
  fetchedAt: string;
  observations: SavedObservation[];
};

function overlaySaved(target: Observation[], saved: SavedSystem | null) {
  if (!saved) return;
  for (const prev of saved.observations) {
    const current = target.find(item => item.code === prev.code);
    if (!current || typeof prev.value !== 'number' || !Number.isFinite(prev.value)) continue;
    if (current.year && Number(current.year) >= Number(prev.year)) continue;
    current.value = prev.value;
    current.year = prev.year;
    current.observationStatus = prev.observationStatus;
  }
}
function validCode(raw: unknown): string | null {
  const code = typeof raw === 'string' ? raw.toUpperCase() : '';
  return /^[A-Z]{2}$/.test(code) || code === 'WLD' ? code : null;
}

export async function readGlobalSystems(raw: unknown) {
  const code = validCode(raw);
  if (!code) return null;
  const indicators = systemIndicators.map(indicator => ({
    ...indicator,
    value: null,
    year: null,
    observationStatus: null,
    sourceUrl: 'https://data.worldbank.org/indicator/' + indicator.code + '?locations=' + code,
  })) as Observation[];
  const recordId = 'country-' + code;
  let cached: SavedSystem | null = null;
  try {
    [cached] = await db.get<SavedSystem>('global_system_snapshots', [recordId], { consistent: true });
  } catch {
    // Public API fetch continues if the optional cache is unavailable.
  }
  const cachedCount = cached?.observations.length || 0;
  const cachedAge = cached ? Date.now() - Date.parse(cached.fetchedAt) : Infinity;
  if (cached && cachedCount >= 7 && cachedAge >= 0 && cachedAge < 8 * 60 * 1000) {
    overlaySaved(indicators, cached);
    return {
      code, checkedAt: cached.fetchedAt, status: cachedCount === systemIndicators.length ? 'complete' : 'partial',
      covered: cachedCount, requested: indicators.length, indicators,
      source: 'World Bank World Development Indicators (source 2)', sourceUrl: 'https://data.worldbank.org/',
      method: 'Saved official observations, identified by source year. No interpolation, projections or causal attribution.',
      warning: 'Cached official observations last retrieved ' + cached.fetchedAt + '; no new upstream check was needed.',
    };
  }
  // The World Bank multi-indicator mrnev endpoint can time out even when
  // the same indicators work as bounded date-range queries. Use three
  // independently settled, paginated-safe subsets instead of one fragile call.
  const codeGroups: string[][] = [];
  for (let i = 0; i < systemIndicators.length; i += 4) {
    codeGroups.push(systemIndicators.slice(i, i + 4).map(item => item.code));
  }
  const requests = codeGroups.map(async group => {
    const url = 'https://api.worldbank.org/v2/country/' + code +
      '/indicator/' + group.join(';') +
      '?source=2&format=json&date=2000:2026&per_page=200';
    const response = await fetch(url, {
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(16000),
    });
    if (!response.ok) throw new Error('World Bank HTTP ' + response.status);
    const data: unknown = await response.json();
    if (!Array.isArray(data) || !Array.isArray(data[1])) {
      throw new Error('World Bank returned an unexpected response');
    }
    return data[1] as WorldBankRow[];
  });
  const outcomes = await Promise.allSettled(requests);
  let successes = 0;
  let failures = 0;
  for (const result of outcomes) {
    if (result.status === 'rejected') {
      failures++;
      continue;
    }
    successes++;
    for (const row of result.value) {
      const match = indicators.find(item => item.code === row.indicator?.id);
      if (!match || typeof row.value !== 'number' || !Number.isFinite(row.value)) continue;
      if (match.year && Number(match.year) >= Number(row.date || '0')) continue;
      match.value = row.value;
      match.year = row.date || null;
      match.observationStatus = row.obs_status || null;
    }
  }
  // Any failed chunk gets an independent small request per indicator. Failed
  // groups must not silently erase economic observations from healthy groups.
  const missingCodes = outcomes.flatMap((result, index) =>
    result.status === 'rejected' ? codeGroups[index] : []
  );
  if (missingCodes.length) {
    const individually = await Promise.allSettled(missingCodes.map(async indicator => {
      const url = 'https://api.worldbank.org/v2/country/' + code +
        '/indicator/' + indicator + '?format=json&mrnev=1';
      const response = await fetch(url, {
        headers: { Accept: 'application/json' },
        signal: AbortSignal.timeout(10500),
      });
      if (!response.ok) throw new Error('World Bank HTTP ' + response.status);
      const data: unknown = await response.json();
      if (!Array.isArray(data) || !Array.isArray(data[1])) throw new Error('Invalid single-indicator response');
      return data[1] as WorldBankRow[];
    }));
    for (const result of individually) {
      if (result.status !== 'fulfilled') continue;
      successes++;
      for (const row of result.value) {
        const match = indicators.find(item => item.code === row.indicator?.id);
        if (!match || typeof row.value !== 'number' || !Number.isFinite(row.value)) continue;
        if (match.year && Number(match.year) >= Number(row.date || '0')) continue;
        match.value = row.value;
        match.year = row.date || null;
        match.observationStatus = row.obs_status || null;
      }
    }
  }

  // Reuse previously observed official values if one requested data subset
  // goes offline. A later observation year always wins; no value is fabricated.
  overlaySaved(indicators, cached);
  let observed = indicators.filter(item => item.value !== null);
  if (successes && observed.length) {
    try {
      const [latest] = await db.get<SavedSystem>('global_system_snapshots', [recordId], { consistent: true });
      overlaySaved(indicators, latest);
      observed = indicators.filter(item => item.value !== null);
      const snapshot: SavedSystem = {
        id: recordId,
        fetchedAt: new Date().toISOString(),
        observations: observed.map(item => ({
          code: item.code,
          value: item.value as number,
          year: item.year || '',
          observationStatus: item.observationStatus,
        })),
      };
      await db.tx.update('global_system_snapshots', [{ id: recordId, record: snapshot }]);
    } catch {
      // A database issue never changes the official numeric observations.
    }
  }
  const reported = indicators.filter(item => item.value !== null).length;
  const sourceStatus: 'ok' | 'unavailable' = successes > 0 || reported > 0 ? 'ok' : 'unavailable';
  const warning = !successes && reported > 0    ? 'Live World Bank queries failed. Displaying previously captured official observations with their original years; freshness is uncertain.'
    : sourceStatus === 'unavailable'
      ? 'World Bank API requests failed; no observations or estimates have been substituted.'
      : failures > 0
        ? 'Some World Bank indicator groups failed; individual retries and prior official observations were used where available.'
        : reported < indicators.length
          ? 'Some series have no reported observation in the requested historical period.'
          : null;
  return {
    code,
    checkedAt: new Date().toISOString(),
    status: sourceStatus === 'unavailable' ? 'unavailable' : reported === indicators.length ? 'complete' : 'partial',
    covered: reported,
    requested: indicators.length,
    indicators,
    source: 'World Bank World Development Indicators (source 2)',
    sourceUrl: 'https://data.worldbank.org/',
    method: 'Most recent non-null reported observation for each indicator, not necessarily the same year. No interpolation, projections or causal attribution.',
    warning: warning || (reported < indicators.length ? 'Some indicators have no reported observation in this source.' : null),
  };
}
