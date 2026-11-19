/**
 * Public-facing treaty context is deliberately separate from U.S. treaty-ally
 * flags used by the existing world map. Verified links below are per-category
 * evidence anchors, not a claim that every global defense agreement is indexed.
 * Review classification periodically; status as of 2026-11-18.
 */
export type SecurityContext = {
  relationship: string;
  securityNote: string;
  usRelationship: string;
  securitySources: { label: string; url: string }[];
};
type CountryLike = {
  code: string;
  relationship: string;
  isTreatyAlly: boolean;
  isMNNA: boolean;
};
const CSTO_URL = 'https://en.odkb-csto.org/25years/';
const RUSSIA_DPRK_URL = 'https://www.everycrsreport.com/reports/IF12760.html';
const CHINA_DPRK_URL = 'https://www.everycrsreport.com/reports/R49319.html';
const CHINA_RUSSIA_URL = 'https://www.everycrsreport.com/reports/R48977.html';
const NATO_URL = 'https://www.nato.int/en/about-us/organization/nato-member-countries';
const DSCA_URL = 'https://samm.dsca.mil/glossary/major-non-nato-allies';
const CSTO = new Set(['RU', 'BY', 'KZ', 'KG', 'TJ', 'AM']);
const ref = (label: string, url: string) => ({label, url});
const INDO_PACIFIC_TREATY_EVIDENCE: Record<string,{label:string;url:string}> = {
  AU: ref('ANZUS security treaty (Australia DFAT)', 'https://www.dfat.gov.au/geo/united-states-of-america/united-states-of-america-country-brief'),
  JP: ref('Japan–U.S. security treaty (Japan MOD)', 'https://www.mod.go.jp/en/j-us-alliance/joint-declaration/treaty/index.html'),
  KR: ref('U.S.–ROK alliance (U.S. State Dept)', 'https://2021-2025.state.gov/u-s-security-cooperation-with-korea/'),
  PH: ref('U.S.–Philippines mutual defense treaty (U.S. State Dept)', 'https://2021-2025.state.gov/u-s-security-cooperation-with-the-philippines/'),
  TH: ref('U.S. collective defense arrangements (CRS)', 'https://www.everycrsreport.com/reports/R40614.html'),
};
export function securityContext(c: CountryLike): SecurityContext {
  const usRelationship = c.isTreatyAlly
    ? c.relationship
    : c.isMNNA
      ? 'U.S. major non-NATO ally designation; not itself a mutual-defense treaty'
      : 'No U.S. NATO / primary Indo-Pacific treaty designation in this index';
  if (c.code === 'RU') return {
    relationship: 'CSTO collective defense · Russia–DPRK mutual assistance (2024)',
    securityNote: 'CSTO member. The Russia–North Korea treaty has a military-assistance clause. Russia–China is a strategic partnership, not a bilateral mutual-defense alliance.',
    usRelationship,
    securitySources: [ref('CSTO treaty history (official)',CSTO_URL),ref('Russia–DPRK treaty (CRS)',RUSSIA_DPRK_URL),ref('Russia–China military partnership (CRS 2026)',CHINA_RUSSIA_URL)],
  };
  if (c.code === 'CN') return {
    relationship: 'China–DPRK mutual-assistance treaty (1961)',
    securityNote: 'Mutual-defense commitment with North Korea. China–Russia maintains a strategic partnership; it is not a mutual-defense alliance.',
    usRelationship,
    securitySources: [ref('China–DPRK 1961 alliance (CRS 2026)',CHINA_DPRK_URL),ref('Russia–China military partnership (CRS 2026)',CHINA_RUSSIA_URL)],
  };
  if (c.code === 'KP') return {
    relationship: 'China–DPRK treaty (1961) · Russia–DPRK treaty (2024)',
    securityNote: 'Two distinct bilateral mutual-assistance commitments; the terms and triggering conditions differ.',
    usRelationship,
    securitySources: [ref('China–DPRK 1961 alliance (CRS 2026)',CHINA_DPRK_URL),ref('Russia–DPRK treaty (CRS)',RUSSIA_DPRK_URL)],
  };
  if (CSTO.has(c.code)) return {
    relationship: c.code === 'AM' ? 'CSTO treaty member — participation frozen' : 'CSTO collective-defense treaty member',
    securityNote: c.code === 'AM'
      ? 'Armenia remains formally listed as a CSTO member but has frozen its participation. Formal membership is not equivalent to active operational participation.'
      : 'Formal CSTO collective-security commitments. This classification does not predict military action.',
    usRelationship,
    securitySources: [ref('CSTO charter and members',CSTO_URL)],
  };
  if (c.relationship === 'NATO treaty ally') return {
    relationship: 'NATO collective-defense treaty ally',
    securityNote: 'Member of NATO; Article 5 invokes treaty obligations, not an automatic identical military response from every ally.',
    usRelationship,
    securitySources: [ref('NATO official members',NATO_URL)],
  };
  if (c.isTreatyAlly) return {
    relationship: 'U.S. bilateral / Indo-Pacific defense-treaty ally',
    securityNote: 'A primary U.S. defense-treaty relationship is indexed; other regional treaty arrangements are not exhaustively catalogued.',
    usRelationship,
    securitySources: INDO_PACIFIC_TREATY_EVIDENCE[c.code] ? [INDO_PACIFIC_TREATY_EVIDENCE[c.code]] : [],
  };
  return {
    relationship: c.isMNNA ? 'U.S. major non-NATO ally designation' : 'Defense-treaty coverage not yet fully verified',
    securityNote: c.isMNNA
      ? 'This U.S. statutory designation does not by itself create a mutual-defense obligation. Other country treaties require independent review.'
      : 'Do not interpret missing coverage as absence of a defense treaty, security cooperation, or hostile intent. The global treaty inventory is incomplete.',
    usRelationship,
    securitySources: c.isMNNA ? [ref('DSCA MNNA designation',DSCA_URL)] : [],
  };
}
export function withSecurityContext<T extends CountryLike>(country: T): T & SecurityContext {
  return {...country, ...securityContext(country)};
}
