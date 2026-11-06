/* Power Atlas · benchmark-led, evidence-first household cost storytelling.
   No local prices are inferred from national spending or Census demographic estimates.
   All figures come from sourced repository data; submitted ZIP is never sent here. */
(function(){
"use strict";
var DATA_URL="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/place-impact/cost-benchmark-drivers-v1.json";
var data=null,topic="housing",geo={zip:null,stateName:null,stateCode:null,local:null};
var colors=["#3c8d81","#65b4a0","#d0a85f","#96aab0","#41677d","#8c8fbe"];
var dollars=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0});
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function url(v){return /^https:\/\/[^\s<>"']+$/.test(v||"")?v:null}
function source(href,label){return url(href)?'<a href="'+esc(href)+'" target="_blank" rel="noopener noreferrer">'+esc(label||"See original source ↗")+'</a>':""}
function card(text,title,detail){
 return '<div class="bs-stat"><span class="bs-stat-label">'+esc(text)+'</span><strong>'+esc(title)+'</strong><small>'+esc(detail)+'</small></div>';
}
function render(){
 var root=document.getElementById("benchmarkStory");if(!root)return;
 var output=root.querySelector("#bsDisplay");
 if(!data){output.innerHTML='<p class="bs-status">Loading the original household-spending benchmarks…</p>';return;}
 var cfg=data.topics[topic];if(!cfg){output.innerHTML='<p role="alert">No verified cost benchmark is available for this category.</p>';return;}
 var head=cfg.headline,heading=root.querySelector("#bsName"),intro=root.querySelector("#bsIntro");
 heading.textContent=cfg.title;intro.textContent=cfg.intro;
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
   local='<div class="bs-local-number"><small>'+esc(indicator.title)+' · area '+esc(geo.zip)+'</small><strong>'+esc(indicator.value)+'</strong><p>'+esc(indicator.limits)+'</p>'+source(indicator.source,"Census definition ↗")+'</div>';
  }else{
   local='<p class="bs-unknown">A matching Census area indicator is '+(indicator&&indicator.status==="unavailable"?"not available":"being checked")+' for this ZIP. No local price has been inferred.</p>';
  }
 }else local='<p class="bs-unknown">Enter a ZIP above to add a sourced Census area indicator. It will only appear when the underlying survey actually measured it.</p>';
 var localNote=cfg.localNote||"National averages do not establish a local price.";
 var influence=(cfg.drivers||[]).map(function(d,i){
  return '<article class="bs-influence"><div class="bs-influence-head"><span class="bs-driver-number">'+(i+1)+'</span><h5>'+esc(d.label)+'</h5></div><p>'+esc(d.why)+'</p><div class="bs-influence-who"><span>Who has a role?</span> '+esc(d.who)+'</div><div class="bs-influence-action"><span>Practical choice</span> '+esc(d.choice)+'</div>'+source(d.source,"Original evidence ↗")+'</article>'
 }).join("");
 output.innerHTML='<div class="bs-metrics">'+headline+'</div>'+
 '<section class="bs-inner" aria-label="Cost components"><h4>1 · What is in the bill?</h4>'+bars+'</section>'+
 '<section class="bs-inner bs-local" aria-label="Community benchmark context"><h4>2 · What do we know about '+(geo.zip?'ZIP '+esc(geo.zip):'your area')+'?</h4>'+local+'<p class="bs-footnote">'+esc(localNote)+'</p><a class="bs-next" href="#sourceMeasured">See all original area measurements ↓</a></section>'+
 '<section class="bs-inner" aria-label="Economic drivers and choices"><h4>3 · What actually moves this cost?</h4><p class="bs-explainer">These are documented economic mechanisms and decision-makers, not a causal ranking for your ZIP. We do not know what share of your bill each one explains without matched price and policy evidence.</p><div class="bs-driver-grid">'+influence+'</div></section>'+
 '<div class="bs-bottom"><p><strong>Evidence boundary:</strong> '+esc(cfg.disclaimer)+' BLS averages are for U.S. consumer units of different sizes, not a fixed basket or a quote. October–November 2025 missing survey data were addressed using BLS weighting.</p><div class="bs-links">'+source(data.primarySource,"Read the 2025 BLS survey ↗")+'<a href="#corporatePaths">Trace documented ownership ↓</a><a href="#missingCostSources">See missing local price evidence ↓</a></div></div>';
}
function setContext(context){
 context=context||{};if(context.topic&&data?.topics?.[context.topic])topic=context.topic;
 else if(context.topic&&["housing","groceries","energy","health","work","schools","transport","public-services","representation"].indexOf(context.topic)>=0)topic=context.topic;
 geo={zip:context.zip||null,stateCode:context.stateCode||null,stateName:context.stateName||null,local:context.local||null};
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
  if(typeof window.PowerAtlasGetBenchmarkContext==="function")setContext(window.PowerAtlasGetBenchmarkContext());
  else render();
 }catch(err){
  root.querySelector("#bsDisplay").innerHTML='<div class="bs-nobenchmark"><strong>Source currently unavailable.</strong><p>No benchmark can be displayed without the original evidence. The independent source links and research below remain available.</p>'+source("https://www.bls.gov/news.release/cesan.htm","Visit BLS data ↗")+'</div>';
 }
}
window.PowerAtlasBenchmarkStory={setContext:setContext};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();