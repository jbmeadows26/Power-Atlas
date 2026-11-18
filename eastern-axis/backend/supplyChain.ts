/**
 * IMF PortWatch public AIS observations, with a bounded daily lookback.
 * Numbers are vessel movements, not proof of causation or shipment origin.
 * No trading-partner claims, AI attribution, or fabricated live incidents.
 */
const PORTWATCH = 'https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query';
const PORTWATCH_HOME = 'https://portwatch.imf.org/';
const MONITORS = [
  {id:'hormuz',name:'Strait of Hormuz',match:/hormuz/i,countries:['IR','OM','AE','QA','BH','KW','SA','IQ'],sector:'Energy',exposure:'Oil, gas, fertilizer feedstocks',pathway:'Restricted tanker passage can affect fuel and fertilizer input costs.'},
  {id:'bab-mandeb',name:'Bab el-Mandeb / Red Sea',match:/mandeb|bab.el.mandab|red sea/i,countries:['YE','DJ','ER','SO','SA','EG'],sector:'Trade routes',exposure:'Asia–Europe container shipping',pathway:'Diversions around southern Africa can extend voyage times and raise freight costs.'},
  {id:'suez',name:'Suez Canal',match:/suez/i,countries:['EG'],sector:'Trade routes',exposure:'Containers, oil, manufactured goods',pathway:'Canal disruptions can increase shipping distances and delivery uncertainty.'},
  {id:'malacca',name:'Strait of Malacca',match:/malacca/i,countries:['MY','SG','ID','CN'],sector:'Industrial goods',exposure:'Electronics, energy and container traffic',pathway:'An interruption can affect Asia-linked manufacturing inputs and energy trade.'},
  {id:'panama',name:'Panama Canal',match:/panama/i,countries:['PA','US'],sector:'Trade routes',exposure:'Container and bulk transit',pathway:'Transit limits can require costly rerouting and alter shipment lead times.'},
  {id:'bosporus',name:'Turkish Straits',match:/bospor|bosphor|dardanell/i,countries:['TR','RU','UA','RO','BG'],sector:'Food & materials',exposure:'Black Sea grain, oil and bulk cargo',pathway:'Traffic disruption can constrain grains, agricultural inputs and energy flows.'},
  {id:'taiwan',name:'Taiwan Strait',match:/taiwan/i,countries:['TW','CN','JP','KR'],sector:'Industrial goods',exposure:'Semiconductors and high-value manufactured goods',pathway:'Routing uncertainty can affect electronics supply chains, without proving factory stoppage.'}
];
type Monitor = typeof MONITORS[number];
type Daily = {date:string; ships:number; cargo:number|null; tankers:number|null; containers:number|null};
type ArcFeature = {attributes?:Record<string,unknown>};
type ArcPayload = {features?:ArcFeature[];error?:{message?:string}};
const validNum = (v:unknown) => typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : null;
const dateMs = (date:string) => Date.parse(date+'T00:00:00Z');
function summarize(m:Monitor, rows:Daily[], latestDate:string) {
  const unique = new Map<string,Daily>();
  for (const row of rows) if (!unique.has(row.date)) unique.set(row.date,row);
  const latest = dateMs(latestDate);
  const recent:Daily[]=[];const previous:Daily[]=[];
  for (const row of unique.values()) {
    const difference=Math.round((latest-dateMs(row.date))/86400000);
    if (difference>=0 && difference<7) recent.push(row);
    if (difference>=7 && difference<14) previous.push(row);
  }
  const enough = recent.length>=5 && previous.length>=5;
  const average=(rs:Daily[])=>rs.length ? rs.reduce((sum,r)=>sum+r.ships,0)/rs.length : null;
  const current=enough?average(recent):null,prior=enough?average(previous):null;
  const change = current!==null && prior!==null && prior>0
    ? Math.round(((current-prior)/prior)*1000)/10 : null;
  return {
    id:m.id,name:m.name,sector:m.sector,exposure:m.exposure,pathway:m.pathway,countries:m.countries,
    reportedDays:unique.size,recentDays:recent.length,baselineDays:previous.length,
    dailyAverage:current===null?null:Math.round(current*10)/10,
    baselineDailyAverage:prior===null?null:Math.round(prior*10)/10,
    percentChange:change,
    observation:change===null?'insufficient observations':change<=-20?'reduced transit screening signal':'observed',
    note:'AIS estimate of daily vessel transits; changes do not identify cause, cargo destination, or individual actors.'
  };
}
let cache: {fetchedAt:number;data:ReturnType<typeof prepare>}|null=null;
function prepare(rows:ArcFeature[]) {
  const grouped = new Map<string,Daily[]>();
  let latestDate='';
  for(const feature of rows){
    const a=feature.attributes||{};
    const date=typeof a.date==='string'?a.date.slice(0,10):'';
    const name=typeof a.portname==='string'?a.portname:'';
    const ships=validNum(a.n_total);
    if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!name||ships===null) continue;
    if(date>latestDate)latestDate=date;
    const monitor=MONITORS.find(m=>m.match.test(name));
    if(!monitor)continue;
    const entry:Daily={date,ships,cargo:validNum(a.n_cargo),tankers:validNum(a.n_tanker),containers:validNum(a.n_container)};
    grouped.set(monitor.id,[...(grouped.get(monitor.id)||[]),entry]);
  }
  if(!latestDate)throw new Error('No valid dated PortWatch observations returned');
  return {latestDate,grouped};
}
async function sourceSnapshot() {
  const now=Date.now();
  if(cache&&now-cache.fetchedAt<20*60*1000)return cache.data;
  const params=new URLSearchParams({
    where:'1=1',
    outFields:'date,portid,portname,n_total,n_cargo,n_tanker,n_container',
    orderByFields:'date DESC',
    resultRecordCount:'1000',
    returnGeometry:'false', f:'json'
  });
  const res=await fetch(PORTWATCH+'?'+params.toString(),{
    signal:AbortSignal.timeout(8500),headers:{Accept:'application/json'}
  });
  if(!res.ok)throw new Error('PortWatch HTTP '+res.status);
  const data=await res.json() as ArcPayload;
  if(data.error||!Array.isArray(data.features))throw new Error('PortWatch did not return valid features');
  const parsed=prepare(data.features);
  cache={fetchedAt:now,data:parsed};
  return parsed;
}
export async function readSupplyChain(code:string) {
  if(code!=='all'&&!/^[A-Z]{2}$/.test(code)) return null;
  const checkedAt=new Date().toISOString();
  const matches=MONITORS.filter(m=>code==='all'||m.countries.includes(code));
  const sources=[
    {name:'IMF PortWatch · daily AIS-derived transit estimates',url:PORTWATCH_HOME,mode:'live request'},
    {name:'Federal Reserve Bank of New York · GSCPI',url:'https://www.newyorkfed.org/research/policy/gscpi',mode:'linked monthly context; not ingested'},
    {name:'World Bank · LPI 2.0',url:'https://lpi.worldbank.org/en/home',mode:'linked logistics benchmark; not ingested'},
    {name:'UN Comtrade',url:'https://comtradeplus.un.org/',mode:'trade registry reference; partner shipment joins not ingested'},
    {name:'UN Trade and Development · maritime transport',url:'https://unctad.org/topic/transport-and-trade-logistics',mode:'context and route analysis'}
  ];
  try{
    const {latestDate,grouped}=await sourceSnapshot();
    const ageDays=Math.max(0,Math.floor((Date.now()-dateMs(latestDate))/86400000));
    return {code,checkedAt,sourceDate:latestDate,sourceStatus:ageDays>10?'stale':'observed',
      dataAgeDays:ageDays,source:PORTWATCH_HOME,
      method:'Most recent 7 dated days versus prior 7, using available-day daily averages; at least 5 observations per window. Source date may lag calendar date.',
      corridors:matches.map(m=>summarize(m,grouped.get(m.id)||[],latestDate)),
      sources,limitations:['Corridor affiliation indicates exposure, not a verified trade dependency or cargo origin/destination.','Transit changes are anomaly-screening signals, not verified attacks, blockades, sanctions breaches or supply shortages.','AIS estimates may omit vessels and can be revised; no route-specific event attribution is automated.'],
      sourceCoverage:code==='all'?'Selected illustrative chokepoints, not the full global PortWatch catalog':'Only corridors explicitly mapped to the selected jurisdiction; others omitted'};
  }catch(e){
    return {code,checkedAt,sourceDate:null,sourceStatus:'unavailable',dataAgeDays:null,
      source:PORTWATCH_HOME,method:'Unavailable: current observations could not be verified.',
      corridors:matches.map(m=>({id:m.id,name:m.name,sector:m.sector,exposure:m.exposure,pathway:m.pathway,countries:m.countries,reportedDays:0,recentDays:0,baselineDays:0,dailyAverage:null,baselineDailyAverage:null,percentChange:null,observation:'unavailable',note:'No live figures substituted.'})),
      sources,limitations:['Live PortWatch fetch failed; no traffic figures or incidents have been invented.'],
      sourceCoverage:'Upstream data unavailable',warning:e instanceof Error?e.message:'Source request failed'};
  }
}
