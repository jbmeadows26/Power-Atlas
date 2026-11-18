import { router, json, error, db } from './runtime-sdk';
import { readIntelligenceDesk, runCollectorCron } from './collector';
import { readEvidenceWorkbench } from './evidence';
import { readWorldSignals } from './worldSignals';
import { readAlliedSanctions, syncUK, syncCanada } from './internationalCoverage';
import { readEnergy, syncEnergy } from './energySupply';
import { readSupplyChain } from './supplyChain';
import {readSupplyMacro,readTradeDependency} from './supplyContext';
import { ARCHIVE_ENTITIES, readFactbook, ARCHIVE_BASELINE, ARCHIVE_REVISION } from './factbook';
import { readGlobalSystems } from './globalSystems';
import { readDefenseIntelligence } from './defenseIntel';
import { checkOfficialReportChanges, readOfficialReportChanges, compareAlliedReports, analyzeSourceChanges } from './militaryMonitor';

export const scheduledMilitaryReportMonitor = checkOfficialReportChanges;

export const scheduledSourceIntake = runCollectorCron;

// Keep the existing five collection schedules. One additional rotating source
// slot checks UK FCDO, Canadian sanctions and OWID energy every ~18 hours each.
export async function scheduledGlobalSources(event:{scheduledTime?:string}) {
  const stamp = Date.parse(event.scheduledTime || new Date().toISOString());
  const slot = Math.floor(stamp / (6 * 3600 * 1000)) % 3;
  const result = slot === 0 ? await syncUK() : slot === 1 ? await syncCanada() : await syncEnergy();
  console.info('Scheduled international source intake', result.source, result.status);
  return { statusCode: 200 };
}

const ISO =
  'AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW'.split(
    ' '
  );
