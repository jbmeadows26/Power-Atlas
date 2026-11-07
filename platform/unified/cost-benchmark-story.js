/* Power Atlas · benchmark-led, evidence-first household cost storytelling.
   No local prices are inferred from national spending or Census demographic estimates.
   All figures come from sourced repository data; submitted ZIP is never sent here. */
(function(){
"use strict";
var DATA_URL="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/place-impact/cost-benchmark-drivers-v1.json";
var data=null,forces=null,topic="housing",geo={zip:null,stateName:null,stateCode:null,local:null,corporateExamples:[],ownershipExamples:[],moneyExample:null};
var FORCES_URL="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/place-impact/economic-forces-v1.json";
var colors=["#3c8d81","#65b4a0","#d0a85f","#96aab0","#41677d","#8c8fbe"];
var dollars=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0});
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function url(v){return /^https:\/\/[^\s<>"']+$/.test(v||"")?v:null}
function source(href,label){return url(href)?'<a href="'+esc(href)+'" target="_blank" rel="noopener noreferrer">'+esc(label||"See original source ↗")+'</a>':""}
function card(text,title,detail){
 return '<div class="bs-stat"><span class="bs-stat-label">'+esc(text)+'</span><strong>'+esc(title)+'</strong><small>'+esc(detail)+'</small></div>';
}

function renderEconomicForces(){
 if(!forces||forces.schema!=="power-atlas.economic-forces.v1")return '<section class="bs-inner"><h4>4 · The wider economy and corporate power</h4><p class="bs-unknown">The verified macroeconomic and ownership source map is unavailable. National spending figures above remain valid, but global or company claims are not inferred.</p></section>';
 var cfg=forces.topics?.[topic];if(!cfg)return "";
 var signals=Object.fromEntries((forces.signals||[]).map(function(s){return [s.id,s]}));
 function badge(kind){
  return '<span class="bs-status-kind'+(kind==="forecast"||kind==="research_estimate"?" projection":kind==="alleged"?" allegation":"")+'">'+esc(kind==="forecast"?"2026 forecast":kind==="measured"?"Measured":kind==="research_estimate"?"Study estimate":kind==="policy_decision"?"Official decision":kind==="alleged"?"Regulatory allegation":kind==="association"?"Observed association":kind==="observed"?"Documented observation":kind==="verified"?"Verified link":kind==="unknown"?"Local effect unknown":kind||"Source-linked")+'</span>';
 }
 function signalCard(s){
  return '<div class="bs-signal"><strong>'+esc(s.value)+'</strong><span class="bs-signal-name">'+esc(s.name)+'</span>'+badge(s.kind)+'<small>'+esc(s.period)+' · '+esc(s.scope)+'</small><small>'+esc(s.explain)+'</small>'+source(s.source,"Official source ↗")+'<details><summary class="bs-footnote">How to interpret it</summary><p class="bs-footnote">'+esc(s.limits)+'</p></details></div>';
 }
 function forceGroup(title,eyebrow,ids,m,scope){
  var cards=(ids||[]).map(function(id){return signals[id]}).filter(Boolean).map(signalCard).join("");
  return '<section class="bs-forces-section" aria-label="'+esc(title)+'"><span class="bs-kicker">'+esc(eyebrow)+'</span><h5>'+esc(title)+'</h5><div class="bs-signals">'+cards+'</div>'+
  '<p class="bs-force-mechanism"><strong>'+esc(m?.[0]||"Economic mechanism")+'</strong> · '+esc(m?.[1]||"")+'</p>'+
  '<p class="bs-footnote">'+(scope==="global"?"Forecasts describe world markets, not what a local family will pay.":"Economic indicators are not a causal price decomposition or a quoted household rate.")+'</p></section>';
 }
 var examples=(geo.corporateExamples||[]).slice(0,3);
 
 var ownershipLinks=(geo.ownershipExamples||[]).slice(0,3).map(function(r){
  var share=typeof r.shares==="number"?' · '+esc(r.shares.toFixed(1))+'% disclosed shares':"";
  var relationship=(r.relation==="BENEFICIAL_SHARES"?"Dated beneficial ownership":r.relation==="FOUNDED_AND_LEADS"?"Dated firm leadership":r.relation==="OPERATES_BUSINESS"?"Reported business operation":r.relation==="LISTED_PORTFOLIO_COMPANY"?"Reported portfolio company":"Documented corporate relationship");
  return '<div class="bs-company-story"><span class="bs-kicker">'+esc(relationship)+share+' · '+esc(r.date)+'</span><h6>'+esc(r.owner)+' → '+esc(r.business)+'</h6><p>'+esc(r.note)+'</p><p class="bs-company-note">This relationship does not demonstrate that this firm serves your ZIP or raised your bill.</p>'+source(r.source,"Inspect corporate filing or disclosure ↗")+'</div>';
 }).join("");
 var money=geo.moneyExample;
 var moneyStory=money?'<article class="bs-company-story"><span class="bs-kicker">Campaign finance and government business · separate disclosed streams</span><h6>'+esc(money.company)+'</h6><p>'+esc(money.finding)+'</p><p><strong>'+esc(money.contributions!=null?dollars.format(money.contributions):"Amount unavailable")+'</strong> · '+esc(money.politicalYear||"Year not specified")+' disclosed corporate + employee-PAC political giving across multiple jurisdictions. This is <strong>not</strong> all federal PAC spending, and is not the cost to taxpayers.</p><p class="bs-company-note">'+esc(money.limitation)+' The filings do not show that contributions purchased government awards or increased a household bill.</p><div class="bs-company-links">'+source(money.politicalSource||money.disclosure,"Read company political disclosure ↗")+'<a href="business-influence.html">Inspect independent awards / political analysis →</a></div></article>':"";
var cases=examples.length?examples.map(function(c){
  var status=c.status||"unknown";
  var links=(c.sources||[]).filter(function(s){return url(s.url)}).slice(0,2).map(function(s){return source(s.url,s.label+" ↗")}).join("");
  var stages=(c.stages||[]).slice(0,4).map(function(st){return '<li><b>'+esc(st.actor)+'</b> · '+badge(st.status)+' '+esc(st.detail)+'</li>'}).join("");
  return '<article class="bs-company-story"><h6>'+esc(c.title||"Source-linked company investigation")+'</h6>'+badge(status)+'<p>'+esc(c.summary||c.question)+'</p><ul class="bs-case-stages">'+stages+'</ul><p class="bs-company-note"><b>What is not proven:</b> '+esc(c.limit||"No local household price effect has been established.")+'</p><div class="bs-company-links">'+links+'</div></article>';
 }).join(""):'<p class="bs-company-note">A current verified, category-specific ownership-to-price case is not yet available. This is a data gap, not evidence that corporate influence is absent. The documented ownership network and business investigations below remain available.</p>';
 var fallback=esc(cfg.firm||"Ownership, pricing and financial decisions can affect costs, but must be tied to verified company records.");
 var walk='<div class="bs-force-trail" aria-label="How an economic shock can reach a household"><span>🌍 Global conditions</span><span>🏦 U.S. economy & policy</span><span>🏢 Companies & major investors</span><span>📍 Local market</span><span>🏠 Household cost</span></div>';
 return '<section class="bs-inner" aria-label="U.S. macroeconomic, international and corporate price drivers"><h4>4 · The wider economy, companies and major investors</h4>'+
 '<p class="bs-force-intro">Why this price exists is a chain—not one villain or one statistic. Trace the <strong>global and national conditions</strong>, then the businesses and decision-makers who can transmit, amplify, or absorb the pressure. The links below distinguish measured facts, projections, allegations and unknown local impacts.</p>'+walk+
 '<div class="bs-force-grid">'+
 forceGroup("U.S. economic and policy pressures","Macroeconomic · nationwide",cfg.domestic,cfg.mechanisms?.[0],"domestic")+
 forceGroup("Global markets and international shocks","International · cross-border",cfg.global,cfg.mechanisms?.[1],"global")+'</div>'+
 '<section class="bs-forces-section" style="margin-top:12px" aria-label="Company and wealthy owner influence"><span class="bs-kicker">Companies · shareholders · private equity · political influence</span><h5>Who can influence the price—and who owns them?</h5>'+
 '<p class="bs-force-mechanism">'+fallback+'</p>'+
 '<div class="bs-company-examples">'+cases+ownershipLinks+moneyStory+'</div>'+
 '<p class="bs-force-more">A named billionaire, fund or donor is shown only when a dated source supports the relationship. Owning shares, lobbying or donating to a campaign does <strong>not</strong> by itself establish illegal conduct, a purchased policy or higher local prices.</p>'+
 '<div class="bs-links"><a href="#corporatePaths">Explore verified ownership →</a><a href="business-influence.html">Business funding & public decisions →</a><a href="donor-intelligence.html">Political money records →</a></div></section></section>';
}

/* Bedroom-level housing reference: HUD Small Area Fair Market Rents.
   Repo-published vetted state files first; CC BY source download as fallback.
   No extrapolation, unverified listings, or ZIP-to-district assumptions. */
var rentStateCache=Object.create(null);
var rentLoader=Object.create(null);
var RENT_FILES="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/housing/bedroom-rents/";
var RENT_PROVIDER="https://multifamily.today/data/zips/";
var RENT_HUD_SOURCE="https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html";
function validRentArray(v){
 return Array.isArray(v)&&v.length===5&&v.every(function(n){return Number.isFinite(n)&&n>0&&n<=50000;});
}
function validRentDocument(v,st){
 if(!v||v.state!==st||v.fy!==2027||!v.zips||typeof v.zips!=="object"||!v.areas||typeof v.areas!=="object")return false;
 return true;
}
function htmlRentUnavailable(reason){
 return '<div class="bs-rent-unavailable"><strong>'+esc(reason)+'</strong><p>No prices have been inferred. You can use HUD’s original lookup while this ZIP is being connected.</p><div class="bs-links">'+source(RENT_HUD_SOURCE,"HUD original rent lookup ↗")+source("https://multifamily.today/","Independent 2027 ZIP lookup ↗")+'</div></div>';
}
function showHousingRent(hud,zip,selectedArea){
 var panel=document.getElementById("housingBedroomPanel");if(!panel||topic!=="housing"||geo.zip!==zip)return;
 var areas=(hud.zips||{})[zip];
 if(!Array.isArray(areas)||!areas.length){
  panel.innerHTML='<h4>1 · Rent by number of bedrooms in '+esc(zip)+'</h4>'+htmlRentUnavailable("HUD FY 2027 ZIP-level bedroom benchmarks are not available for this ZIP.");
  return;
 }
 var good=areas.filter(function(e){
  return Array.isArray(e)&&typeof e[0]==="string"&&validRentArray(e[1])&&!!hud.areas[e[0]];
 });
 if(!good.length){
  panel.innerHTML='<h4>1 · Rent by number of bedrooms in '+esc(zip)+'</h4>'+htmlRentUnavailable("The available ZIP data could not be verified against the published HUD area.");
  return;
 }
 var idx=Number.isInteger(selectedArea)&&selectedArea>=0&&selectedArea<good.length?selectedArea:0;
 var item=good[idx],area=hud.areas[item[0]],held=validRentArray(item[2]),amounts=held?item[2]:item[1];
 var max=Math.max.apply(null,amounts),labels=["Studio","1 bedroom","2 bedrooms","3 bedrooms","4 bedrooms"];
 var choices=good.length>1?'<label class="bs-rent-region">HUD rent area for this ZIP <select id="bsRentRegion" aria-label="Choose HUD rent area for ZIP '+esc(zip)+'">'+good.map(function(e,i){
  return '<option value="'+i+'"'+(i===idx?' selected':'')+'>'+esc(hud.areas[e[0]].name)+'</option>';
 }).join("")+'</select></label><p class="bs-rent-note">This ZIP spans multiple HUD areas. Select the actual applicable area; the ZIP alone cannot identify a property’s jurisdiction.</p>':'<p class="bs-rent-note">HUD area: <strong>'+esc(area.name)+'</strong>.</p>';
 var tiles=labels.map(function(label,i){
  return '<article class="bs-rent-tile"><span class="bs-rent-name">'+esc(label)+'</span><strong class="bs-rent-amount">'+esc(dollars.format(amounts[i]))+'<small>/mo</small></strong><div class="bs-rent-track" aria-hidden="true"><span style="width:'+Math.round(amounts[i]/max*100)+'%"></span></div></article>';
 }).join("");
 var areaFmr=Array.isArray(area.fmr)&&validRentArray(area.fmr)?area.fmr:null;
 var compare=areaFmr&&!held?
 '<details class="bs-rent-compare"><summary>How is this different from the larger HUD area?</summary><p>This ZIP’s 2-bedroom HUD benchmark is <strong>'+esc(dollars.format(amounts[2]))+'</strong>; the larger area’s 2-bedroom FMR is <strong>'+esc(dollars.format(areaFmr[2]))+'</strong>. These are distinct published reference geographies, not competing listings or proof of an actual rent premium.</p></details>':"";
 panel.innerHTML='<div class="bs-rent-header"><div><span class="bs-eyebrow">Housing · FY '+(held?"2026 retained":"2027")+' HUD rent reference</span><h4>Rent reference by bedroom count · ZIP '+esc(zip)+'</h4></div><span class="bs-rent-loc">'+esc(geo.stateCode||"United States")+'</span></div>'+
 choices+'<div class="bs-rent-grid">'+tiles+'</div>'+
 '<p class="bs-rent-explain"><strong>What these numbers mean:</strong> HUD Small Area Fair Market Rents estimate <strong>monthly gross rent, including tenant-paid utilities</strong> for the housing voucher program. They are <strong>not today’s advertised apartment prices</strong> or the average paid by renters in this ZIP.</p>'+
 (held?'<p class="bs-rent-status"><strong>Reevaluation note:</strong> This ZIP has an FY 2026 amount marked as remaining in effect while HUD reevaluates FY 2027 values. Confirm the current applicable figures with HUD before relying on them.</p>':'<p class="bs-rent-note">FY 2027 effective October 1, 2026. Some areas may have reevaluation exceptions.</p>')+
 compare+'<div class="bs-links bs-rent-sources">'+source(RENT_HUD_SOURCE,"HUD rent methodology and official lookup ↗")+source("https://multifamily.today/data/","Data: Multifamily Today (CC BY 4.0) ↗")+'</div>';
 var select=panel.querySelector("#bsRentRegion");
 if(select)select.addEventListener("change",function(){showHousingRent(hud,zip,Number(this.value));});
}
function renderHousingRents(){
 var panel=document.getElementById("housingBedroomPanel");
 if(!panel||topic!=="housing")return;
 var zip=geo.zip,st=geo.stateCode;
 if(!zip||!/^[0-9]{5}$/.test(zip)){
  panel.innerHTML='<h4>1 · What does a studio, 1-, 2-, 3- or 4-bedroom cost?</h4><p class="bs-rent-note">Enter your ZIP code in Step 1 to see monthly HUD rent benchmarks for each bedroom size. No national number is substituted for an unknown local rent.</p><a class="bs-next" href="#where">Enter a ZIP code ↑</a>';
  return;
 }
 if(!st||!/^[A-Z]{2}$/.test(st)){
  panel.innerHTML='<h4>1 · Bedroom rents for ZIP '+esc(zip)+'</h4>'+htmlRentUnavailable("We could not verify the ZIP’s state, so no bedroom rent was assigned.");
  return;
 }
 if(rentStateCache[st]){
  showHousingRent(rentStateCache[st],zip);
  return;
 }
 panel.innerHTML='<h4>Rent reference by bedroom count · ZIP '+esc(zip)+'</h4><p class="bs-rent-note" role="status">Loading FY 2027 HUD bedroom-level reference rents for '+esc(st)+'…</p>';
 if(!rentLoader[st]){
  rentLoader[st]=(async function(){
   var urls=[RENT_FILES+st+".json",RENT_PROVIDER+st+".json"],last="";
   for(var i=0;i<urls.length;i++){
    try{
     var reply=await fetch(urls[i],{cache:"no-store"});
     if(!reply.ok)throw Error("HTTP "+reply.status);
     var payload=await reply.json();
     if(!validRentDocument(payload,st))throw Error("Rent source year or geography mismatch");
     rentStateCache[st]=payload;return payload;
    }catch(err){last=String(err);}
   }
   throw Error(last||"No compatible data source");
  })();
 }
 rentLoader[st].then(function(j){
  if(topic==="housing"&&geo.zip===zip&&geo.stateCode===st)showHousingRent(j,zip);
 }).catch(function(){
  if(topic==="housing"&&geo.zip===zip&&geo.stateCode===st){
   var current=document.getElementById("housingBedroomPanel");
   if(current)current.innerHTML='<h4>Rent reference by bedroom count · ZIP '+esc(zip)+'</h4>'+htmlRentUnavailable("The official-source rent table could not be loaded.");
  }
  delete rentLoader[st];
 });
}
function render(){
 var root=document.getElementById("benchmarkStory");if(!root)return;
 var output=root.querySelector("#bsDisplay");
 if(!data){output.innerHTML='<p class="bs-status">Loading the original household-spending benchmarks…</p>';return;}
 var cfg=data.topics[topic];if(!cfg){output.innerHTML='<p role="alert">No verified cost benchmark is available for this category.</p>';return;}
 var head=cfg.headline,heading=root.querySelector("#bsName"),intro=root.querySelector("#bsIntro");
 heading.textContent=cfg.title;
 intro.textContent=topic==="housing"?"Monthly gross-rent reference prices by studio, 1-, 2-, 3- and 4-bedroom homes for your ZIP, followed by the forces that influence them. HUD benchmarks are not live apartment listing prices.":cfg.intro;
 var headline="";
 if(head){
  var monthly=Math.round(head.annual/12),delta=(head.annual-head.prior)/head.prior*100;
  var kind=head.kind==="income"?"Income context · not a household cost":"National spending benchmark";
  headline='<div class="bs-highlight"><span class="bs-eyebrow">'+esc(kind)+'</span><strong class="bs-value">'+esc(dollars.format(monthly))+'<span>/month</span></strong><div class="bs-label">'+esc(head.label)+'</div><div class="bs-period">2025 mean per U.S. consumer unit · annualized ÷ 12</div></div>'+
   '<div class="bs-change">'+card("Reported annual change", (delta>=0?"+":"")+delta.toFixed(1)+"%","2024 to 2025 · spending/income, not price inflation")+
   card("Annual U.S. average",dollars.format(head.annual),"BLS Consumer Expenditure Survey, 2025")+'</div>';
 }else headline='<div class="bs-nobenchmark"><strong>There is no defensible one-number household benchmark for this topic.</strong><p>'+esc(cfg.intro)+'</p><p>The evidence below traces decision-makers and mechanisms without assigning an invented dollar cost to political activity or local taxes.</p></div>';
 var slices=cfg.slices||[],sum=slices.reduce(function(n,x){return n+x[1]},0),bars="";
 if(slices.length&&head&&head.kind==="spend"){
  bars='<div class="bs-segments" role="img" aria-label="Share of '+esc(cfg.title)+' national average spending by component. Individual values and source are listed below.">'+slices.map(function(x,i){
   return '<span style="width:'+Math.max(0,x[1]/sum*100).toFixed(3)+'%;background:'+colors[i%colors.length]+'" title="'+esc(x[0])+'"></span>'
  }).join("")+'</div><div class="bs-bars">'+slices.map(function(x,i){
   return '<div class="bs-bar-row"><span class="bs-dot" style="background:'+colors[i%colors.length]+'"></span><span class="bs-bar-name">'+esc(x[0])+'</span><strong>'+esc(dollars.format(Math.round(x[1]/12)))+'/mo</strong><span class="bs-bar-share">'+Math.round(x[1]/sum*100)+'%</span></div>'
  }).join("")+'</div><p class="bs-footnote">These colors show <strong>where money was spent</strong>—not the percent of a price increase caused by a company, regulation or politician. Component estimates are survey averages and may differ slightly from totals due to rounding.</p>';
 }else if(cfg.secondary){
  bars='<div class="bs-rate">'+card(cfg.secondary.label,Number(cfg.secondary.value).toFixed(2)+cfg.secondary.unit,esc(cfg.secondary.year)+" · "+cfg.secondary.definition)+source(cfg.secondary.source,"How the EIA measures this rate ↗")+'</div><p class="bs-footnote">The national utilities spending figure above includes several services; it cannot be converted into your energy bill without your metered usage and tariff.</p>';
 }else bars='<p class="bs-footnote">A source-verified national line-item breakdown that matches this specific question has not been established. We are not fabricating percentages.</p>';
 var local="";
 if(geo.zip){
  var indicator=geo.local;
  if(indicator&&indicator.value!=null){
   local='<div class="bs-local-number"><div class="bs-local-pair"><div class="bs-local-primary"><small>'+esc(indicator.title)+' · ZIP area '+esc(geo.zip)+'</small><strong>'+esc(indicator.value)+'</strong></div>'+(indicator.usValue!=null?'<div class="bs-local-compare"><span>U.S. median · same 2020–2024 Census survey</span><strong>'+esc(indicator.usValue)+'</strong></div>':'')+'</div><p>'+esc(indicator.limits)+'</p>'+source(indicator.source,"Census definition ↗")+'</div>';
  }else{
   local='<p class="bs-unknown">A matching Census area indicator is '+(indicator&&indicator.status==="unavailable"?"not available":"being checked")+' for this ZIP. No local price has been inferred.</p>';
  }
 }else local='<p class="bs-unknown">Enter a ZIP above to add a sourced Census area indicator. It will only appear when the underlying survey actually measured it.</p>';
 var localNote=cfg.localNote||"National averages do not establish a local price.";
 var influence=(cfg.drivers||[]).map(function(d,i){
  return '<article class="bs-influence"><div class="bs-influence-head"><span class="bs-driver-number">'+(i+1)+'</span><h5>'+esc(d.label)+'</h5></div><p>'+esc(d.why)+'</p><div class="bs-influence-who"><span>Who has a role?</span> '+esc(d.who)+'</div><div class="bs-influence-action"><span>Practical choice</span> '+esc(d.choice)+'</div>'+source(d.source,"Original evidence ↗")+'</article>'
 }).join("");
 var spendBlock='<div class="bs-metrics">'+headline+'</div>'+
 '<section class="bs-inner" aria-label="Cost components"><h4>'+(topic==="housing"?"Other housing spending, beyond rent":"1 · What is in the bill?")+'</h4>'+bars+'</section>';
 if(topic==="housing")spendBlock='<details class="bs-rent-other"><summary>Also see the broader housing-spending average (not the rent for an apartment)</summary>'+spendBlock+'</details>';
 if(topic==="transport")spendBlock='<details class="bs-rent-other"><summary>Optional · National average transport spending (not a subway fare or route cost)</summary>'+spendBlock+'</details>';
 output.innerHTML=(topic==="housing"?'<section class="bs-inner bs-housing" id="housingBedroomPanel" aria-label="HUD rent benchmarks for studios through four bedrooms" aria-live="polite"><p>Loading bedroom rents…</p></section>':'')+
 (topic==="transport"?'<section class="bs-inner ts-story" id="transportCostStory" aria-label="Transit fares, actual tolls, trip cost scenarios and transportation contract oversight"><h4>1 · Real trip costs and public accountability</h4><p>Loading source-backed transportation charges…</p></section>':'')+spendBlock+
 (topic==="housing"?'<details class="bs-housing-context"><summary>See another rental reference: Census median for all bedroom sizes</summary><div class="bs-inner bs-local" aria-label="Census median rent context">'+local+'<p class="bs-footnote">'+esc(localNote)+'</p><a class="bs-next" href="#sourceMeasured">See all original area measurements ↓</a></div></details>':'<section class="bs-inner bs-local" aria-label="Community benchmark context"><h4>2 · What do we know about '+(geo.zip?'ZIP '+esc(geo.zip):'your area')+'?</h4>'+local+'<p class="bs-footnote">'+esc(localNote)+'</p><a class="bs-next" href="#sourceMeasured">See all original area measurements ↓</a></section>')+
 '<section class="bs-inner" aria-label="Economic drivers and choices"><h4>'+(topic==="housing"?"2 · Why are rents this high?":"3 · What actually moves this cost?")+'</h4><p class="bs-explainer">These are documented economic mechanisms and decision-makers, not a causal ranking for your ZIP. We do not know what share of your bill each one explains without matched price and policy evidence.</p><div class="bs-driver-grid">'+influence+'</div></section>'+
 renderEconomicForces()+
 '<div class="bs-bottom"><p><strong>Evidence boundary:</strong> '+esc(cfg.disclaimer)+' BLS averages are for U.S. consumer units of different sizes, not a fixed basket or a quote. October–November 2025 missing survey data were addressed using BLS weighting.</p><div class="bs-links">'+source(data.primarySource,"Read the 2025 BLS survey ↗")+'<a href="#corporatePaths">Trace documented ownership ↓</a><a href="#missingCostSources">See missing local price evidence ↓</a></div></div>';
 if(topic==="housing")renderHousingRents();
 if(topic==="transport")window.PowerAtlasTransport?.render();
}
function setContext(context){
 context=context||{};if(context.topic&&data?.topics?.[context.topic])topic=context.topic;
 else if(context.topic&&["housing","groceries","energy","health","work","schools","transport","public-services","representation"].indexOf(context.topic)>=0)topic=context.topic;
 geo={zip:context.zip||null,stateCode:context.stateCode||null,stateName:context.stateName||null,local:context.local||null,corporateExamples:Array.isArray(context.corporateExamples)?context.corporateExamples:[],ownershipExamples:Array.isArray(context.ownershipExamples)?context.ownershipExamples:[],moneyExample:context.moneyExample||null};
 render();
}
async function init(){
 var root=document.getElementById("benchmarkStory");if(!root)return;
 if(typeof window.PowerAtlasGetBenchmarkContext==="function"){
  var c=window.PowerAtlasGetBenchmarkContext();if(c)setContext(c);
 }
 try{
  var r=await fetch(DATA_URL,{cache:"no-store"});
  if(!r.ok)throw Error("HTTP "+r.status);
  var j=await r.json();
  if(j.schema!=="power-atlas.cost-benchmark-drivers.v1"||!j.topics?.housing||!j.topics?.groceries)throw Error("Unexpected schema");
  data=j;
  try{
   var econResponse=await fetch(FORCES_URL,{cache:"no-store"});
   if(!econResponse.ok)throw Error("Macro source HTTP "+econResponse.status);
   var econ=await econResponse.json();
   if(econ.schema!=="power-atlas.economic-forces.v1"||!econ.topics?.housing||!econ.signals?.length)throw Error("Invalid macroeconomic source schema");
   forces=econ;
  }catch(error){forces=null;}
  if(typeof window.PowerAtlasGetBenchmarkContext==="function")setContext(window.PowerAtlasGetBenchmarkContext());
  else render();
 }catch(err){
  root.querySelector("#bsDisplay").innerHTML='<div class="bs-nobenchmark"><strong>Source currently unavailable.</strong><p>No benchmark can be displayed without the original evidence. The independent source links and research below remain available.</p>'+source("https://www.bls.gov/news.release/cesan.htm","Visit BLS data ↗")+'</div>';
 }
}
window.PowerAtlasBenchmarkStory={setContext:setContext};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();