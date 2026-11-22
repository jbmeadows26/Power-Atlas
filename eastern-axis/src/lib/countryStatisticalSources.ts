/**
 * Canonical statistical-source registry for Eastern Axis country dossiers.
 *
 * Source discovery is NOT a claim that an API has been ingested or that
 * a country has any particular value. All measurements remain tied to
 * their original publisher, definition, year, observation and source URL.
 * ISO-3166 alpha-2/alpha-3 crosswalk is defined by official standard
 * country codes (249 entries; pycountry ISO catalogue 24.6.1).
 * Aggregate WLD and disputed XK are intentionally NOT mapped to ISO3.
 */
const codes = `AD:AND AE:ARE AF:AFG AG:ATG AI:AIA AL:ALB AM:ARM AO:AGO AQ:ATA AR:ARG AS:ASM AT:AUT AU:AUS AW:ABW AX:ALA AZ:AZE BA:BIH BB:BRB BD:BGD BE:BEL BF:BFA BG:BGR BH:BHR BI:BDI BJ:BEN BL:BLM BM:BMU BN:BRN BO:BOL BQ:BES BR:BRA BS:BHS BT:BTN BV:BVT BW:BWA BY:BLR BZ:BLZ CA:CAN CC:CCK CD:COD CF:CAF CG:COG CH:CHE CI:CIV CK:COK CL:CHL CM:CMR CN:CHN CO:COL CR:CRI CU:CUB CV:CPV CW:CUW CX:CXR CY:CYP CZ:CZE DE:DEU DJ:DJI DK:DNK DM:DMA DO:DOM DZ:DZA EC:ECU EE:EST EG:EGY EH:ESH ER:ERI ES:ESP ET:ETH FI:FIN FJ:FJI FK:FLK FM:FSM FO:FRO FR:FRA GA:GAB GB:GBR GD:GRD GE:GEO GF:GUF GG:GGY GH:GHA GI:GIB GL:GRL GM:GMB GN:GIN GP:GLP GQ:GNQ GR:GRC GS:SGS GT:GTM GU:GUM GW:GNB GY:GUY HK:HKG HM:HMD HN:HND HR:HRV HT:HTI HU:HUN ID:IDN IE:IRL IL:ISR IM:IMN IN:IND IO:IOT IQ:IRQ IR:IRN IS:ISL IT:ITA JE:JEY JM:JAM JO:JOR JP:JPN KE:KEN KG:KGZ KH:KHM KI:KIR KM:COM KN:KNA KP:PRK KR:KOR KW:KWT KY:CYM KZ:KAZ LA:LAO LB:LBN LC:LCA LI:LIE LK:LKA LR:LBR LS:LSO LT:LTU LU:LUX LV:LVA LY:LBY MA:MAR MC:MCO MD:MDA ME:MNE MF:MAF MG:MDG MH:MHL MK:MKD ML:MLI MM:MMR MN:MNG MO:MAC MP:MNP MQ:MTQ MR:MRT MS:MSR MT:MLT MU:MUS MV:MDV MW:MWI MX:MEX MY:MYS MZ:MOZ NA:NAM NC:NCL NE:NER NF:NFK NG:NGA NI:NIC NL:NLD NO:NOR NP:NPL NR:NRU NU:NIU NZ:NZL OM:OMN PA:PAN PE:PER PF:PYF PG:PNG PH:PHL PK:PAK PL:POL PM:SPM PN:PCN PR:PRI PS:PSE PT:PRT PW:PLW PY:PRY QA:QAT RE:REU RO:ROU RS:SRB RU:RUS RW:RWA SA:SAU SB:SLB SC:SYC SD:SDN SE:SWE SG:SGP SH:SHN SI:SVN SJ:SJM SK:SVK SL:SLE SM:SMR SN:SEN SO:SOM SR:SUR SS:SSD ST:STP SV:SLV SX:SXM SY:SYR SZ:SWZ TC:TCA TD:TCD TF:ATF TG:TGO TH:THA TJ:TJK TK:TKL TL:TLS TM:TKM TN:TUN TO:TON TR:TUR TT:TTO TV:TUV TW:TWN TZ:TZA UA:UKR UG:UGA UM:UMI US:USA UY:URY UZ:UZB VA:VAT VC:VCT VE:VEN VG:VGB VI:VIR VN:VNM VU:VUT WF:WLF WS:WSM YE:YEM YT:MYT ZA:ZAF ZM:ZMB ZW:ZWE`;

const iso2To3 = new Map(codes.split(' ').map(pair=>pair.split(':') as [string,string]));
const iso3To2 = new Map([...iso2To3.entries()].map(([a,b])=>[b,a]));
export const isoCrosswalkSize=iso2To3.size;
export const isoAlpha3=(code?:string|null):string|null=>{
  const normalized=(code||'').trim().toUpperCase();
  if(normalized.length===2)return iso2To3.get(normalized)||null;
  if(normalized.length===3&&iso3To2.has(normalized))return normalized;
  return null;
};
export const isoAlpha2=(code?:string|null):string|null=>{
  const normalized=(code||'').trim().toUpperCase();
  if(normalized.length===2&&iso2To3.has(normalized))return normalized;
  return iso3To2.get(normalized)||null;
};

export type StatisticalSourceStatus='ingested'|'partial'|'discovery'|'archived';
export type StatisticalSource={
  id:string;name:string;status:StatisticalSourceStatus;topics:string;metricExamples:string;
  landingUrl:string;apiDocsUrl:string;identifierPolicy:string;coverageNote:string;
};