const TERRITORIES = new Set(
  'AI AQ AS AW AX BL BM BQ BV CC CK CW CX EH FK FO GF GG GI GL GP GS GU HK HM IM IO JE KY MF MO MP MQ MS NC NF NU PF PM PN PR RE SH SJ SX TC TF TK UM VG VI WF YT'.split(
    ' '
  )
);
const NATO = new Set(
  'AL BE BG CA HR CZ DK EE FI FR DE GR HU IS IT LV LT LU ME MK NL NO PL PT RO SK SI ES SE TR GB US'.split(
    ' '
  )
);
const DEFENSE = new Set('AU JP KR PH TH'.split(' '));
const MNNA = new Set(
  'AR AU BH BR CO EG IL JP JO KE KW MA NZ PK PH QA KR TH TN TW'.split(' ')
);
const REGION_GROUPS: Record<string, string[]> = {
  Europe: [
    'AD',
    'AL',
    'AT',
    'AX',
    'BA',
    'BE',
    'BG',
    'BY',
    'CH',
    'CY',
    'CZ',
    'DE',
    'DK',
    'EE',
    'ES',
    'FI',
    'FO',
    'FR',
    'GB',
    'GG',
    'GI',
    'GR',
    'HR',
    'HU',
    'IE',
    'IM',
    'IS',
    'IT',
    'JE',
    'LI',
    'LT',
    'LU',
    'LV',
    'MC',
    'MD',
    'ME',
    'MK',
    'MT',
    'NL',
    'NO',
    'PL',
    'PT',
    'RO',
    'RS',
    'RU',
    'SE',
    'SI',
    'SJ',
    'SK',
    'SM',
    'UA',
    'VA',
  ],
  Asia: [
    'AF',
    'AE',
    'AM',
    'AZ',
    'BD',
    'BH',
    'BN',
    'BT',
    'CN',
    'GE',
    'HK',
    'ID',
    'IL',
    'IN',
    'IQ',
    'IR',
    'JO',
    'JP',
    'KG',
    'KH',
    'KP',
    'KR',
    'KW',
    'KZ',
    'LA',
    'LB',
    'LK',
    'MM',
    'MN',
    'MO',
    'MV',
    'MY',
    'NP',
    'OM',
    'PH',
    'PK',
    'PS',
    'QA',
    'SA',
    'SG',
    'SY',
    'TH',
    'TJ',
    'TL',
    'TM',
    'TR',
    'TW',
    'UZ',
    'VN',
    'YE',
  ],
  Africa: [
    'AO',
    'BF',
    'BI',
    'BJ',
    'BW',
    'CD',
    'CF',
    'CG',
    'CI',
    'CM',
    'CV',
    'DJ',
    'DZ',
    'EG',
    'EH',
    'ER',
    'ET',
    'GA',
    'GH',
    'GM',
    'GN',
    'GQ',
    'GW',
    'KE',
    'KM',
    'LR',
    'LS',
    'LY',
    'MA',
    'MG',
    'ML',
    'MR',
    'MU',
    'MW',
    'MZ',
    'NA',
    'NE',
    'NG',
    'RE',
    'RW',
    'SC',
    'SD',
    'SH',
    'SL',
    'SN',
    'SO',
    'SS',
    'ST',
    'SZ',
    'TD',
    'TG',
    'TN',
    'TZ',
    'UG',
    'YT',
    'ZA',
    'ZM',
    'ZW',
  ],
  Americas: [
    'AG',
    'AI',
    'AR',
    'AW',
    'BB',
    'BL',
    'BM',
    'BO',
    'BQ',
    'BR',
    'BS',
    'BZ',
    'CA',
    'CL',
    'CO',
    'CR',
    'CU',
    'CW',
    'DM',
    'DO',
    'EC',
    'FK',
    'GF',
    'GL',
    'GP',
    'GD',
    'GT',
    'GY',
    'HN',
    'HT',
    'JM',
    'KN',
    'KY',
    'LC',
    'MF',
    'MQ',
    'MS',
    'MX',
    'NI',
    'PA',
    'PE',
    'PM',
    'PR',
    'PY',
    'SR',
    'SV',
    'SX',
    'TC',
    'TT',
    'US',
    'UY',
    'VC',
    'VE',
    'VG',
    'VI',
  ],
  Oceania: [
    'AS',
    'AU',
    'CC',
    'CK',
    'CX',
    'FJ',
    'FM',
    'GU',
    'KI',
    'MH',
    'MP',
    'NC',
    'NF',
    'NR',
    'NU',
    'NZ',
    'PF',
    'PG',
    'PN',
    'PW',
    'SB',
    'TK',
    'TO',
    'TV',
    'UM',
    'VU',
    'WF',
    'WS',
  ],
};
const CASES = [
{
    "id": "china-apt31-2024",
    "code": "CN",
    "date": "2024-03-25",
    "title": "APT31 alleged long-running cyber espionage",
    "topic": "Cyber operations",
    "status": "Indictment · allegations at publication",
    "level": "Charges, not a conviction",
    "summary": "DOJ charged seven PRC nationals over alleged intrusions targeting businesses, officials, political figures and critics of China. The indictment allegations are not final judicial findings.",
    "impact": "U.S. businesses, government accounts and political communications",
    "source": "https://www.justice.gov/usao-edny/pr/seven-hackers-associated-chinese-government-charged-computer-intrusions-targeting",
    "agency": "U.S. Department of Justice"
  },
  {
    "id": "russia-gru29155-2024",
    "code": "RU",
    "date": "2024-09-05",
    "title": "GRU Unit 29155 alleged cyber intrusions",
    "topic": "Cyber operations",
    "status": "Indictment · allegations at publication",
    "level": "Charges, not a conviction",
    "summary": "DOJ described alleged hacking of Ukrainian government systems and reconnaissance against NATO-related targets by five Russian GRU officers and an alleged civilian collaborator.",
    "impact": "Ukraine and allied government information systems",
    "source": "https://www.justice.gov/archives/opa/pr/five-russian-gru-officers-and-one-civilian-charged-conspiring-hack-ukrainian-government",
    "agency": "U.S. Department of Justice"
  },
  {
    "id": "iran-2024-election-hack",
    "code": "IR",
    "date": "2024-09-27",
    "title": "IRGC-linked election hack-and-leak charges",
    "topic": "Influence operations",
    "status": "Indictment · allegations at publication",
    "level": "Charges, not a conviction",
    "summary": "DOJ charged three Iranian nationals with an alleged cyber campaign involving account intrusions and attempts to distribute stolen campaign material in the 2024 U.S. election cycle.",
    "impact": "U.S. election information and campaign communications",
    "source": "https://www.justice.gov/archives/opa/pr/three-irgc-cyber-actors-indicted-hack-and-leak-operation-designed-influence-2024-us",
    "agency": "U.S. Department of Justice"
  },
  {
    id: 'russia-doppelganger',
    code: 'RU',
    date: '2024-09-04',
    title: 'Covert media influence: Doppelganger',
    topic: 'Influence operations',
    status: 'Seizure action / affidavit allegations',
    level: 'Official court-linked action',
    summary:
      'DOJ announced the seizure of 32 domains alleged to be used in a Russian government-directed influence campaign. The affidavit describes an operation; its allegations are not a blanket finding of guilt for named parties.',
    impact: 'US voters, information environment',
    source:
      'https://www.justice.gov/archives/opa/pr/justice-department-disrupts-covert-russian-government-sponsored-foreign-malign-influence',
    agency: 'U.S. Department of Justice',
  },
  {
    id: 'china-ai-ip',
    code: 'CN',
    date: '2025-02-04',
    title: 'AI trade-secret theft prosecution',
    topic: 'Economic espionage',
    status: 'Superseding indictment · allegations at publication',
    level: 'Charges, not a conviction',
    summary:
      'A superseding federal indictment charged a former Google engineer with economic espionage and theft of trade secrets involving proprietary AI technology. The cited release describes allegations as of February 2025.',
    impact: 'US technology and proprietary R&D',
    source:
      'https://www.justice.gov/opa/pr/superseding-indictment-charges-chinese-national-relation-alleged-plan-steal-proprietary-ai',
    agency: 'U.S. Department of Justice',
  },
  {
    id: 'iran-cyber',
    code: 'IR',
    date: '2024-04-23',
    title: 'Iran-linked intrusion campaign',
    topic: 'Cyber operations',
    status: 'Indictment · allegations at publication',
    level: 'Charges, not a conviction',
    summary:
      'DOJ unsealed charges against four Iranian nationals over an alleged multi-year campaign targeting U.S. agencies, defense contractors and companies. Government sponsorship and individual culpability must be evaluated from the source documents.',
    impact: 'US agencies and private companies',
    source:
      'https://www.justice.gov/archives/opa/pr/justice-department-charges-four-iranian-nationals-multi-year-cyber-campaign-targeting-us',
    agency: 'U.S. Department of Justice',
  },
  {
    id: 'dprk-remote-workers',
    code: 'KP',
    date: '2026-10-13',
    title: 'Remote IT-worker fraud disruption',
    topic: 'Sanctions evasion',
    status: 'Arrests, indictment and seizures',
    level: 'Mixed procedural actions',
    summary:
      'DOJ announced coordinated actions involving alleged DPRK remote-worker schemes affecting over 70 U.S. companies, including charges, arrests and seizures. Details reflect the October 2026 announcement, not all final case outcomes.',
    impact: 'US employers, identity theft and revenue flows',
    source:
      'https://www.justice.gov/opa/pr/justice-department-announces-coordinated-actions-combat-north-korean-remote-it-worker',
    agency: 'U.S. Department of Justice',
  },
  {
    id: 'dprk-2025',
    code: 'KP',
    date: '2025-06-30',
    title: 'Nationwide laptop-farm investigations',
    topic: 'Identity & employment fraud',
    status: 'Indictments, plea agreement, seizures',
    level: 'Mixed procedural actions',
    summary:
      'DOJ announced related cases and disruptions involving alleged DPRK IT-worker schemes in multiple states. Some actions were allegations, others included a plea agreement and seizures.',
    impact: 'US companies and worker identities',
    source:
      'https://www.justice.gov/opa/pr/justice-department-announces-coordinated-nationwide-actions-combat-north-korean-remote',
    agency: 'U.S. Department of Justice',
  },
];
const SOURCES = [
  {
    id: 'usgs',
    name: 'USGS Earthquake GeoJSON',
    category: 'Environmental signals',
    mode: 'On-demand API',
    cost: 'Free public feed · no key',
    url: 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php',
    description: 'Earthquake M4.5+ location markers for the last 24 hours, from actual USGS events; not indicators of foreign interference.',
  },
  {
    id: 'factbook-archive',
    name: 'CIA World Factbook final archive',
    category: 'History & geography',
    mode: 'On-demand archive',
    cost: 'Free · public-domain data',
    url: 'https://github.com/factbook/factbook.json',
    description: 'Pinned January 2026 historical baseline, GEC/ISO crosswalk, source file revision and content checksum. Not current intelligence.',
  },
  {
    id: 'world-bank',
    name: 'World Bank Indicators',
    category: 'Economy',
    mode: 'On-demand API',
    cost: 'Free API · no key',
    url: 'https://datahelpdesk.worldbank.org/knowledgebase/articles/889392',
    description:
      'GDP, population and life expectancy in country briefs; 12 additional economy, energy, resources, trade and social indicators in Global systems. Each keeps its own observation year.',
  },
  {
    id: 'nato',
    name: 'NATO membership',
    category: 'Diplomacy',
    mode: 'Reviewed reference',
    cost: 'Free public record',
    url: 'https://www.nato.int/en/about-us/organization/nato-member-countries',
    description:
      'Primary source for current NATO membership; alliance status needs periodic revalidation.',
  },
  {
    id: 'dsca',
    name: 'DSCA major non-NATO allies',
    category: 'Diplomacy',
    mode: 'Reviewed reference',
    cost: 'Free public record',
    url: 'https://samm.dsca.mil/glossary/major-non-nato-allies',
    description:
      'Statutory MNNA designations. These are not automatically mutual-defense guarantees.',
  },
  {
    id: 'doj',
    name: 'DOJ / National Security Division',
    category: 'Justice',
    mode: 'Curated + scheduled intake',
    cost: 'Free public record',
    url: 'https://www.justice.gov/nsd',
    description:
      'Charges, case outcomes, seizures and national security prosecutions; procedural status matters.',
  },
  {
    id: 'ofac',
    name: 'Treasury OFAC Sanctions List Service',
    category: 'Sanctions',
    mode: 'SDN intake scheduled · verify source health',
    cost: 'Free public files / API',
    url: 'https://ofac.treasury.gov/sanctions-list-service',
    description:
      'SDN CSV intake and program aggregation scheduled. The separate non-SDN list, aliases, ownership and geographic identities are not yet ingested.'
  },
  {
    id: 'fara',
    name: 'DOJ FARA eFile',
    category: 'Influence',
    mode: 'Scheduled intake · check health',
    cost: 'Free public records',
    url: 'https://efile.fara.gov/',
    description:
      'Registration documents for foreign principals and agents; registration itself is not evidence of illicit conduct.',
  },
  {
    id: 'cisa',
    name: 'CISA cyber advisories',
    category: 'Cyber',
    mode: 'CISA KEV scheduled · advisories linked',
    cost: 'Free public record',
    url: 'https://www.cisa.gov/news-events/cybersecurity-advisories',
    description:
      'Cyber advisories and mitigations; attribution must be read in each original advisory.',
  },
  {
    id: 'mitre',
    name: 'MITRE ATT&CK',
    category: 'Cyber',
    mode: 'Linked discovery',
    cost: 'Free public reference',
    url: 'https://attack.mitre.org/',
    description:
      'Adversary behaviors and ATT&CK group descriptions; taxonomy is not criminal adjudication.',
  },
  {
    id: 'osint',
    name: 'OSINT Framework',
    category: 'Research tools',
    mode: 'Tool directory',
    cost: 'Free index · tools vary',
    url: 'https://osintframework.com/',
    description:
      'Find OSINT research utilities. A directory, not a collected feed or standalone proof.',
  },
  {
    id: 'un',
    name: 'UN Digital Library',
    category: 'Diplomacy',
    mode: 'Linked discovery',
    cost: 'Free public record',
    url: 'https://digitallibrary.un.org/',
    description:
      'UN documents and recorded votes for country-level diplomatic analysis.',
  },
  {
    id: "eonet",
    name: "NASA EONET Natural Events",
    category: "Environmental signals",
    mode: "On-demand API · point events only",
    cost: "Free public API · no key",
    url: "https://eonet.gsfc.nasa.gov/",
    description: "NASA EONET source-reported natural events with point coordinates; polygon-only events excluded. Data not attributed to conflict or foreign action.",
  },
  {
    id: "opensky",
    name: "OpenSky Aviation Network",
    category: "Aviation",
    mode: "Linked discovery · limits apply",
    cost: "Community access · registration/limits",
    url: "https://opensky-network.org/",
    description: "Aircraft transponder observations and API references. No live flight telemetry is currently displayed or claimed.",
  },
  {
    id: "coast-guard",
    name: "US Coast Guard Navigation Center",
    category: "Maritime",
    mode: "Linked discovery · not ingested",
    cost: "Free public safety notices",
    url: "https://navcen.uscg.gov/maritime-safety-information",
    description: "Official navigation notices, port status and AIS information. This is not a live global ship-tracking feed.",
  },
  {
    id: "fred",
    name: "Federal Reserve FRED",
    category: "Markets",
    mode: "Linked discovery · requires key",
    cost: "Free account / API key",
    url: "https://fred.stlouisfed.org/docs/api/fred/",
    description: "Federal Reserve economic and financial series. API calls require a user-registered key; no current price quote is assumed.",
  },
  {
    id: "un-comtrade",
    name: "UN Comtrade",
    category: "Trade",
    mode: "Linked discovery · not ingested",
    cost: "Free public access · usage limits",
    url: "https://comtradeapi.un.org/",
    description: "International trade flows and cross-border economic relationships. Not yet calculated or joined to cases.",
  },
  {
    id: "ioda",
    name: "Georgia Tech IODA",
    category: "Cyber",
    mode: "Linked discovery · not ingested",
    cost: "Open research portal",
    url: "https://ioda.inetintel.cc.gatech.edu/",
    description: "Internet outage detection and visibility. Outages are not evidence of an attack or its perpetrator.",
  },
  {
    id: "nws",
    name: "NOAA National Weather Service API",
    category: "Environmental signals",
    mode: "Linked discovery · not ingested",
    cost: "Free public API",
    url: "https://www.weather.gov/documentation/services-web-api",
    description: "U.S. official weather alerts and forecasts. No global weather overlay is currently claimed.",
  },
  {
    id: 'gdelt',
    name: 'GDELT Project',
    category: 'Media',
    mode: 'Not yet ingested',
    cost: 'Open public data',
    url: 'https://www.gdeltproject.org/',
    description:
      'Media-event discovery only; reports are leads, not verified government actions.',
  },
  {
    id: 'opensanctions',
    name: "OpenSanctions research index",
    category: "Sanctions",
    mode: "Linked discovery · terms/access restrictions",
    cost: "Public search; dataset and API terms vary",
    url: 'https://www.opensanctions.org/',
    description: "Third-party cross-references to sanctions and PEP information; check each original designation, license and permitted reuse.",
  },
  {
    id: 'occrp-aleph',
    name: "OCCRP Aleph",
    category: "Ownership",
    mode: "Linked research portal · not ingested",
    cost: "Public search; access restrictions",
    url: 'https://aleph.occrp.org/',
    description: "Investigative document search. Third-party matches require primary-register verification and independent corroboration.",
  },
  {
    id: 'icij-offshore',
    name: "ICIJ Offshore Leaks",
    category: "Ownership",
    mode: "Linked research portal · not ingested",
    cost: "Public search",
    url: 'https://offshoreleaks.icij.org/',
    description: "Historical offshore disclosures. Appearance in a leak is not evidence of unlawful conduct.",
  },
  {
    id: 'usaspending',
    name: "USAspending federal awards",
    category: "Public finance",
    mode: "Linked official portal · not ingested",
    cost: "Free public data",
    url: 'https://www.usaspending.gov/',
    description: "Federal spending, grants and contracts; not yet matched to foreign-ownership or influence records.",
  },
  {
    id: 'internet-archive',
    name: "Internet Archive Wayback Machine",
    category: "Historical evidence",
    mode: "Linked historical reference",
    cost: "Free public service · usage rules",
    url: 'https://web.archive.org/',
    description: "Historical webpage discovery only. Archive records are not equivalent to local immutable evidence preservation.",
  },
  {
    id: 'osint-source',
    name: "OSINT Framework source code",
    category: "Research tools",
    mode: "Linked source directory",
    cost: "MIT-licensed source index",
    url: 'https://github.com/lockfale/OSINT-Framework',
    description: "Public-source research-tool directory maintained by community contributors, not an evidence repository.",
  },
  {
    id: 'uk-companies',
    name: "UK Companies House",
    category: "Ownership",
    mode: "Linked official registry · not ingested",
    cost: "Public filings; API key/limits apply",
    url: 'https://find-and-update.company-information.service.gov.uk/',
    description: "Public company filings, officers and PSC data. Ownership assertions require time-scoped original filings.",
  },
  {
    id: 'uk-sanctions',
    name: "UK Sanctions List",
    category: "Sanctions",
    mode: "Official UK FCDO file · captured and scheduled",
    cost: "Public government data",
    url: 'https://www.gov.uk/government/publications/the-uk-sanctions-list',
    description: "UK sanctions designations; verify identity and date, separate from OFAC and court judgments.",
  },
  {
    id: 'eu-sanctions',
    name: "EU Sanctions Map",
    category: "Sanctions",
    mode: "Linked official portal · not ingested",
    cost: "Public information",
    url: 'https://www.sanctionsmap.eu/',
    description: "EU regimes and restrictions; not yet reconciled to U.S./UK entity records.",
  },
  {
    id: 'canadian-sanctions',
    name: "Global Affairs Canada sanctions",
    category: "Sanctions",
    mode: "Official XML snapshot · on-demand + scheduled",
    cost: "Public government data",
    url: 'https://www.international.gc.ca/world-monde/international_relations-relations_internationales/sanctions/current-actuelles.aspx',
    description: "Canada's official XML autonomous sanctions reference is parsed and country-regime indexed; only the originating regulations establish actual legal restrictions.",
  },
  {
    id: 'australia-sanctions',
    name: "Australian DFAT sanctions",
    category: "Sanctions",
    mode: "Linked official portal · not ingested",
    cost: "Public government data",
    url: 'https://www.dfat.gov.au/international-relations/security/sanctions/consolidated-list',
    description: "Australian consolidated sanctions list; not yet reconciled into cross-jurisdiction matches.",
  },
  {
    id: 'nz-sanctions',
    name: "New Zealand MFAT sanctions",
    category: "Sanctions",
    mode: "Linked official portal · not ingested",
    cost: "Public government data",
    url: 'https://www.mfat.govt.nz/en/peace-rights-and-security/sanctions',
    description: "New Zealand official public sanctions resources; not yet ingested.",
  },
  {
    id: 'usgs-minerals',
    name: "USGS Mineral Commodity Summaries",
    category: "Energy & resources",
    mode: "Linked annual report · not ingested",
    cost: "Free U.S. government publication",
    url: 'https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries',
    description: "Official mineral production, supply and market report. Not a current beneficial-ownership or shipment feed.",
  },
  {
    id: 'world-bank-energy',
    name: "World Bank energy and resources indicators",
    category: "Energy & resources",
    mode: "On-demand API · 4 indicators",
    cost: "Free public API",
    url: 'https://data.worldbank.org/topic/energy-and-mining',
    description: "Electricity access, renewable energy share, energy-import exposure and natural-resource rents displayed in Global systems with source years.",
  },
  {
    id: 'owid-physical-energy',
    name: 'Our World in Data updated energy dataset',
    category: 'Energy & resources',
    mode: 'On-demand validated snapshot · 220 countries',
    cost: 'Public CC BY-licensed dataset',
    url: 'https://catalog.ourworldindata.org/energy/owid_energy/',
    description: 'Annual oil, gas, coal and electricity observations from the updated dataset. Figures are not supplier ownership, political influence or bilateral transactions.',
  },
];
const NAME_OVERRIDES: Record<string, string> = {
  KP: 'North Korea',
  KR: 'South Korea',
  RU: 'Russia',
  IR: 'Iran',
  CN: 'China',
  TW: 'Taiwan',
  TR: 'Türkiye',
  PS: 'Palestine',
  VA: 'Holy See',
  CD: 'DR Congo',
  CG: 'Republic of the Congo',
  MM: 'Myanmar',
  CZ: 'Czechia',
  GB: 'United Kingdom',
  US: 'United States',
};
const display = new Intl.DisplayNames(['en'], { type: 'region' });

