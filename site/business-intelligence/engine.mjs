import {validateProvenance} from "./documents.mjs";
// External intelligence for importers, distributors and manufacturers.
export const feeds={
 shortage:{title:"Product shortage outlook",path:"eastern-axis/public/analysis/product-shortage-outlook.json",array:"forecasts"},
 physical:{title:"Physical early warning",path:"eastern-axis/public/analysis/physical-early-warning.json",array:"metrics"},
 conflicts:{title:"Global conflict watch",path:"eastern-axis/public/analysis/global-conflict-watch.json",array:"zones"},
 warning:{title:"Early warning triage",path:"eastern-axis/public/analysis/early-warning-triage.json",array:"reviews"},
 markets:{title:"Financial markets",path:"eastern-axis/public/analysis/financial-markets.json",array:"metrics"},
 finance:{title:"Financial transmission",path:"eastern-axis/public/analysis/financial-transmission.json",array:"householdMetrics"},
 marketPower:{title:"Market power evidence",path:"data/market-power/evidence-v1.json",array:"cases"},
 influence:{title:"Business influence evidence",path:"data/business-influence/evidence-v1.json",array:"cases"}
};
export const products={fuel:"Transport fuels",sugar:"Sugar-containing foods",appliances:"Appliances and metal components",batteries:"Battery and energy-storage components",bread:"Wheat-based foods",wiring:"Electrical wiring and equipment",rice:"Rice-based staples",maize:"Corn and animal feed",meat:"Meat and animal protein","cooking-oils":"Cooking oils",dairy:"Dairy products",fertilizer:"Agricultural fertilizers",medicines:"Essential medicines",semiconductors:"Semiconductors and electronics"};
export const corridors=["Hormuz","Suez","Panama","Malacca","Bab el-Mandeb","Taiwan Strait","Cape of Good Hope","Gibraltar","Bosporus","Dover"];
export const marketTopics=["Food","Health","Jobs","Digital","Travel","Housing","Payments","Utilities"];
export const currency=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:2}).format(n);
export const pct=n=>(n>0?"+":"")+n.toFixed(1)+"%";
const number=n=>typeof n==="number"&&Number.isFinite(n);
const text=s=>typeof s==="string"&&s.trim()&&s.length<=500;
export function safeURL(s){try{const u=new URL(s);return u.protocol==="https:"&&!u.username&&!u.password?u.href:null;}catch{return null;}}
export function observation(s,now=Date.now(),maxDays=90){
 if(typeof s!=="string"||!/^\d{4}-\d{2}(?:-\d{2})?(?:T.*Z)?$/.test(s))return "undated";
 const stamp=Date.parse(s.length===7?s+"-01":s);
 if(!Number.isFinite(stamp)||stamp>now+86400000)return "invalid";
 if(s.length===10&&new Date(stamp).toISOString().slice(0,10)!==s)return "invalid";
 return now-stamp>maxDays*86400000?"stale":"dated";
}
export function validFeed(key,x){return !!(Object.hasOwn(feeds,key)&&x&&typeof x==="object"&&Array.isArray(x[feeds[key].array])&&x[feeds[key].array].every(r=>r&&typeof r==="object"&&!Array.isArray(r)));}
const rows=x=>Array.isArray(x)?x.filter(v=>v&&typeof v==="object"&&!Array.isArray(v)):[];
const evidence=(label,source,date,url,now,maxDays=90)=>{
 const u=safeURL(url),vintage=observation(date,now,maxDays);return text(label)&&text(source)&&u&&vintage==="dated"?{label,source,date,url:u}:null;
};
export function validateProfile(p){
 if(!p||!["importer","distributor","manufacturer","other"].includes(p.type))throw Error("Choose the business type.");
 if(!Array.isArray(p.dependencies)||p.dependencies.length>30)throw Error("A maximum of 30 dependencies can be evaluated.");
 const dependencies=p.dependencies.map((d,i)=>{
  const name=String(d.name||"").trim(),country=String(d.country||"").trim().toUpperCase();
  if(!name||name.length>80)throw Error("Give each dependency a short label.");
  if(country&&!/^[A-Z]{2}$/.test(country))throw Error("Use a two-letter ISO country code.");
  if(d.product&&!Object.hasOwn(products,d.product))throw Error("Unknown product group.");
  if(d.corridor&&!corridors.includes(d.corridor))throw Error("Unknown transport corridor.");
  if(d.monthlyCost!==null&&(!number(d.monthlyCost)||d.monthlyCost<0||d.monthlyCost>1e10))throw Error("Invalid monthly cost.");
  const id=d.id==null?String(i+1):String(d.id);if(!/^[A-Za-z0-9:-]{1,100}$/.test(id))throw Error("Invalid dependency ID.");
  const twinPath=d.twinPath??[];if(!Array.isArray(twinPath)||twinPath.length>500||twinPath.some(id=>typeof id!=="string"||!/^[A-Za-z0-9:-]{1,100}$/.test(id)))throw Error("Invalid relationship path.");
  return {id,twinPath,provenance:validateProvenance(d.provenance),name,country,product:d.product||"",corridor:d.corridor||"",monthlyCost:d.monthlyCost};
 });
 if(new Set(dependencies.map(d=>d.id)).size!==dependencies.length)throw Error("Duplicate dependency IDs.");
 const topic=p.marketTopic||"";if(topic&&!marketTopics.includes(topic))throw Error("Unknown market topic.");
 return {type:p.type,dependencies,marketTopic:topic,financing:p.financing===true,usDemand:p.usDemand===true};
}
function finding(domain,dep,title,status,detail,action,items){return {domain,dependencyId:dep?.id||null,dependency:dep?.name||null,relationshipPath:dep?.twinPath||[],title,status,detail,action,evidence:items.filter(Boolean)};}
export function analyze(data,profile,now=Date.now()){
 const p=validateProfile(profile),out=[],gaps=[];
 data=Object.fromEntries(Object.entries(data||{}).filter(([k,v])=>validFeed(k,v)));
 const active=Object.keys(feeds).filter(k=>validFeed(k,data[k]));
 for(const d of p.dependencies){
  if(!d.product&&!d.country&&!d.corridor){gaps.push(d.name+": add product group, origin country or shipping corridor.");continue;}
  if(d.product){
   const r=data.shortage?.forecasts?.find(x=>x.id===d.product);
   if(!r){gaps.push(d.name+": no matching product outlook.");}
   else{
    const ev=rows(r.evidence).map(e=>evidence(e.title,e.publisher,e.period,e.url,now)).filter(Boolean);
    if(r.status==="data-gap"||!ev.length){gaps.push(d.name+": product-level evidence is missing or stale.");}
    else{
     const status=r.status==="input-cost-watch"?"Input-cost watch":r.status==="cross-source-watch"?"Cross-source watch":r.status==="transit-watch"?"Transit watch":r.status==="inventory-watch"?"Inventory watch":r.status==="baseline"?"Monitored":"Review source";
     out.push(finding("Supply",d,products[d.product],status,"Matched product dependency. "+(text(r.summary)?r.summary:"Review the underlying observations.")+" Product-specific supply, importer dependence and actual stockouts are not established by these proxy indicators.","Confirm supplier lead times, inventory and alternative quotes before changing purchase orders.",ev.slice(0,8)));
     for(const e of rows(r.evidence)){const proof=evidence(e.title,e.publisher,e.period,e.url,now);
      if(e.kind!=="input-price"||!proof||!number(e.changePct))continue;
      if(e.changePct<=-5)out.push(finding("Opportunity",d,e.title+" input-price decline","Quote review candidate","Published proxy change "+pct(e.changePct)+". No contractual pass-through or realized saving established.","Request an updated written supplier quote; compare landed cost and terms.",[proof]));
      if(e.changePct>=5)out.push(finding("Cost",d,e.title+" input-price increase","Cost pressure watch","Published proxy change "+pct(e.changePct)+". This is not the company's cost increase.","Review price-adjustment clauses, current quotes and alternate sources.",[proof]));
     }
    }
   }
  }
  if(d.corridor){
   const matches=(data.shortage?.forecasts||[]).flatMap(r=>rows(r.evidence)).filter(e=>e.kind==="corridor-transit"&&e.title===d.corridor&&number(e.changePct)).map(e=>({e,proof:evidence(e.title,e.publisher,e.period,e.url,now,21)})).filter(x=>x.proof).sort((a,b)=>b.proof.date.localeCompare(a.proof.date));
   const match=matches[0];if(!match)gaps.push(d.name+": no recent observation for declared corridor.");
   else out.push(finding("Logistics",d,d.corridor+" transit activity","Observed route context","Published transit change "+pct(match.e.changePct)+". Vessel counts are not cargo-specific delay, capacity or freight-price estimates.","Ask the carrier or forwarder for shipment-specific ETA, routing and current surcharge details.",[match.proof]));
  }
  if(d.country){
   const zones=(data.conflicts?.zones||[]).filter(z=>Array.isArray(z.countryCodes)&&z.countryCodes.includes(d.country));
   let matched=0;for(const z of zones){
    const ev=rows(z.evidence).map(e=>evidence(z.name,e.source,e.observedAt,e.url,now,90)).filter(Boolean);
    if(!ev.length||z.measurementFresh!==true)continue;matched++;
    out.push(finding("Geopolitics",d,z.name,z.promoted===true?"Upstream elevated watch":"Country context","Country matches a published monitoring zone. Upstream direction: "+String(z.direction||"unassessed").slice(0,60)+". Country-wide exposure is not proof of supplier disruption.","Verify supplier site, transport paths and continuity arrangements; assess legal restrictions separately.",ev.slice(0,5)));
   }if(!matched)gaps.push(d.name+": no recent matched conflict-zone record; this is not an all-clear.");
  }
 }
 if(p.financing){
  const m=data.physical?.metrics?.find(x=>x.id==="sofr-rate");
  const e=m&&evidence(m.label,m.source,m.period,m.sourceUrl,now,14);
  if(e&&number(m.value))out.push(finding("Finance",null,m.label,"Rate context",m.value+"% annualized. Benchmark is not the company's loan rate.","Check reference-rate terms, repricing date and floating-rate balance.",[e]));
  else gaps.push("Financing: current SOFR source unavailable or stale.");
 }
 if(p.usDemand){
  for(const id of ["UNRATE","PSAVERT"]){const m=data.finance?.householdMetrics?.find(x=>x.id===id),e=m&&evidence(m.label,m.source,m.period,m.sourceUrl,now,120);if(e&&number(m.value))out.push(finding("Demand",null,m.label,"US aggregate context",m.value+" "+m.unit+". Aggregate conditions are not company revenue or demand forecasts.","Compare customer orders, cancellations and sales pipeline against actual prior periods.",[e]));else gaps.push("Demand: "+id+" unavailable or stale.");}
 }
 if(p.marketTopic){
  for(const r of data.marketPower?.cases||[]){if(r.topic!==p.marketTopic||!safeURL(r.source)||!text(r.period)||!text(r.name))continue;
   out.push(finding("Market structure",null,r.name,"Historical research · "+String(r.kind||"context"),String(r.scope||"Scope unavailable")+". "+String(r.mechanism||"Review source.").slice(0,500),"Evaluate actual alternatives and contract terms; research does not establish your supplier's conduct.",[{label:r.name,source:r.sourceLabel||"Power Atlas source",date:r.period,url:safeURL(r.source)}]));
  }
 }
 const unique=new Map();for(const x of out)unique.set(JSON.stringify([x.domain,x.dependencyId,x.title,x.status,x.evidence.map(e=>[e.url,e.date])]),x);
 return {findings:[...unique.values()].map(f=>enrichFinding(f,now)).sort((a,b)=>b.priority-a.priority),gaps:[...new Set(gaps)],active};
}
export function scenario(cost,quoteChange){
 if(!number(cost)||cost<0||cost>1e10||!number(quoteChange)||quoteChange< -100||quoteChange>1000)return null;
 const delta=Math.round((cost*quoteChange/100)*100)/100;return {monthly:delta,annual:Math.round(delta*1200)/100,alternative:Math.round((cost+delta)*100)/100};
}
export function publicContext(data,now=Date.now()){
 const items=[];
 for(const m of rows(data.markets?.metrics)){const e=evidence(m.label,"FRED",m.period,m.sourceUrl,now,21);if(e&&number(m.value))items.push({title:m.label,value:String(m.value)+" "+m.unit,evidence:e});}
 const r=data.warning?.summary;if(r&&Number.isInteger(r.monitoring)&&Number.isInteger(r.elevated)&&observation(data.warning.generatedAt,now,2)==="dated")items.push({title:"Upstream early-warning screen",value:r.monitoring+" monitored / "+r.elevated+" elevated",evidence:null});
 return items;
}

