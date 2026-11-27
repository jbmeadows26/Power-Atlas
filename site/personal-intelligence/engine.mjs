// Pure deterministic evidence rules. No model output, personal inference, or synthetic defaults.
export const paths={
 affordability:"data/affordability/bergen-basic-needs-2026.json",
 telecom:"data/consumer-costs/telecom-picks-v1.json",
 shortage:"eastern-axis/public/analysis/product-shortage-outlook.json",
 finance:"eastern-axis/public/analysis/financial-transmission.json",
 warning:"eastern-axis/public/analysis/early-warning-triage.json"
};
export const sourcePath=k=>"https://github.com/jbmeadows26/Power-Atlas/blob/main/"+paths[k];
export const money=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}).format(n);
const num=n=>typeof n==="number"&&Number.isFinite(n);
const actual=n=>num(n)&&n>=0;
export function dateOK(d){return typeof d==="string"&&/^\d{4}-\d{2}(?:-\d{2})?/.test(d)&&Number.isFinite(Date.parse(d));}
export function analyze(feeds,p={}){
 const out=[];
 const a=feeds.affordability;
 if(a?.location?.countyFips===p.county&&typeof p.household==="string"&&actual(p.gross)&&dateOK(a.asOf)&&Array.isArray(a.sources)&&a.sources.some(x=>x.url==="https://livingwage.mit.edu/counties/34003")){
   const s=a.scenarios?.find(x=>x.id===p.household);
   if(s&&actual(s.gross)){const d=p.gross-s.gross;out.push({key:"affordability",title:"Compare income with modeled basic needs",status:"Personal calculation",value:money(Math.abs(d))+(d<0?" below":d>0?" above":" difference from")+" annual benchmark",detail:"Your entered gross income: "+money(p.gross)+". County household model: "+money(s.gross)+". This is not an individual expense estimate or benefits test.",date:a.asOf,source:"https://livingwage.mit.edu/counties/34003"});}
 }
 const t=feeds.telecom,b=t?.factualBaseline;
 if(p.lines===2&&t?.schema==="power-atlas.consumer-costs.telecom-picks.v1"&&b?.eligibleVoiceLines===2&&num(b.sharedPicks)&&dateOK(t.reviewedUtc)){
  out.push({key:"telecom",title:"Check shared wireless promotion limits",status:"Dated terms — verify current offer",value:b.sharedPicks+" account-level Picks",detail:"Power Atlas reviewed T-Mix More for two lines. Compare current written terms and full contract costs before switching. No personalized savings or current eligibility established.",date:t.reviewedUtc,source:"https://www.t-mobile.com/cell-phone-plans"});
 }
 const f=feeds.shortage?.forecasts?.find(x=>x.id==="fuel");
 if(p.drives===true&&f?.status==="input-cost-watch"&&f.confirmedShortage===false){
  const oil=f.evidence?.find(x=>x.kind==="input-price"&&x.title==="Brent crude oil");
  if(oil&&num(oil.changePct)&&dateOK(oil.period)){out.push({key:"shortage",title:"Monitor transport fuel input costs",status:"Monitoring — not confirmed shortage",value:oil.changePct+"% Brent change",detail:"Input-price movement does not establish your pump price or local supply. Compare actual fuel receipts before changing your budget.",date:oil.period,source:oil.url});}
 }
 const fm=feeds.finance?.householdMetrics;
 if(p.employed===true&&Array.isArray(fm)){const u=fm.find(x=>x.id==="UNRATE"&&x.status==="ok");if(u&&num(u.value)&&dateOK(u.period)){out.push({key:"finance",title:"Review employment context",status:"National context only",value:u.value+"% U.S. unemployment",detail:"This is an aggregate, not a probability of losing your job. No occupation-level forecast is supported by this record.",date:u.period,source:u.sourceUrl});}}
 if(actual(p.net)&&actual(p.expenses)){const d=p.net-p.expenses;out.push({key:"profile",title:"Review your actual monthly cash flow",status:"Personal calculation",value:money(d)+" per month",detail:d<0?"Your entered expenses exceed your entered take-home income.":"Calculated from your actual entered income and expenses. No external savings estimate.",date:null,source:null});}
 return out;
}
export function publicContext(feeds){
 const a=feeds.affordability,t=feeds.telecom,f=feeds.shortage?.forecasts?.find(x=>x.id==="fuel"),m=feeds.finance?.householdMetrics,w=feeds.warning;
 const out=[];
 if(a?.location?.countyFips==="34003"&&dateOK(a.asOf)&&Array.isArray(a.scenarios))out.push({key:"affordability",title:"Bergen County household benchmarks",value:a.scenarios.length+" modeled household configurations",status:"County model",date:a.asOf,detail:"County model, not ZIP-specific or a personal budget.",source:"https://livingwage.mit.edu/counties/34003"});
 if(t?.schema==="power-atlas.consumer-costs.telecom-picks.v1"&&dateOK(t.reviewedUtc)&&num(t.factualBaseline?.sharedPicks))out.push({key:"telecom",title:"Wireless promotion terms",value:t.factualBaseline.sharedPicks+" shared Picks",status:"Dated carrier review",date:t.reviewedUtc,detail:"Not a current quote. Verify eligibility and pricing.",source:"https://www.t-mobile.com/cell-phone-plans"});
 if(f?.confirmedShortage===false){const inv=f.evidence?.find(x=>x.kind==="direct-inventory"&&x.title==="U.S. total motor gasoline stocks");if(inv&&num(inv.value)&&dateOK(inv.period))out.push({key:"shortage",title:"U.S. motor gasoline inventories",value:inv.value+" "+inv.unit,status:"Observed inventory; no confirmed shortage in this record",date:inv.period,detail:"Wholesale national inventories do not establish local availability.",source:inv.url});}
 if(Array.isArray(m))for(const id of ["UNRATE","PSAVERT"]){const x=m.find(y=>y.id===id&&y.status==="ok");if(x&&num(x.value)&&dateOK(x.period))out.push({key:"finance",title:x.label,value:x.value+"%",status:"National observation",date:x.period,detail:"Aggregate context, not a personal outcome.",source:x.sourceUrl});}
 if(num(w?.summary?.elevated)&&dateOK(w.generatedAt))out.push({key:"warning",title:"Eastern Axis elevated signals",value:String(w.summary.elevated),status:"Platform review count",date:w.generatedAt,detail:"This count is not an assurance that no risks exist.",source:null});
 return out;
}
export function safeLink(s){try{const u=new URL(s);return u.protocol==="https:"?u.href:null}catch{return null}}