function makeCountry(code: string) {
  const region =
    Object.entries(REGION_GROUPS).find(([, list]) =>
      list.includes(code)
    )?.[0] || 'Other';
  return {
    code,
    name: NAME_OVERRIDES[code] || display.of(code) || code,
    region,
    scope: TERRITORIES.has(code)
      ? 'territory'
      : code === 'TW'
        ? 'separately-administered'
        : 'state-or-observer',
    relationship: NATO.has(code)
      ? 'NATO treaty ally'
      : DEFENSE.has(code)
        ? 'Defense treaty ally'
        : MNNA.has(code)
          ? 'Major non-NATO ally'
          : 'No NATO / listed bilateral alliance',
    isTreatyAlly: NATO.has(code) || DEFENSE.has(code),
    isMNNA: MNNA.has(code),
    caseCount: CASES.filter(c => c.code === code).length,
  };
}
const COUNTRIES = ISO.map(makeCountry).sort((a, b) =>
  a.name.localeCompare(b.name)
);
const WB_BASE = 'https://api.worldbank.org/v2/country';
const METRICS = [
  { key: 'gdp', indicator: 'NY.GDP.MKTP.CD', label: 'GDP', unit: 'USD' },
  {
    key: 'population',
    indicator: 'SP.POP.TOTL',
    label: 'Population',
    unit: 'people',
  },
  {
    key: 'lifeExpectancy',
    indicator: 'SP.DYN.LE00.IN',
    label: 'Life expectancy',
    unit: 'years',
  },
];

