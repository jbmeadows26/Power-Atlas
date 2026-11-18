// Source coverage is not an assertion that a metric has been ingested.
// Public source links are discovery / validation targets; some require licensing or manual review.
export type Coverage = 'measured' | 'public-source' | 'restricted' | 'not-connected';
export type EarlyDomain = {
  id: string; title: string; horizon: string; explanation: string;
  geos: string[]; indicators: { label: string; evidence: string; source: string; url: string; coverage: Coverage; cadence: string }[];
};
export const earlyDomains: EarlyDomain[] = [
  { id:'maritime',title:'Maritime auctions & war-risk insurance',horizon:'Hours to weeks',
    explanation:'Compare pre-transit pricing and booking constraints with measured vessel flows; insured-route quotations are generally commercial.',
    geos:['PA','EG','IR','OM','SA','YE','DJ'],
    indicators:[
      {label:'Panama Canal slot auctions',evidence:'Auction notices, booking rules and slot availability; accepted bid prices require verified access',source:'Panama Canal Authority',url:'https://pancanal.com/en/transit-reservation-system/',coverage:'public-source',cadence:'Daily / event'},
      {label:'Red Sea / Hormuz war-risk premium',evidence:'Market insurance quotations and insured-route clauses; no public real-time premium series',source:'Lloyd’s Market Association',url:'https://www.lmalloyds.com/',coverage:'restricted',cadence:'Daily when licensed'},
      {label:'Chokepoint vessel throughput',evidence:'Observed AIS-based transits, not advance auction/insurance quotes',source:'IMF PortWatch',url:'https://portwatch.imf.org/',coverage:'measured',cadence:'Daily'}
    ]},
  {id:'water',title:'Industrial hydrology & cooling water',horizon:'Days to months',
    explanation:'Water stress can constrain generation or manufacturing, but facility-level effects require permit and operator evidence.',
    geos:['US','TW','DE','NL','FR','CH','CN','IN','ZA'],
    indicators:[
      {label:'River temperature & discharge',evidence:'Monitored stations, thermal discharge regulations and validated downstream exposure',source:'USGS Water Data',url:'https://api.waterdata.usgs.gov/',coverage:'public-source',cadence:'Daily (US)'},
      {label:'Reservoir & drought anomaly',evidence:'Regional reservoir records and climate-based drought anomaly',source:'Copernicus Global Drought Observatory',url:'https://drought.emergency.copernicus.eu/',coverage:'public-source',cadence:'Weekly / monthly'},
      {label:'Taiwan industrial water supply',evidence:'Reservoir and water-resource conditions; fab impact must be separately sourced',source:'Taiwan Water Resources Agency',url:'https://eng.wra.gov.tw/',coverage:'public-source',cadence:'Daily / weekly'},
      {label:'Rhine navigable-water constraints',evidence:'Gauge levels and published navigational restrictions',source:'German Federal Waterways / ELWIS',url:'https://www.elwis.de/',coverage:'public-source',cadence:'Daily'}
    ]},
  {id:'transformers',title:'Grid transformers & restoration capacity',horizon:'Months to years',
    explanation:'Equipment backlogs may worsen restoration duration; copper pricing alone does not measure transformer availability.',
    geos:['US','CN','DE','IN','JP','KR','FR','GB'],
    indicators:[
      {label:'Large-power-transformer lead times',evidence:'Manufacturer lead times, orders and production capacity; often private',source:'U.S. Department of Energy',url:'https://www.energy.gov/oe/',coverage:'public-source',cadence:'Quarterly / report'},
      {label:'Transformer factory order backlog',evidence:'Manufacturer-reported backlog and delivery timetables',source:'Company filings and investor releases',url:'https://www.sec.gov/edgar/search/',coverage:'public-source',cadence:'Quarterly'},
      {label:'Copper input price',evidence:'Monthly published copper price, not a lead-time measurement',source:'World Bank Pink Sheet',url:'https://www.worldbank.org/en/research/commodity-markets',coverage:'measured',cadence:'Monthly'}
    ]},
  {id:'minerals',title:'Critical mineral controls & customs',horizon:'Weeks to years',
    explanation:'Legal restrictions, export volumes, customs clearance, and downstream industry exposure are separate evidence chains.',
    geos:['CN','US','AU','CA','JP','KR','DE','IN','RU','ID'],
    indicators:[
      {label:'Gallium, germanium & graphite restrictions',evidence:'New licenses, quotas and export prohibitions verified against official notices',source:'WTO Quantitative Restrictions',url:'https://data.wto.org/dataset/ext_qr',coverage:'public-source',cadence:'Event / notification'},
      {label:'Critical-mineral exports',evidence:'Monthly/annual HS-code exports; products and reporting lag must be disclosed',source:'UN Comtrade',url:'https://comtradeplus.un.org/en/',coverage:'public-source',cadence:'Monthly / annual'},
      {label:'Mine & processing concentration',evidence:'Published output and processing estimates, not current inventory',source:'USGS Mineral Commodity Summaries',url:'https://www.usgs.gov/centers/national-minerals-information-center',coverage:'public-source',cadence:'Annual'},
      {label:'Customs clearance & strategic stockpiles',evidence:'Actual clearing times and official reserve transactions; generally not consistently public',source:'Customs and industry records',url:'https://www.wto.org/english/tratop_e/tradfa_e/tradfa_e.htm',coverage:'not-connected',cadence:'Event / partner feed'}
    ]},
  {id:'labor',title:'Port & freight labor negotiations',horizon:'Weeks to years',
    explanation:'Contract deadlines are verified dates, not predictions of strikes; monitor official union/employer communications.',
    geos:['US','CA','GB','DE','FR','NL','BE','AU','ZA','KR','JP','IN'],
    indicators:[
      {label:'Atlantic / Gulf longshore contract',evidence:'ILA-USMX master agreement expiry: September 30, 2030',source:'International Longshoremen’s Association',url:'https://ilaunion.org/international-longshoremens-association-and-united-states-maritime-alliance-officially-sign-historic-six-year-master-contract-agreement-at-ceremonies-in-new-jersey-ila-longshore-workers-on-a/',coverage:'public-source',cadence:'Expiry: 2030-09-30'},
      {label:'U.S. Pacific longshore contract',evidence:'ILWU-PMA labor agreement in place through 2028; exact expiry requires contract review',source:'Pacific Maritime Association',url:'https://www.pmanet.org/what-we-do/',coverage:'public-source',cadence:'Through 2028'},
      {label:'Top-50 ports & freight rail expirations',evidence:'Country-specific contracts and official expiration documents; complete registry not verified',source:'International Transport Workers’ Federation',url:'https://www.itfglobal.org/en',coverage:'not-connected',cadence:'Contract-dependent'},
      {label:'Regional labor cost pressure',evidence:'Official wage, cost-of-living, inflation data; cannot infer strike probability from sentiment',source:'ILO Statistics',url:'https://ilostat.ilo.org/',coverage:'public-source',cadence:'Monthly / quarterly'}
    ]},
  {id:'food',title:'Food supply, crop conditions & fertilizer',horizon:'Weeks to harvest seasons',
    explanation:'Inputs, crop development, prices and unrest are distinct. A fertilizer cost increase does not guarantee reduced yields.',
    geos:['BR','AR','IN','CN','UA','RU','US','EG','PK','ET','KE','NG'],
    indicators:[
      {label:'Natural gas & fertilizer input costs',evidence:'Monthly natural gas, urea and DAP prices with source month and units',source:'World Bank Pink Sheet',url:'https://www.worldbank.org/en/research/commodity-markets',coverage:'measured',cadence:'Monthly'},
      {label:'Crop-condition anomalies',evidence:'Satellite-informed crop-condition assessments; not assured tonnage yield predictions',source:'GEOGLAM Crop Monitor',url:'https://www.cropmonitor.org/',coverage:'public-source',cadence:'Monthly'},
      {label:'Food price pressure',evidence:'Monthly global commodity price index, not local retail price or famine risk',source:'FAO Food Price Index',url:'https://www.fao.org/worldfoodsituation/foodpricesindex',coverage:'measured',cadence:'Monthly'},
      {label:'Export volumes & country food balances',evidence:'Export volumes, production, consumption, and stock-to-use estimates',source:'FAO GIEWS',url:'https://www.fao.org/giews/data-tools/en',coverage:'public-source',cadence:'Monthly / seasonal'}
    ]},
  {id:'suppliers',title:'Tier 2/3 supplier health',horizon:'Days to quarters',
    explanation:'Company-level OTIF, inventory and quality telemetry usually require supplier authorization, not open-web scraping.',
    geos:[],
    indicators:[
      {label:'On-time in-full (OTIF)',evidence:'Supplier-level verified order lines delivered on schedule in full',source:'Authorized procurement / ERP feeds',url:'https://www.oecd.org/en/topics/supply-chains.html',coverage:'restricted',cadence:'Daily / weekly'},
      {label:'Lead-time variance & quality returns',evidence:'Historical line-item lead-time spread and defects against matched baselines',source:'Supplier operational systems',url:'https://www.oecd.org/en/topics/supply-chains.html',coverage:'restricted',cadence:'Weekly'},
      {label:'Work in progress & demand-plan deviation',evidence:'Authorized inventory, WIP and order-book snapshots',source:'Authorized supplier systems',url:'https://www.oecd.org/en/topics/supply-chains.html',coverage:'not-connected',cadence:'Weekly'}
    ]},
  {id:'freight',title:'Freight price & port congestion',horizon:'Days to weeks',
    explanation:'Price indices can lead capacity constraints in some markets; AIS queue measures are often contemporaneous or lagging.',
    geos:['CN','US','SG','NL','DE','GB','IN','PA','EG','AE'],
    indicators:[
      {label:'Ocean container spot prices',evidence:'Route-level freight rate index and license terms',source:'Freightos Baltic Index',url:'https://www.freightos.com/freight-resources/freightos-baltic-index-global-container-pricing-index/',coverage:'restricted',cadence:'Weekly / daily'},
      {label:'Air cargo pricing & demand',evidence:'Commercial route-level air-cargo rate and booking metrics',source:'Freightos Air Index',url:'https://www.freightos.com/',coverage:'restricted',cadence:'Weekly'},
      {label:'Port congestion & vessel wait',evidence:'Vessel traffic and observable queues; consistent global waiting-time series not connected',source:'IMF PortWatch',url:'https://portwatch.imf.org/',coverage:'measured',cadence:'Daily'},
      {label:'Global supply-chain pressure',evidence:'Published standardized composite index, not proof of a particular chokepoint',source:'New York Fed GSCPI',url:'https://www.newyorkfed.org/research/policy/gscpi',coverage:'measured',cadence:'Monthly'}
    ]},
  {id:'inputs',title:'Commodity prices & industrial inputs',horizon:'Days to quarters',
    explanation:'Use a physical input-price panel with matched currencies and units, and separate regulatory action from price moves.',
    geos:[],
    indicators:[
      {label:'Energy inputs',evidence:'Crude oil, natural gas and coal monthly source price series',source:'World Bank Pink Sheet',url:'https://www.worldbank.org/en/research/commodity-markets',coverage:'measured',cadence:'Monthly'},
      {label:'Industrial metals & copper',evidence:'Monthly commodity spot benchmark averages; no direct supply-allocation claim',source:'World Bank Pink Sheet',url:'https://www.worldbank.org/en/research/commodity-markets',coverage:'measured',cadence:'Monthly'},
      {label:'Agricultural / fertilizer costs',evidence:'Published inputs including urea and phosphate-based fertilizers',source:'World Bank Pink Sheet',url:'https://www.worldbank.org/en/research/commodity-markets',coverage:'measured',cadence:'Monthly'},
      {label:'Trade restrictions',evidence:'Effective dates, notification status and product coverage',source:'WTO Trade Monitoring',url:'https://data.wto.org/dataset/wto_tmdb',coverage:'public-source',cadence:'Event / reporting lag'}
    ]},
  {id:'climate',title:'Climate & aging infrastructure',horizon:'Hours to decades',
    explanation:'Geospatial hazards must intersect specific exposed assets before operational risk can be assigned.',
    geos:[],
    indicators:[
      {label:'Flood, drought & heat exposure',evidence:'Location-specific anomaly, mapped asset footprint and hazard severity',source:'Copernicus Emergency Management',url:'https://emergency.copernicus.eu/',coverage:'public-source',cadence:'Daily / weekly'},
      {label:'Active disaster events',evidence:'Officially reported global disasters; not a complete all-hazards loss estimate',source:'NASA EONET',url:'https://eonet.gsfc.nasa.gov/',coverage:'measured',cadence:'Daily'},
      {label:'Infrastructure condition & maintenance',evidence:'Age, reliability, maintenance and inspection findings; incomplete outside specific jurisdictions',source:'National regulators and agencies',url:'https://infrastructurereportcard.org/',coverage:'not-connected',cadence:'Annual / irregular'}
    ]},
  {id:'gnss',title:'GNSS, orbital timing & PTP integrity',horizon:'Minutes to weeks',
    explanation:'Aviation GNSS anomalies are a regional interference proxy, not direct measurements of telecom, trading or datacenter clock drift. Failover varies by system and holdover design.',
    geos:[],
    indicators:[
      {label:'GNSS jamming & spoofing reports',evidence:'Geolocated aviation occurrence reports; compare with ADS-B quality anomalies and affected airspace',source:'EASA / EUROCONTROL',url:'https://www.easa.europa.eu/en/domains/air-operations/global-navigation-satellite-system-outages-and-alterations',coverage:'public-source',cadence:'Event / periodic'},
      {label:'Flight-derived GNSS quality anomalies',evidence:'ADS-B position-integrity anomaly clusters; noisy proxies that cannot prove intent or attribution',source:'GPSInterference.com (ADS-B derived; credit required)',url:'https://gpsinterference.com/docs',coverage:'measured',cadence:'Daily'},
      {label:'PTP and holdover oscillator drift',evidence:'Authenticated device clock offset, holdover status, sync error and redundancy paths',source:'Authorized operator telemetry',url:'https://www.nist.gov/pml/time-and-frequency-division',coverage:'restricted',cadence:'Seconds / minutes'},
      {label:'GNSS service advisories',evidence:'Official system notices and documented interference/disruption reports',source:'US GPS.gov',url:'https://www.gps.gov/support/user/',coverage:'public-source',cadence:'Event'}
    ]},
  {id:'liquidity',title:'Overnight repo & financial plumbing',horizon:'Days to quarters',
    explanation:'A financing stress screen combines rates, transaction volumes, central-bank operations and peer benchmarks; no single rate change proves mistrust or an imminent freeze.',
    geos:['US','GB','DE','FR','NL','JP','CH','CA'],
    indicators:[
      {label:'Secured overnight funding rate (SOFR)',evidence:'Daily observed transaction-based secured funding rate and publication date',source:'New York Fed',url:'https://www.newyorkfed.org/markets/reference-rates/sofr',coverage:'measured',cadence:'Business daily'},
      {label:'Overnight repo volume and rate distribution',evidence:'Daily secured borrowing volume, rate percentile dispersion and comparable prior observations',source:'New York Fed Markets API',url:'https://markets.newyorkfed.org/static/docs/markets-api.html',coverage:'measured',cadence:'Business daily'},
      {label:'Liquidity facilities & standing repo operations',evidence:'Fed operations and publicly reported usage; support action alone does not establish counterparty mistrust',source:'New York Fed / Federal Reserve',url:'https://www.newyorkfed.org/markets/desk-operations',coverage:'public-source',cadence:'Daily / weekly'},
      {label:'International money market comparison',evidence:'Local overnight indices, central bank facilities and funding-market structural differences',source:'ECB euro short-term rate',url:'https://www.ecb.europa.eu/stats/financial_markets_and_interest_rates/euro_short-term_rate/html/index.en.html',coverage:'public-source',cadence:'Business daily'}
    ]},
  {id:'oss',title:'Open-source maintainer & dependency resilience',horizon:'Weeks to years',
    explanation:'Track software supply-chain hygiene and code changes. Maintainer turnover and dormant-account activity are non-accusatory review leads, not evidence of a hostile actor.',
    geos:[],
    indicators:[
      {label:'OpenSSF Scorecard trends',evidence:'Published project security practices including code review, release signing, branch protection and maintenance',source:'OpenSSF Scorecard',url:'https://scorecard.dev/',coverage:'public-source',cadence:'Daily / monthly'},
      {label:'Dependency graph & package ecosystem',evidence:'Versioned upstream and transitive dependencies; dependency attribution must be verified',source:'Google deps.dev',url:'https://deps.dev/',coverage:'public-source',cadence:'Daily / release'},
      {label:'Ownership and release-process changes',evidence:'Project governance, role changes, review policies and signed release provenance',source:'GitHub public repository metadata',url:'https://docs.github.com/en/rest',coverage:'public-source',cadence:'Daily / event'},
      {label:'Known vulnerability disclosures',evidence:'Publicly reported vulnerability advisories; distinguish known CVEs from speculative compromise',source:'OSV.dev',url:'https://osv.dev/',coverage:'public-source',cadence:'Daily / event'},
      {label:'Maintainer social-engineering concerns',evidence:'Review only credible corroborated notices, do not score individuals or infer malicious intent from identity/churn',source:'OpenSSF guidance',url:'https://openssf.org/',coverage:'not-connected',cadence:'Evidence-dependent'}
    ]},
  {id:'topology',title:'Network dependency & cascade analysis',horizon:'Scenario-based',
    explanation:'Graph centrality requires independently sourced supplier and asset relationships. Illustrative pathways cannot produce validated contagion probabilities.',
    geos:[],
    indicators:[
      {label:'Verified multi-tier dependency graph',evidence:'Reviewed asset, facility, carrier, supplier and component relationships',source:'Public filings + licensed procurement data',url:'https://lpi.worldbank.org/en/home',coverage:'not-connected',cadence:'Entity-by-entity'},
      {label:'Betweenness & critical-node ranking',evidence:'Computed only on a sufficiently complete, versioned, evidence-linked network',source:'Analyst-reviewed graph',url:'https://portwatch.imf.org/',coverage:'not-connected',cadence:'On graph updates'},
      {label:'Failure propagation & susceptibility',evidence:'Calibrated conditional likelihood with known priors and validation; no unsupported percentage',source:'Scenario and historical failure analysis',url:'https://www.oecd.org/en/topics/supply-chains.html',coverage:'not-connected',cadence:'Model validation'}
    ]}
];
export const scenarios = [
  {id:'shipping',label:'Maritime choke',nodes:['War-risk premium or canal bidding','Booking availability','Route capacity','Freight delivery','Manufacturing inventory','Consumer availability']},
  {id:'water',label:'Water → compute',nodes:['Reservoir / river anomaly','Industrial cooling constraint','Fab / data-center operations','Component or cloud capacity','Downstream users']},
  {id:'grid',label:'Grid recovery',nodes:['Transformer backlog','Grid repair capability','Restoration duration','Industry / compute interruption','Regional economic impact']},
  {id:'chips',label:'Minerals → chips',nodes:['Mineral licensing / export controls','Refining and shipment availability','Chip and magnet input supply','Electronics and vehicle assembly','Hardware lead times']},
  {id:'food',label:'Food chain',nodes:['Gas and fertilizer input price','Farmer input decisions','Weather and growing conditions','Harvest / available grain','Wholesale and retail food price']},
  {id:'labor',label:'Labor stoppage',nodes:['Negotiation deadline or dispute','Actual work stoppage','Port / rail throughput','Parts delivery delays','Factory / retail adjustment']}
  ,{id:'timing',label:'Timing outage',nodes:['Regional GNSS interference observations','Independent operator PTP / holdover alerts','Clock drift beyond equipment tolerance','Service-specific failover or inconsistency','Potential communication or transaction disruption']}
  ,{id:'finance',label:'Funding shock',nodes:['Overnight repo rate / volume anomaly','Other secured funding benchmarks','Facility usage / lending conditions','Trade-finance cost and availability','Logistics and supplier liquidity']}
  ,{id:'software',label:'Open-source integrity',nodes:['Verified governance or release-policy change','Unexpected software artifact or dependency alteration','Independent code review / provenance evidence','Downstream affected version inventory','Patch, mitigation and recovery']}
] as const;
