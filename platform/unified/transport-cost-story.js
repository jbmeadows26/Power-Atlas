/* Power Atlas · actual travel charges and transport accountability.
 * No routes, eligible fares, trip quantities or misconduct inferred from a ZIP.
 * Scenario input never leaves the browser or persists.
 */
(function(){
"use strict";
const BASE="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/place-impact/";
const FARES_URL=BASE+"transport-fares-v1.json";
const WATCH_URL=BASE+"transport-accountability-v1.json";
const REGIONS=["NYNJ","CHI","OTHER"];
const money=n=>Number(n||0).toLocaleString("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2});
const safe=n=>Number.isFinite(n)&&n>=0?n:0;
const escapeHTML=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ext=(url,label)=>/^https:\/\/[^\s<>"']+$/.test(url||"")?'<a href="'+escapeHTML(url)+'" target="_blank" rel="noopener noreferrer">'+escapeHTML(label||"Original source ↗")+'</a>':"";
let fares=null,watch=null,geo={stateCode:null,zip:null},lastRegionState=null;
let userRegion=false;
let state={
 region:"OTHER",days:5,fares:{},tolls:{},
 fareCounts:{},tollCounts:{},fareOverrides:{},tollOverrides:{},
 parking:0,fuel:0,other:0,vehicle:0,congestionCredit:0
};
function regionByState(code){return code==="NY"||code==="NJ"?"NYNJ":code==="IL"?"CHI":"OTHER";}
function available(){return fares&&watch&&fares.schema==="power-atlas.transport-fares.v1"&&watch.schema==="power-atlas.transport-accountability.v1";}
function getCostFor(item,overrides){return item.price==null?safe(overrides[item.id]):safe(item.price);}
function eligibleItems(ids,items){return ids.map(id=>items.find(item=>item.id===id)).filter(Boolean);}
function inputsReset(){
 state.fares={};state.tolls={};state.fareCounts={};state.tollCounts={};
 state.fareOverrides={};state.tollOverrides={};
 state.parking=0;state.fuel=0;state.other=0;state.vehicle=0;state.congestionCredit=0;
}
function selectedRegion(){return fares.regions.find(x=>x.id===state.region)||fares.regions[fares.regions.length-1];}
function field(label,key,unit,max,step){
 let val=state[key]||0;
 return '<label class="ts-field"><span>'+escapeHTML(label)+'</span><span class="ts-fieldwrap"><input type="number" min="0" max="'+max+'" step="'+step+'" inputmode="decimal" data-extra="'+key+'" value="'+val+'" aria-label="'+escapeHTML(label)+'"><small>'+escapeHTML(unit)+'</small></span></label>';
}
function line(item,kind){
 const active=!!state[kind][item.id],isFare=kind==="fares";
 const counts=isFare?state.fareCounts:state.tollCounts;
 const overrides=isFare?state.fareOverrides:state.tollOverrides;
 const rate=getCostFor(item,overrides);
 const name=item.label;
 const priceLabel=item.price===null?"Enter actual fare":money(item.price);
 return '<div class="ts-line'+(active?" is-active":"")+'" data-transport-item="'+escapeHTML(item.id)+'">'+
  '<label class="ts-pick"><input type="checkbox" data-toggle="'+kind+'" data-id="'+escapeHTML(item.id)+'"'+(active?' checked':'')+'><span class="ts-name">'+escapeHTML(name)+'</span></label>'+
  '<div class="ts-price"><strong>'+escapeHTML(priceLabel)+'</strong> <span>'+escapeHTML(item.unit)+'</span></div>'+
  (item.price===null?'<label class="ts-price-entry">Actual $ per charge <input type="number" inputmode="decimal" min="0" max="10000" step=".01" value="'+(overrides[item.id]||"")+'" placeholder="Enter fare" data-override="'+kind+'" data-id="'+escapeHTML(item.id)+'"></label>':'')+
  '<label class="ts-count">Charges per commute day <input type="number" inputmode="numeric" min="0" max="20" step="1" data-count="'+kind+'" data-id="'+escapeHTML(item.id)+'" value="'+(Number.isInteger(counts[item.id])?counts[item.id]:isFare?2:1)+'"></label>'+
  '<div class="ts-line-notes"><small>'+escapeHTML(item.note||"")+'</small>'+
   (item.capWeekly?'<small>OMNY eligible seven-day cap: '+money(item.capWeekly)+'</small>':item.monthlyPass?'<small>30-day pass reference: '+money(item.monthlyPass)+' (not automatically applied)</small>':"")+
   ext(item.source,"Original rate ↗")+'</div></div>';
}
function sourceSection(title,items,kind){
 return '<div class="ts-source-group"><h5>'+escapeHTML(title)+'</h5>'+items.map(v=>line(v,kind)).join("")+'</div>';
}
function cardStatus(s){
 const info={
 civil_resolution_and_guilty_pleas:"Civil resolution + guilty pleas",
 auditor_finding:"Inspector-general audit",
 inspector_general_reported_misconduct:"Inspector-general finding",
 charged_allegations:"Charges · not adjudicated"
 };
 return info[s]||"Source reported";
}
function renderAccountability(){
 const pathways=watch.pathways.map((p,i)=>'<details class="ts-audit-step"><summary><span class="ts-index">'+(i+1)+'</span>'+escapeHTML(p.title)+'</summary><p>'+escapeHTML(p.ask)+'</p><p><b>Evidence needed:</b> '+escapeHTML(p.needed.join(" · "))+'</p><div class="ts-links">'+(p.sources||[]).map(x=>ext(x.url,x.label+" ↗")).join("")+'</div></details>').join("");
 const examples=watch.examples.map(e=>'<article class="ts-case"><span class="ts-case-kind">'+escapeHTML(cardStatus(e.status))+' · '+escapeHTML(e.dated)+'</span><h5>'+escapeHTML(e.name)+'</h5><small>'+escapeHTML(e.place)+'</small><p>'+escapeHTML(e.finding)+'</p><p class="ts-case-limit"><strong>What this does not prove:</strong> '+escapeHTML(e.unproven)+'</p>'+ext(e.source,"Read the original watchdog record ↗")+'</article>').join("");
 return '<section class="ts-audit" aria-label="Investigate corruption and fare increases"><div class="ts-audit-head"><span class="bs-eyebrow">Accountability · documented vs alleged</span><h4>Is waste, influence or corruption raising transportation costs?</h4><p>A price increase is not proof of corruption. To connect misconduct to a fare or toll, the records must establish a chain from <strong>contracts or decisions → agency budget → approved rate → rider charge</strong>.</p></div>'+
 '<div class="ts-audit-flow" aria-label="Four accountability checks">Documented contract or spending <span>→</span> Oversight findings <span>→</span> Rate-setting decision <span>→</span> Household charge</div>'+
 '<div class="ts-audit-steps">'+pathways+'</div>'+
 '<h5 class="ts-audit-example-title">What watchdogs have actually found</h5><p class="ts-note">National examples, not automatically linked to the selected ZIP or an agency’s published fare.</p>'+
 '<div class="ts-cases">'+examples+'</div><p class="ts-case-limit">No example shown assigns a dollar amount of misconduct to a household fare. Political giving, an ownership stake, or a costly contract alone cannot establish bribery or a causal price effect.</p>'+
 '<div class="ts-links">'+watch.sources.map(x=>ext(x.url,x.label+" ↗")).join("")+'</div></section>';
}
function build(){
 const root=document.getElementById("transportCostStory");if(!root)return;
 if(!available()){
  root.innerHTML='<h4>1 · Real transit fares, tolls and the cost of commuting</h4><p class="ts-note">Loading official-source transport rates and independent accountability findings…</p>';return;
 }
 let region=selectedRegion(),fareItems=eligibleItems(region.fareIds,fares.fares),tollItems=eligibleItems(region.tollIds,fares.tolls);
 root.innerHTML='<div class="ts-heading"><span class="bs-eyebrow">Commute costs · actual charges</span><h4>1 · What does getting there really cost?</h4><p>Subways, commuter rail, buses, bridge and tunnel tolls, congestion charges, parking and fuel can all add up. Select only the costs your trip actually incurs.</p></div>'+
 '<div class="ts-top"><label class="ts-regionlabel">Fare examples for <select id="ts-region" aria-label="Select region of your actual trip">'+fares.regions.map(r=>'<option value="'+escapeHTML(r.id)+'"'+(region.id===r.id?" selected":"")+'>'+escapeHTML(r.name)+'</option>').join("")+'</select></label>'+
 '<label class="ts-dayslabel">Commute days per week <input id="ts-days" type="number" inputmode="numeric" min="1" max="7" step="1" value="'+state.days+'" aria-label="Commute days per week"></label></div>'+
 '<p class="ts-note">Region suggested by state when available, but <strong>not a detected route</strong>. A ZIP cannot identify which agency, crossing, transfer or discounted pass you actually use. All options begin unselected. <strong>Check a charge to enter how often you pay it.</strong></p>'+
 '<div class="ts-picker-grid">'+sourceSection("Subway, bus, rail and other fares",fareItems,"fares")+sourceSection("Road tolls and congestion charges",tollItems,"tolls")+'</div>'+
 '<div class="ts-expenses"><h5>Other real costs</h5><div class="ts-expense-grid">'+
 field("Parking","parking","$/commute day",1000,"0.01")+
 field("Fuel / charging","fuel","$/commute day",1000,"0.01")+
 field("Other trip expenses","other","$/month",20000,"0.01")+
 field("Vehicle loan, insurance and upkeep (optional)","vehicle","$/month",20000,"0.01")+
 field("Eligible congestion credit (optional)","congestionCredit","$/commute day",100,"0.01")+
 '</div><p class="ts-note">The optional vehicle amount is a fixed ownership cost, not an additional toll or transit fare. Only subtract a documented congestion credit if the selected peak/overnight zone charge actually qualifies.</p></div>'+
 '<div class="ts-output" aria-live="polite" id="ts-output"><strong>Choose a fare, toll or expense to see a monthly scenario.</strong></div>'+
 '<div class="ts-links">'+region.sources.map(u=>ext(u,"Official fare/toll source ↗")).join("")+'</div>'+
 renderAccountability()+
 '<p class="ts-source-note"><strong>Method:</strong> '+escapeHTML(fares.disclosure)+' Month is modeled as 52 weeks ÷ 12, not precisely four weeks. National BLS transportation spending below is a separate survey average, not the sum of this scenario.</p>';
 root.dataset.region=region.id;root.dataset.ready="1";
 if(root.dataset.bound!=="1"){bind(root);root.dataset.bound="1";}
 updateTotals(root);
}
function totals(){
 const reg=selectedRegion();
 const days=Math.max(1,Math.min(7,Math.round(Number(state.days)||5)));
 const perMonth=52/12;
 const fareItems=eligibleItems(reg.fareIds,fares.fares).filter(x=>state.fares[x.id]);
 const tollItems=eligibleItems(reg.tollIds,fares.tolls).filter(x=>state.tolls[x.id]);
 let transit=0,tolls=0,credit=0,warnings=[];
 const mta= fareItems.filter(x=>x.id==="mta-local"||x.id==="mta-express");
 fareItems.forEach(item=>{
  const count=Math.min(20,Math.max(0,Number(state.fareCounts[item.id]??2)));
  let weekly=getCostFor(item,state.fareOverrides)*count*days;
  if(mta.length===1&&item.capWeekly!=null){
   weekly=Math.min(weekly,item.capWeekly);
   if(count*days>0)warnings.push(item.id==="mta-local"?"MTA seven-day $35 fare cap applied for one eligible full-fare rider using one consistent OMNY payment method.":"MTA express-bus $67 cap applied for eligible single-service use; verify account-specific rules.");
  }
  transit+=weekly*perMonth;
  if(item.monthlyPass&&weekly*perMonth>item.monthlyPass)warnings.push(item.label+": a published "+money(item.monthlyPass)+" 30-day pass may beat single fares; this calculator has not silently substituted a pass.");
  if(item.price==null&&getCostFor(item,state.fareOverrides)===0)warnings.push(item.label+": enter the exact fare for your route.");
 });
 if(mta.length>1)warnings.push("Mixed local and express-bus OMNY cap rules are not modeled. Verify actual weekly charges.");
 const congestion=tollItems.filter(x=>/^nyc-congestion/.test(x.id));
 tollItems.forEach(item=>{
  const askedCount=Math.min(20,Math.max(0,Number(state.tollCounts[item.id]??1)));
  const count=/^nyc-congestion/.test(item.id)?Math.min(1,askedCount):askedCount;
  if(/^nyc-congestion/.test(item.id)&&askedCount>1)warnings.push("Congestion-zone passenger vehicle toll is capped at once per day for the modeled charge.");
  let unit=getCostFor(item,state.tollOverrides);
  let charged=unit*count*days*perMonth;
  if(/^nyc-congestion/.test(item.id)&&state.congestionCredit>0){
   const original=charged;
   charged=Math.max(0,charged-Math.min(unit,safe(state.congestionCredit))*Math.min(count,1)*days*perMonth);
   credit+=original-charged;
  }
  tolls+=charged;
  if(item.price==null&&unit===0)warnings.push(item.label+": enter your actual toll amount after available discounts.");
 });
 const parking=safe(state.parking)*days*perMonth;
 const fuel=safe(state.fuel)*days*perMonth;
 const other=safe(state.other)+safe(state.vehicle);
 if(!congestion.length&&safe(state.congestionCredit)>0)warnings.push("Congestion discount ignored because no eligible congestion charge was selected.");
 let total=transit+tolls+parking+fuel+other;
 const any=!!(fareItems.length||tollItems.length||parking||fuel||other);
 return {any,total,annual:total*12,parts:[["Transit fares",transit],["Tolls and congestion",tolls],["Parking",parking],["Fuel / charging",fuel],["Other & vehicle",other]],warnings,credit};
}
function updateTotals(root){
 const out=root.querySelector("#ts-output");if(!out)return;
 const t=totals();
 if(!t.any){out.innerHTML='<p class="ts-empty"><strong>Select the fares and tolls your trip uses, or enter a parking/fuel cost.</strong> Nothing is assumed from your ZIP.</p>';return;}
 const max=t.total||1;
 out.innerHTML='<div class="ts-cost-head"><div><span>Illustrative monthly travel cost</span><strong>'+money(t.total)+'</strong><small>'+money(t.annual)+' per year · '+state.days+' commute days per week</small></div><div class="ts-price-ledger" role="img" aria-label="Breakdown of estimated monthly transportation spending">'+t.parts.map((p,i)=>p[1]>0?'<span style="width:'+Math.max(1,100*p[1]/max).toFixed(2)+'%;background:'+["#3e9787","#d8a553","#859bb1","#6e9fbd","#7a8c83"][i]+'" title="'+escapeHTML(p[0])+' '+money(p[1])+'"></span>':"").join("")+'</div></div>'+
 '<div class="ts-cost-lines">'+t.parts.filter(p=>p[1]>0).map(p=>'<div><span>'+escapeHTML(p[0])+'</span><strong>'+money(p[1])+'/mo</strong></div>').join("")+'</div>'+
 (t.credit>0?'<p class="ts-note">Applied user-entered congestion credit: '+money(t.credit)+'/month. Check actual eligibility.</p>':'')+
 (t.warnings.length?'<ul class="ts-warnings">'+Array.from(new Set(t.warnings)).map(w=>'<li>'+escapeHTML(w)+'</li>').join("")+'</ul>':'')+
 '<p class="ts-note">A <strong>user-selected scenario</strong>, not a quoted route or an observed average. Rides, crossing direction, passes, account eligibility, discounted transfers, parking and the number of weeks worked change the result. Do not add these same charges twice in the optional household worksheet.</p>';
}
function exclusiveToll(id){return /^pa-(peak|offpeak|mail)$/.test(id)?"pa":/^nyc-congestion/.test(id)?"congestion":null;}
function bind(root){
 root.addEventListener("change",function(ev){
  const el=ev.target;
  if(el.id==="ts-region"){
   if(!REGIONS.includes(el.value))return;
   userRegion=true;state.region=el.value;inputsReset();build();return;
  }
  if(el.id==="ts-days"){
   state.days=Math.max(1,Math.min(7,Math.round(Number(el.value)||5)));el.value=state.days;updateTotals(root);return;
  }
  if(el.dataset.toggle){
   const kind=el.dataset.toggle,id=el.dataset.id;
   if(kind!=="fares"&&kind!=="tolls")return;
   if(kind==="tolls"&&el.checked){
    const group=exclusiveToll(id);
    if(group){Object.keys(state.tolls).forEach(k=>{if(exclusiveToll(k)===group)state.tolls[k]=false});}
   }
   state[kind][id]=el.checked;
   el.closest(".ts-line")?.classList.toggle("is-active",Boolean(el.checked));
   if(kind==="tolls"&&el.checked&&exclusiveToll(id))build();else updateTotals(root);
  }
 });
 root.addEventListener("input",function(ev){
  const el=ev.target,val=Number(el.value);
  if(el.id==="ts-days"){state.days=Math.max(1,Math.min(7,Math.round(val||5)));updateTotals(root);return;}
  if(el.dataset.extra){
   if(!["parking","fuel","other","vehicle","congestionCredit"].includes(el.dataset.extra))return;
   state[el.dataset.extra]=Math.min(20000,safe(val));updateTotals(root);return;
  }
  if(el.dataset.count){
   const kind=el.dataset.count,bag=kind==="fares"?state.fareCounts:state.tollCounts;
   bag[el.dataset.id]=Math.max(0,Math.min(20,Math.round(val||0)));updateTotals(root);return;
  }
  if(el.dataset.override){
   const kind=el.dataset.override,bag=kind==="fares"?state.fareOverrides:state.tollOverrides;
   bag[el.dataset.id]=Math.min(10000,safe(val));updateTotals(root);
  }
 });
}
function setContext(context){
 context=context||{};
 geo={stateCode:context.stateCode||null,zip:context.zip||null};
 if(!userRegion&&fares){
  const implied=regionByState(geo.stateCode);
  if(state.region!==implied){state.region=implied;inputsReset();}
 }
 build();
}
async function init(){
 if(!document.getElementById("benchmarkStory"))return;
 try{
  const [a,b]=await Promise.all([fetch(FARES_URL,{cache:"no-store"}),fetch(WATCH_URL,{cache:"no-store"})]);
  if(!a.ok||!b.ok)throw Error("missing source");
  [fares,watch]=await Promise.all([a.json(),b.json()]);
  if(!available())throw Error("unexpected data schema");
  if(typeof window.PowerAtlasGetBenchmarkContext==="function")setContext(window.PowerAtlasGetBenchmarkContext());
  else build();
 }catch(e){
  const box=document.getElementById("transportCostStory");
  if(box)box.innerHTML='<div class="bs-rent-unavailable"><b>Transportation source temporarily unavailable.</b><p>Fare amounts cannot be estimated safely without the original records. View the source agencies directly.</p>'+ext("https://www.transit.dot.gov/ntd","Official transit agency directory ↗")+'</div>';
 }
}
window.PowerAtlasTransport={render:build,setContext:setContext};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();