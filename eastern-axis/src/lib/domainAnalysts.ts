/**
 * Evidence-bounded, deterministic analyst readouts.
 * Every observation must trace to an existing public source and reporting period.
 * This is NOT an LLM judgement or an attribution / forecast engine.
 */
export type EvidenceMetric={label:string;value:string;detail?:string};
export type EvidenceLink={title:string;url:string;date?:string};
export type EvidenceBrief={
  title:string;analyst:string;status:'source-dated'|'monitoring'|'coverage-gap';
  scope:string;asOf:string;finding:string;direction:string;implication:string;
  beneficiaries:string;watch:string;limitation:string;metrics:EvidenceMetric[];
  sources:EvidenceLink[];chart?:{label:string;values:number[];dates:string[]};
  coverage:string;
};
export type BriefInput={
  view:string;focus:string;country:string;countryName?:string;horizon?:string;severity?:string;
  cases:Array<{code?:string;topic?:string;source?:string;title?:string}>;
  snapshots:Record<string,unknown>;systems?:unknown;failures:string[];
};
export const ANALYST_ROUTE_KEYS=[
  'Overview','Forecast intelligence','Forecast track record','AI analyst','Collection desk','Verification lab','Coverage audit','Source library','Methodology',
  'Countries','World Factbook','Investigations','Defense intelligence','Global conflict watch','Military asset changes',
  'Cyber resilience','Economic intelligence:overview','Economic intelligence:signals','Economic intelligence:risk',
  'Economic intelligence:supply','Economic intelligence:shortages','Macro indicators','Trade indicators',
  'Corporate intelligence','Energy & resources','Demographics & biosecurity'
] as const;
export const SNAPSHOT_PATHS={
  source:'analysis/manifest.json',
  triage:'analysis/early-warning-triage.json',
  markets:'analysis/financial-markets.json',
  transmission:'analysis/financial-transmission.json',
  conflict:'analysis/global-conflict-watch.json',
  inventory:'analysis/military-inventory.json',
  changes:'analysis/military-asset-changes.json',
  shortage:'analysis/product-shortage-outlook.json',
  early:'analysis/physical-early-warning.json',
  resilience:'telemetry/resilience.json'
} as const;
type Obj=Record<string,any>;
const o=(v:unknown):Obj=>v&&typeof v==='object'&&!Array.isArray(v)?v as Obj:{};
const a=(v:unknown):Obj[]=>Array.isArray(v)?v.filter(x=>x&&typeof x==='object'&&!Array.isArray(x)) as Obj[]:[];
const s=(v:unknown):string=>typeof v==='string'&& !['null','undefined','nan'].includes(v.toLowerCase())?v:'';
const n=(v:unknown):number|null=>typeof v==='number'&&Number.isFinite(v)?v:null;
const f=(v:number|null,decimal=0):string=>v===null?'—':v.toLocaleString('en-US',{maximumFractionDigits:decimal});
const pct=(v:number|null):string=>v===null?'—':(v>0?'+':'')+f(v,1)+'%';
const latest=(...dates:string[]):string=>dates.filter(x=>Number.isFinite(Date.parse(x))).sort().at(-1)||'Not reported';
const source=(row:Obj):EvidenceLink|null=>{
 const url=s(row.sourceUrl)||s(row.url);
 if(!url.startsWith('https://'))return null;
 return {title:s(row.publisher)||s(row.source)||s(row.agency)||s(row.name)||s(row.title)||'Original public source',
         url,date:s(row.period)||s(row.published)||s(row.date)||s(row.observedAt)};
};
const sources=(rows:Obj[],max=4):EvidenceLink[]=>{
 const seen=new Set<string>(),list:EvidenceLink[]=[];
 for(const row of rows){const x=source(row);if(x&&!seen.has(x.url)){list.push(x);seen.add(x.url);}if(list.length>=max)break;}
 return list;
};
const countries=(rows:Obj[]):number=>new Set(rows.map(r=>s(r.code)).filter(Boolean)).size;
const count=(rows:Obj[],p:(r:Obj)=>boolean)=>rows.filter(p).length;
const forCountry=(rows:Obj[],country:string,key='code')=>country==='all'?rows:rows.filter(x=>x[key]===country);
const base=(title:string,analyst:string,scope:string):EvidenceBrief=>({
 title,analyst,status:'coverage-gap',scope,asOf:'Not reported',finding:'No verified current reading is available for this view.',
 direction:'Outside-normal change: not established.',implication:'A missing observation cannot establish improvement, deterioration, or absence of activity.',
 beneficiaries:'Beneficiaries or causal winners have not been established by the indexed evidence.',
 watch:'Next check: retrieve comparable source-dated observations before classifying a change.',
 limitation:'No figure is substituted for unavailable data.',metrics:[],sources:[],coverage:'Unverified coverage'
});
const metric=(label:string,value:number|null,detail?:string,decimal=0):EvidenceMetric=>({label,value:f(value,decimal),detail});
const exposure=(b:EvidenceBrief,rows:Obj[])=>{
 b.sources=sources(rows);b.coverage=rows.length+' source-linked observations in scope';
 if(rows.length)b.status='source-dated';
 return b;
};
/** Only analyst routes that consume WDI context may request it. */
export function needsGlobalSystems(view:string,focus:string):boolean{
 return ['Macro indicators','Trade indicators','Energy & resources','Demographics & biosecurity'].includes(view)
   ||(view==='Economic intelligence'&&['overview','signals','risk','systems','supply','shortages'].includes(focus));
}
export function buildDomainBrief(input:BriefInput):EvidenceBrief{
 const {view,focus,country,countryName,cases,snapshots,systems,failures}=input;
 const key=view==='Economic intelligence'?(focus==='systems'?'Macro indicators':'Economic intelligence:'+focus):view;
 const scope=country==='all'?'Worldwide':countryName||country;
 const data=(key:string)=>o(snapshots[key]);
 const triage=data('triage'),manifest=data('source'),inventory=data('inventory'),conflict=data('conflict');
 const markets=data('markets'),transmission=data('transmission'),shortage=data('shortage');
 const early=data('early'),change=data('changes'),resilience=data('resilience'),system=o(systems);
 const reviews=a(triage.reviews),documents=a(manifest.records),assets=forCountry(a(inventory.assets),country);
 const earlyMetrics=a(early.metrics),marketMetrics=a(markets.metrics),households=a(transmission.householdMetrics);
 const forecasts=a(shortage.forecasts),zones=a(conflict.zones).filter(z=>country==='all'||(Array.isArray(z.countryCodes)&&z.countryCodes.includes(country)));
 const historical=a(system.indicators);
 const reported=historical.filter(x=>n(x.value)!==null);
 const localCases=country==='all'?cases:cases.filter(c=>c.code===country);
 let b:EvidenceBrief;
 if(view==='Forecast intelligence'||view==='Forecast track record') return {...base(view,'Forecast verification analyst',scope),finding:'No validated point-in-time forecast cohort is published.',watch:'Validate historical observations and independently resolved outcomes before issuing probabilities.',metrics:[metric('Validated forecasts',null),metric('Brier score',null)],coverage:'Forecast evidence unavailable'};
 const recent=latest(s(triage.generatedAt),s(manifest.generatedAt));
 if(['Overview','AI analyst','Collection desk','Verification lab','Coverage audit','Source library','Methodology'].includes(view)){
   b=base(view==='Overview'?'Cross-domain intelligence status':view+' · evidence review','Cross-domain verification analyst','Worldwide source coverage');
   const screened=count(reviews,r=>r.screened===true), reviewed=count(reviews,r=>r.modelReviewed===true);
   const promoted=count(reviews,r=>r.status==='elevated'&&r.fresh===true&&r.modelReviewed===true&&r.anomalous===true&&r.corroborated===true);
   b.metrics=[metric('Source publications',documents.length,'Indexed leads, not verified threats'),
              metric('Signals reviewed',reviewed,screened+' screened'),
              metric('Corroborated alerts',promoted,'Validated metric anomalies only')];
   b.asOf=recent;b.finding=documents.length+' dated public-source records are indexed; '+reviewed+' signals have an analyst review. '+promoted+' meet the complete promotion gate.';
   b.direction='System-wide direction cannot be inferred from the number of publications or screened anomalies.';
   b.implication='The command center is a review queue; unchanged alert counts do not imply an absence of threats.';
   b.watch='Check source freshness, original report links, missing jurisdictions, and unreviewed observations before escalation.';
   b.limitation='Publisher jurisdiction and headline mentions are not proof of state attribution. Reviewed signals and source records are different measures.';
   b.beneficiaries='No geopolitical or market beneficiaries are inferred from source-volume counts.';
   b=exposure(b,documents);b.sources=sources([...reviews,...documents].filter(x=>source(x)),4);b.status=reviews.length||documents.length?'monitoring':'coverage-gap';
 }else if(['Countries','World Factbook','Investigations'].includes(view)){
   b=base(view==='World Factbook'?'Country evidence & historical context':view==='Investigations'?'Documented investigations':'Country intelligence coverage','Geopolitical evidence analyst',scope);
   const docs=documents.filter(d=>{
    if(country==='all')return Array.isArray(d.countries)&&d.countries.length>0;
    return Array.isArray(d.countries)&&d.countries.includes(country);
   });
   const mentions=documents.filter(d=>Array.isArray(d.inferredCountries)&&d.inferredCountries.some((e:Obj)=>e.code===country));
   b.metrics=[metric('Indexed case files',localCases.length,'Legal case records, not proven state direction'),
              metric('Country-tagged reports',docs.length,'Explicit source country tags'),
              metric(country==='all'?'World-aggregate WDI indicators':'Historical WDI indicators',reported.length,country==='all'?'Worldwide figures only, not country attribution':'Non-null observations')];
   b.finding=country==='all'?
     cases.length+' case files and '+documents.length+' government/publication records are indexed across the directory.':
     scope+' has '+localCases.length+' indexed legal cases and '+docs.length+' explicitly tagged source publications.'+(mentions.length?' '+mentions.length+' title-derived mentions are indexed separately.':'');
   b.asOf=latest(s(manifest.generatedAt),s(system.checkedAt));
   b.direction='More indexed reports do not establish rising foreign activity, security risk, or a trend.';
   b.implication='Compare the linked case outcomes and historical country indicators before interpreting country exposure.';
   b.beneficiaries='No responsible government, financial beneficiary, or ownership chain follows solely from a country association.';
   b.watch='Examine updated case disposition, source dates, country tag basis, and the next comparable WDI release.';
   b.limitation='World Factbook material is historical; the intelligence index is incomplete. Inferred headline mentions do not establish attribution.';
   b.sources=sources([...localCases.map(c=>({url:c.source,source:'DOJ case file'})),...docs,...reported],4);
   b.coverage=docs.length+' explicitly country-tagged publications; '+localCases.length+' cases';
   b.status=b.sources.length?'source-dated':'coverage-gap';
 }else if(view==='Defense intelligence'){
   b=base('Military capability inventory','Defense inventory analyst',scope);
   const quantified=assets.filter(x=>n(x.value)!==null&&s(x.quantity)!=='Not quantified');
   const nuclear=assets.find(x=>x.status==='military-stockpile'&&n(x.value)!==null);
   const example=assets.find(x=>x.category==='Naval'&&n(x.value)!==null)||assets.find(x=>x.category==='Air'&&n(x.value)!==null);
   const feature=nuclear||example;
   b.metrics=[metric('Sourced observations',assets.length,'Not a count of equipment'),
              metric('Quantified records',quantified.length,'Source-dated estimates'),
              country==='all'?metric('Countries represented',countries(assets),'Observations are not complete inventories'):
              {label:feature?'Example: '+s(feature.name):'Reported categories',
               value:feature?s(feature.quantity)||'—':(assets.length?f(new Set(assets.map(x=>x.category)).size):'—'),
               detail:feature?s(feature.published)+' · '+s(feature.publisher):'Source coverage; not equipment totals'}];
   b.finding=assets.length+' source-attributed observations are indexed'+(country==='all'?' across '+countries(assets)+' countries':' for '+scope)+'. '+quantified.length+' contain quantities or monetary values.'+(country!=='all'&&nuclear?' '+s(nuclear.quantity)+' warheads is the published military-stockpile estimate, not the deployed total.':'');
   b.direction='These are snapshots, not evidence of inventory growth or decline. Compare identical equipment definitions and observation years.';
   b.implication='No readiness, deployable strength, or procurement rate can be inferred by summing military record counts.';
   b.beneficiaries='An equipment estimate alone cannot identify a military advantage, beneficiary, or conflict outcome.';
   b.watch='Compare independently dated inventory snapshots by unit, basis, and year; separate active, stored, deployed and retired categories.';
   b.limitation='Warhead subsets overlap; spending is not equipment; historic personnel estimates are not current force counts.';
   b.asOf=latest(s(inventory.generatedAt),s(inventory.reviewedAsOf));
   b=exposure(b,assets);
 }else if(view==='Global conflict watch'){
   b=base('Armed-conflict deviation watch','Conflict anomaly analyst',scope);
   const review=zones.filter(z=>z.status==='review'&&z.modelReviewed!==true);
   const promoted=zones.filter(z=>z.promoted===true);
   const comparable=zones.filter(z=>o(z.change).status==='assessable'&&n(o(z.change).robustZ)!==null&&n(o(z.change).changePct)!==null)
     .sort((x,y)=>Math.abs(n(o(y.change).robustZ)||0)-Math.abs(n(o(x.change).robustZ)||0));
   const lead=comparable[0];
   b.metrics=[metric('Monitored theaters',zones.length,'UCDP-coded event baseline'),
              metric('Pending verification',review.length,'Not command alerts'),
              metric('Elevated / corroborated',promoted.length,'Only verified exceptions')];
   b.finding=zones.length+' conflict theaters are indexed; '+review.length+' require review and '+promoted.length+' have passed the escalation criteria.'+(lead?' Largest screened historical departure: '+s(lead.name)+' '+pct(n(o(lead.change).changePct))+' relative to its source baseline; '+(lead.status==='review'?'awaiting review':'monitored')+'.':'');
   b.direction=promoted.length===0?'Historical event-count deviations are only candidates; no current exceptional deterioration or improvement has passed the independent gate.':'Source-qualified exception reviews are present; inspect each theater before concluding a global trend.';
   b.implication='Coded-event history describes recorded incidents, not real-time military positions or civilian safety forecasts.';
   b.beneficiaries=lead&&s(lead.whoBenefits)?s(lead.whoBenefits):'The available event trends do not establish who gains territory or political advantage.';
   b.watch='Compare like-for-like coded-event windows, reporting delays, verified actor claims and new humanitarian evidence.';
   b.limitation='UCDP candidate records are retrospective, and news mentions are not event verification. No beneficiary is inferred from actor lists.';
   b.asOf=latest(s(conflict.generatedAt),s(o(conflict.measurement).latestCodedEvent));
   b.sources=sources(zones.flatMap(z=>a(z.evidence)),4);
   b.coverage=zones.length+' theaters; '+review.length+' review candidates';b.status=zones.length?'monitoring':'coverage-gap';
 }else if(view==='Military asset changes'){
   b=base('Military capability change detection','Military anomaly analyst',scope);
   const observations=forCountry(a(change.assessments),country);
   const verified=count(observations,r=>r.reviewedException===true);
   const queued=count(observations,r=>r.status==='review'||r.status==='review-queue');
   b.metrics=[metric('Historical change series',observations.length,'Compare identical equipment definitions'),
              metric('Reviewed exceptions',verified,'Not confirmed force movements'),
              metric('Pending reviews',queued,'Unverified anomalies')];
   b.finding=observations.length?observations.length+' dated change-series observations are indexed; '+verified+' are assessed exceptions.':
      'The country-level change-series snapshot is unavailable or contains no comparable observations.';
   b.direction=verified?'Historical deviations have been reviewed; present-day changes require new corroboration.':'No current out-of-normal force change is established by the available series.';
   b.implication='Annual arms deliveries, military spending, and in-service equipment holdings are different metrics.';
   b.beneficiaries='No source-backed beneficiary determination is available from the change series alone.';
   b.watch='Confirm the baseline, type, country, independent source and observation period before promotion.';
   b.limitation='A static inventory is not evidence of a change. Missing multiyear holdings cannot be imputed as zero.';
   b.asOf=s(change.generatedAt)||'Not published';b=exposure(b,observations);
 }else if(view==='Cyber resilience'){
   b=base('Systems and cyber-resilience monitor','Cyber resilience analyst','Worldwide infrastructure telemetry');
   const observations=a(resilience.observations),incidents=a(resilience.incidents);
   const current=!failures.includes('resilience')&&resilience.status!=='unavailable'&&observations.length>0&&Number.isFinite(Date.parse(s(resilience.checkedAt)))&&Date.now()-Date.parse(s(resilience.checkedAt))<=120*60000;
   b.metrics=[metric('Sampled observations',current?observations.length:null,'Current telemetry; unavailable or stale is not zero'),
              metric('Corroborated incidents',current?incidents.length:null,'Current source-specific classification'),
              metric('Collection capabilities',a(resilience.capabilities).length,'Availability is not active sampling')];
   b.finding=observations.length?observations.length+' published observations and '+incidents.length+' incident records are available.':'No current independently sampled resilience observations have been published.';
   b.direction='Network deterioration or recovery cannot be assessed without comparable fresh samples.';
   b.implication='Do not interpret an unavailable collector as zero cyber activity or operational stability.';
   b.beneficiaries='Attribution and beneficiary analysis require corroborated incident evidence not present in this aggregate.';
   b.watch='Check live collector health, failed regions, sample times and cross-network corroboration.';
   b.limitation='Sampling coverage is partial; a provider outage and a malicious attack are not equivalent.';
   b.asOf=s(resilience.checkedAt)||'Not yet collected';b=exposure(b,observations);if(!current){b.status='coverage-gap';b.finding='No current independently sampled resilience telemetry is usable; archived observations do not establish present network conditions.';}
 }else if(['Economic intelligence:overview','Economic intelligence:signals','Economic intelligence:risk','Macro indicators'].includes(key)){
   b=base(key==='Economic intelligence:risk'?'Systemic financial risk interpretation':key==='Economic intelligence:signals'?'Market anomalies & warning':'Macroeconomic change dashboard','Macroeconomic risk analyst',scope);
   const market=marketMetrics.find(x=>x.id==='SP500')||marketMetrics[0];
   const screened=count(reviews,r=>r.screened===true);
   const anomalous=count(reviews,r=>r.anomalous===true);
   const flagged=count(reviews,r=>r.modelReviewed&&r.status==='elevated'&&r.corroborated);
   const inflation=historical.find(x=>x.code==='FP.CPI.TOTL.ZG');
   b.metrics=[{label:'S&P 500 · 5 sessions',value:pct(n(market?.change5Pct)),detail:'US market benchmark, not local-country data'},
              {label:'Reviewed warning signals',value:f(count(reviews,r=>r.modelReviewed===true)),detail:screened+' screened; '+anomalous+' statistical exceptions'},
              {label:country==='all'?'World-aggregate inflation':'Country inflation',value:inflation&&n(inflation.value)!==null?pct(n(inflation.value)):'—',detail:inflation?.year?'Reported '+inflation.year:'No comparable observation'}];
   b.finding=market?
     'The cited U.S. S&P 500 benchmark moved '+pct(n(market.change5Pct))+' over five trading sessions; '+flagged+' screened signals currently meet all promotion gates.':
     'Current benchmark market movement is unavailable; '+screened+' global warning signals have been screened.';
   b.direction='The observed benchmark move is not, by itself, proof of an exceptional macroeconomic regime or a future crash.';
   b.implication='Market volatility, credit impairment, and national economic growth are different indicators; confirm transmission before declaring systemic stress.';
   b.beneficiaries='Who profits from or absorbs losses in a market move is not identifiable from headline index observations.';
   b.watch='Monitor comparable market history, corporate credit filings, liquidity and official GDP/employment releases.';
   b.limitation='Market snapshot is US-wide; country WDI measurements are historical. This readout does not apply the navigation time filter to historical observations.';
   b.asOf=latest(s(markets.checkedAt),s(triage.generatedAt),s(system.checkedAt));
   b.sources=sources([...marketMetrics,...reviews,...reported],4);
   b.coverage=marketMetrics.length+' market series · '+reviews.length+' warning reviews';
   b.status=b.sources.length?'monitoring':'coverage-gap';
   if(market){const hist=a(market.history).filter(x=>n(x.value)!==null&&Number.isFinite(Date.parse(s(x.date)))).slice(-16);const values=hist.map(x=>n(x.value) as number);
    if(values.length>=3)b.chart={label:s(market.label)+' · last '+values.length+' reported closes',values,dates:hist.map(x=>s(x.date))};}
 }else if(['Economic intelligence:supply','Economic intelligence:shortages','Trade indicators'].includes(key)){
   b=base(key==='Economic intelligence:shortages'?'Product shortage forecast audit':key==='Trade indicators'?'Trade dependence & exposure':'Supply chain pressure screen','Supply chain analyst',scope);
   const watch=count(forecasts,x=>x.status==='cross-source-watch');
   const watchLead=forecasts.find(x=>x.status==='cross-source-watch');
   const confirmed=count(forecasts,x=>x.confirmedShortage===true);
   const eligible=count(forecasts,x=>x.commandEligible===true);
   const trade=historical.find(x=>x.code==='NE.TRD.GNFS.ZS');
   b.metrics=[metric('Products screened',forecasts.length,'Scenario forecasts, not confirmed disruptions'),
              metric('Cross-source watches',watch,'Require investigation'),
              {label:key==='Trade indicators'?'Trade / GDP':'Confirmed shortages',value:key==='Trade indicators'?(trade&&n(trade.value)!==null?pct(n(trade.value)):'—'):f(confirmed),detail:key==='Trade indicators'?'Country WDI reporting period: '+(trade?.year||'missing'):'Do not confuse watches with stockouts'}];
   b.finding=key==='Trade indicators'&&trade&&n(trade.value)!==null?
     scope+' reported trade openness of '+pct(n(trade.value))+' in '+s(trade.year)+'. A high ratio is not a direct measure of dependency on any one country.':
     forecasts.length+' product groups are screened; '+watch+' have cross-source watches and '+confirmed+' are independently confirmed as shortages.'+(watchLead?' Highest-priority watch: '+s(watchLead.product)+'; not a verified retail stockout.':'');
   b.direction='A price increase, transit disruption, or reduced shipment volume alone cannot establish a retail shortage.';
   b.implication='Demand, inventory, delivery and substitution conditions must be verified before making a shortage prediction.';
   b.beneficiaries='Potential importer, supplier or consumer gains/losses are hypotheses until exposures and contract terms are documented.';
   b.watch=watchLead&&Array.isArray(watchLead.missingEvidence)?'Evidence still needed for '+s(watchLead.product)+': '+watchLead.missingEvidence.filter((v:unknown)=>typeof v==='string').slice(0,3).join('; ')+'.':'Corroborate product-specific stock levels, order books, shipping origins/destinations and subsequent replenishment.';
   b.limitation='Scenario watch scores are not calibrated shortage probabilities. Worldwide shipping signals are not automatically country-specific.';
   b.asOf=latest(s(shortage.generatedAt),s(system.checkedAt));
   b.sources=sources([...forecasts.flatMap(x=>a(x.evidence)),...reported],4);
   b.coverage=forecasts.length+' product groups · '+eligible+' eligible for command promotion';
   b.status=b.sources.length?'monitoring':'coverage-gap';
 }else if(view==='Corporate intelligence'){
   b=base('Corporate credit and balance-sheet coverage','Corporate exposure analyst','U.S. public issuer and lending benchmarks');
   const issuers=a(transmission.issuers),filings=a(transmission.filings);
   const secUnavailable=issuers.length>0&&issuers.every(x=>x.status==='unavailable');
   b.metrics=[metric('Issuers indexed',issuers.length,'Coverage does not equal current SEC filings'),
              metric('Retrieved filings',secUnavailable?null:filings.length,'Original SEC documents; blocked access is not zero filings'),
              metric('Household credit metrics',households.length,'Dated official benchmarks')];
   b.finding=issuers.length+' issuer references and '+households.length+' household credit series are indexed; '+(secUnavailable?'SEC issuer filings are unavailable.':filings.length+' source filings are currently retrieved.');
   b.direction='Balance-sheet deterioration or credit contagion cannot be confirmed without comparable filings and exposure dates.';
   b.implication='A missing SEC filing is a collection gap, not evidence of a clean or distressed company.';
   b.beneficiaries='Lender, borrower or hedge-fund gains and losses cannot be quantified without security-level exposure data.';
   b.watch='Collect current EDGAR filings, debt maturity schedules and issuer-to-lender financing commitments.';
   b.limitation='This feed is U.S.-focused, not a comprehensive international corporate counterparty graph.';
   b.asOf=s(transmission.checkedAt)||'Unreported';
   b.sources=sources([...households,...issuers],4);b.coverage=issuers.length+' issuer references, '+filings.length+' filings';
   b.status=b.sources.length?'monitoring':'coverage-gap';
 }else if(view==='Energy & resources'){
   b=base('Energy, resources and physical supply','Energy-security analyst',scope);
   const energy=earlyMetrics.filter(x=>/energy|oil|petrol|gas|electric|power|fuel|coal|crude|commodity/i.test([x.group,x.label,x.id].join(' ')));
   const energyWdi=reported.filter(x=>['EG.ELC.ACCS.ZS','EG.FEC.RNEW.ZS','EG.IMP.CONS.ZS','NY.GDP.TOTL.RT.ZS'].includes(x.code));
   const brent=energy.find(x=>/Brent crude oil/i.test(s(x.label)));
   b.metrics=[metric('Physical-source series',energy.length,'Global signals, not country attribution'),
              metric('Country / world WDI',energyWdi.length,'Historical national or worldwide context'),
              {label:'Brent crude · global',value:brent&&n(brent.value)!==null?'$'+f(n(brent.value),2)+'/bbl':'—',detail:brent?s(brent.period)+' reported price, not local retail cost':'No current benchmark'}];
   b.finding=energy.length+' energy-relevant monitored physical indicators are indexed; '+energyWdi.length+' reported World Bank energy indicators are in this country scope.';
   b.direction='A change in electricity access, commodity pricing or energy imports cannot be classified as abnormal without a matching historical baseline.';
   b.implication='Distinguish energy production, consumption, dependence, route constraints and retail price effects.';
   b.beneficiaries='Producers and importers may face different exposures; beneficiaries are not established without volumes, contracts and costs.';
   b.watch='Confirm generation capacity, latest energy mix, corridor disruptions and comparable import/export reporting periods.';
   b.limitation='Cross-country baselines have differing publication years. Aggregate sector metrics cannot be presented as national supply counts.';
   b.asOf=latest(s(early.checkedAt),s(system.checkedAt));b.sources=sources([...energy,...energyWdi],4);
   b.coverage=energy.length+' physical series; '+energyWdi.length+' WDI country indicators';b.status=b.sources.length?'monitoring':'coverage-gap';
 }else if(view==='Demographics & biosecurity'){
   b=base('Population, emissions and human security','Demographic & climate analyst',scope);
   const indicators=reported.filter(x=>['SI.POV.GINI','SP.DYN.LE00.IN','EN.ATM.CO2E.PC'].includes(x.code));
   const life=indicators.find(x=>x.code==='SP.DYN.LE00.IN');
   const carbon=indicators.find(x=>x.code==='EN.ATM.CO2E.PC');
   const gini=indicators.find(x=>x.code==='SI.POV.GINI');
   b.metrics=[{label:'Life expectancy',value:life&&n(life.value)!==null?f(n(life.value),1)+' years':'—',detail:life?.year||'No national observation'},
              {label:'CO₂ / person',value:carbon&&n(carbon.value)!==null?f(n(carbon.value),2)+' tonnes':'—',detail:carbon?.year||'No national observation'},
              {label:'Gini index',value:gini&&n(gini.value)!==null?f(n(gini.value),1):'—',detail:gini?.year||'No comparable survey'}];
   b.finding=indicators.length+' historical population, inequality or climate indicators are reported for this geographic scope.';
   b.direction='A current population or epidemiological emergency cannot be inferred from historical annual demographic readings.';
   b.implication='Track survey methodology and observation years; environmental exposure and measured disease events are different datasets.';
   b.beneficiaries='No beneficiary or causal policy attribution is supported by these aggregate indicators.';
   b.watch='Verify latest country-year observations and independent, directly sampled public-health or climate event feeds.';
   b.limitation='No active epidemic or outbreak monitoring is implied by the World Bank demographic series.';
   b.asOf=s(system.checkedAt)||'Country data unreported';
   b.sources=sources(indicators,4);b.coverage=indicators.length+' national context indicators';
   b.status=b.sources.length?'source-dated':'coverage-gap';
 }else{
   b=base(view+' · source assessment','Evidence validation analyst',scope);
   b.limitation='This workspace has not been mapped to an approved evidence stream. Its existing charts and data remain available.';
 }
 if(!ANALYST_ROUTE_KEYS.includes(key as (typeof ANALYST_ROUTE_KEYS)[number])){
   b.status='coverage-gap';b.watch='Map this section to a verified source-backed analyst before publication.';
 }
 const needed={
  'Overview':['triage','source'],'AI analyst':['triage'],'Collection desk':['source'],
  'Verification lab':['source'],'Coverage audit':['source'],'Source library':['source'],
  'Methodology':['source'],'Countries':['source'],'World Factbook':['source'],
  'Investigations':['source'],'Defense intelligence':['inventory'],'Global conflict watch':['conflict'],
  'Military asset changes':['changes'],'Cyber resilience':['resilience'],
  'Economic intelligence:overview':['markets','triage'],
  'Economic intelligence:signals':['markets','triage'],'Economic intelligence:risk':['markets','transmission'],
  'Economic intelligence:supply':['shortage'],'Economic intelligence:shortages':['shortage'],
  'Macro indicators':[],'Trade indicators':[],
  'Corporate intelligence':['transmission'],'Energy & resources':[],
  'Demographics & biosecurity':['source']
 } as Record<string,string[]>;
 // Baseline cards must describe the chosen country and category, not repeat U.S. market or worldwide shortage statistics.
 const baselineCodes:Record<string,string[]>={
  'Macro indicators':['NY.GDP.MKTP.KD.ZG','FP.CPI.TOTL.ZG','SL.UEM.TOTL.ZS'],
  'Trade indicators':['NE.TRD.GNFS.ZS','BX.KLT.DINV.WD.GD.ZS'],
  'Energy & resources':['EG.ELC.ACCS.ZS','EG.FEC.RNEW.ZS','EG.IMP.CONS.ZS','NY.GDP.TOTL.RT.ZS']
 };
 const baselineLabels:Record<string,string>={
  'NY.GDP.MKTP.KD.ZG':'GDP growth','FP.CPI.TOTL.ZG':'Consumer inflation','SL.UEM.TOTL.ZS':'Unemployment',
  'NE.TRD.GNFS.ZS':'Trade / GDP','BX.KLT.DINV.WD.GD.ZS':'FDI / GDP','EG.ELC.ACCS.ZS':'Electricity access',
  'EG.FEC.RNEW.ZS':'Renewable consumption','EG.IMP.CONS.ZS':'Net energy imports','NY.GDP.TOTL.RT.ZS':'Resource rents'
 };
 if(baselineCodes[key]){
  const ids=baselineCodes[key],rows=ids.map(id=>reported.find(x=>x.code===id));
  b.metrics=ids.map((id,index)=>{const row=rows[index];return {label:baselineLabels[id],value:row?pct(n(row.value)):'—',detail:row?s(row.year)+' · '+(s(row.sourceName)||'Original source'):'No comparable country observation'};});
  const present=rows.filter((row):row is Obj=>!!row);
  b.sources=sources(present,4);b.coverage=present.length+'/'+ids.length+' country or world-aggregate baseline series';
  b.asOf=s(system.checkedAt)||'Not reported';b.status=present.length===ids.length?'source-dated':'coverage-gap';
  b.finding=present.length?scope+' has '+present.length+' of '+ids.length+' source-dated baseline indicators; each retains its original reporting year.':'Country baseline observations are currently unavailable, not zero.';
  b.direction='Annual historical indicators cannot establish a current anomaly without comparable observations.';
  b.chart=undefined;
 }
 const missing=(needed[key]||[]).filter(x=>failures.includes(x)||!o(snapshots[x]).schemaVersion);
 if(missing.length){b.coverage+=' · Missing source channel: '+missing.join(', ');
  b.limitation+=' Required source channels unavailable or refresh failed: '+missing.join(', ')+'. Last valid dated observations may remain visible as historical context.';
  b.status='coverage-gap';}
 if(!manifest.schemaVersion&&missing.includes('source')&&['Overview','AI analyst','Collection desk','Verification lab','Coverage audit','Source library','Methodology'].includes(view)){
  const triageReady=Boolean(triage.schemaVersion);
  b.finding='Government publication coverage unavailable (not zero). '+
    (triageReady?count(reviews,r=>r.modelReviewed===true)+' analyst reviews remain source-dated.':'Signal review coverage is also unavailable.');
 }
 if(!manifest.schemaVersion&&missing.includes('source')&&['Countries','World Factbook','Investigations'].includes(view)){
  b.finding=localCases.length+' indexed legal cases remain visible; government source-publication coverage is unavailable, not zero.';
 }
 if((needed[key]||[]).length>0&&missing.length===(needed[key]||[]).length&&!b.sources.length){
  b.finding='The required source snapshot for this view is unavailable or has not been published. No measurements have been substituted.';
  b.direction='Current improvement, deterioration, and exceptional deviation are not assessable from missing evidence.';
 }
 // A missing collection channel must never turn into a displayed numeric zero.
 // Each tile declares its controlling dataset; still show independently verified tiles.
 const tileSources:Record<string,string[]>={
  'Overview':['source','triage','triage'],'AI analyst':['source','triage','triage'],
  'Collection desk':['source','triage','triage'],'Verification lab':['source','triage','triage'],
  'Coverage audit':['source','triage','triage'],'Source library':['source','triage','triage'],
  'Methodology':['source','triage','triage'],
  'Countries':['cases','source','country'],'World Factbook':['cases','source','country'],
  'Investigations':['cases','source','country'],'Defense intelligence':['inventory','inventory','inventory'],
  'Global conflict watch':['conflict','conflict','conflict'],
  'Military asset changes':['changes','changes','changes'],
  'Cyber resilience':['resilience','resilience','resilience'],
  'Economic intelligence:overview':['markets','triage','country'],
  'Economic intelligence:signals':['markets','triage','country'],
  'Economic intelligence:risk':['markets','triage','country'],
  'Macro indicators':['country','country','country'],
  'Economic intelligence:supply':['shortage','shortage','shortage'],
  'Economic intelligence:shortages':['shortage','shortage','shortage'],
  'Trade indicators':['country','country'],
  'Corporate intelligence':['transmission','transmission','transmission'],
  'Energy & resources':['country','country','country','country'],
  'Demographics & biosecurity':['country','country','country']
 };
 const available=(channel:string)=>channel==='cases'||(channel==='country'
    ? Array.isArray(system.indicators)
    : Boolean(o(snapshots[channel]).schemaVersion));
 b.metrics=b.metrics.map((m,index)=>{
   const channel=tileSources[key]?.[index];
   if(channel&&!available(channel))return {...m,value:'—',detail:'No source-verified observation; not zero'};
   if(channel&&failures.includes(channel))return {...m,detail:(m.detail?m.detail+' · ':'')+'Last valid snapshot; refresh failed'};
   return m;
 });
 if(Object.keys(snapshots).length===0&&!baselineCodes[key]){
   b.status='coverage-gap';
   b.finding=failures.length?'No validated evidence snapshots are currently available for this view.':
     'Loading source-validated intelligence observations for this view.';
   b.direction='No improvement, deterioration, or exceptional deviation can yet be evaluated.';
   b.sources=[];b.chart=undefined;
 }
 if((input.horizon&&input.horizon!=='all')||(input.severity&&input.severity!=='all')){
   b.limitation+=' Time and threat controls filter the alert inbox; this assessment preserves full, dated source comparisons.';
 }
 if(country!=='all'&&['Economic intelligence:overview','Economic intelligence:signals','Economic intelligence:risk','Economic intelligence:supply','Economic intelligence:shortages','Corporate intelligence','Cyber resilience'].includes(key)){
   b.scope+=' · global or U.S. comparator (NOT country-attributed)';
 }
 return b;
}
