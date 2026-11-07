/* Power Atlas · read-only official unpaid-toll penalty baselines. No user input. */
(function(){
"use strict";
const SOURCE="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/place-impact/toll-penalties-v1.json";
const cash=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2}).format(n);
const esc=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const link=(url,label)=>/^https:\/\/[^\s<>"']+$/.test(url||"")?'<a target="_blank" rel="noopener noreferrer" href="'+esc(url)+'">'+esc(label||"Original source ↗")+'</a>':"";
let data=null,region="OTHER";
const STANDARD_TOLL=5;
function charge(stage,count){
 if(stage.feePerTxn==null||stage.feePerBill==null||stage.feePerNotice==null)return null;
 return STANDARD_TOLL*count + stage.feePerTxn*count + stage.feePerBill + stage.feePerNotice;
}
function operators(){
 if(!data)return [];
 const group=data.groups.find(x=>x.id===region);
 if(!group||region==="OTHER"){
  return data.operators.filter(a=>["ny-mta","ny-thruway","nj-turnpike","il-standard"].includes(a.id));
 }
 return group.operatorIds.map(id=>data.operators.find(x=>x.id===id)).filter(Boolean);
}
function card(op){
 const steps=op.stageDefinitions.filter(x=>x.id!=="collections").map((stage,i)=>{
  const total=charge(stage,1);
  return '<div class="tp-static-step"><span>'+esc(stage.name)+'</span><strong>'+(total===null?"Not verified":cash(total))+'</strong>'+
   '<small>'+esc(stage.description)+'</small></div>';
 }).join("");
 const note=op.id==="ny-thruway"?'<p class="tp-static-extra"><strong>Fee-unit example:</strong> Three separate $5 tolls grouped on one Thruway violation notice would total <strong>$65</strong> ($15 in tolls plus $50 <em>per notice</em>), not $165.</p>':
 op.id==="ny-mta"?'<p class="tp-static-extra"><strong>Fee-unit distinction:</strong> The listed $50 violation fee is <em>per toll transaction</em>; three $5 tolls in violation could total $165 if no waiver applies.</p>':"";
 const risk=op.stageDefinitions.find(x=>x.id==="collections");
 return '<article class="tp-static-card" data-penalty-operator="'+esc(op.id)+'">'+
 '<div class="tp-static-header"><span class="bs-eyebrow">'+esc(op.issuer)+'</span><h5>'+esc(op.name)+'</h5></div>'+
 '<div class="tp-static-stages">'+steps+'</div>'+note+
 '<p class="tp-static-risk"><strong>Collections / registration:</strong> '+esc(risk?.description||"Additional rules depend on your authority.")+'</p>'+
 '<p class="tp-static-relief"><strong>Dispute or waiver rights:</strong> '+esc(op.relief)+'</p>'+
 '<p class="tp-note">'+esc(op.limit)+'</p>'+
 '<div class="ts-links">'+op.sources.map((url,i)=>link(url,"Official penalty rule "+(i+1)+" ↗")).join("")+'</div></article>';
}
function render(){
 const root=document.getElementById("transportPenaltyPanel");if(!root)return;
 if(!data){
  root.innerHTML='<h4>Unpaid toll: official fees and enforcement stages</h4><p class="ts-note">Loading the original authority fee schedules…</p>';return;
 }
 const group=region==="OTHER"?"Examples from New York, New Jersey and Illinois":(data.groups.find(x=>x.id===region)?.name||"Regional examples");
 const rights=(data.rights||[]).filter(x=>region==="OTHER"||x.region===region).map(x=>'<div class="tp-relief"><strong>'+esc(x.title)+'</strong><p>'+esc(x.description)+'</p>'+link(x.source,"Official protection ↗")+'</div>').join("");
 const oversight=(data.financialWatch||[]).map(x=>'<details class="tp-account"><summary>'+esc(x.title)+'</summary><p>'+esc(x.description)+'</p>'+link(x.source,"Investigate record ↗")+'</details>').join("");
 root.innerHTML='<div class="tp-head"><span class="bs-eyebrow">Unpaid tolls · baseline by authority</span>'+
 '<h4>How much can an unpaid toll grow?</h4>'+
 '<p>Compare official stages on the same illustrative <strong>$5 original toll</strong>. Nothing to enter. These are <strong>fee-schedule examples, not actual local toll rates or money owed</strong>. Some agencies charge per bill, others per unpaid transaction or per notice.</p></div>'+
 '<p class="tp-base-region">Showing: <strong>'+esc(group)+'</strong>. The ZIP never establishes where a missed toll occurred.</p>'+
 '<div class="tp-static-cards">'+operators().map(card).join("")+'</div>'+
 '<h5>How drivers can challenge or avoid fees</h5><div class="tp-relief-grid">'+rights+'</div>'+
 '<details class="tp-account-wrap"><summary>Who collects penalties, and where does that money go?</summary>'+
 '<p>Investigate assessed versus collected fees, collection-vendor contracts and the public budgets receiving the funds. Penalty revenue is not automatically dedicated to infrastructure improvements. Contracting relationships alone are not proof of corruption.</p>'+
 oversight+'</details>'+
 '<p class="tp-method"><strong>Method:</strong> '+esc(data.comparison)+' An authority may waive a charge, require extra notice or assess additional unverified collection fees. Always consult the actual dated notice and official appeal policy.</p>';
 root.dataset.ready="1";
}
function setRegion(r){
 if(!["NYNJ","CHI","OTHER"].includes(r))return;
 if(region!==r){region=r;render();}
}
function setContext(c){
 const st=c?.stateCode||"";
 setRegion(["NY","NJ"].includes(st)?"NYNJ":st==="IL"?"CHI":"OTHER");
}
async function init(){
 if(!document.getElementById("benchmarkStory"))return;
 try{
  const result=await fetch(SOURCE,{cache:"no-store"});
  if(!result.ok)throw Error("HTTP "+result.status);
  const j=await result.json();
  if(j.schema!=="power-atlas.toll-penalties.v1"||!Array.isArray(j.operators))throw Error("Invalid schema");
  data=j;
  if(typeof window.PowerAtlasGetBenchmarkContext==="function"&&region==="OTHER")setContext(window.PowerAtlasGetBenchmarkContext());
  render();
 }catch(err){
  const root=document.getElementById("transportPenaltyPanel");
  if(root)root.innerHTML='<div class="tp-error"><strong>Penalty source temporarily unavailable.</strong><p>No fee is inferred from a ZIP or from this missing table.</p>'+
   link("https://www.e-zpassny.com/tbm/no-pay","Official NY toll violation schedule ↗")+
   link("https://agency.illinoistollway.com/ves","Illinois official schedule ↗")+'</div>';
 }
}
window.PowerAtlasTollPenalty={render,setRegion,setContext};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();