// Deterministic interpretation metadata; public observations never become private facts.
export function enrichFinding(f,now=Date.now()){
 const historical=f.status.startsWith('Historical research');
 const elevated=['Cost pressure watch','Upstream elevated watch','Cross-source watch','Input-cost watch','Inventory watch','Transit watch'].includes(f.status);
 const kind=f.domain==='Opportunity'?'opportunity':elevated?'risk':'context';
 const gapsByDomain={Finance:['Floating-rate balance and loan spread','Reference-rate repricing dates and hedging terms'],Demand:['Company orders, cancellations and sales pipeline','Customer and geographic revenue exposure'],Geopolitics:['Actual supplier site and shipment routes','Continuity arrangements and applicable legal restrictions'],Logistics:['Shipment-specific route and current carrier ETA','Inventory cover and contractual delivery deadlines'],'Market structure':['Actual supplier alternatives and contract terms','Company purchasing exposure and switching constraints']};
 const informationGaps=gapsByDomain[f.domain]||['Current supplier quote and contractual pass-through','Affected quantity, inventory cover and delivery commitments','Alternative supplier availability and switching constraints'];
 const options=[{action:f.action,basis:f.evidence.map(e=>e.url),cost:null,benefit:null,tradeOff:'Requires supplier or internal verification; no saving or avoided loss is established.'},{action:'Retain current arrangements while collecting the missing business inputs.',basis:f.evidence.map(e=>e.url),cost:null,benefit:null,tradeOff:'Avoids an unsupported change but leaves the documented exposure unresolved.'}];
 return {...f,kind,classification:'Analytical assessment',priority:kind==='risk'?2:kind==='opportunity'?1:0,
  whatChanged:f.title,implication:f.detail,
  relationshipBasis:f.relationshipPath?.length?'Declared dependency path; no external verification of private relationships.':f.dependency?'Customer-declared dependency match.':'Explicitly enabled business context.',
  observationFreshness:f.evidence.map(e=>({url:e.url,observationDate:e.date,state:historical?'historical':observation(e.date,now)})),
  sourceReliability:'Attributable published source; source authority does not establish customer impact.',
  informationCredibility:'Public observation retained; customer relevance is a deterministic assessment, not corroborated company impact.',
  materiality:{state:'unquantified',amount:null,reason:'Approved quantities, pass-through terms and operational sensitivity are insufficient for an impact estimate.'},
  unsupportedConclusions:['No confirmed supplier failure, stockout, legal applicability, realized saving or company-specific forecast.'],
  informationGaps,managementOptions:options,
  invalidationConditions:['Observation corrected or stale','Dependency or approved relationship changes','Supplier-specific evidence contradicts the proxy'],
  forecast:{state:'withheld',label:'Forecast withheld — insufficient evidence.'}};
}
