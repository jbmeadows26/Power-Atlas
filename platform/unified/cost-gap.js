/* Power Atlas Cost Gap: two-place evidence comparison, not a household calculator. */
(function(){"use strict";
const byId=id=>document.getElementById(id),fmt=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0});
const base="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/housing/bedroom-rents/";
const states={bed:2,topic:"housing",a:null,b:null,loading:false};
const titles={housing:"Housing",transport:"Transportation",groceries:"Groceries",utilities:"Utilities",health:"Healthcare",schools:"Childcare & education"};
const follow={
 transport:{why:"A true two-city transportation comparison needs the same commuting assumptions, dated fares, toll rules and vehicle costs. A subway fare cannot represent all transportation expenses.",sources:[["National transportation benchmarks","https://www.bls.gov/news.release/cesan.htm"],["Local transit evidence","my-life.html#transport"]]},
 groceries:{why:"A verified, identical grocery basket with current local item and unit prices is not available for both ZIPs. U.S. average grocery spending cannot substitute for city prices.",sources:[["U.S. food spending benchmarks","https://www.bls.gov/news.release/cesan.htm"],["Explore grocery market forces","my-life.html#groceries"]]},
 utilities:{why:"Utility tariffs, suppliers, fixed charges and consumption vary within cities. A national or state average is not a ZIP-specific household bill.",sources:[["Energy price data by state","https://www.eia.gov/electricity/data/browser/"],["Explore energy drivers","my-life.html#energy"]]},
 health:{why:"Premiums, provider networks, coverage and out-of-pocket charges differ. There is no defensible universal ZIP-level healthcare bill without defining insurance and services.",sources:[["National household healthcare spending","https://www.bls.gov/news.release/cesan.htm"],["Explore healthcare and policy","my-life.html#health"]]},
 schools:{why:"Childcare prices depend on age, hours, provider and subsidies. Education taxes and school spending are different measures and should not be summed as a family bill.",sources:[["U.S. child and dependent care evidence","https://www.bls.gov/news.release/cesan.htm"],["Explore schools and families","my-life.html#schools"]]}
};
const esc=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const safeUrl=v=>/^(https:\/\/|[a-z0-9-]+\.html#?)/.test(v)?v:"#cg-method-title";
function status(s,error){const el=byId("cg-status");el.textContent=s;el.classList.toggle("error",!!error)}
function zipOkay(z){return /^\d{5}$/.test(z)}
function locate(zip){return fetch("https://api.zippopotam.us/us/"+encodeURIComponent(zip),{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("Postal area not found ("+zip+")");return r.json()}).then(j=>{const p=j.places&&j.places[0];if(!p||!p["state abbreviation"])throw Error("No location mapping for "+zip);return {zip:zip,city:p["place name"],state:p["state abbreviation"]}})}
function getRents(place){return fetch(base+encodeURIComponent(place.state)+".json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("HUD-derived rent reference unavailable for "+place.zip);return r.json()}).then(d=>{
if(d.fy!==2027||d.state!==place.state||!d.zips)throw Error("The rent dataset failed its source/scope check for "+place.zip);
const records=d.zips[place.zip];if(!Array.isArray(records)||!records.length)throw Error("No comparable ZIP-level HUD reference for "+place.zip);
const chosen=records.map(row=>{const carry=Array.isArray(row[2]);return {area:d.areas&&d.areas[row[0]]&&d.areas[row[0]].name||"HUD area not named",values:carry?row[2]:row[1],fy:carry?2026:2027}});
if(chosen.some(r=>!Array.isArray(r.values)||r.values.length!==5||r.values.some(v=>!Number.isFinite(v)||v<=0)))throw Error("Invalid bedroom values for "+place.zip);
if(chosen.some(r=>r.fy!==chosen[0].fy||r.values.some((v,i)=>v!==chosen[0].values[i])))throw Error("This ZIP maps to differing HUD areas; an unambiguous single reference is unavailable.");
return {...place,values:chosen[0].values,area:chosen[0].area,fy:chosen[0].fy,effective:d.effective,source:d.source,official:d.officialSource,compiler:d.compiledBy};
})}
function labels(p){return esc(p.city+", "+p.state)+" <span>("+esc(p.zip)+")</span>"}
function renderHousing(){const view=byId("cg-view");if(!states.a||!states.b){view.innerHTML='<div class="cg-empty"><strong>Compare two places first.</strong><p>Select example ZIP codes or enter your own.</p></div>';return}
const a=states.a,b=states.b,comparable=a.fy===b.fy,months=["Studio","1 bedroom","2 bedrooms","3 bedrooms","4 bedrooms"],max=Math.max(...a.values,...b.values),x=states.bed;
const diff=b.values[x]-a.values[x],abs=Math.abs(diff),percent=Math.round(100*abs/a.values[x]),direction=diff===0?"the same":diff>0?"lower in Place A":"higher in Place A";
byId("cg-period").textContent=comparable?"HUD FY"+a.fy+" / gross-rent reference":"Mixed reference vintages · see warning";
byId("cg-scope").textContent="HUD ZIP-level Small Area Fair Market Rent reference. Not a listing price or the amount a household actually pays.";
const bar=(v,other)=>'<span class="cg-bar'+(other?' second':'')+'"><i style="width:'+Math.max(1,100*v/max).toFixed(1)+'%"></i></span>';
const bars=months.map((l,i)=>'<button type="button" class="cg-bed" data-bedroom="'+i+'" aria-pressed="'+(i===x)+'"><span class="cg-bed-name">'+esc(l)+'</span><span class="cg-bars">'+bar(a.values[i],false)+bar(b.values[i],true)+'</span><span class="cg-bed-numbers"><span>'+fmt.format(a.values[i])+'</span><span>'+fmt.format(b.values[i])+'</span></span></button>').join("");
const gap=comparable?('<div><small>MONTHLY GAP / '+esc(months[x])+'</small><strong>'+fmt.format(abs)+'</strong><p>'+ (diff===0?"The two references are equal.":diff>0?esc(a.city)+" has a "+percent+"% lower reference than "+esc(b.city)+".":esc(a.city)+" has a "+percent+"% higher reference than "+esc(b.city)+".")+'</p></div><div><small>REFERENCE TYPE</small><p>HUD FY'+a.fy+' SAFMR · gross rent, not advertised rent</p></div>'):('<div><small>COMPARISON WITHHELD</small><strong>Different source years</strong><p>One area is carrying a prior-year reference. Values remain visible but the dollar gap is not calculated.</p></div>');
view.innerHTML='<div class="cg-locations"><div class="cg-place"><small>Place A · mint bar</small><h3>'+labels(a)+'</h3><p>'+esc(a.area)+' · FY'+a.fy+'</p></div><div class="cg-place"><small>Place B · gold bar</small><h3>'+labels(b)+'</h3><p>'+esc(b.area)+' · FY'+b.fy+'</p></div></div>'+
'<div class="cg-gap">'+gap+'</div><h3 class="cg-chart-title">Compare by bedroom count · monthly HUD reference</h3><div class="cg-chart" role="group" aria-label="Choose a bedroom count to explore its difference">'+bars+'</div>'+
'<div class="cg-chosen"><h3>'+esc(months[x])+' · what does this mean?</h3><p>These published rent references cover gross rent, including relevant tenant-paid utilities. They do not measure rent paid by every household, available apartments, total housing costs, local pay or affordability.</p><small>'+(!comparable?"Different reference years: no numerical comparison. ":"FY"+a.fy+" reference; effective date in the compiled data: "+esc(a.effective)+". ")+'A rent difference alone cannot identify its cause.</small><div class="cg-linkset"><a href="'+esc(a.official)+'" target="_blank" rel="noopener noreferrer">HUD method ↗</a><a href="'+esc(a.source)+'" target="_blank" rel="noopener noreferrer">Compiled ZIP dataset ↗</a><a href="corporate-ownership.html">Trace ownership →</a></div></div>';
view.querySelectorAll("[data-bedroom]").forEach(el=>el.addEventListener("click",()=>{states.bed=Number(el.dataset.bedroom);renderHousing()}));
}
function renderUnknown(){const t=follow[states.topic];if(!t)return;byId("cg-period").textContent="Insufficient comparable local evidence";
byId("cg-scope").textContent="No validated identical city-level measure is loaded for "+titles[states.topic].toLowerCase()+".";
byId("cg-view").innerHTML='<div class="cg-unsupported"><span class="cg-unknown-pill">Data gap / no invented estimate</span><h3>'+esc(titles[states.topic])+': what would a fair comparison require?</h3><p>'+esc(t.why)+'</p><p>Power Atlas does not convert national averages into local bills, or silently treat one city&#39;s reporting method as equivalent to another.</p><div class="cg-linkset">'+t.sources.map(s=>'<a href="'+esc(safeUrl(s[1]))+'"'+(s[1].startsWith("https")?' target="_blank" rel="noopener noreferrer"':'')+'>'+esc(s[0])+' ↗</a>').join("")+'</div></div>'}
function render(){document.querySelectorAll(".cg-topic").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.topic===states.topic)));if(states.topic==="housing")renderHousing();else renderUnknown()}
async function compare(){if(states.loading)return;const za=byId("cg-zip-a").value.trim(),zb=byId("cg-zip-b").value.trim();
if(!zipOkay(za)||!zipOkay(zb)){status("Enter two valid five-digit U.S. ZIP codes.",true);return}
if(za===zb){status("Choose two different ZIP codes.",true);return}
states.loading=true;status("Looking up postal areas and source-backed rent references…");byId("cg-form").querySelector(".cg-action").disabled=true;
try{const [placeA,placeB]=await Promise.all([locate(za),locate(zb)]);const [a,b]=await Promise.all([getRents(placeA),getRents(placeB)]);states.a=a;states.b=b;status("Evidence loaded for "+a.city+", "+a.state+" and "+b.city+", "+b.state+".");render();byId("cg-comparison").scrollIntoView({behavior:"smooth",block:"start"})}
catch(e){states.a=null;states.b=null;render();status("Comparison unavailable: "+String(e.message||e).slice(0,175)+" No figures have been inferred.",true)}
finally{states.loading=false;byId("cg-form").querySelector(".cg-action").disabled=false}
}
byId("cg-form").addEventListener("submit",e=>{e.preventDefault();compare()});
document.querySelectorAll(".cg-presets button").forEach(btn=>btn.addEventListener("click",()=>{byId("cg-zip-a").value=btn.dataset.a;byId("cg-zip-b").value=btn.dataset.b;compare()}));
document.querySelectorAll(".cg-topic").forEach(btn=>btn.addEventListener("click",()=>{states.topic=btn.dataset.topic;render()}));
render();
})();