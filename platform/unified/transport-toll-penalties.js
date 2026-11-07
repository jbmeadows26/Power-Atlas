/* Power Atlas toll penalty timelines. Illustrations, not legal or billing advice. */
(function(){
"use strict";
const SOURCE="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/place-impact/toll-penalties-v1.json";
const fmt=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumFractionDigits:2,maximumFractionDigits:2}).format(n);
const esc=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const link=(url,label)=>/^https:\/\/[^\s<>"']+$/.test(url||"")?'<a target="_blank" rel="noopener noreferrer" href="'+esc(url)+'">'+esc(label||"Original source ↗")+'</a>':"";
let data=null,region="OTHER",operator=null,manualRegion=false;
let amount=5,transactions=1;
function clamp(n,min,max){return Number.isFinite(n)?Math.min(max,Math.max(min,n)):min}
function operatorList(){let r=data?.groups?.find(x=>x.id===region);return r?r.operatorIds.map(id=>data.operators.find(x=>x.id===id)).filter(Boolean):[];}
function current(){return operatorList().find(x=>x.id===operator)||operatorList()[0]||null;}
function feeFor(stage,n){
 if(stage.feePerTxn==null||stage.feePerBill==null||stage.feePerNotice==null)return null;
 return stage.feePerTxn*n+stage.feePerBill+stage.feePerNotice;
}
function rightsFor(){return (data.rights||[]).filter(x=>x.region===region);}
function financialOversight(){
 const rows=(data.financialWatch||[]).map(x=>
 '<details class="tp-account"><summary>'+esc(x.title)+'</summary><p>'+esc(x.description)+'</p>'+link(x.source,"Original public record ↗")+'</details>').join("");
 return '<details class="tp-account-wrap"><summary>Where do penalties and collection fees go—and who benefits?</summary><p>Trace <strong>fees actually collected</strong> into audited revenue, enforcement contracts, debt collection payments, and road or transit investments. Do not equate fines assessed with cash recovered, or procurement contracts with corruption.</p>'+rows+'</details>';
}
function stageCard(s,i){
 const fee=feeFor(s,transactions),base=amount*transactions,total=fee===null?null:fee+base;
 const late=!!s.unknownFurtherFees,showUnknown=fee===null?"Amount unverified":late?"Known minimum":"Illustrative total";
 let pct=fee!=null&&base>0?fee/base:0;
 const risk=fee===null||late;
 return '<article class="tp-stage'+(i===0?' tp-stage-first':'')+'"><div class="tp-stage-head"><span>STEP '+(i+1)+'</span><h6>'+esc(s.name)+'</h6></div>'+
  '<div class="tp-stage-number"><strong>'+(total===null?'—':fmt(total))+'</strong><small>'+showUnknown+'</small></div>'+
  '<p class="tp-stage-base">'+(total===null?'No reliable numeric total at this stage':fmt(base)+' original toll'+(transactions===1?'':'s')+' + '+fmt(fee)+' fees')+'</p>'+
  '<div class="tp-stage-track" aria-hidden="true">'+(total===null?'': '<span class="tp-fee-track" style="width:'+Math.min(100,Math.max(0,fee/Math.max(total,.01)*100)).toFixed(2)+'%"></span>')+'</div>'+
  '<p>'+esc(s.description)+'</p>'+
  (risk?'<p class="tp-stage-warning">Other costs, eligibility or legal procedures may not be quantified.</p>':'')+'</article>';
}
function render(){
 const root=document.getElementById("transportPenaltyPanel");if(!root)return;
 if(!data){root.innerHTML='<h4>Unpaid-toll penalties and E-ZPass disputes</h4><p class="ts-note">Loading official agency fee schedules…</p>';return;}
 const op=current(),groups=data.groups||[];
 let regionSelect='<label class="tp-select-label">Toll authority region <select id="tp-region" aria-label="Toll penalty region">'+groups.map(x=>'<option value="'+esc(x.id)+'"'+(region===x.id?' selected':'')+'>'+esc(x.name)+'</option>').join("")+'</select></label>';
 let choose=op?'<label class="tp-select-label">Issuer / toll operator <select id="tp-agency" aria-label="Toll authority">'+operatorList().map(x=>'<option value="'+esc(x.id)+'"'+(op.id===x.id?' selected':'')+'>'+esc(x.name)+'</option>').join("")+'</select></label>':'';
 const top='<div class="tp-head"><span class="bs-eyebrow">Unpaid tolls · fee escalation</span><h4>How can a missed toll turn into a much larger bill?</h4><p>Different toll authorities use different warning periods, violation fees, and collection rules. <strong>A $50 charge may apply per transaction or per notice—not necessarily per bill.</strong></p></div>';
 if(!op){
 root.innerHTML=top+'<div class="tp-selects">'+regionSelect+'</div><p class="tp-note">Choose a participating toll authority to see documented penalty examples. No fee is assigned to a ZIP or inferred from an E-ZPass tag.</p>'+financialOversight();
 bind(root);return;
 }
 const limits='<p class="tp-method"><strong>Illustrative scenario, not your liability.</strong> We assume '+transactions+' unpaid transaction'+(transactions===1?'':'s')+' with the same original toll and <strong>one bill/one notice</strong> when a charge is per bill or per notice. '+esc(op.limit)+' Verify the actual notice and fee schedule before paying or disputing.</p>';
 const rightLinks=rightsFor().map(x=>'<div class="tp-relief"><strong>'+esc(x.title)+'</strong><p>'+esc(x.description)+'</p>'+link(x.source,"Official rights and guidance ↗")+'</div>').join("");
 root.innerHTML=top+
 '<div class="tp-selects">'+regionSelect+choose+'</div>'+
 '<div class="tp-assumptions"><label>Original toll per transaction, illustrative $ <input id="tp-amount" type="number" inputmode="decimal" min="0.01" max="500" step="0.01" value="'+amount+'" aria-label="Original toll amount per transaction"></label>'+
 '<label>Number of missed tolls <input id="tp-count" type="number" inputmode="numeric" min="1" max="20" step="1" value="'+transactions+'" aria-label="Number of unpaid toll transactions"></label></div>'+
 '<p class="tp-note">Starting at $5 is only an editable illustration—not a rate quoted for your crossing or vehicle.</p>'+
 '<div class="tp-stages" role="list" aria-label="Escalation from original toll to fees and collections">'+op.stageDefinitions.map(stageCard).join("")+'</div>'+
 limits+
 '<div class="tp-relief-head"><h5>How to prevent, check or contest these fees</h5><p>'+esc(op.relief)+'</p></div>'+
 '<div class="tp-relief-grid">'+rightLinks+'</div>'+
 '<p class="tp-note"><strong>Important:</strong> '+esc(op.nuance)+'</p>'+
 '<div class="ts-links">'+(op.sources||[]).map((x,i)=>link(x,"Original policy "+(i+1)+" ↗")).join("")+'</div>'+
 financialOversight()+
 '<p class="tp-footnote">'+esc(data.privacy)+' '+esc(data.comparison)+'</p>';
 bind(root);
}
function bind(root){
 if(root.dataset.tpBound==="1")return;
 root.dataset.tpBound="1";
 root.addEventListener("change",e=>{
  const x=e.target;
  if(x.id==="tp-region"){
   if(!data.groups.some(g=>g.id===x.value))return;
   region=x.value;operator=null;manualRegion=true;render();
  }else if(x.id==="tp-agency"){
   if(!operatorList().some(a=>a.id===x.value))return;
   operator=x.value;render();
  }else if(x.id==="tp-count"||x.id==="tp-amount"){
   render();
  }
 });
 root.addEventListener("input",e=>{
  const x=e.target,n=Number(x.value);
  if(x.id==="tp-amount"){
   amount=Math.round(clamp(n,.01,500)*100)/100;
   const target=root.querySelector(".tp-stages");
   if(target){const op=current();if(op)target.innerHTML=op.stageDefinitions.map(stageCard).join("");}
  }
  if(x.id==="tp-count"){
   transactions=Math.round(clamp(n,1,20));
   const target=root.querySelector(".tp-stages");
   if(target){const op=current();if(op)target.innerHTML=op.stageDefinitions.map(stageCard).join("");}
  }
 });
}
function setRegion(newRegion){
 if(manualRegion)return;
 const group=(data?.groups||[{id:"NYNJ"},{id:"CHI"},{id:"OTHER"}]).find(g=>g.id===newRegion);
 if(group&&region!==group.id){region=group.id;operator=null;render();}
}
function setContext(c){
 if(manualRegion)return;
 const code=c?.stateCode||null;
 const group=(data?.groups||[]).find(x=>x.states.includes(code));
 const next=group?.id||"OTHER";
 if(data){if(next!==region){region=next;operator=null;}render();}
 else region=next;
}
async function init(){
 if(!document.getElementById("benchmarkStory"))return;
 try{
  const r=await fetch(SOURCE,{cache:"no-store"});if(!r.ok)throw Error("HTTP "+r.status);
  const j=await r.json();if(j.schema!=="power-atlas.toll-penalties.v1"||!Array.isArray(j.operators))throw Error("Unexpected schema");
  data=j;
  if(typeof window.PowerAtlasGetBenchmarkContext==="function"&&region==="OTHER")setContext(window.PowerAtlasGetBenchmarkContext());
  else render();
 }catch(err){
  root.innerHTML='<div class="tp-error"><strong>Unpaid-toll fee schedule unavailable.</strong><p>Do not rely on a generic penalty estimate. Contact the original toll authority shown on the notice.</p>'+link("https://www.e-zpassny.com/tbm/no-pay","NY official fees ↗")+link("https://agency.illinoistollway.com/ves","Illinois official fees ↗")+'</div>';
 }
}
window.PowerAtlasTollPenalty={render:render,setRegion:setRegion,setContext:setContext};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();