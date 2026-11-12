/* Power Atlas: poverty guideline vs modeled living costs.
   County-specific illustration, never a real ZIP estimate, eligibility test
   or individualized household budget. Static cited evidence only. */
(()=>{"use strict";
const URL="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/affordability/bergen-basic-needs-2026.json";
const SUPPORTED_ZIP="07010";
const fmt=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0});
const labels={
 "one-adult-0":"1 adult · no children",
 "one-adult-1":"1 adult · 1 child",
 "two-adults-one-worker-1":"2 adults · 1 working · 1 child",
 "two-adults-both-working-1":"2 adults · 2 working · 1 child",
 "two-adults-one-worker-2":"2 adults · 1 working · 2 children",
 "two-adults-both-working-2":"2 adults · 2 working · 2 children"
};
const costs=[
 ["Housing","housing"],["Food","food"],["Transportation","transportation"],
 ["Medical","medical"],["Internet & mobile","internetMobile"],
 ["Civic participation","civic"],["Other necessities","otherNecessities"],["Paid childcare","childcare"]
];
const e=(tag,klass,label)=>{const node=document.createElement(tag);if(klass)node.className=klass;if(label!==undefined)node.textContent=label;return node;};
let dataset=null,requested=false,zip="";
let panel,body,choice,sourceLinks;
function init(){
 if(document.getElementById("pa-basic-needs"))return;
 const anchor=document.querySelector("main #what");
 if(!anchor)return;
 panel=e("section","pa-basic-needs");
 panel.id="pa-basic-needs";
 panel.hidden=true;
 panel.setAttribute("aria-labelledby","pa-basic-needs-title");
 const head=e("div","pa-basic-head");
 const titleWrap=e("div");
 titleWrap.append(e("span","pa-basic-kicker","POWER ATLAS · WHAT LIFE REALLY COSTS"),
 e("h2",null,"Above poverty. Still short."),
 e("p",null,"The federal guideline and the local cost of essentials answer different questions. Compare them side by side."));
 head.append(titleWrap);
 const country=e("span","pa-basic-scope","COUNTY MODEL · NOT AN INDIVIDUAL BUDGET");
 head.append(country);
 const controls=e("div","pa-basic-controls");
 const label=e("label",null,"Household situation");
 label.htmlFor="pa-basic-family";
 choice=e("select","pa-basic-select");
 choice.id="pa-basic-family";
 for(const [key,text] of Object.entries(labels)){
  const opt=e("option",null,text);opt.value=key;
  if(key==="two-adults-one-worker-1")opt.selected=true;
  choice.append(opt);
 }
 choice.addEventListener("change",draw);
 controls.append(label,choice);
 body=e("div","pa-basic-body");
 body.setAttribute("aria-live","polite");
 const disclosure=e("details","pa-basic-disclosure");
 disclosure.append(e("summary",null,"What's included—and what's missing?"));
 disclosure.append(e("p",null,
   "MIT models minimum adequate needs at county level, not current asking rent or what a particular family actually pays. The HHS federal guideline is an administrative threshold. A federal poverty guideline is different from the Census Bureau's official statistical poverty threshold."));
 const details=e("p",null,
   "Modeled needs may exclude debt repayment, savings, retirement, leisure, unpaid leave and emergencies. For a household with two adults and one worker, MIT assumes the other adult provides childcare without paid care costs—unpaid labor and lost earnings are not valued here.");
 disclosure.append(details);
 sourceLinks=e("div","pa-basic-sources");
 const btn=e("a",null,"HHS 2026 guidelines ↗");
 btn.href="https://aspe.hhs.gov/poverty-guidelines";btn.target="_blank";btn.rel="noopener noreferrer";
 const mit=e("a",null,"MIT local living-wage model ↗");
 mit.href="https://livingwage.mit.edu/counties/34003";mit.target="_blank";mit.rel="noopener noreferrer";
 sourceLinks.append(btn,mit);
 panel.append(head,controls,body,disclosure,sourceLinks);
 anchor.insertAdjacentElement("beforebegin",panel);
}
function unavailable(){
 if(!panel)return;
 panel.hidden=false;
 choice.disabled=true;body.replaceChildren();
 body.append(e("p","pa-basic-unavailable",
   "No verified local basic-needs model is connected for this ZIP yet. The national poverty guideline alone cannot establish what it costs to live here."));
 const locator=e("a",null,"Find your county's MIT estimate ↗");
 locator.href="https://livingwage.mit.edu/";locator.rel="noopener noreferrer";locator.target="_blank";
 body.append(locator);
}
function validate(doc){
 if(doc?.schema!=="power-atlas.local-basic-needs-gap.2026.v1"||
    doc.year!==2026||doc.location?.countyFips!=="34003"||
    doc.location?.verifiedZipExample!==SUPPORTED_ZIP||
    !Array.isArray(doc.scenarios)||doc.scenarios.length<4)throw Error("Unverified local affordability dataset");
 for(const s of doc.scenarios){
  if(!(s.gross>0&&s.hhs>0&&s.net>0&&s.taxes>0&&Math.abs(s.gross-s.net-s.taxes)<=2))throw Error("Inconsistent local needs amount");
  if(s.expenseBreakdown){
   const sum=Object.values(s.expenseBreakdown).reduce((a,b)=>a+b,0);
   if(sum!==s.net)throw Error("Basic-needs component mismatch");
  }
 }
 return doc;
}
function bar(label,value,max,isHHS){
 const wrap=e("div","pa-basic-track-row");
 const item=e("div","pa-basic-track-header");
 item.append(e("span",null,label),e("strong",null,fmt.format(value)));
 const track=e("div","pa-basic-track");
 track.setAttribute("role","img");
 track.setAttribute("aria-label",label+" "+fmt.format(value)+" per year");
 const fill=e("span","pa-basic-track-fill"+(isHHS?" pa-basic-track-fill--hhs":""));
 fill.style.width=(100*value/max).toFixed(1)+"%";
 track.append(fill);wrap.append(item,track);return wrap;
}
function draw(){
 if(!dataset||!body||!choice)return;
 const s=dataset.scenarios.find(s=>s.id===choice.value);
 if(!s)return;
 body.replaceChildren();
 const amounts=e("div","pa-basic-headlines");
 const tile=e("div","pa-basic-amount");
 tile.append(e("span",null,"Federal poverty guideline"),e("strong",null,fmt.format(s.hhs)),e("small",null,"HHS 2026 · annual"));
 const budget=e("div","pa-basic-amount pa-basic-amount--needed");
 budget.append(e("span",null,"Estimated local basic needs"),e("strong",null,fmt.format(s.gross)),e("small",null,"MIT 2026 · annual, before taxes"));
 amounts.append(tile,budget);
 body.append(amounts);
 const bars=e("div","pa-basic-bars");
 bars.append(bar("Federal guideline",s.hhs,s.gross,true),bar("Local basic-needs estimate",s.gross,s.gross,false));
 body.append(bars);
 const insight=e("p","pa-basic-insight");
 const multiple=(s.gross/s.hhs).toFixed(2);
 const difference=s.gross-s.hhs;
 insight.append(e("strong",null,multiple+"× the federal guideline"),
   document.createTextNode(" · "+fmt.format(difference)+" higher annually in this modeled comparison."));
 body.append(insight);
 const foot=e("p","pa-basic-note",
   dataset.location.county+", "+dataset.location.state+
   " · Countywide MIT model; not a ZIP-specific listing price, paycheck estimate, or eligibility determination.");
 body.append(foot);
 if(s.expenseBreakdown){
  const detail=e("details","pa-basic-expense-detail");
  detail.append(e("summary",null,"Explore what goes into this budget"));
  const list=e("div","pa-basic-expense-list");
  for(const [name,key] of costs){
   const value=s.expenseBreakdown[key];
   const entry=e("div","pa-basic-expense");
   entry.append(e("span",null,name),e("strong",null,fmt.format(value)));
   list.append(entry);
  }
  detail.append(list,e("p",null,"Expenses shown after taxes; annual income before taxes also covers estimated taxes. Paid childcare is modeled as $0 when the second adult provides unpaid care."));
  body.append(detail);
 }
}
async function load(){
 if(requested)return;
 requested=true;
 try{
  const r=await fetch(URL,{cache:"force-cache"});
  if(!r.ok)throw Error("No published local basic-needs dataset");
  dataset=validate(await r.json());
  if(zip===SUPPORTED_ZIP){choice.disabled=false;draw();}
 }catch(_){
  if(zip===SUPPORTED_ZIP){choice.disabled=true;body.replaceChildren(e("p",null,"The local basic-needs model cannot be verified right now. No estimate has been substituted."));}
 }
}
function onZip(event){
 const newZip=event?.detail?.zip;
 if(!/^\d{5}$/.test(newZip||""))return;
 zip=newZip;
 if(!panel)init();
 if(!panel)return;
 if(zip!==SUPPORTED_ZIP){unavailable();return;}
 panel.hidden=false;
 choice.disabled=!dataset;
 if(dataset)draw();
 else{
  body.replaceChildren(e("p","pa-basic-loading","Loading independently sourced local cost benchmarks…"));
  load();
 }
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
window.addEventListener("poweratlas:zip-visual-context",onZip);
})();