async function readSnapshot() {
  try {
    const [record] = await db.get<{
      updatedAt: string;
      countries: Record<string, Record<string, unknown>>;
    }>('economic_snapshots', ['latest']);
    return record;
  } catch {
    return null;
  }
}

async function worldBankFetch(url: string): Promise<unknown[]> {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(14000),
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error('World Bank HTTP ' + response.status);
  const body: unknown = await response.json();
  if (!Array.isArray(body) || !Array.isArray(body[1]))
    throw new Error('Unexpected World Bank response');
  return body[1] as unknown[];
}

type WBRow = {
  country?: { id?: string };
  date?: string;
  value?: number | null;
};

export async function refreshEconomicSnapshot() {
  const pages = await Promise.all(
    METRICS.map(metric =>
      worldBankFetch(
        WB_BASE +
          '/all/indicator/' +
          metric.indicator +
          '?format=json&mrv=1&per_page=500'
      )
    )
  );
  const data: Record<string, Record<string, unknown>> = {};
  let observations = 0;
  METRICS.forEach((metric, i) => {
    for (const raw of pages[i]) {
      const row = raw as WBRow;
      const code = row.country?.id || '';
      if (
        !ISO.includes(code) ||
        row.value === null ||
        typeof row.value !== 'number'
      )
        continue;
      if (!data[code]) data[code] = {};
      data[code][metric.key] = {
        value: row.value,
        year: row.date,
        indicator: metric.indicator,
        source: 'World Bank',
      };
      observations++;
    }
  });
  if (observations < 30)
    throw new Error('Insufficient observations; preserving previous snapshot');
  const updatedAt = new Date().toISOString();
  const result = await db.tx.update('economic_snapshots', [
    {
      id: 'latest',
      record: {
        updatedAt,
        countries: data,
        observationCount: observations,
        source: 'World Bank Indicators API',
      },
    },
  ]);
  if (!result[0]) throw new Error('Snapshot write not confirmed');
  return { updatedAt, observations, countries: Object.keys(data).length };
}