/** Status describes Eastern Axis integration, not the publisher's availability. */
export const countryStatisticalSources:readonly StatisticalSource[]=[
  {id:'world-bank',name:'World Bank Open Data',status:'ingested',
   topics:'Economy · energy · social · climate',
   metricExamples:'GDP growth, inflation, unemployment, electricity, trade, life expectancy',
   landingUrl:'https://data.worldbank.org/',apiDocsUrl:'https://datahelpdesk.worldbank.org/knowledgebase/articles/889392',
   identifierPolicy:'Country ISO alpha-2 and alpha-3 mapped explicitly; WLD is a non-ISO aggregate.',
   coverageNote:'12 source-dated WDI indicators available in country systems; this is not the entire World Bank catalog.'},
  {id:'owid',name:'Our World in Data',status:'partial',
   topics:'Climate · energy · inequality · demographics',
   metricExamples:'Historical energy mix, CO₂, and separately defined Gini measures',
   landingUrl:'https://ourworldindata.org/',apiDocsUrl:'https://docs.owid.io/projects/etl/api/chart-api/',
   identifierPolicy:'Standard OWID country codes often use ISO alpha-3, but OWID_ aggregates must never be joined as countries.',
   coverageNote:'Selected OWID series and supplements are ingested. Other OWID charts remain unindexed.'},
  {id:'imf',name:'IMF Data and DataMapper',status:'partial',
   topics:'Macroeconomy · public finance · economic forecasts',
   metricExamples:'Real GDP, inflation, unemployment, public debt, fiscal balance',
   landingUrl:'https://www.imf.org/external/datamapper/',apiDocsUrl:'https://data.imf.org/en/Resource-Pages/IMF-API',
   identifierPolicy:'IMF dataflow-specific country codes require an audited ISO3 concordance before joining.',
   coverageNote:'IMF PortWatch is used in supply chains; the DataMapper forecast series have not been integrated.'},
  {id:'undata',name:'UNdata and UN SDG Statistics',status:'discovery',
   topics:'Population · migration · SDGs · social statistics',
   metricExamples:'UN population and agency indicators, reported SDG series',
   landingUrl:'https://data.un.org/',apiDocsUrl:'https://data.un.org/Host.aspx?Content=API',
   identifierPolicy:'UN M49/SDMX country identifiers must be resolved against verified ISO3 codes.',
   coverageNote:'Reference access only. No normalized UNdata country measurement feed is connected.'},
  {id:'oecd',name:'OECD Data Explorer',status:'discovery',
   topics:'Workforce · productivity · tax · healthcare · research',
   metricExamples:'Labor productivity, wages, tax burden, R&D and health expenditure',
   landingUrl:'https://data-explorer.oecd.org/',apiDocsUrl:'https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html',
   identifierPolicy:'Dataset-specific SDMX codelists must be verified against ISO3 before comparisons.',
   coverageNote:'Reference access only; OECD coverage and definitions vary by economy and dataset.'},
  {id:'unctad',name:'UNCTADstat',status:'discovery',
   topics:'Trade · investment · development',
   metricExamples:'Merchandise and services trade, FDI and trade partner measures',
   landingUrl:'https://unctadstat.unctad.org/',apiDocsUrl:'https://unctadstat.unctad.org/',
   identifierPolicy:'UNCTAD geography IDs require a verified country crosswalk; no name-based joins.',
   coverageNote:'Reference access only; UNCTAD bilateral flows are not automatically ingested.'},
  {id:'comtrade',name:'UN Comtrade',status:'partial',
   topics:'Bilateral trade · products · partners',
   metricExamples:'Reporter/partner commodity imports and exports by HS classification',
   landingUrl:'https://comtradeplus.un.org/',apiDocsUrl:'https://comtrade.un.org/en/api-docs',
   identifierPolicy:'Reporter and partner use UN M49 numeric IDs; map to ISO3 only through verified M49 codes.',
   coverageNote:'Some U.S.-reported partner/commodity comparisons are available on demand, not a global trade matrix.'},
  {id:'who',name:'WHO Global Health Observatory',status:'discovery',
   topics:'Health · biosecurity · mortality',
   metricExamples:'Vaccination, disease burden, cause-specific mortality and health systems',
   landingUrl:'https://www.who.int/data/gho',apiDocsUrl:'https://www.who.int/data/gho/info/gho-odata-api',
   identifierPolicy:'Validate country code and health-indicator definitions; distinguish estimates from reported cases.',
   coverageNote:'Reference access only; no active WHO country observation collector is connected.'},
  {id:'cia-archive',name:'CIA World Factbook · historical',status:'archived',
   topics:'Historical country background and geography',
   metricExamples:'Archived population, government, economy, geography and military structure',
   landingUrl:'https://www.cia.gov/the-world-factbook/',apiDocsUrl:'https://github.com/factbook/factbook.json',
   identifierPolicy:'Historical CIA GEC codes differ from ISO2/ISO3 and must be mapped explicitly.',
   coverageNote:'CIA retired the Factbook on February 4, 2026. Pinned snapshots are historical, not live indicators.'}
];

export const sourceTotals=()=>({
  ingested:countryStatisticalSources.filter(x=>x.status==='ingested').length,
  partial:countryStatisticalSources.filter(x=>x.status==='partial').length,
  discovery:countryStatisticalSources.filter(x=>x.status==='discovery').length,
  archived:countryStatisticalSources.filter(x=>x.status==='archived').length
});
