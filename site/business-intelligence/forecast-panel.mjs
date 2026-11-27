import {safeURL} from "./engine.mjs";
// Public benchmark only: fixed same-origin fetch, never a customer-dependent URL.
export async function mountForecast(mount){
 if(!mount)return;
 const panel=document.createElement('section');panel.id='benchmark-forecast';
 const add=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;panel.append(n);return n;};
 add('h2','Fuel benchmark forecast');const status=add('p','Forecast withheld — insufficient evidence.');mount.append(panel);
 try{
  const response=await fetch('./data/brent-forecast.json',{credentials:'omit'});if(!response.ok)throw Error('Public forecast unavailable');const r=await response.json();
  status.textContent=r.forecastStatus;
  if(r.withheldReason)add('p',r.withheldReason);
  const age=(Date.now()-Date.parse(r.createdAt))/86400000;
  const currentMonth=new Date().toISOString().slice(0,7);
  if(!Number.isFinite(age)||age<0||age>7||!r.targetPeriod||r.targetPeriod<=currentMonth){status.textContent='Forecast withheld — insufficient evidence.';add('p','Issue stale or target month has begun. Historical evaluation remains available.');}
  else if(r.forecastId&&Number.isFinite(r.predicted)){
   add('p',`${r.targetPeriod} Brent benchmark: $${r.predicted.toFixed(2)}/bbl. Observation: ${r.observationPeriod}. Issued: ${r.createdAt}.`);
   add('p',`Descriptive historical error range: $${r.uncertainty.lower.toFixed(2)}–$${r.uncertainty.upper.toFixed(2)}/bbl. Not a calibrated probability interval.`);
  }
  if(r.evaluation){const e=r.evaluation;add('p',`${e.origins} chronological evaluation origins; mean absolute error $${e.mae.toFixed(2)}/bbl versus persistence $${e.persistenceMae.toFixed(2)}/bbl. ${e.beatsPersistence?'Lower historical error does not establish prospective skill.':'This model did not beat the simple persistence baseline.'}`);}
  if(r.source&&safeURL(r.source.url)){const a=add('a','World Bank source');a.href=safeURL(r.source.url);a.rel='noopener noreferrer';add('p',`Retrieved ${r.source.retrievedAt}; publisher publication date unavailable.`);}
  if(r.managementConsideration)add('p',r.managementConsideration);
  const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Methodology, limitations and forecast record';details.append(summary);panel.append(details);
  for(const text of r.limitations||[]){const p=document.createElement('p');p.textContent=text;details.append(p);}
  const a=document.createElement('a');a.textContent='Evaluation and supporting observations';a.href='./data/brent-forecast.json';details.append(a);
 }catch{add('p','Public benchmark artifact unavailable. No private information was sent.');}
}