export const dailyEconomicSync = async () => {
  try {
    const result = await refreshEconomicSnapshot();
    console.info('Economic snapshot synced', result);
  } catch (err) {
    console.error('Economic snapshot sync failed; existing data retained', err);
  }
  return { statusCode: 200 };
};

async function countryBrief(code: string) {
  if (!ISO.includes(code)) return null;
  const snapshot = await readSnapshot();
  if (snapshot?.countries?.[code]) {
    return {
      code,
      updatedAt: snapshot.updatedAt,
      mode: 'scheduled-snapshot',
      metrics: snapshot.countries[code],
    };
  }
  const entries = await Promise.allSettled(
    METRICS.map(m =>
      worldBankFetch(
        WB_BASE +
          '/' +
          code +
          '/indicator/' +
          m.indicator +
          '?format=json&mrv=1&per_page=5'
      )
    )
  );
  const metrics: Record<string, unknown> = {};
  METRICS.forEach((m, i) => {
    const res = entries[i];
    if (res.status !== 'fulfilled') return;
    const row = (res.value[0] || null) as WBRow | null;
    if (row && row.value !== null && typeof row.value === 'number') {
      metrics[m.key] = {
        value: row.value,
        year: row.date,
        indicator: m.indicator,
        source: 'World Bank',
      };
    }
  });
  return {
    code,
    updatedAt: new Date().toISOString(),
    mode: 'on-demand',
    metrics,
    warning:
      Object.keys(metrics).length === 0
        ? 'No live indicator response available'
        : undefined,
  };
}

