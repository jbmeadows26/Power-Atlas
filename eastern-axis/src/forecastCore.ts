// Forecast foundation: empirical reference classes, no fabricated probabilities.
export type Indicator = {id:string;entity:string;value:number;unit:string;source:string;license:string;observedAt:string;availableAt:string;latencyClass:string;stale:boolean};
export type Event = {id:string;type:string;entity:string;onset:string;severity:string;confidence:number;source:string};
export type Forecast = {id:string;entity:string;target:string;horizonDays:number;issuedAt:string;resolutionDate:string;criteria:string;probability:number;baseRate:number;modelVersion:string;status:'open'|'resolved'|'void'};
export type Outcome = {forecastId:string;value:0|1;resolvedAt:string;source:string};
export type Trial = {start:string;end:string;availableAt:string;outcome:0|1};
export function baseline(trials:Trial[], asOf:string, min=30) {
 const cutoff=Date.parse(asOf);
 const eligible=trials.filter(t=>Number.isFinite(Date.parse(t.start))&&Date.parse(t.start)<Date.parse(t.end)&&Date.parse(t.end)<=cutoff&&Date.parse(t.availableAt)<=cutoff&&Date.parse(t.availableAt)>=Date.parse(t.end)&&(t.outcome===0||t.outcome===1)).sort((a,b)=>Date.parse(a.start)-Date.parse(b.start));
 const independent:Trial[]=[]; for(const t of eligible) if(!independent.length||Date.parse(t.start)>=Date.parse(independent[independent.length-1].end)) independent.push(t);
 const n=independent.length, hits=independent.reduce((s,t)=>s+t.outcome,0);
 return {n,hits,probability:n>=min?(hits+1)/(n+2):null};
}
export function score(forecasts:Forecast[],outcomes:Outcome[]) {
 const seen=new Set<string>(); const pairs=forecasts.flatMap(f=>{const matches=outcomes.filter(o=>o.forecastId===f.id);const o=matches[0];if(seen.has(f.id)||matches.length!==1||f.status!=='resolved'||!o||!o.source||!f.criteria||!(Date.parse(f.issuedAt)<Date.parse(f.resolutionDate))||!(Date.parse(o.resolvedAt)>=Date.parse(f.issuedAt))||!(f.probability>=0&&f.probability<=1&&f.baseRate>=0&&f.baseRate<=1)||(o.value!==0&&o.value!==1))return [];seen.add(f.id);return [{p:f.probability,b:f.baseRate,y:o.value}];});
 const n=pairs.length;const avg=(fn:(v:typeof pairs[number])=>number)=>n?pairs.reduce((s,v)=>s+fn(v),0)/n:null;
 const loss=(p:number,y:number)=>{const q=Math.max(1e-6,Math.min(1-1e-6,p));return -(y*Math.log(q)+(1-y)*Math.log(1-q));};
 return {n,brier:avg(v=>(v.p-v.y)**2),benchmarkBrier:avg(v=>(v.b-v.y)**2),logLoss:avg(v=>loss(v.p,v.y)),benchmarkLogLoss:avg(v=>loss(v.b,v.y)),calibration:Array.from({length:10},(_,i)=>{const bin=pairs.filter(v=>Math.min(9,Math.floor(v.p*10))===i);return {bin:i,n:bin.length,p:bin.length?bin.reduce((s,v)=>s+v.p,0)/bin.length:null,observed:bin.length?bin.reduce((s,v)=>s+v.y,0)/bin.length:null};})};
}
