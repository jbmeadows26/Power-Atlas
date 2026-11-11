/* Market Power investigation: same visual-first interaction architecture as Dark Money.
   Every displayed measurement and legal status comes from market-power.json. */
(()=>{
"use strict";
const choices=[
 {id:"pbms",name:"Medicine",icon:"✚",tag:"PRESCRIPTION GATEKEEPERS",headline:"Who stands between you and your medicine?",
 summary:"A few pharmacy benefit managers control much of the claims pipeline. Look at their influence on networks, reimbursements and prices.",
 stages:[["CUSTOMER","Patient or health plan"],["MIDDLEMAN","Pharmacy benefit manager"],["LEVER","Drug lists & network rules"],["QUESTION","Cost & pharmacy access"]],
 gap:"Prescription share is not a measured medicine price markup. Savings and patient costs can differ by drug, plan and pharmacy."},
 {id:"beef",name:"Groceries",icon:"▥",tag:"FOOD SUPPLY POWER",headline:"Who can negotiate with the rancher?",
 summary:"Large processors buy most finished cattle. Their purchasing position may matter long before meat reaches the checkout.",
 stages:[["PRODUCER","Cattle rancher"],["BUYER","Major meatpacker"],["LEVER","Fewer competing bids"],["QUESTION","Farm & retail prices"]],
 gap:"Concentration in cattle purchases does not measure the share of your grocery bill caused by meatpacking."},
 {id:"hospitals",name:"Hospitals",icon:"✚",tag:"LOCAL HEALTHCARE MARKETS",headline:"How many hospital systems can you choose?",
 summary:"Hospital competition is local. Consolidation can change negotiations with insurers and patients' available choices.",
 stages:[["PATIENT","Care near home"],["PROVIDER","Local hospital systems"],["LEVER","Insurance negotiations"],["QUESTION","Prices & access"]],
 gap:"A metro-area concentration measure does not identify your local hospital choices or how much any individual bill increased."},
 {id:"jobs",name:"Paychecks",icon:"◇",tag:"EMPLOYER BUYER POWER",headline:"Can workers negotiate when employers are scarce?",
 summary:"Employers compete for people as buyers of labor. Local industry concentration can limit outside job offers.",
 stages:[["WORKER","Skills & time"],["BUYERS","Local employers"],["LEVER","Job alternatives"],["QUESTION","Wages & bargaining"]],
 gap:"An observed association is not a proven causal wage loss for a specific worker, employer or town."},
 {id:"search",name:"Search",icon:"◎",tag:"DIGITAL MARKET POWER",headline:"Who controls the doorway to the internet?",
 summary:"Search defaults and distribution agreements influence whether competing services can reach users.",
 stages:[["USER","Search for information"],["PLATFORM","Google Search"],["LEVER","Default agreements"],["QUESTION","Rivals & choice"]],
 gap:"A historical search share is not a current measurement. A court ruling establishes specific violations, not a universal consumer surcharge."},
 {id:"tickets",name:"Tickets",icon:"▣",tag:"LIVE EVENTS & ACCESS",headline:"Who controls your way into a concert?",
 summary:"Ticketing, venues and promotion may be connected. Keep government allegations and proposed settlements distinct from findings.",
 stages:[["FAN","Buy event access"],["BUSINESS","Ticketing & promotion"],["LEVER","Venue / platform access"],["QUESTION","Fees & competition"]],
 gap:"A proposed settlement or pending complaint is not a final finding of liability or a calculated fee overcharge."}
];
const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;};
const link=(href,txt,cls,external)=>{const a=el("a",cls,txt);a.href=href;if(external){a.target="_blank";a.rel="noopener noreferrer";}return a;};
const stateName=k=>({finding:"COURT FINDING",allegation:"ALLEGATION / PROCEEDING",measured:"MEASURED RESEARCH",context:"REGULATED STRUCTURE"}[k]||"SOURCE EVIDENCE");
const metricValue=c=>typeof c.metric==="number"?(c.unit==="~%"?"~":c.unit===">%"?">":"")+c.metric+"%":null;
function mount(host){
 if(!host||host.querySelector(".mpx"))return;
 host.classList.add("vs6-topic--mpx");
 const wrap=el("div","mpx");wrap.id="market-power-pathways";wrap.setAttribute("aria-label","Explore how market power can affect everyday life");
 const intro=el("div","mpx-intro");
 intro.append(el("span","mpx-kicker","SIX WAYS POWER REACHES YOUR LIFE"),
   el("h2","mpx-h2","The company behind the price."),
   el("p","mpx-sub","Pick a market. Trace the leverage, the evidence and what we still don't know."));
 wrap.append(intro);
 const tabs=el("div","mpx-pathways");tabs.setAttribute("role","group");tabs.setAttribute("aria-label","Choose a market power investigation");
 const buttons=new Map();
 for(const choice of choices){
  const b=el("button","mpx-path");b.type="button";b.dataset.pathway=choice.id;
  b.setAttribute("aria-pressed","false");
  b.append(el("span","mpx-path-icon",choice.icon),el("span","mpx-path-name",choice.name));
  tabs.append(b);buttons.set(choice.id,b);
 }
 wrap.append(tabs);
 const chapter=el("div","mpx-chapter");chapter.setAttribute("aria-live","polite");chapter.setAttribute("aria-atomic","true");
 const kicker=el("span","mpx-tag"),title=el("h3","mpx-title"),summary=el("p","mpx-explain");
 const measure=el("div","mpx-measure");
 const metric=el("strong","mpx-metric"),metricLabel=el("span","mpx-metric-label");
 measure.append(metric,metricLabel);
 const route=el("div","mpx-route");route.setAttribute("aria-label","Conceptual market power mechanism");
 const caption=el("p","mpx-caption","Concept map: these are mechanisms to investigate, not proof that every step caused the next.");
 const split=el("div","mpx-evidence");
 const recorded=el("div","mpx-fact"),gap=el("div","mpx-gap");
 const knownState=el("span","mpx-state mpx-state--filed","● SOURCE EVIDENCE");
 const gapState=el("span","mpx-state mpx-state--gap","◌ NOT ESTABLISHED");
 const knownBody=el("p"),gapBody=el("p");
 recorded.append(knownState,knownBody);gap.append(gapState,gapBody);split.append(recorded,gap);
 const actions=el("div","mpx-actions");
 const deep=link("#","Explore all evidence →","mpx-mainlink");
 const original=link("#","Original source ↗","mpx-sourcelink",true);
 actions.append(deep,original);
 const status=el("small","mpx-coverage");
 chapter.append(kicker,title,summary,measure,route,caption,split,actions,status);
 wrap.append(chapter);
 const bridge=el("div","mpx-bridge");
 bridge.append(el("div","mpx-bridge-copy","Want to follow the consequences?"));
 const bridgeLinks=el("div","mpx-bridge-links");
 bridgeLinks.append(link("corporate-ownership.html","Who owns what? →"),
    link("my-life.html#why","Effects on daily life →"),
    link("consumer-practices.html","Consumer Watch →"),
    link("reform-lab.html","What could change? →"));
 bridge.append(bridgeLinks);wrap.append(bridge);
 const disclosure=el("details","mpx-method");
 disclosure.append(el("summary",null,"What counts as evidence of market power?"),
  el("p",null,"First define the actual product, buyer and geography. Compare competition, prices, wages, access, quality and alternative explanations. A measured concentration ratio is not proof of illegal conduct or a household overcharge; an allegation is not a finding."));
 wrap.append(disclosure);
 const cta=host.querySelector(".vs6-expand");
 if(cta)host.insertBefore(wrap,cta);else host.append(wrap);
 let cases=new Map();
 function select(id){
  const t=choices.find(x=>x.id===id)||choices[0],c=cases.get(t.id);if(!c)return;
  for(const [key,b] of buttons)b.setAttribute("aria-pressed",String(key===t.id));
  kicker.textContent=t.tag+" · "+stateName(c.kind);
  title.textContent=t.headline;summary.textContent=t.summary;
  metric.replaceChildren();
  const val=metricValue(c);
  metric.textContent=val||"Source record";
  metricLabel.textContent=c.metricLabel+" · "+c.period;
  measure.dataset.kind=c.kind;
  route.replaceChildren();
  for(const [i,step] of t.stages.entries()){
   const node=el("div","mpx-node"+(i===t.stages.length-1?" mpx-node--question":""));
   node.append(el("small",null,step[0]),el("strong",null,step[1]));route.append(node);
   if(i<t.stages.length-1)route.append(el("span","mpx-route-arrow","→"));
  }
  knownState.textContent="● "+stateName(c.kind);
  knownBody.textContent=val?val+" "+c.metricLabel+". "+c.period+".":c.metricLabel+". "+c.status+".";
  gapBody.textContent=t.gap;
  deep.href="market-power.html?case="+encodeURIComponent(c.id)+"#explore";
  deep.textContent="Open "+c.name+" case →";
  original.href=c.source;original.textContent="Original "+c.topic+" evidence ↗";
  status.textContent="Market: "+c.scope+" · Evidence status: "+c.status+".";
 }
 tabs.addEventListener("click",e=>{const b=e.target.closest("button[data-pathway]");if(b&&tabs.contains(b))select(b.dataset.pathway);});
 const requested=new URLSearchParams(location.search).get("story");
 fetch("./market-power.json",{cache:"no-store"})
   .then(r=>{if(!r.ok)throw Error("Source unavailable");return r.json();})
   .then(data=>{if(data.schema!=="power-atlas.market-power.v1"||!Array.isArray(data.cases))throw Error("Incorrect source schema");
     cases=new Map(data.cases.map(c=>[c.id,c]));select(choices.some(c=>c.id===requested)?requested:"pbms");
     if(location.hash==="#market-power-pathways")requestAnimationFrame(()=>wrap.scrollIntoView({block:"start",behavior:"auto"}));
   })
   .catch(()=>{chapter.replaceChildren(el("p","mpx-explain","The evidence register did not load. You can still open the original twelve-case research explorer below."));});
}
window.PowerAtlasMarketPower={mount};
})();