export const handler = router({
  'GET /api/cron/:job': [
    async ({ params, headers }) => {
      const secret = process.env.CRON_SECRET;
      if (!secret || headers?.authorization !== 'Bearer ' + secret) return error('Unauthorized', 401);
      const job = params.job;
      if (['doj', 'fara', 'cisa', 'ofac'].includes(job)) {
        await runCollectorCron({ payload: { sourceId: job } });
      } else if (job === 'uk') {
        await syncUK();
      } else if (job === 'canada') {
        await syncCanada();
      } else if (job === 'energy') {
        await syncEnergy();
      } else if (job === 'military') {
        await checkOfficialReportChanges();
      } else if (job === 'worldbank') {
        await dailyEconomicSync();
      } else {
        return error('Unknown collection job', 404);
      }
      return json({ job, invoked: true, checkedAt: new Date().toISOString(),
        note: 'Invocation is not proof of collection success. Verify the saved source health and observations.' });
    },
  ],
  'GET /api/_healthcheck': [
    async () => json({ message: 'Success', service: 'Eastern Axis' }),
  ],
  'GET /api/allied-sanctions/:code': [
    async ({ params }) => {
      try {
        const result = await readAlliedSanctions(params.code.toUpperCase() === 'ALL' ? 'all' : params.code.toUpperCase());
        return result ? json(result) : error('Invalid country code', 400);
      } catch (e) {
        console.error('Allied sanctions read failure', e);
        return error('International sanctions source temporarily unavailable', 503);
      }
    }
  ],
  'GET /api/energy-supply/:code': [
    async ({ params }) => {
      const code = params.code.toUpperCase() === 'ALL' ? 'all' : params.code.toUpperCase();
      if (code !== 'all' && !ISO.includes(code)) return error('Unknown country code', 404);
      try {
        const result = await readEnergy(code, COUNTRIES.find(c=>c.code===code)?.name);
        return result ? json(result) : error('Invalid country code', 400);
      } catch (e) {
        console.error('Physical energy source read failed', e);
        return error('Physical energy source unavailable', 503);
      }
    }
  ],
  'GET /api/supply-macro': [
    async () => json(await readSupplyMacro()),
  ],
  'GET /api/supply-trade/:code/:hs': [
    async ({params}) => {
      const code=params.code.toUpperCase(),hs=params.hs.toUpperCase();
      if(!ISO.includes(code))return error('Unknown country code',404);
      const result=await readTradeDependency(code,hs);
      return result?json(result):error('Invalid commodity group',400);
    },
  ],
  'GET /api/supply-chain/:code': [
    async ({ params }) => {
      const code = params.code.toUpperCase() === 'ALL' ? 'all' : params.code.toUpperCase();
      if (code !== 'all' && !ISO.includes(code)) return error('Unknown country code', 404);
      const response = await readSupplyChain(code);
      return response ? json(response) : error('Invalid country code', 400);
    },
  ],
  'GET /api/global-systems/:code': [
    async ({ params }) => {
      const result = await readGlobalSystems(params.code);
      return result ? json(result) : error('Invalid country code', 400);
    },
  ],
  'GET /api/defense-intel': [
    async () => json(readDefenseIntelligence()),
  ],
  'GET /api/source-monitor': [
    async () => {
      try { return json(await readOfficialReportChanges()); }
      catch (e) { console.error('Official source monitor read error', e); return error('Source monitor unavailable', 503); }
    }
  ],
  'POST /api/compare-allies': [
    async ({ body }) => {
      try {
        const requested = body as { code?: string } | null;
        const result = await compareAlliedReports(requested?.code);
        return result.status === 'invalid' ? error('Invalid country code', 400) : json(result);
      } catch (e) {
        console.error('Allied comparison failed', e);
        return error('AI comparison unavailable', 503);
      }
    }
  ],
  'POST /api/watch-analyze': [
    async ({ body }) => {
      try {
        const requested = body as { code?: string } | null;
        return json(await analyzeSourceChanges(requested?.code));
      } catch (e) {
        console.error('Publication AI review failed', e);
        return error('Publication analysis unavailable', 503);
      }
    }
  ],
  'GET /api/world-signals': [
    async () => {
      try { return json(await readWorldSignals()); }
      catch(err) { console.error('USGS feed unavailable',err); return error('USGS feed unavailable',503); }
    }
  ],
  'GET /api/evidence-workbench': [
    async () => {
      try { return json(await readEvidenceWorkbench()); }
      catch (err) { console.error('Evidence workbench read failed', err); return error('Evidence audit unavailable', 503); }
    }
  ],
  'GET /api/intelligence': [
    async () => {
      try { return json(await readIntelligenceDesk()); }
      catch (err) {
        console.error('Intelligence desk read failed', err);
        return error('Collector status temporarily unavailable', 503);
      }
    },
  ],
  'GET /api/factbook/countries': [
    async () => json({
      baseline: ARCHIVE_BASELINE,
      revision: ARCHIVE_REVISION,
      countries: ARCHIVE_ENTITIES.map(item => ({
        ...item,
        region: item.iso ? COUNTRIES.find(c => c.code === item.iso)?.region || 'Other' : 'Other',
      })),
    }),
  ],
  'GET /api/factbook/compare': [
    async ({ query }) => {
      const codes = (query.codes || '').toUpperCase().split(',').map(c => c.trim()).filter(Boolean);
      if (!codes.length || codes.length > 3 || new Set(codes).size !== codes.length ||
          codes.some(c => !ISO.includes(c))) return error('Choose 1-3 unique ISO country codes', 400);
      const results = await Promise.allSettled(codes.map(c => countryBrief(c)));
      return json({
        rows: results.map((result, i) => ({
          code: codes[i],
          name: COUNTRIES.find(c => c.code === codes[i])?.name || codes[i],
          metrics: result.status === 'fulfilled' && result.value ? result.value.metrics : {},
        })),
        warning: 'World Bank observations retain their individual reporting years. Missing measurements are not estimated.',
      });
    },
  ],
  'GET /api/factbook/:code': [
    async ({ params }) => {
      const code = params.code.toUpperCase();
      const entry = ARCHIVE_ENTITIES.find(c => c.code === code);
      if (!entry) return error('Unknown archived entity', 404);
      const region = entry.iso ? COUNTRIES.find(c => c.code === entry.iso)?.region || '' : '';
      try {
        return json(await readFactbook(code, region));
      } catch (err) {
        console.error('Factbook archival source failed', err);
        return error('Archived source unavailable', 503);
      }
    },
  ],
  'GET /api/fields/:field': [
    async ({ params }) => {
      const key = params.field;
      if (!METRICS.some(m => m.key === key)) return error('Unsupported metric', 400);
      const snapshot = await readSnapshot();
      const countries = COUNTRIES.flatMap(c => {
        const metric = snapshot?.countries?.[c.code]?.[key];
        return metric && typeof metric === 'object' &&
          typeof (metric as { value?: unknown }).value === 'number'
          ? [{ code: c.code, name: c.name, metric }] : [];
      });
      return json({
        field: key, status: snapshot ? 'stored_snapshot' : 'unavailable',
        updatedAt: snapshot?.updatedAt || null, countries,
        warning: !snapshot ? 'No synchronized World Bank snapshot is available; values were not invented.' : undefined,
      });
    },
  ],
  'GET /api/overview': [
    async () => {
      const snapshot = await readSnapshot();
      return json({
        countries: COUNTRIES,
        cases: CASES,
        sources: SOURCES,
        snapshot: snapshot
          ? {
              updatedAt: snapshot.updatedAt,
              coveredCountries: Object.keys(snapshot.countries || {}).length,
            }
          : null,
        classificationAsOf: '2026-11-15',
        scopeDefinition:
          'Excludes NATO members and the five primary US Indo-Pacific bilateral / minilateral defense allies. Other treaty obligations, including the Rio Treaty, must be reviewed separately.',
        classificationSources: [
          'https://www.nato.int/en/about-us/organization/nato-member-countries',
          'https://samm.dsca.mil/glossary/major-non-nato-allies',
        ],
      });
    },
  ],
  'GET /api/brief/:code': [
    async ({ params }) => {
      const code = params.code.toUpperCase();
      if (!ISO.includes(code)) return error('Unknown ISO code', 404);
      try {
        return json(await countryBrief(code));
      } catch {
        return json({
          code,
          mode: 'unavailable',
          metrics: {},
          warning:
            'The World Bank feed is temporarily unavailable. Historical or estimated values have not been substituted.',
        });
      }
    },
  ],
});
