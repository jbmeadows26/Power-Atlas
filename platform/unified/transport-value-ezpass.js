/* Power Atlas fare-vs-service and toll-accountability comparison.
   Dated snapshots: budget authorization is NOT project completion. */
(function(){
"use strict";
const BASE="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/place-impact/";
const DATA_URL=BASE+"transport-value-audit-v1.json";
const EZ_URL=BASE+"ezpass-value-audit-v1.json";
const fmt=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:2}).format(n);
const esc=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const link=(url,label)=>/^https:\/\/[^\s<>"']+$/.test(url||"")?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label||"Original source ↗")+'</a>':"";
let transit=null,ez=null,region="OTHER",activeTransit=null,activeToll=null,userTransit=false,userToll=false;
function agencyFor(id,kind){
 const data=kind==="transit"?transit:ez;
 const options=(data?.agencies||[]).filter(x=>x.region===region);
 return options.find(x=>x.id===id)||options[0]||null;
}
function agencyPicker(options,selected,id,label){
 return '<label class="tv-label">'+esc(label)+' <select id="'+id+'" aria-label="'+esc(label)+'">'+options.map(o=>'<option value="'+esc(o.id)+'"'+(o.id===selected?' selected':'')+'>'+esc(o.name)+'</option>').join("")+'</select></label>';
}
function smallSource(url,label){return link(url,label||"Inspect source ↗");}
function priceTile(row){
 let value="—",unit="";
 if(row.before!=null&&row.after!=null) {
  value=(row.displayUnit==="index"?String(row.before)+" → "+String(row.after):fmt(row.before)+" → "+fmt(row.after));
  if(row.displayUnit==="index")unit="Indexed change, NOT ticket price";
 }else if(row.after!=null) {
  value=(row.displayUnit==="delta_usd"?"+":"")+(row.displayUnit==="percentage"?String(row.after)+"%":fmt(row.after));
  unit=row.displayUnit==="delta_usd"?"Toll increment, not full toll":row.displayUnit==="percentage"?"Budget assumption, not individual fare":"";
 }
 return '<div class="tv-price"><span class="tv-price-label">'+esc(row.name)+'</span><strong>'+esc(value)+'</strong><small>'+esc(row.oldDate||"")+" "+(row.oldDate?"→":"")+esc(row.newDate||"")+'</small>'+ (unit?'<small>'+esc(unit)+'</small>':"")+
 '<p>'+esc(row.cadence||"")+'</p>'+smallSource(row.source,"Original fare or policy ↗")+'</div>';
}
function performanceCard(r){
 const diff=r.newer-r.older,good=(diff>=0)===Boolean(r.higherIsBetter),pp=Math.abs(diff);
 return '<div class="tv-otp"><span class="tv-price-label">'+esc(r.name)+'</span>'+
 '<div class="tv-otp-values"><div><strong>'+Number(r.older).toFixed(1)+'%</strong><small>'+esc(r.olderPeriod)+'</small></div><span class="tv-trend'+(good?" good":" bad")+'">'+(good?"↑":"↓")+' '+pp.toFixed(1)+' percentage points</span><div><strong>'+Number(r.newer).toFixed(1)+'%</strong><small>'+esc(r.newerPeriod)+'</small></div></div>'+
 '<p>'+esc(r.interpretation)+'</p><div class="tv-links">'+smallSource(r.sourceOlder,"Earlier period ↗")+smallSource(r.sourceNewer,"Later period ↗")+'</div></div>';
}
function capitalCard(c){
 const hasCommit=c.committedBillions!=null&&c.authorizedBillions>0;
 const pct=hasCommit?Math.max(0,Math.min(100,c.committedBillions/c.authorizedBillions*100)):null;
 return '<div class="tv-capital"><span class="tv-price-label">'+esc(c.label)+'</span><strong>'+fmt(c.authorizedBillions)+' billion planned</strong>'+
 (hasCommit?'<div class="tv-capital-bar" role="img" aria-label="'+pct.toFixed(1)+' percent of plan is committed; not delivered"><span style="width:'+pct.toFixed(1)+'%"></span></div><p><strong>'+fmt(c.committedBillions)+'B committed</strong> · '+esc(c.committedAsOf||"")+' · '+pct.toFixed(0)+'% of authorization</p>':'<p><strong>Actual committed, spent or completed amounts not verified.</strong></p>')+
 '<p>'+esc(c.scope)+' · '+esc(c.warning)+'</p><div class="tv-links">'+smallSource(c.allocationSource,"Official program ↗")+(c.commitmentSource?smallSource(c.commitmentSource,"Independent assessment ↗"):"")+'</div></div>';
}
function renderTransit(){
 const target=document.getElementById("transportValuePanel");
 if(!target)return;
 if(!transit||!ez){target.innerHTML='<h4>Are higher fares buying better transport?</h4><p class="ts-note">Loading dated fares, performance and infrastructure commitments…</p>';return;}
 const options=(transit.agencies||[]).filter(x=>x.region===region);
 const chosen=agencyFor(activeTransit,"transit"); if(chosen)activeTransit=chosen.id;
 const head='<div class="tv-head"><span class="bs-eyebrow">Fare accountability · service and delivery</span><h4>Did higher fares buy a better commute?</h4><p>Compare the price riders paid with <strong>reliability, safety, accessibility and actual project delivery</strong>. A billion-dollar plan is not the same as a finished repair. A fare hike is not proof of corruption.</p></div>';
 if(!options.length){
  target.innerHTML=head+'<p class="tv-unknown">Local fare-versus-service source series is not yet linked for this region. The <a href="https://www.transit.dot.gov/ntd" target="_blank" rel="noopener">FTA National Transit Database</a> and local agency performance reports can supply a new comparable series.</p>';
  return;
 }
 const priceCards=chosen.fares.map(priceTile).join("");
 const metrics=chosen.performance?.length?chosen.performance.map(performanceCard).join(""):'<div class="tv-unknown"><strong>Service trend not validated.</strong><p>We have no matching before-and-after reliability measure for this agency. An announced investment or timetable change cannot fill that gap.</p></div>';
 const capital=chosen.capital?.length?chosen.capital.map(capitalCard).join(""):'<div class="tv-unknown"><strong>Capital delivery not joined.</strong><p>Agency-specific project completion, spending and asset-condition data remain needed.</p></div>';
 const concerns=(chosen.concerns||[]).map(x=>'<div class="tv-concern"><strong>'+esc(x.name)+'</strong><p>'+esc(x.finding)+'</p><small>'+esc(x.status.replaceAll("_"," "))+' · '+esc(x.warning)+'</small>'+smallSource(x.source,"Read evidence ↗")+'</div>').join("");
 target.innerHTML=head+
 '<div class="tv-selector">'+agencyPicker(options,chosen.id,"tv-transit-agency","Choose transit or toll operator")+'</div>'+
 '<div class="tv-verdict"><strong>'+esc(chosen.headline)+'</strong><p>'+esc(chosen.ratingBasis)+'</p></div>'+
 '<div class="tv-value-grid"><section><h5>1 · What changed in price?</h5>'+priceCards+'</section><section><h5>2 · Did service improve?</h5>'+metrics+'</section></div>'+
 '<div class="tv-capital-wrapper"><h5>3 · What infrastructure was actually delivered?</h5><div class="tv-capital-grid">'+capital+'</div>'+
 '<p class="tv-warning"><strong>Evidence boundary:</strong> A plan is a promise. Committed funds are contracts or obligations. Actual spending and completed projects must be independently verified. Comparisons do not prove that fare policy caused performance changes.</p></div>'+
 '<details class="tv-details"><summary>Why the numbers may not tell the whole story</summary><div class="tv-concerns">'+concerns+'</div>'+
 '<h5>What remains to be measured</h5><ul>'+chosen.nextMeasures.map(x=>'<li>'+esc(x)+'</li>').join("")+'</ul><p><b>What riders can do:</b> '+esc(chosen.action)+'</p><div class="tv-links">'+chosen.sources.map(x=>smallSource(x.url,x.label+" ↗")).join("")+'</div></details>';
}
function ezMetricCard(m){
 const kind={"independent_audit":"Independent audit","historical_audit":"Historical audit","agency_report":"Agency reported","data_gap":"Evidence missing","adopted_policy":"Policy","observed_activity":"Observed activity","budget_authorization":"Approved budget","observed_revenue":"Revenue, not price"}[m.kind]||m.kind?.replaceAll("_"," ");
 return '<article class="tv-ez-item"><span>'+esc(m.name)+'</span><strong>'+esc(m.value)+'</strong><small>'+esc(m.period)+' · '+esc(kind||"Source-linked")+'</small><p>'+esc(m.details||m.description||"")+'</p>'+
 (m.limitation?'<p class="tv-ez-limit">'+esc(m.limitation)+'</p>':"")+
 smallSource(m.source,"Original record ↗")+'</article>';
}
function renderEZ(){
 const target=document.getElementById("transportEZPanel");
 if(!target)return;
 if(!ez||!transit){target.innerHTML='<h4>E-ZPass / I-PASS accountability</h4><p class="ts-note">Loading official tolling audits and contract records…</p>';return;}
 const options=(ez.agencies||[]).filter(x=>x.region===region);
 const chosen=agencyFor(activeToll,"ez"); if(chosen)activeToll=chosen.id;
 const head='<div class="tv-head"><span class="bs-eyebrow">E-ZPass, I-PASS · tolling system oversight</span><h4>Where does the toll money go—and is the E-ZPass system working?</h4><p>Electronic toll collection is separate from physical road maintenance. Inspect the original toll, image-processing errors, customer disputes, revenue collected, contractor operations and completed infrastructure.</p></div>';
 if(!options.length){
  target.innerHTML=head+'<p class="tv-unknown">A connected toll authority audit is not yet available here. Do not infer local billing errors from another state.</p>'+smallSource("https://www.fhwa.dot.gov/ipd/tolling_and_pricing/","U.S. tolling and pricing resources ↗");
  return;
 }
 const prices=chosen.prices.map(ezMetricCard).join(""),audits=chosen.outcomes.map(ezMetricCard).join(""),projects=chosen.delivery.map(ezMetricCard).join("");
 target.innerHTML=head+'<div class="tv-selector">'+agencyPicker(options,chosen.id,"tv-ez-agency","Choose E-ZPass / I-PASS operator")+'</div>'+
 '<div class="tv-verdict"><strong>'+esc(chosen.verdict)+'</strong><p>'+esc(chosen.scope)+'</p></div>'+
 '<div class="tv-value-grid"><section><h5>1 · Tolls and money collected</h5>'+prices+'</section><section><h5>2 · Billing errors and performance</h5>'+audits+'</section></div>'+
 '<div class="tv-capital-wrapper"><h5>3 · Promised upgrades versus proven delivery</h5><div class="tv-capital-grid">'+projects+'</div></div>'+
 '<details class="tv-details"><summary>How to investigate this toll authority</summary><p>Follow funds through original toll records, actual collection revenue, private processing contracts, audits, and crossing-specific completed repairs. A fee increase is not by itself evidence of contractor wrongdoing.</p>'+
 '<h5>Where the money can go</h5><ul>'+chosen.money.map(x=>'<li>'+esc(x)+'</li>').join("")+'</ul>'+
 '<h5>Outstanding questions</h5><ul>'+chosen.next.map(x=>'<li>'+esc(x)+'</li>').join("")+'</ul>'+
 '<p><b>For toll bill questions:</b> '+esc(chosen.rights.note)+'</p><div class="tv-links">'+smallSource(chosen.rights.url,chosen.rights.label+" ↗")+'</div></details>'+
 '<p class="tv-warning">An audited sample at one toll plaza is <strong>not</strong> a network-wide error rate. Collections, budget allocations and maintenance are different measures. Dates and source limitations appear with every number.</p>';
}
function render(){
 renderTransit();renderEZ();
}
function setRegion(r){
 if(!["NYNJ","CHI","OTHER"].includes(r))return;
 if(region!==r){region=r;activeTransit=null;activeToll=null;render();}
}
function setContext(c){
 const st=c?.stateCode||null;
 setRegion(st==="NY"||st==="NJ"?"NYNJ":st==="IL"?"CHI":"OTHER");
}
async function init(){
 if(!document.getElementById("benchmarkStory"))return;
 try{
  const responses=await Promise.all([fetch(DATA_URL,{cache:"no-store"}),fetch(EZ_URL,{cache:"no-store"})]);
  if(responses.some(x=>!x.ok))throw Error("Missing external source");
  [transit,ez]=await Promise.all(responses.map(x=>x.json()));
  if(transit.schema!=="power-atlas.transport-value-audit.v1"||ez.schema!=="power-atlas.ezpass-value-audit.v1")throw Error("Invalid evidence schema");
  if(typeof window.PowerAtlasGetBenchmarkContext==="function")setContext(window.PowerAtlasGetBenchmarkContext());
  else render();
 }catch(e){
  const target=document.getElementById("transportValuePanel");
  if(target)target.innerHTML='<div class="tv-unknown"><strong>Transit performance evidence unavailable.</strong><p>Agency outcomes cannot be rated without original source data.</p>'+smallSource("https://www.transit.dot.gov/ntd","FTA data ↗")+'</div>';
  const ezroot=document.getElementById("transportEZPanel");
  if(ezroot)ezroot.innerHTML='<div class="tv-unknown"><strong>E-ZPass audit evidence unavailable.</strong><p>No false billing or road-condition claim is inferred.</p>'+smallSource("https://www.osc.ny.gov/","NY State Comptroller ↗")+'</div>';
 }
}
document.addEventListener("change",e=>{
 const x=e.target;
 if(x.id==="tv-transit-agency"){activeTransit=x.value;renderTransit();}
 if(x.id==="tv-ez-agency"){activeToll=x.value;renderEZ();}
});
window.PowerAtlasTransportValue={render:render,setRegion:setRegion,setContext:setContext};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();