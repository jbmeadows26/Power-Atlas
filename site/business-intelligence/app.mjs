import {setupDecisions} from "./decision-ui.mjs";
import {validateDecisions} from "./decisions.mjs";
import {setupDocuments} from "./documents.mjs";
import {setupAdaptive} from "../private-workspace/adaptive-ui.mjs";
import {setupSuppliers} from "./suppliers.mjs";
import {setupProcurement} from "./procurement.mjs";
import {feeds,products,corridors,marketTopics,validFeed,validateProfile,analyze,publicContext,currency,scenario} from "./engine.mjs";
const $=id=>document.getElementById(id),data={},errors={};
let applied=null,result=null,busy=false,serial=0;
const adaptive=setupAdaptive();
const procurement=setupProcurement();let procurementLoaded=false;
const suppliers=setupSuppliers();let suppliersLoaded=false;
function el(tag,value,cls){const n=document.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;return n;}
function option(select,value,label){const n=el("option",label);n.value=value;select.append(n);}
function label(parent,caption,input){const n=el("label",caption);n.append(input);parent.append(n);}
function select(items){const s=el("select");option(s,"","Not provided");for(const [v,l] of items)option(s,v,l);return s;}
function input(type,max){const n=el("input");n.type=type;n.autocomplete="off";if(max)n.maxLength=max;return n;}
function dep(value=null){
 if($("dependencies").children.length>=30){$("profile-status").textContent="Maximum 30 dependencies.";return;}
 const n=el("div",undefined,"dep");n.dataset.id=value?.id||crypto.randomUUID();n.provenance=value?.provenance||null;const title=el("div",undefined,"section-head");title.append(el("h3","Dependency "+(++serial)));
 const rm=el("button","Remove","secondary");rm.type="button";rm.onclick=()=>{n.remove();invalidate();};title.append(rm);n.append(title);
 const g=el("div",undefined,"formgrid"),name=input("text",80),country=input("text",2),product=select(Object.entries(products)),corridor=select(corridors.map(x=>[x,x])),cost=input("number");
 cost.min="0";cost.max="10000000000";cost.step="any";name.dataset.field="name";country.dataset.field="country";product.dataset.field="product";corridor.dataset.field="corridor";cost.dataset.field="monthlyCost";
 label(g,"Dependency label",name);label(g,"Origin country (ISO alpha-2)",country);label(g,"Product group",product);label(g,"Shipping corridor",corridor);label(g,"Actual monthly USD cost (optional)",cost);n.append(g);n.addEventListener("input",invalidate);$("dependencies").append(n);if(value)for(const field of n.querySelectorAll("[data-field]"))field.value=value[field.dataset.field]??"";invalidate();
}
function invalidate(){applied=null;result=null;$("profile-status").textContent="Profile changed. Analyze again to use the current inputs.";render();}
function profile(){return validateProfile({type:$("business-type").value,marketTopic:$("market-topic").value,financing:$("financing").checked,usDemand:$("us-demand").checked,dependencies:[...$("dependencies").children].map(n=>{const d={id:n.dataset.id,provenance:n.provenance};for(const f of n.querySelectorAll("[data-field]")){if(!f.validity.valid)throw Error("Correct the invalid dependency input.");d[f.dataset.field]=f.dataset.field==="monthlyCost"?(f.value===""?null:Number(f.value)):f.value;}return d;})});}
function route(){const h=location.hash.slice(1),id=["overview","profile","decisions","scenarios","procurement","suppliers","evidence"].includes(h)?h:"overview";for(const x of document.querySelectorAll("[data-screen]"))x.hidden=x.dataset.screen!==id;for(const a of document.querySelectorAll("nav a")){if(a.hash==="#"+id)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");}if(id==="procurement"&&!procurementLoaded){procurementLoaded=true;procurement.load();}if(id==="suppliers"&&!suppliersLoaded){suppliersLoaded=true;suppliers.load();}scrollTo(0,0);}
function proof(e){const p=el("p"),a=el("a",e.label+" · "+e.source+" · "+e.date);a.href=e.url;a.target="_blank";a.rel="noopener noreferrer";p.append(a);return p;}
const decisionMount=el("section",undefined,"panel");decisionMount.id="decision-journal";$("decisions").append(decisionMount);
const decisionJournal=setupDecisions(decisionMount);
function finding(x){const box=el("details",undefined,"finding"),s=el("summary");s.append(el("small",x.domain+" · "+x.status,"tag"),el("h3",x.title));if(x.dependency)s.append(el("small",x.dependency));box.append(s,el("p",x.detail),el("h3","Management check"),el("p",x.action));for(const e of x.evidence)box.append(proof(e));decisionJournal.attach(box,x);return box;}
function render(){
 if(applied){try{result=analyze(data,applied);}catch{result=null;$("profile-status").textContent="Source format changed. Analysis unavailable; no findings inferred.";}}
 const items=result?.findings||[],gaps=result?.gaps||[];
 adaptive.setItems(items);
 $("feed-count").textContent=Object.keys(data).length+" / "+Object.keys(feeds).length;$("dep-count").textContent=applied?String(applied.dependencies.length):"—";$("finding-count").textContent=result?String(items.length):"—";$("gap-count").textContent=result?String(gaps.length):"—";
 const priority=$("priority");priority.replaceChildren();const actionable=items.filter(x=>x.status.includes("watch")||x.status.includes("candidate")||x.status==="Upstream elevated watch");
 if(actionable.length)for(const x of actionable.slice(0,8))priority.append(finding(x));else{const e=el("p",applied?"No matched watch or quote-review candidate in the retrieved evidence. This is not an all-clear.":"Declare actual business dependencies to receive matching intelligence.","empty"),a=el("a","Map exposures ›");a.href="#profile";e.append(document.createElement("br"),a);priority.append(e);}
 const context=$("context");context.replaceChildren();for(const x of publicContext(data)){const n=el("div",undefined,"source");n.append(el("small",x.title),el("h3",x.value));if(x.evidence)n.append(proof(x.evidence));context.append(n);}if(!context.children.length)context.append(el("p","Current public indicators unavailable.","empty"));
 const domain=$("domain"),old=domain.value;domain.replaceChildren();option(domain,"","All domains");for(const x of [...new Set(items.map(r=>r.domain))])option(domain,x,x);domain.value=[...domain.options].some(o=>o.value===old)?old:"";
 const f=$("findings");f.replaceChildren();for(const x of items.filter(x=>!domain.value||x.domain===domain.value))f.append(finding(x));if(!f.children.length)f.append(el("p","No evidence-supported match for this selection.","empty"));
 const g=$("gaps");g.replaceChildren();for(const x of gaps)g.append(el("p",x,"source"));if(!gaps.length)g.append(el("p",applied?"No specific gap identified by matching rules. Coverage remains limited.":"No profile evaluated.","empty"));
 const sources=$("sources");sources.replaceChildren();for(const [k,def] of Object.entries(feeds)){const box=el("div",undefined,"source"),a=el("a",def.title);a.href="https://github.com/jbmeadows26/Power-Atlas/blob/main/"+def.path;a.target="_blank";a.rel="noopener noreferrer";box.append(a,el("p",data[k]?"Retrieved · "+data[k][def.array].length+" records · source vintage varies":errors[k]||"Awaiting retrieval"));sources.append(box);}
 const sel=$("scenario-dep"),previous=sel.value;sel.replaceChildren();option(sel,"","Choose dependency");for(const d of applied?.dependencies||[])if(d.monthlyCost!==null)option(sel,d.id,d.name);if([...sel.options].some(x=>x.value===previous))sel.value=previous;renderScenario();
}
function renderScenario(){const d=applied?.dependencies.find(x=>x.id===$("scenario-dep").value),quote=$("quote"),v=quote.value!==""&&quote.validity.valid?Number(quote.value):null,s=d?scenario(d.monthlyCost,v):null;$("base").textContent=d?currency(d.monthlyCost):"—";$("monthly").textContent=s?currency(s.monthly):"—";$("annual").textContent=s?currency(s.annual):"—";$("scenario-note").textContent=s?"Conditional on the entered quote change and unchanged volume for 12 months. No saving or loss independently verified.":"A scenario is conditional, not a forecast or verified saving.";}
async function refresh(){if(busy)return;busy=true;$("refresh").disabled=true;$("status").textContent="Retrieving public intelligence…";await Promise.all(Object.entries(feeds).map(async ([k,f])=>{try{const r=await fetch("https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/"+f.path,{cache:"no-store",credentials:"omit",referrerPolicy:"no-referrer",signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error("Source unavailable");const x=await r.json();if(!validFeed(k,x))throw Error("Source format changed");data[k]=x;delete errors[k];}catch{delete data[k];errors[k]="Unavailable; no data inferred";}}));busy=false;$("refresh").disabled=false;$("status").textContent=Object.keys(data).length+" of "+Object.keys(feeds).length+" public feeds retrieved · "+new Date().toLocaleString()+". Not a guarantee of current observations.";render();}
for(const t of marketTopics)option($("market-topic"),t,t);
for(const id of ["business-type","market-topic","financing","us-demand"])$(id).addEventListener("input",invalidate);
$("add").onclick=()=>dep();$("apply").onclick=()=>{try{applied=profile();$("profile-status").textContent="Exposure evaluated in this tab.";render();location.hash="decisions";}catch(e){$("profile-status").textContent=e.message;}};
$("clear").onclick=()=>{decisionJournal.reset();adaptive.reset();procurement.reset();suppliers.reset();for(const id of ["business-type","market-topic","quote"])$(id).value="";for(const id of ["financing","us-demand"])$(id).checked=false;$("dependencies").replaceChildren();serial=0;invalidate();$("profile-status").textContent="Private inputs cleared.";};
$("domain").onchange=render;$("quote").oninput=renderScenario;$("scenario-dep").onchange=renderScenario;$("refresh").onclick=refresh;
addEventListener("hashchange",route);route();render();refresh();setInterval(()=>{if(document.visibilityState==="visible")refresh();},300000);


import {setupVault} from "../private-workspace/vault-ui.mjs";
function validateVaultBusiness(value){
 if(!value||typeof value!=="object"||Array.isArray(value)||typeof value.type!=="string"||typeof value.marketTopic!=="string"||typeof value.financing!=="boolean"||typeof value.usDemand!=="boolean"||!Array.isArray(value.dependencies)||value.dependencies.length>30)throw Error("Invalid business profile backup.");
 for(const d of value.dependencies){
  if(!d||typeof d.name!=="string"||typeof d.country!=="string"||typeof d.product!=="string"||typeof d.corridor!=="string"||!(d.monthlyCost===null||typeof d.monthlyCost==="number"))throw Error("Invalid business dependency in backup.");
 }
 return {...validateProfile(value),decisions:validateDecisions(value.decisions??[])};
}
function restoreVaultBusiness(p){
 $("clear").click();
 $("business-type").value=p.type;$("market-topic").value=p.marketTopic;$("financing").checked=p.financing;$("us-demand").checked=p.usDemand;
 for(const d of p.dependencies){
  dep(d);const row=$("dependencies").lastElementChild;
  for(const input of row.querySelectorAll("[data-field]"))input.value=d[input.dataset.field]??"";
 }
 decisionJournal.restore(p.decisions??[]);applied=validateProfile(p);render();$("profile-status").textContent="Restored locally from an encrypted profile.";
}
const vaultMount=el("section",undefined,"panel");vaultMount.id="business-vault";$("profile").append(vaultMount);
const businessVault=setupVault({mount:vaultMount,scope:"business",getProfile:()=>({...profile(),decisions:decisionJournal.get()}),validate:validateVaultBusiness,restore:restoreVaultBusiness,clearProfile:()=>$("clear").click()});
$("clear").addEventListener("click",()=>businessVault.reset());

const documentMount=el("section",undefined,"panel");documentMount.id="business-documents";$("profile").append(documentMount);
const documents=setupDocuments({mount:documentMount,products,approve:d=>{if($("dependencies").children.length>=30)throw Error("Remove a dependency first; maximum 30.");dep(d);}});
$("clear").addEventListener("click",()=>documents.reset());
