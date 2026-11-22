/**
 * Country source registry and ISO-3166 canonical crosswalk.
 * A source link is NOT a collected dataset. Only 'connected' and 'partial'
 * status may describe data already exposed elsewhere in Eastern Axis.
 * 'reference' is discovery only; archive is historical, not current.
 */
export type SourceAvailability='connected'|'partial'|'reference'|'archive';
export type SourceFamily='economy'|'trade'|'health'|'social'|'historical';
export type MultilateralSource={
 id:string;name:string;family:SourceFamily;status:SourceAvailability;
 metrics:string;access:string;url:string;scope:string;notes:string;
};
// ISO 3166-1 alpha-2 → alpha-3 (249 assigned codes). Non-ISO territories
// and aggregate pseudo-codes, including WLD and XK, remain unmapped.
const mapping=`AD:AND AE:ARE AF:AFG AG:ATG AI:AIA AL:ALB AM:ARM AO:AGO AQ:ATA AR:ARG AS:ASM AT:AUT AU:AUS AW:ABW AX:ALA AZ:AZE BA:BIH BB:BRB BD:BGD BE:BEL BF:BFA BG:BGR BH:BHR BI:BDI BJ:BEN BL:BLM BM:BMU BN:BRN BO:BOL BQ:BES BR:BRA BS:BHS BT:BTN BV:BVT BW:BWA BY:BLR BZ:BLZ CA:CAN CC:CCK CD:COD CF:CAF CG:COG CH:CHE CI:CIV CK:COK CL:CHL CM:CMR CN:CHN CO:COL CR:CRI CU:CUB CV:CPV CW:CUW CX:CXR CY:CYP CZ:CZE DE:DEU DJ:DJI DK:DNK DM:DMA DO:DOM DZ:DZA EC:ECU EE:EST EG:EGY EH:ESH ER:ERI ES:ESP ET:ETH FI:FIN FJ:FJI FK:FLK FM:FSM FO:FRO FR:FRA GA:GAB GB:GBR GD:GRD GE:GEO GF:GUF GG:GGY GH:GHA GI:GIB GL:GRL GM:GMB GN:GIN GP:GLP GQ:GNQ GR:GRC GS:SGS GT:GTM GU:GUM GW:GNB GY:GUY HK:HKG HM:HMD HN:HND HR:HRV HT:HTI HU:HUN ID:IDN IE:IRL IL:ISR IM:IMN IN:IND IO:IOT IQ:IRQ IR:IRN IS:ISL IT:ITA JE:JEY JM:JAM JO:JOR JP:JPN KE:KEN KG:KGZ KH:KHM KI:KIR KM:COM KN:KNA KP:PRK KR:KOR KW:KWT KY:CYM KZ:KAZ LA:LAO LB:LBN LC:LCA LI:LIE LK:LKA LR:LBR LS:LSO LT:LTU LU:LUX LV:LVA LY:LBY MA:MAR MC:MCO MD:MDA ME:MNE MF:MAF MG:MDG MH:MHL MK:MKD ML:MLI MM:MMR MN:MNG MO:MAC MP:MNP MQ:MTQ MR:MRT MS:MSR MT:MLT MU:MUS MV:MDV MW:MWI MX:MEX MY:MYS MZ:MOZ NA:NAM NC:NCL NE:NER NF:NFK NG:NGA NI:NIC NL:NLD NO:NOR NP:NPL NR:NRU NU:NIU NZ:NZL OM:OMN PA:PAN PE:PER PF:PYF PG:PNG PH:PHL PK:PAK PL:POL PM:SPM PN:PCN PR:PRI PS:PSE PT:PRT PW:PLW PY:PRY QA:QAT RE:REU RO:ROU RS:SRB RU:RUS RW:RWA SA:SAU SB:SLB SC:SYC SD:SDN SE:SWE SG:SGP SH:SHN SI:SVN SJ:SJM SK:SVK SL:SLE SM:SMR SN:SEN SO:SOM SR:SUR SS:SSD ST:STP SV:SLV SX:SXM SY:SYR SZ:SWZ TC:TCA TD:TCD TF:ATF TG:TGO TH:THA TJ:TJK TK:TKL TL:TLS TM:TKM TN:TUN TO:TON TR:TUR TT:TTO TV:TUV TW:TWN TZ:TZA UA:UKR UG:UGA UM:UMI US:USA UY:URY UZ:UZB VA:VAT VC:VCT VE:VEN VG:VGB VI:VIR VN:VNM VU:VUT WF:WLF WS:WSM YE:YEM YT:MYT ZA:ZAF ZM:ZMB ZW:ZWE`;
export const ISO2_TO_ISO3:Readonly<Record<string,string>>=Object.freeze(Object.fromEntries(
 mapping.split(' ').map(pair=>pair.split(':'))
));
export function iso3Of(code:string|null|undefined):string|null{
 const value=String(code||'').trim().toUpperCase();
 if(value.length===3&&Object.values(ISO2_TO_ISO3).includes(value))return value;
 return ISO2_TO_ISO3[value]||null;
}
export const MULTILATERAL_SOURCES:ReadonlyArray<MultilateralSource>=[
 {id:'wdi',name:'World Bank · World Development Indicators',family:'economy',status:'connected',
  metrics:'GDP, inflation, employment, inequality, health and energy indicators',
  access:'Official API / country profiles',url:'https://data.worldbank.org/',
  scope:'12 on-demand country indicators plus separately sourced historic country figures',
  notes:'Existing WDI integration; original country-year and methodology preserved. Not all 1,400+ WDI indicators are collected.'},
 {id:'owid',name:'Our World in Data',family:'social',status:'partial',
  metrics:'Energy production, electricity, CO₂ and source-identified Gini supplements',
  access:'Published datasets and chart CSV',url:'https://ourworldindata.org/',
  scope:'Existing bounded physical-energy and social supplements, not the entire chart catalogue',
  notes:'Dataset definitions differ from World Bank measures. WID pre-tax Gini must not be merged with survey Gini.'},
 {id:'imf',name:'IMF DataMapper / World Economic Outlook',family:'economy',status:'reference',
  metrics:'GDP growth, inflation, unemployment, debt, fiscal projections',
  access:'Data Portal / DataMapper API',url:'https://data.imf.org/',
  scope:'Discovery only; IMF WEO country forecasts are not yet normalized into country comparisons',
  notes:'Use the current IMF portal, not the retired legacy IMF data portal. Forecasts must be labelled separately from actuals.'},
 {id:'portwatch',name:'IMF PortWatch',family:'trade',status:'partial',
  metrics:'Maritime chokepoint vessel traffic and disruption exposure',
  access:'IMF-supported maritime monitoring',url:'https://portwatch.imf.org/',
  scope:'Existing bounded on-demand shipping context on Supply Chains',
  notes:'AIS-derived route events are not national import/export quantities or proven causal shocks.'},
 {id:'undata',name:'UNdata / UN Statistics Division',family:'social',status:'reference',
  metrics:'Population, SDG indicators, migration and social statistics',
  access:'UNdata portal / official SDG API',url:'https://unstats.un.org/sdgapi/swagger/',
  scope:'Discovery only; not yet ingested as national indicator time series',
  notes:'The UN SDG data API uses UN area codes; these must be mapped independently rather than treated as ISO country IDs.'},
 {id:'oecd',name:'OECD Data Explorer',family:'economy',status:'reference',
  metrics:'Taxation, wages, productivity, health spending and R&D',
  access:'SDMX API',url:'https://sdmx.oecd.org/public/',
  scope:'Discovery only; no validated OECD country/time-series collector yet',
  notes:'OECD has partial country membership. Absence of a country in OECD data does not imply an observed zero.'},
 {id:'unctad',name:'UNCTADstat',family:'trade',status:'reference',
  metrics:'Services trade, merchandise flows, tariffs and trade profiles',
  access:'UNCTAD Data Hub',url:'https://unctadstat.unctad.org/',
  scope:'Discovery only; no complete bilateral flows have been indexed',
  notes:'Trade methodology, currency, flow and reporting year must be preserved for each bilateral observation.'},
 {id:'comtrade',name:'UN Comtrade',family:'trade',status:'partial',
  metrics:'Reporter-partner-commodity trade flows and merchandise value',
  access:'Official API / bounded reporter comparisons',url:'https://comtradeapi.un.org/',
  scope:'Limited U.S.-reporter partner/commodity comparison already present in Supply Chains',
  notes:'Reporters and partners are separate roles. Not yet a complete bilateral global trade matrix.'},
 {id:'who',name:'WHO Global Health Observatory',family:'health',status:'reference',
  metrics:'Life expectancy, mortality causes, vaccination and health systems',
  access:'WHO data portal and public API documentation',url:'https://www.who.int/data/gho',
  scope:'Discovery only; health observations are not yet collected from a confirmed current API',
  notes:'WHO announced retirement of its earlier GHO OData implementation; do not promise an unchanged legacy API.'},
 {id:'cia',name:'CIA World Factbook · historical archive',family:'historical',status:'archive',
  metrics:'Historical government, geography, infrastructure, language and defense summaries',
  access:'Pinned January 2026 archive',url:'https://www.cia.gov/the-world-factbook/',
  scope:'Historical snapshot already browsable here; no new CIA updates after February 2026 closure',
  notes:'Not a live source. Archived figures are never silently substituted for current UN/World Bank measurements.'},
];
/** Source coverage represents actual integration, not a provider count. */
export const multilateralCoverage={
 integrated:MULTILATERAL_SOURCES.filter(x=>x.status==='connected'||x.status==='partial').length,
 reference:MULTILATERAL_SOURCES.filter(x=>x.status==='reference').length,
 archived:MULTILATERAL_SOURCES.filter(x=>x.status==='archive').length,
};
export function countrySourceUrl(id:string,iso2:string|null|undefined):string{
 const src=MULTILATERAL_SOURCES.find(s=>s.id===id);
 if(!src)return '';
 if(id==='wdi'){
  const iso3=iso3Of(iso2);
  if(iso3)return 'https://data.worldbank.org/country/'+iso3;
 }
 return src.url;
}
